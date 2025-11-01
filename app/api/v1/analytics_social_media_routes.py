from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.analytics.shared.models import Analytic, AnalyticDevice, Device
from typing import Optional

router = APIRouter()

@router.get("/analytics/{analytic_id}/social-media-correlation")
def social_media_correlation(
    analytic_id: int,
    platform: Optional[str] = Query("Instagram", description='Platform filter: "Instagram", "Facebook", "WhatsApp", "TikTok", "Telegram", "X"'),
    db: Session = Depends(get_db),
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        return JSONResponse(
            {"status": 404, "message": f"Analytic with ID {analytic_id} not found", "data": {}},
            status_code=404
        )
    
    if analytic.method != "Social Media Correlation":
        return JSONResponse(
            content={
                "status": 400, 
                "message": f"This endpoint is only for Social Media Correlation. Current analytic method is '{analytic.method}'", 
                "data": None
            },
            status_code=400,
        )
    device_links = (
        db.query(AnalyticDevice)
        .filter(AnalyticDevice.analytic_id == analytic_id)
        .all()
    )
    if not device_links:
        return JSONResponse(
            {"status": 404, "message": "No devices found for this analytic", "data": {}},
            status_code=404
        )

    device_ids = []
    for link in device_links:
        device_ids.extend(link.device_ids)
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()

    if not devices:
        return JSONResponse(
            {"status": 404, "message": "Devices not found", "data": {}},
            status_code=404
        )

    # Normalize platform name
    platform_lower = (platform or "Instagram").lower().strip()
    platform_map = {
        "instagram": "instagram",
        "facebook": "facebook",
        "whatsapp": "whatsapp",
        "tiktok": "tiktok",
        "telegram": "telegram",
        "x": "x",
        "twitter": "x"
    }
    selected_platform = platform_map.get(platform_lower, "instagram")
    
    # Map platform to column names in new structure
    platform_column_map = {
        "instagram": {"id_col": "instagram_id", "platform_name": "instagram"},
        "whatsapp": {"id_col": "whatsapp_id", "platform_name": "whatsapp"},
        "telegram": {"id_col": "telegram_id", "platform_name": "telegram"},
        "x": {"id_col": "X_id", "platform_name": "x"},
        "facebook": {"id_col": "facebook_id", "platform_name": "facebook"},
        "tiktok": {"id_col": "tiktok_id", "platform_name": "tiktok"}
    }
    
    platform_info = platform_column_map.get(selected_platform, platform_column_map["instagram"])
    id_column = platform_info["id_col"]
    platform_display = platform_info["platform_name"]
    
    # Validate id_column to prevent SQL injection (only allow known columns)
    allowed_columns = ["instagram_id", "whatsapp_id", "telegram_id", "X_id", "facebook_id", "tiktok_id"]
    if id_column not in allowed_columns:
        id_column = "instagram_id"
        platform_display = "instagram"
    
    # Build SQL query dynamically based on platform
    sql_query = text(f"""
        WITH 
        device_file_ids AS (
            SELECT DISTINCT 
                d.id AS device_id, 
                d.file_id,
                d.owner_name,
                d.phone_number,
                ROW_NUMBER() OVER (ORDER BY d.id) as device_num,
                CASE 
                    WHEN ROW_NUMBER() OVER (ORDER BY d.id) <= 26 
                    THEN CHR(64 + ROW_NUMBER() OVER (ORDER BY d.id)::INTEGER)
                    ELSE CHR(64 + ((ROW_NUMBER() OVER (ORDER BY d.id)::INTEGER - 26) / 26)) || 
                         CHR(64 + ((ROW_NUMBER() OVER (ORDER BY d.id)::INTEGER - 26) % 26))
                END AS device_label
            FROM devices d
            INNER JOIN analytic_device ad ON d.id = ANY(ad.device_ids)
            WHERE ad.analytic_id = :analytic_id
        ),
        social_accounts AS (
            SELECT 
                -- account_identifier: gunakan platform_id jika ada, fallback ke account_name
                LOWER(TRIM(COALESCE(sm.{id_column}::TEXT, sm.account_name, ''))) AS account_identifier,
                -- display_name: gunakan account_name, fallback ke platform_id
                COALESCE(sm.account_name, sm.{id_column}::TEXT, '') AS display_name,
                '{platform_display}' AS platform,
                dfi.device_id,
                dfi.device_label,
                dfi.owner_name AS device_owner,
                dfi.phone_number AS device_phone,
                dfi.device_num,
                sm.file_id
            FROM social_media sm
            INNER JOIN device_file_ids dfi ON sm.file_id = dfi.file_id
            WHERE 
                sm.{id_column} IS NOT NULL
                AND (
                    sm.account_name IS NOT NULL AND TRIM(sm.account_name) != '' AND LOWER(TRIM(sm.account_name)) NOT IN ('nan', 'none', 'null')
                    OR sm.{id_column} IS NOT NULL
                )
        ),
        account_device_counts AS (
            SELECT 
                account_identifier,
                display_name,
                platform,
                COUNT(DISTINCT device_id) AS device_count,
                ARRAY_AGG(DISTINCT device_id ORDER BY device_id) AS device_ids,
                STRING_AGG(DISTINCT device_owner, ', ' ORDER BY device_owner) AS device_owners
            FROM social_accounts
            GROUP BY account_identifier, display_name, platform
            HAVING COUNT(DISTINCT device_id) >= 2
        )
        SELECT 
            adc.account_identifier,
            adc.display_name AS account_name,
            adc.platform,
            adc.device_count AS total_connections,
            adc.device_owners,
            sa.device_label,
            sa.device_id,
            sa.device_owner,
            sa.device_phone,
            sa.device_num
        FROM account_device_counts adc
        INNER JOIN social_accounts sa ON 
            adc.account_identifier = sa.account_identifier 
            AND adc.platform = sa.platform
        ORDER BY 
            adc.device_count DESC,
            adc.display_name ASC,
            sa.device_num ASC
    """)
    
    # Execute query
    query_result = db.execute(
        sql_query, 
        {"analytic_id": analytic_id, "selected_platform": selected_platform}
    ).fetchall()
    
    # Process query results
    device_order = sorted(devices, key=lambda d: d.id)
    device_label_map = {}
    device_labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    for idx, d in enumerate(device_order):
        if idx < len(device_labels):
            device_label_map[d.id] = device_labels[idx]
        else:
            first_char = chr(65 + (idx - 26) // 26)
            second_char = chr(65 + (idx - 26) % 26)
            device_label_map[d.id] = f"{first_char}{second_char}"
    
    # Group results by account and device
    account_info_map = {}  # account_identifier -> {display_name, device_count, devices: [device_ids]}
    account_device_map = {}  # account_identifier -> {device_id: {device_label, device_owner, device_phone}}
    
    for row in query_result:
        account_id = row.account_identifier
        if account_id not in account_info_map:
            account_info_map[account_id] = {
                'display_name': row.account_name,
                'device_count': row.total_connections,
                'devices': set()
            }
        account_info_map[account_id]['devices'].add(row.device_id)
        
        if account_id not in account_device_map:
            account_device_map[account_id] = {}
        account_device_map[account_id][row.device_id] = {
            'device_label': row.device_label,
            'device_owner': row.device_owner,
            'device_phone': row.device_phone
        }
    
    # Build devices_data with connected accounts only
    devices_data = []
    for d in device_order:
        connected_accounts = []
        for account_id, account_info in sorted(account_info_map.items(), key=lambda x: x[1]['device_count'], reverse=True):
            if d.id in account_info['devices']:
                connected_accounts.append({
                    "account_id": account_id,
                    "account_name": account_info['display_name'],
                    "device_count": account_info['device_count']
                })
        devices_data.append({
            "device_label": device_label_map.get(d.id),
            "device_id": d.id,
            "owner_name": d.owner_name,
            "phone_number": d.phone_number,
            "created_at": str(d.created_at),
            "accounts": connected_accounts
        })

    total_devices = len(device_order)
    platform_display_map = {
        "instagram": "Instagram",
        "facebook": "Facebook",
        "whatsapp": "WhatsApp",
        "tiktok": "TikTok",
        "telegram": "Telegram",
        "x": "X"
    }
    
    if total_devices < 2:
        # Return only selected platform (empty buckets)
        platform_display_name = platform_display_map.get(selected_platform, "Instagram")
        return JSONResponse(
            {
                "status": 200,
                "message": f"Success analyzing social media correlation for '{analytic.analytic_name}'",
                "data": {
                    "analytic_id": analytic.id,
                    "analytic_name": analytic.analytic_name,
                    "total_devices": total_devices,
                    "devices": devices_data,
                    "correlations": {
                        platform_display_name: {"buckets": []}
                    },
                    "summary": getattr(analytic, 'summary', None)
                }
            },
            status_code=200
        )

    # Build correlation buckets: group by account, showing which devices share it
    correlations = {}
    buckets = []
    
    # Process accounts from SQL query results, sorted by device_count
    for account_id, account_info in sorted(account_info_map.items(), key=lambda x: x[1]['device_count'], reverse=True):
        display_name = account_info['display_name']
        device_list = sorted(list(account_info['devices']))
        device_count = account_info['device_count']
        
        # Build device details from account_device_map
        device_details = []
        for dev_id in device_list:
            if dev_id in account_device_map[account_id]:
                device_info = account_device_map[account_id][dev_id]
                device_details.append({
                    "device_label": device_info['device_label'],
                    "device_id": dev_id,
                    "owner_name": device_info['device_owner'],
                    "phone_number": device_info['device_phone']
                })
        
        if not device_details:
            continue
        
        # Anchor device is the first device in sorted order
        anchor_device = device_details[0]
        # Matched devices are all other devices
        matched_devices = device_details[1:] if len(device_details) > 1 else []
        
        buckets.append({
            "label": f"{device_count} koneksi",
            "device_label": anchor_device['device_label'],
            "device_owner": anchor_device['owner_name'],
            "analyzed_account": display_name,
            "account_id": account_id,
            "total_connections": device_count,
            "connected_accounts": [display_name],
            "matched_devices": [
                {
                    "device_label": m["device_label"],
                    "device_id": m["device_id"],
                    "owner_name": m["owner_name"],
                    "matched_account": display_name,
                    "interaction_count": 1
                }
                for m in matched_devices
            ]
        })

    buckets_sorted = buckets  # Already sorted by device_count
    platform_display_name = platform_display_map.get(selected_platform, "Instagram")
    # Only return selected platform (no empty buckets for other platforms)
    correlations[platform_display_name] = {"buckets": buckets_sorted}

    return JSONResponse(
        {
            "status": 200,
            "message": f"Success analyzing social media correlation for '{analytic.analytic_name}'",
            "data": {
                "analytic_id": analytic.id,
                "analytic_name": analytic.analytic_name,
                "total_devices": total_devices,
                "devices": devices_data,
                "correlations": correlations,
                "summary": analytic.summary if hasattr(analytic, 'summary') and analytic.summary else None
            }
        },
        status_code=200
    )
