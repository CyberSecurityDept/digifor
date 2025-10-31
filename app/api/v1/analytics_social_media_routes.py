from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, AnalyticDevice, Device, SocialMedia
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

    file_ids = [d.file_id for d in devices if getattr(d, 'file_id', None) is not None]
    file_id_to_device_id = {d.file_id: d.id for d in devices if getattr(d, 'file_id', None) is not None}

    social_accounts = (
        db.query(SocialMedia)
        .filter(SocialMedia.file_id.in_(file_ids))
        .all()
    )

    device_labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    device_order = sorted(devices, key=lambda d: d.id)
    device_label_map = {}
    for idx, d in enumerate(device_order):
        if idx < len(device_labels):
            device_label_map[d.id] = device_labels[idx]
        else:
            first_char = chr(65 + (idx - 26) // 26)
            second_char = chr(65 + (idx - 26) % 26)
            device_label_map[d.id] = f"{first_char}{second_char}"

    platform_names = ["instagram", "facebook", "whatsapp", "tiktok", "telegram", "x"]
    accounts_by_device_platform = {d.id: {p: set() for p in platform_names} for d in devices}
    account_to_devices = {p: {} for p in platform_names}
    for acc in social_accounts:
        platform_raw = (acc.platform or "").lower()
        if platform_raw not in platform_names:
            continue
        dev_id = file_id_to_device_id.get(getattr(acc, 'file_id', None))
        if not dev_id:
            continue
        name = (acc.account_name or acc.account_id or "").strip()
        if not name:
            continue
        accounts_by_device_platform[dev_id][platform_raw].add(name)
        s = account_to_devices[platform_raw].setdefault(name, set())
        s.add(dev_id)

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
    
    devices_data = []
    for d in device_order:
        connected_accounts = set()
        for name in accounts_by_device_platform.get(d.id, {}).get(selected_platform, set()):
            if len(account_to_devices[selected_platform].get(name, set())) >= 2:
                connected_accounts.add(name)
        devices_data.append({
            "device_label": device_label_map.get(d.id),
            "device_id": d.id,
            "owner_name": d.owner_name,
            "phone_number": d.phone_number,
            "created_at": str(d.created_at),
            "accounts": sorted(list(connected_accounts))
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

    correlations = {}
    buckets = []
    for anchor in device_order:
        anchor_accounts_raw = accounts_by_device_platform.get(anchor.id, {}).get(selected_platform, set())
        anchor_accounts = {acc for acc in anchor_accounts_raw if len(account_to_devices[selected_platform].get(acc, set())) >= 2}
        if not anchor_accounts:
            continue
        matched_devices = []
        connected_contacts = set()
        for other in device_order:
            if other.id == anchor.id:
                continue
            other_accounts = accounts_by_device_platform.get(other.id, {}).get(selected_platform, set())
            inter = anchor_accounts.intersection(other_accounts)
            if inter:
                matched_devices.append({
                    "device_label": device_label_map.get(other.id),
                    "device_id": other.id,
                    "owner_name": other.owner_name,
                    "matched_account": sorted(list(inter))[0],
                    "interaction_count": len(inter)
                })
                connected_contacts.update(inter)
        if matched_devices:
            total_connections = 1 + len(matched_devices)
            buckets.append({
                "label": f"{total_connections} koneksi",
                "device_label": device_label_map.get(anchor.id),
                "device_owner": anchor.owner_name,
                "analyzed_account": sorted(list(anchor_accounts))[0],
                "total_connections": total_connections,
                "connected_contacts": sorted(list(connected_contacts)),
                "matched_devices": matched_devices
            })

    buckets_sorted = sorted(buckets, key=lambda b: b.get("total_connections", 0), reverse=True)
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
