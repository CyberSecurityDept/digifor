from fastapi import APIRouter, Depends, Query
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
from datetime import datetime
from datetime import datetime 
import os

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


class CreateAnalyticWithDevicesRequest(BaseModel):
    analytic_name: str
    method: str

@router.post("/analytics/start-analyzing")
def create_analytic_with_devices(
    data: CreateAnalyticWithDevicesRequest, 
    db: Session = Depends(get_db)
):
    try:
        if not data.analytic_name.strip():
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
        
        if data.method not in valid_methods:
            return JSONResponse(
                content={
                "status": 400,
                "message": f"Invalid method. Must be one of: {valid_methods}",
                "data": []
                },
                status_code=400
            )

        new_analytic = store_analytic(
            db=db,
            analytic_name=data.analytic_name,
            method=data.method,
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

        return {
            "status": 200,
            "message": "Analytics created successfully",
            "data": result
        }

    except Exception as e:
        db.rollback()
        return {
            "status": 500,
            "message": f"Gagal membuat analytic: {str(e)}",
            "data": []
        }
    
@hashfile_router.get("/analytic/{analytsic_id}/hashfile-analytics")
def get_hashfile_analytics(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    try:
        min_devices = 2

        # ==============================================
        # 1️⃣ Validasi Analytic
        # ==============================================
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                {"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )
        if analytic.method != "Hashfile Analytics":
            return JSONResponse(
                {
                    "status": 400,
                    "message": f"This endpoint is only for Hashfile Analytics. Current method: '{analytic.method}'",
                    "data": None,
                },
                status_code=400,
            )

        # ==============================================
        # 2️⃣ Ambil semua device terkait analytic
        # ==============================================
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

        # Buat label (Device A, B, C, ...)
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

        # ==============================================
        # 3️⃣ Ambil HashFile dari semua file_id
        # ==============================================
        hashfiles = (
            db.query(
                HashFile.file_id,
                HashFile.name,
                HashFile.md5_hash,
                HashFile.sha1_hash,
                HashFile.path_original,
                HashFile.kind,
                HashFile.size_bytes,
                HashFile.file_type,
                HashFile.file_extension,
                HashFile.is_suspicious,
                HashFile.risk_level,
                HashFile.source_tool,
                HashFile.created_at_original,
                HashFile.modified_at_original,
            )
            .filter(HashFile.file_id.in_(file_ids))
            .filter(or_(HashFile.md5_hash != None, HashFile.sha1_hash != None))
            .all()
        )

        if not hashfiles:
            return JSONResponse(
                {"status": 200, "message": "No hashfile data found", "data": {"devices": [], "hashfiles": []}},
                status_code=200,
            )

        # ==============================================
        # 4️⃣ Bangun correlation: berdasarkan hash + name
        # ==============================================
        from collections import defaultdict

        correlation_map = defaultdict(lambda: {"records": [], "devices": set()})

        for hf in hashfiles:
            hash_value = hf.md5_hash or hf.sha1_hash
            if not hash_value or not hf.name:
                continue

            key = f"{hash_value}::{hf.name.strip().lower()}"  # unik per kombinasi hash+name
            device_id = file_to_device.get(hf.file_id)
            if not device_id:
                continue

            correlation_map[key]["records"].append(hf)
            correlation_map[key]["devices"].add(device_id)

        # ==============================================
        # 5️⃣ Filter: hanya muncul di >= min_devices
        # ==============================================
        correlated = {
            key: data for key, data in correlation_map.items()
            if len(data["devices"]) >= min_devices
        }

        # ==============================================
        # 6️⃣ Format hasil untuk frontend
        # ==============================================
        hashfile_list = []
        for key, info in correlated.items():
            first = info["records"][0]
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
            file_name = os.path.basename(file_path) if file_path != "Unknown" else (first.name or "Unknown")
            file_type = first.file_type or "Unknown"
            if first.file_extension:
                file_type = f"{file_type} ({first.file_extension.upper()})"

            device_labels_found = [
                device_labels[i]
                for i, d in enumerate(devices)
                if d.id in device_ids_found
            ]

            hash_value = first.md5_hash or first.sha1_hash
            hashfile_list.append({
                "hash_value": hash_value,
                "file_name": first.name or file_name,
                "file_type": file_type,
                # "file_size": size_display,
                # "file_path": file_path,
                # "created_at": (
                #     first.created_at_original.strftime("%Y-%m-%d %H:%M:%S")
                #     if first.created_at_original else "Unknown"
                # ),
                # "modified_at": (
                #     first.modified_at_original.strftime("%Y-%m-%d %H:%M:%S")
                #     if first.modified_at_original else "Unknown"
                # ),
                "devices": device_labels_found,
            })

        # Urutkan berdasarkan jumlah devices yang terlibat
        hashfile_list.sort(key=lambda x: len(x["devices"]), reverse=True)

        # ==============================================
        # 7️⃣ Build device list
        # ==============================================
        devices_list = [
            {
                "device_label": device_labels[i],
                "owner_name": d.owner_name,
                "phone_number": d.phone_number,
            }
            for i, d in enumerate(devices)
        ]

        # ==============================================
        # 8️⃣ Response
        # ==============================================
        summary = analytic.summary if analytic.summary else None
        return JSONResponse(
            {
                "status": 200,
                "message": "Hashfile correlation (by hash + name) completed successfully",
                "data": {
                    "devices": devices_list,
                    "correlations": hashfile_list,
                    "summary": summary,
                },
            },
            status_code=200,
        )

    except Exception as e:
        return JSONResponse(
            {
                "status": 500,
                "message": f"Failed to get hashfile analytics: {str(e)}",
                "data": None,
            },
            status_code=500,
        )


@router.post("/analytics/{analytic_id}/start-extraction")
def start_data_extraction(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    try:
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                {"status": 404, "message": "Analytic not found", "data": []},
                status_code=404
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

        method = analytic.method
        
        if method == "Contact Correlation":
            return JSONResponse(
                {
                    "status": 200,
                    "message": "Data extraction completed. Use GET /analytic/{analytic_id}/contact-correlation to retrieve results",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method,
                        "device_count": len(device_ids),
                        "status": "completed",
                        "next_step": f"GET /api/v1/analytic/{analytic_id}/contact-correlation"
                    }
                },
                status_code=200
            )
        elif method == "Hashfile Analytics":
            return JSONResponse(
                {
                    "status": 200,
                    "message": "Data extraction completed. Use GET /analytic/{analytic_id}/hashfile-analytics to retrieve results",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method,
                        "device_count": len(device_ids),
                        "status": "completed",
                        "next_step": f"GET /api/v1/analytic/{analytic_id}/hashfile-analytics"
                    }
                },
                status_code=200
            )
        elif method == "Deep Communication Analytics":
            return JSONResponse(
                {
                    "status": 200,
                    "message": "Data extraction completed. Use GET /analytic/{analytic_id}/deep-communication-analytics to retrieve results",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method,
                        "device_count": len(device_ids),
                        "status": "completed",
                        "next_step": f"GET /api/v1/analytic/{analytic_id}/deep-communication-analytics"
                    }
                },
                status_code=200
            )
        elif method == "Social Media Correlation":
            return JSONResponse(
                {
                    "status": 200,
                    "message": "Data extraction completed. Use GET /analytic/{analytic_id}/social-media-correlation to retrieve results",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method,
                        "device_count": len(device_ids),
                        "status": "completed",
                        "next_step": f"GET /api/v1/analytic/{analytic_id}/social-media-correlation"
                    }
                },
                status_code=200
            )

    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Failed to start data extraction: {str(e)}", "data": []},
            status_code=500
        )

