from fastapi import APIRouter, Depends, Query, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.db.session import get_db
from app.analytics.analytics_management.service import store_analytic, get_all_analytics
from app.analytics.shared.models import Device, Analytic, AnalyticDevice, File, Contact
from app.analytics.device_management.models import HashFile
from app.analytics.analytics_management.models import ApkAnalytic
from typing import List, Optional
from pydantic import BaseModel
from app.utils.timezone import get_indonesia_time
from app.core.config import settings
from datetime import datetime, date, time
import logging, os
from collections import defaultdict
from app.auth.models import User
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

def check_analytic_access(analytic: Analytic, current_user) -> bool:
    if current_user is None:
        return False
    
    user_role = getattr(current_user, 'role', None)
    if user_role == "admin":
        return True
    
    user_fullname = getattr(current_user, 'fullname', '') or ''
    user_email = getattr(current_user, 'email', '') or ''
    analytic_name = analytic.analytic_name or ''
    analytic_summary = analytic.summary or ''
    analytic_created_by = analytic.created_by or ''
    
    return (user_fullname.lower() in analytic_name.lower() or 
            user_email.lower() in analytic_name.lower() or
            user_fullname.lower() in analytic_summary.lower() or 
            user_email.lower() in analytic_summary.lower() or
            user_fullname.lower() in analytic_created_by.lower() or 
            user_email.lower() in analytic_created_by.lower())

def parse_date_string(date_str: str) -> datetime:
    try:
        parsed = datetime.strptime(date_str, "%d/%m/%Y")
        if parsed.day > 31:
            return datetime.strptime(date_str, "%m/%d/%Y")
        return parsed
    except ValueError:
        pass
    
    try:
        return datetime.strptime(date_str, "%m/%d/%Y")
    except ValueError:
        pass
    
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass
    
    raise ValueError(f"Invalid date format: {date_str}. Supported formats: DD/MM/YYYY, MM/DD/YYYY, or YYYY-MM-DD")

class SummaryRequest(BaseModel):
    summary: str

def format_file_size(size_bytes):
    if size_bytes is None:
        return None
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

router = APIRouter()

hashfile_router = APIRouter(tags=["Hashfile Analytics"])

