from fastapi import APIRouter, Depends, Query  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from sqlalchemy import or_, and_  # type: ignore
from app.db.session import get_db
from app.analytics.analytics_management.service import store_analytic, get_all_analytics
from app.analytics.shared.models import Device, Analytic, AnalyticDevice, File, Contact
from app.analytics.device_management.models import HashFile
from app.analytics.analytics_management.models import ApkAnalytic
from typing import List, Optional
from pydantic import BaseModel  # type: ignore
from app.utils.timezone import get_indonesia_time
from app.core.config import settings
from datetime import datetime

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
            "Deep communication analytics",
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

@hashfile_router.get("/analytic/{analytic_id}/hashfile-analytics")
def get_hashfile_analytics(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    try:
        min_devices = 2
        
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                content={"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )
        
        if analytic.method != "Hashfile Analytics":
            return JSONResponse(
                content={
                    "status": 400, 
                    "message": f"This endpoint is only for Hashfile Analytics. Current analytic method is '{analytic.method}'", 
                    "data": None
                },
                status_code=400,
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).all()
        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        device_ids = list(set(device_ids))
        
        if not device_ids:
            return JSONResponse(
                content={"status": 400, "message": "No devices linked to this analytic", "data": None},
                status_code=400,
            )

        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        device_info = {
            d.id: {
                "id": d.id,
                "owner_name": d.owner_name,
                "phone_number": d.phone_number,
                "device_name": getattr(d, 'device_name', d.owner_name)
            }
            for d in devices
        }
        
        file_ids = [d.file_id for d in devices]
        
        device_labels = []
        for i, device in enumerate(devices):
            if i < 26:
                device_label = f"Device {chr(65 + i)}"
            else:
                first_char = chr(65 + (i - 26) // 26)
                second_char = chr(65 + (i - 26) % 26)
                device_label = f"Device {first_char}{second_char}"
            device_labels.append(device_label)

        hashfiles = db.query(HashFile).filter(
            HashFile.file_id.in_(file_ids)
        ).all()

        hashfile_groups = {}
        for hashfile in hashfiles:
            hash_value = hashfile.md5_hash or hashfile.sha1_hash
            if hash_value:
                if hash_value not in hashfile_groups:
                    hashfile_groups[hash_value] = {
                        "hash_value": hash_value,
                        "md5_hash": hashfile.md5_hash or "",
                        "sha1_hash": hashfile.sha1_hash or "",
                        "file_path": hashfile.path_original,
                        "file_kind": hashfile.kind or "Unknown",
                        "file_size_bytes": hashfile.size_bytes or 0,
                        "file_type": hashfile.file_type,
                        "file_extension": hashfile.file_extension,
                        "is_suspicious": hashfile.is_suspicious == "True" if hashfile.is_suspicious else False,
                        "risk_level": hashfile.risk_level or "Low",
                        "source_type": hashfile.source_type,
                        "source_tool": hashfile.source_tool,
                        "devices": set(),
                        "hashfile_records": []
                    }

                hashfile_device_id = None
                for d in devices:
                    if d.file_id == hashfile.file_id:
                        hashfile_device_id = d.id
                        break
                if hashfile_device_id:
                    hashfile_groups[hash_value]["devices"].add(hashfile_device_id)
                hashfile_groups[hash_value]["hashfile_records"].append(hashfile)

        common_hashfiles = {
            hash_value: info for hash_value, info in hashfile_groups.items() 
            if len(info["devices"]) >= min_devices
        }

        hashfile_list = []
        for hash_value, info in common_hashfiles.items():
            hashfile_records = info["hashfile_records"]
            device_hashfiles = {}
            
            for record in hashfile_records:
                hashfile_device_id = None
                for d in devices:
                    if d.file_id == record.file_id:
                        hashfile_device_id = d.id
                        break
                if hashfile_device_id:
                    device_hashfiles[hashfile_device_id] = record
            
            first_record = hashfile_records[0] if hashfile_records else None
            if not first_record:
                continue
                
            file_size_bytes = first_record.size_bytes or 0
            if file_size_bytes > 0:
                formatted_size = f"{file_size_bytes:,}".replace(",", ".")
                if file_size_bytes >= 1024 * 1024 * 1024:
                    size_display = f"{file_size_bytes / (1024 * 1024 * 1024):.1f} GB"
                elif file_size_bytes >= 1024 * 1024:
                    size_mb = file_size_bytes / (1000 * 1000)
                    size_display = f"{size_mb:.1f} MB"
                elif file_size_bytes >= 1024:
                    size_display = f"{file_size_bytes / 1024:.1f} KB"
                else:
                    size_display = f"{file_size_bytes} bytes"
                file_size_display = f"{formatted_size} ({size_display} on disk)"
            else:
                file_size_display = "Unknown size"

            if first_record.created_at:
                created_at = first_record.created_at.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                created_at = "Unknown"

            if first_record.updated_at:
                modified_at = first_record.updated_at.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                modified_at = "Unknown"

            device_labels_for_hashfile = []
            for i, device in enumerate(devices):
                if device.id in info["devices"]:
                    device_labels_for_hashfile.append(device_labels[i])
            
            file_path = first_record.path_original or "Unknown"
            file_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1] if '\\' in file_path else file_path
            
            file_type = first_record.file_type or "Unknown"
            if first_record.file_extension:
                file_type = f"{file_type} ({first_record.file_extension.upper()})"
            
            general_info = {
                "kind": first_record.kind or "Unknown",
                "size": file_size_display,
                "where": file_path,
                "created": created_at.replace('T', ' ').replace('-', ' '),
                "modified": modified_at.replace('T', ' ').replace('-', ' '),
                "stationery_pad": False,
                "locked": first_record.is_suspicious == "True" if first_record.is_suspicious else False
            }
            
            hashfile_data = {
                "hash_value": hash_value,
                "file_name": file_name,
                "file_type": file_type,
                "file_size": size_display if file_size_bytes > 0 else "Unknown",
                "file_path": file_path,
                "created_at": created_at,
                "modified_at": modified_at,
                "devices": device_labels_for_hashfile,
                "general_info": general_info
            }
            
            hashfile_list.append(hashfile_data)

        hashfile_list.sort(key=lambda x: len(x["devices"]), reverse=True)

        devices_list = []
        for i, device in enumerate(devices):
            devices_list.append({
                "device_label": device_labels[i],
                "owner_name": device.owner_name,
                "phone_number": device.phone_number
            })

        summary = analytic.summary if analytic.summary else None

        return JSONResponse(
            content={
                "status": 200,
                "message": "Hashfile correlation analysis completed successfully",
                "data": {
                    "devices": devices_list,
                    "hashfiles": hashfile_list,
                    "summary": summary
                }
            },
            status_code=200,
        )

    except Exception as e:
        return JSONResponse(
            content={"status": 500, "message": f"Failed to get hashfile analytics: {str(e)}", "data": None},
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
        elif method == "Deep communication analytics":
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
        else:
            return JSONResponse(
                {
                    "status": 200,
                    "message": f"Data extraction completed for method: {method}",
                    "data": {
                        "analytic_id": analytic.id,
                        "method": method,
                        "device_count": len(device_ids),
                        "status": "completed"
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
                    # Include the entire day by adding 23:59:59
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