@router.get("/analytics/get-all-analytic")
def get_all_analytic(
    search: Optional[str] = Query(None, description="Search by analytics name or notes (summary)"),
    method: Optional[str] = Query(None, description="Filter by method"),
    date_from: Optional[str] = Query(None, description="Filter by date from (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (format: YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Analytic)
        
        if search:
            search_pattern = f"%{search}%"
            search_conditions = [
                Analytic.analytic_name.ilike(search_pattern)
            ]
            search_conditions.append(
                Analytic.summary.ilike(search_pattern)
            )
            query = query.filter(or_(*search_conditions))
        
        if method:
            query = query.filter(Analytic.method == method)
        
        if date_from or date_to:
            date_conditions = []
            
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                    date_conditions.append(Analytic.created_at >= date_from_obj)
                except ValueError:
                    return JSONResponse(
                        content={
                            "status": 400,
                            "message": "Invalid date_from format. Use YYYY-MM-DD",
                            "data": []
                        },
                        status_code=400
                    )
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                    date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
                    date_conditions.append(Analytic.created_at <= date_to_obj)
                except ValueError:
                    return JSONResponse(
                        content={
                            "status": 400,
                            "message": "Invalid date_to format. Use YYYY-MM-DD",
                            "data": []
                        },
                        status_code=400
                    )
            
            if date_conditions:
                query = query.filter(and_(*date_conditions))
        
        total_count = query.count()
        
        analytics = query.order_by(Analytic.created_at.desc()).offset(skip).limit(limit).all()
        
        formatted_analytics = []
        for analytic in analytics:
            formatted_analytic = {
                "id": analytic.id,
                "analytic_name": analytic.analytic_name,
                "method": analytic.method,
                "summary": analytic.summary,
                "date": analytic.created_at.strftime("%d/%m/%Y") if analytic.created_at else None
            }
            formatted_analytics.append(formatted_analytic)
        
        return JSONResponse(
            content={
            "status": 200,
                "message": f"Retrieved {len(formatted_analytics)} analytics successfully",
                "data": formatted_analytics,
                "pagination": {
                    "total": total_count,
                    "skip": skip,
                    "limit": limit,
                    "returned": len(formatted_analytics)
        }
            },
            status_code=200
        )

    except Exception as e:
        return JSONResponse(
            content={
            "status": 500,
            "message": f"Gagal mengambil data: {str(e)}",
            "data": []
            },
            status_code=500
        )


__all__ = ["router", "hashfile_router"]