@router.post("/analytics/start-analyzing")
def create_analytic_with_devices(
    analytic_name: str = Form(...),
    method: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not analytic_name.strip():
            return JSONResponse(
                content={
                "status": 400,
                "message": "analytic_name wajib diisi",
                "data": []
                },
                status_code=400
            )

        valid_methods = [
            "Deep Communication Analytics",
            "Social Media Correlation",
            "Contact Correlation",
            "APK Analytics",
            "Hashfile Analytics"
        ]
        
        if method not in valid_methods:
            return JSONResponse(
                content={
                "status": 400,
                "message": f"Invalid method. Must be one of: {valid_methods}",
                "data": []
                },
                status_code=400
            )

        # Add user information to created_by field for access control filtering
        user_fullname = getattr(current_user, 'fullname', '') or ''
        user_email = getattr(current_user, 'email', '') or ''
        created_by_info = f"Created by: {user_fullname} ({user_email})" if user_fullname or user_email else ""
        
        new_analytic = store_analytic(
            db=db,
            analytic_name=analytic_name,
            method=method,
            created_by=created_by_info
        )
        
        db.commit()
        db.refresh(new_analytic)

        result = {
            "analytic": {
                "id": new_analytic.id,
                "analytic_name": new_analytic.analytic_name,
                "method": new_analytic.method,
                "summary": new_analytic.summary,
                "created_at": str(new_analytic.created_at)
            }
        }

        return JSONResponse(
            content={
                "status": 200,
                "message": "Analytics created successfully",
                "data": result
            },
            status_code=200
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating analytic: {str(e)}")
        return JSONResponse(
            content={
                "status": 500,
                "message": f"Gagal membuat analytic: {str(e)}",
                "data": None
            },
            status_code=500
        )
    
def _get_hashfile_analytics_data(
    analytic_id: int,
    db: Session,
    current_user=None
):
    try:
        min_devices = 2
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                {"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )
        
        if current_user is not None and not check_analytic_access(analytic, current_user):
            return JSONResponse(
                {"status": 403, "message": "You do not have permission to access this analytic", "data": None},
                status_code=403,
            )
        method_value = analytic.method
        if method_value is None or str(method_value) != "Hashfile Analytics":
            return JSONResponse(
                {
                    "status": 400,
                    "message": f"This endpoint is only for Hashfile Analytics. Current method: '{analytic.method}'",
                    "data": None,
                },
                status_code=400,
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).all()

        device_ids = list({d for link in device_links for d in link.device_ids})
        if not device_ids:
            return JSONResponse(
                {"status": 400, "message": "No devices linked to this analytic", "data": None},
                status_code=400,
            )

        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        if not devices:
            return JSONResponse(
                {"status": 404, "message": "No valid devices found", "data": None},
                status_code=404,
            )

        device_labels = []
        for i in range(len(devices)):
            if i < 26:
                device_labels.append(f"Device {chr(65 + i)}")
            else:
                first = chr(65 + (i // 26) - 1)
                second = chr(65 + (i % 26))
                device_labels.append(f"Device {first}{second}")

        file_ids = [d.file_id for d in devices]
        file_to_device = {d.file_id: d.id for d in devices}

        hashfiles = (
            db.query(
                HashFile.file_id,
                HashFile.file_name,
                HashFile.md5_hash,
                HashFile.sha1_hash,
                HashFile.path_original,
                HashFile.size_bytes,
                HashFile.file_type,
                HashFile.source_tool,
                HashFile.created_at_original,
                HashFile.modified_at_original,
            )
            .filter(HashFile.file_id.in_(file_ids))
            .filter(or_(HashFile.md5_hash != None, HashFile.sha1_hash != None))
            .all()
        )

        devices_list_empty = [
            {
                "device_label": device_labels[i],
                "owner_name": d.owner_name,
                "phone_number": d.phone_number,
            }
            for i, d in enumerate(devices)
        ]
        
        if not hashfiles:
            summary_value = analytic.summary
            summary = summary_value if summary_value is not None else None
            return JSONResponse(
                content={
                    "status": 200,
                    "message": "No hashfile data found",
                    "data": {
                        "devices": devices_list_empty,
                        "correlations": [],
                        "summary": summary,
                        "total_correlations": 0
                    }
                },
                status_code=200,
            )

        print(f"[DEBUG] Found {len(hashfiles)} hashfiles for file_ids: {file_ids}")
        print(f"[DEBUG] Devices: {[{'id': d.id, 'file_id': d.file_id, 'owner': d.owner_name} for d in devices]}")
        
        correlation_map: dict[str, dict[str, list | set]] = defaultdict(lambda: {"records": [], "devices": set()})

        for hf in hashfiles:
            hash_value = hf.md5_hash or hf.sha1_hash
            if not hash_value:
                continue

            if not hf.file_name:
                continue
            
            key = f"{hash_value}::{hf.file_name.strip().lower()}"
            device_id = file_to_device.get(hf.file_id)
            if device_id is None:
                continue

            records_list = correlation_map[key]["records"]
            if isinstance(records_list, list):
                records_list.append(hf)
            devices_set = correlation_map[key]["devices"]
            if isinstance(devices_set, set):
                devices_set.add(device_id)

        logger.info(f"Total correlation keys (unique hash+filename combinations): {len(correlation_map)}")
        
        sample_keys = list(correlation_map.items())[:5]
        for key, data in sample_keys:
            hash_part, filename_part = key.split("::", 1) if "::" in key else (key[:20], "unknown")
            logger.debug(f"Sample correlation key - Hash: {hash_part[:20]}..., Filename: {filename_part[:30]}..., "
                        f"Devices: {len(data['devices'])}, Records: {len(data['records'])}")

        correlated = {
            key: data for key, data in correlation_map.items()
            if len(data["devices"]) >= min_devices
        }
        
        logger.info(f"Correlated items (appearing in >= {min_devices} devices): {len(correlated)}")
        
        total_hashfiles_before_filter = len(hashfiles)
        total_unique_keys = len(correlation_map)
        total_correlated_keys = len(correlated)
        logger.info(f"Hashfile Analytics Statistics:")
        logger.info(f"  - Total hashfiles found: {total_hashfiles_before_filter}")
        logger.info(f"  - Unique hash+filename combinations: {total_unique_keys}")
        logger.info(f"  - Correlated (>= {min_devices} devices): {total_correlated_keys}")
        logger.info(f"  - Filtered out (single device only): {total_unique_keys - total_correlated_keys}")

        hashfile_list = []
        for key, info in correlated.items():
            records_list = info["records"]
            if not isinstance(records_list, list) or len(records_list) == 0:
                continue
            first = records_list[0]
            device_ids_found = info["devices"]

            file_size_bytes = first.size_bytes or 0
            if file_size_bytes >= 1024**3:
                size_display = f"{file_size_bytes / (1024**3):.1f} GB"
            elif file_size_bytes >= 1024**2:
                size_display = f"{file_size_bytes / (1024**2):.1f} MB"
            elif file_size_bytes >= 1024:
                size_display = f"{file_size_bytes / 1024:.1f} KB"
            else:
                size_display = f"{file_size_bytes} bytes"

            file_path = first.path_original or "Unknown"
            file_name = os.path.basename(file_path) if file_path != "Unknown" else (first.file_name or "Unknown")
            file_type = first.file_type or "Unknown"

            device_labels_found = [
                device_labels[i]
                for i, d in enumerate(devices)
                if d.id in device_ids_found
            ]

            hash_value = first.md5_hash or first.sha1_hash
            hashfile_list.append({
                "hash_value": hash_value,
                "file_name": first.file_name or file_name,
                "file_type": file_type,
                "devices": device_labels_found,
            })

        hashfile_list.sort(key=lambda x: len(x["devices"]), reverse=True)
        total_correlations = len(hashfile_list)
        logger.info(f"Returning {total_correlations} correlated hashfiles (sorted by number of devices)")

        if hashfile_list:
            sample = hashfile_list[0]
            logger.info(f"Sample correlation - Filename: {sample.get('file_name', 'Unknown')[:50]}, "
                       f"Hash: {sample.get('hash_value', 'Unknown')[:20]}..., "
                       f"Devices: {sample.get('devices', [])}")

        devices_list = [
            {
                "device_label": device_labels[i],
                "owner_name": d.owner_name,
                "phone_number": d.phone_number,
            }
            for i, d in enumerate(devices)
        ]

        summary_value = analytic.summary
        summary = summary_value if summary_value is not None else None
        return JSONResponse(
            content={
                "status": 200,
                "message": "Hashfile correlation completed successfully",
                "data": {
                    "devices": devices_list,
                    "correlations": hashfile_list,
                    "summary": summary,
                    "total_correlations": total_correlations
                },
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error getting hashfile analytics: {str(e)}")
        return JSONResponse(
            content={
                "status": 500,
                "message": f"Failed to get hashfile analytics: {str(e)}",
                "data": None,
            },
            status_code=500,
        )

@hashfile_router.get("/analytics/hashfile-analytics")
def get_hashfile_analytics(
    analytic_id: int = Query(..., description="Analytic ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return _get_hashfile_analytics_data(analytic_id, db, current_user)


@router.post("/analytics/start-extraction")
def start_data_extraction(
    analytic_id: int = Query(..., description="Analytic ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                {"status": 404, "message": "Analytic not found", "data": []},
                status_code=404
            )
        
        if current_user is not None and not check_analytic_access(analytic, current_user):
            return JSONResponse(
                {"status": 403, "message": "You do not have permission to access this analytic", "data": []},
                status_code=403
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).all()

        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        device_ids = list(set(device_ids))
        
        if len(device_ids) < 2:
            return JSONResponse(
                {
                    "status": 400,
                    "message": f"Minimum 2 devices required. Currently have {len(device_ids)} device(s)",
                    "data": {
                        "device_count": len(device_ids),
                        "required": 2
                    }
                },
                status_code=400
            )

        method_value = analytic.method
        method_str = str(method_value) if method_value is not None else ""
        
        if method_str == "Contact Correlation":
            return JSONResponse(
                {
                    "status": 200,
                    "message": f"Data extraction completed {method_str}",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method_str,
                        "device_count": len(device_ids),
                        "status": "completed",
                        "next_step": f"GET /api/v1/analytic/{analytic_id}/contact-correlation"
                    }
                },
                status_code=200
            )
        elif method_str == "Hashfile Analytics":
            return JSONResponse(
                {
                    "status": 200,
                    "message": f"Data extraction completed {method_str}",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method_str,
                        "device_count": len(device_ids),
                        "status": "completed",
                        "next_step": f"GET /api/v1/analytic/{analytic_id}/hashfile-analytics"
                    }
                },
                status_code=200
            )
        elif method_str == "Deep Communication Analytics":
            return JSONResponse(
                {
                    "status": 200,
                    "message": f"Data extraction completed {method_str}",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method_str,
                        "device_count": len(device_ids),
                        "status": "completed",
                        "next_step": f"GET /api/v1/analytic/deep-communication-analytics?analytic_id={analytic_id}"
                    }
                },
                status_code=200
            )
        elif method_str == "Social Media Correlation":
            return JSONResponse(
                {
                    "status": 200,
                    "message": f"Data extraction completed {method_str}",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method_str,
                        "device_count": len(device_ids),
                        "status": "completed",
                        "next_step": f"GET /api/v1/analytics/social-media-correlation?analytic_id={analytic_id}"
                    }
                },
                status_code=200
            )
        else:
            return JSONResponse(
                {
                    "status": 400,
                    "message": f"Unsupported method: {method_str}. Supported methods: Contact Correlation, Hashfile Analytics, Deep Communication Analytics, Social Media Correlation",
                    "data": None
                },
                status_code=400
            )

    except Exception as e:
        logger.error(f"Error starting data extraction: {str(e)}")
        return JSONResponse(
            content={
                "status": 500,
                "message": f"Failed to start data extraction: {str(e)}",
                "data": None
            },
            status_code=500
        )

@router.get("/analytics/get-all-analytic")
def get_all_analytic(
    search: Optional[str] = Query(None, description="Search by analytics name, method, or notes (summary)"),
    method: Optional[str] = Query(None, description="Filter by method"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Analytic)
        
        user_role = getattr(current_user, 'role', None)
        if user_role != "admin":
            user_fullname = getattr(current_user, 'fullname', '') or ''
            user_email = getattr(current_user, 'email', '') or ''
            if user_fullname or user_email:
                query = query.filter(
                    or_(
                        Analytic.analytic_name.ilike(f"%{user_fullname}%"),
                        Analytic.analytic_name.ilike(f"%{user_email}%"),
                        Analytic.summary.ilike(f"%{user_fullname}%"),
                        Analytic.summary.ilike(f"%{user_email}%"),
                        Analytic.created_by.ilike(f"%{user_fullname}%"),
                        Analytic.created_by.ilike(f"%{user_email}%")
                    )
                )

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Analytic.analytic_name.ilike(search_pattern),
                    Analytic.method.ilike(search_pattern),
                    Analytic.summary.ilike(search_pattern)
                )
            )

        if method:
            query = query.filter(Analytic.method == method)

        analytics = query.order_by(Analytic.created_at.desc()).all()

        formatted_analytics = [
            {
                "id": a.id,
                "analytic_name": a.analytic_name,
                "method": a.method,
                "summary": a.summary,
                "date": a.created_at.strftime("%d/%m/%Y") if a.created_at is not None else None
            }
            for a in analytics
        ]

        return JSONResponse(
            content={
                "status": 200,
                "message": f"Retrieved {len(formatted_analytics)} analytics successfully",
                "data": formatted_analytics
            },
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error getting all analytics: {str(e)}")
        return JSONResponse(
            content={
                "status": 500,
                "message": f"Gagal mengambil data: {str(e)}",
                "data": None
            },
            status_code=500
        )

__all__ = ["router", "hashfile_router"]

