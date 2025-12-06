from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.analytics.shared.models import Analytic, AnalyticDevice, Device, SocialMedia
from typing import Optional
from app.auth.models import User
from app.api.deps import get_current_user
from app.api.v1.analytics_management_routes import check_analytic_access
from app.utils.security import validate_sql_injection_patterns, sanitize_input
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def _get_social_media_correlation_data(
    analytic_id: int,
    db: Session,
    platform: Optional[str] = "Instagram",
    current_user=None
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        return JSONResponse(
            {
                "status": 404,
                "message": f"Analytic with ID {analytic_id} not found",
                "data": {
                    "analytic_info": {
                        "analytic_id": analytic_id,
                        "analytic_name": "Unknown"
                    },
                    "next_action": "create_analytic",
                    "redirect_to": "/analytics/start-analyzing",
                    "instruction": "Please create a new analytic with method 'Social Media Correlation'"
                }
            },
            status_code=404,
        )
    
    if current_user is not None:
        if not check_analytic_access(analytic, current_user):
            return JSONResponse(
                {"status": 403, "message": "You do not have permission to access this analytic", "data": {}},
                status_code=403,
            )

    method_value = getattr(analytic, 'method', None)
    if method_value is None or str(method_value) != "Social Media Correlation":
        return JSONResponse(
            {
                "status": 400,
                "message": f"This endpoint is only for Social Media Correlation. Current analytic method is '{method_value}'",
                "data": {
                    "analytic_info": {
                        "analytic_id": analytic_id,
                        "analytic_name": getattr(analytic, 'analytic_name', None) or "Unknown",
                        "current_method": str(method_value) if method_value else None
                    },
                    "next_action": "create_analytic",
                    "redirect_to": "/analytics/start-analyzing",
                    "instruction": "Please create a new analytic with method 'Social Media Correlation'"
                },
            },
            status_code=400,
        )

    device_links = (
        db.query(AnalyticDevice)
        .filter(AnalyticDevice.analytic_id == analytic_id)
        .all()
    )
    if not device_links:
        analytic_name_value = getattr(analytic, 'analytic_name', None) or "Unknown"
        return JSONResponse(
            {
                "status": 404,
                "message": "No devices linked to this analytic",
                "data": {
                    "analytic_info": {
                        "analytic_id": analytic_id,
                        "analytic_name": analytic_name_value
                    },
                    "device_count": 0,
                    "required_minimum": 2,
                    "next_action": "add_device",
                    "redirect_to": "/analytics/devices",
                    "instruction": "Please add at least 2 devices to continue with Social Media Correlation"
                }
            },
            status_code=404,
        )

    device_ids = []
    for link in device_links:
        device_ids.extend(link.device_ids)
    device_ids = list(set(device_ids))
    
    min_devices = 2
    total_device_count = len(device_ids)
    if total_device_count < min_devices:
        analytic_name_value = getattr(analytic, 'analytic_name', None) or "Unknown"
        return JSONResponse(
            {
                "status": 404,
                "message": f"Social Media Correlation requires minimum {min_devices} devices. Current analytic has {total_device_count} device(s).",
                "data": {
                    "analytic_info": {
                        "analytic_id": analytic_id,
                        "analytic_name": analytic_name_value
                    },
                    "device_count": total_device_count,
                    "required_minimum": min_devices,
                    "next_action": "add_device",
                    "redirect_to": "/analytics/devices",
                    "instruction": f"Please add at least {min_devices} devices to continue with Social Media Correlation"
                }
            },
            status_code=404
        )

    devices = (
        db.query(Device)
        .filter(Device.id.in_(device_ids))
        .order_by(Device.id)
        .all()
    )
    if not devices:
        analytic_name_value = getattr(analytic, 'analytic_name', None) or "Unknown"
        return JSONResponse(
            {
                "status": 404,
                "message": "Devices not found for this analytic",
                "data": {
                    "analytic_info": {
                        "analytic_id": analytic_id,
                        "analytic_name": analytic_name_value
                    },
                    "device_count": 0,
                    "required_minimum": 2,
                    "next_action": "add_device",
                    "redirect_to": "/analytics/devices",
                    "instruction": "Please add at least 2 devices to continue with Social Media Correlation"
                }
            },
            status_code=404,
        )

    platform_lower = (platform or "Instagram").lower().strip()
    platform_map = {
        "instagram": "instagram",
        "facebook": "facebook",
        "whatsapp": "whatsapp",
        "tiktok": "tiktok",
        "telegram": "telegram",
        "x": "x",
        "twitter": "x",
    }
    selected_platform = platform_map.get(platform_lower, "instagram")

    id_column = f"{selected_platform}_id"
    if selected_platform == "x":
        id_column = "X_id"

    file_ids = [d.file_id for d in devices]
    socials = (
        db.query(SocialMedia)
        .filter(SocialMedia.file_id.in_(file_ids))
        .filter(SocialMedia.source.ilike(f"%{selected_platform}%"))
        .filter(
            getattr(SocialMedia, id_column).isnot(None)
            | (SocialMedia.account_name.isnot(None))
        )
        .all()
    )

    device_map = {d.file_id: d for d in devices}
    platform_display = selected_platform.capitalize()

    devices_data = [
        {
            "device_id": d.id,
            "owner_name": d.owner_name,
            "phone_number": d.phone_number,
            "device_name": getattr(d, "device_name", d.owner_name),
            "created_at": str(d.created_at),
        }
        for d in devices
    ]

    if not socials:
        return JSONResponse(
            {
                "status": 200,
                "message": f"No social media data found for platform '{selected_platform}'",
                "data": {
                    "analytic_id": analytic.id,
                    "analytic_name": analytic.analytic_name,
                    "total_devices": len(devices),
                    "devices": devices_data,
                    "correlations": {
                        platform_display: {"buckets": []}
                    },
                    "summary": getattr(analytic, "summary", None),
                },
            },
            status_code=200,
        )

    correlation_map = {}
    for sm in socials:
        platform_id_value = getattr(sm, id_column, None)
        account_name_value = sm.account_name
        
        if platform_id_value is None and account_name_value is None:
            continue

        key = platform_id_value
        if key is None or (isinstance(key, str) and str(key).lower() in ["", "nan", "none", "null"]):
            key = account_name_value
        if key is None or (isinstance(key, str) and str(key).strip() == ""):
            continue

        key = str(key).strip().lower()
        record = {
            "account_key": key,
            "account_name": sm.account_name,
            "full_name": sm.full_name,
            "platform_id": platform_id_value,
            "phone_number": sm.phone_number,
            "device": device_map.get(sm.file_id),
        }
        correlation_map.setdefault(key, []).append(record)

    bucket_map = {}
    for key, records in correlation_map.items():
        devices_present = {r["device"].id: r for r in records if r["device"]}
        if len(devices_present) < 2:
            continue

        label = f"{len(devices_present)} koneksi"
        bucket_map.setdefault(label, [])

        row = []
        for dev in devices:
            if dev.id in devices_present:
                rec = devices_present[dev.id]
                if selected_platform == "whatsapp":
                    value = rec["full_name"] or rec["phone_number"]
                else:
                    value = (
                        rec["full_name"] or 
                        rec["account_name"] or 
                        rec["platform_id"] or 
                        rec["phone_number"]
                    )
                row.append(value if value is not None else "Unknown")
            else:
                row.append("Unknown")
        bucket_map[label].append(row)

    sorted_buckets = []
    for label in sorted(
        bucket_map.keys(), key=lambda x: int(x.split()[0]), reverse=True
    ):
        sorted_buckets.append({"label": label, "devices": bucket_map[label]})

    return JSONResponse(
        {
            "status": 200,
            "message": f"Success analyzing social media correlation for '{analytic.analytic_name}'",
            "data": {
                "analytic_id": analytic.id,
                "analytic_name": analytic.analytic_name,
                "total_devices": len(devices),
                "devices": devices_data,
                "correlations": {
                    platform_display: {"buckets": sorted_buckets}
                },
                "summary": getattr(analytic, "summary", None),
            },
        },
        status_code=200,
    )

@router.get("/analytics/social-media-correlation")
def social_media_correlation(
    analytic_id: int = Query(..., description="Analytic ID"),
    platform: Optional[str] = Query(
        "Instagram",
        description='Platform filter: "Instagram", "Facebook", "WhatsApp", "TikTok", "Telegram", "X"',
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if platform:
        if not validate_sql_injection_patterns(platform):
            logger.warning(f"SQL injection attempt detected in platform: {platform[:50]}")
            return JSONResponse(
                content={
                    "status": 400,
                    "message": "Invalid characters detected in platform. Please remove any SQL injection attempts or malicious code.",
                    "data": None
                },
                status_code=400,
            )
        platform = sanitize_input(platform, max_length=50)
    
    return _get_social_media_correlation_data(analytic_id, db, platform, current_user)
