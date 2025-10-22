from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.analytics_management.service import store_analytic, get_all_analytics
from app.analytics.shared.models import Device, Analytic, AnalyticDevice, File
from typing import List
from pydantic import BaseModel

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

@router.get("/analytics/get-all-analytic")
def get_all_analytic(db: Session = Depends(get_db)):
    try:
        analytics = get_all_analytics(db)
        return {
            "status": 200,
            "message": f"Retrieved {len(analytics)} analytics successfully",
            "data": analytics
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal mengambil data: {str(e)}",
            "data": []
        }




class CreateAnalyticWithDevicesRequest(BaseModel):
    analytic_name: str
    method: str
    device_ids: List[int]

@router.post("/analytics/create-analytic-with-devices")
def create_analytic_with_devices(
    data: CreateAnalyticWithDevicesRequest, 
    db: Session = Depends(get_db)
):
    try:
        if not data.analytic_name.strip():
            return {
                "status": 400,
                "message": "analytic_name wajib diisi",
                "data": []
            }

        valid_methods = [
            "Contact Correlation",
            "Deep Communication", 
            "Social Media Correlation",
            "Hashfile Analytics",
            "APK Analytics"
        ]
        
        if data.method not in valid_methods:
            return {
                "status": 400,
                "message": f"Invalid method. Must be one of: {valid_methods}",
                "data": []
            }

        existing_devices = db.query(Device).filter(Device.id.in_(data.device_ids)).all()
        existing_device_ids = [d.id for d in existing_devices]
        missing_device_ids = [did for did in data.device_ids if did not in existing_device_ids]
        
        if missing_device_ids:
            return {
                "status": 400,
                "message": f"Devices not found: {missing_device_ids}",
                "data": []
            }

        new_analytic = store_analytic(
            db=db,
            analytic_name=data.analytic_name,
            type=data.method,
            method=data.method,
        )

        linked_count = 0
        already_linked = 0
        
        for device_id in data.device_ids:
            existing_link = db.query(AnalyticDevice).filter(
                AnalyticDevice.analytic_id == new_analytic.id,
                AnalyticDevice.device_id == device_id
            ).first()
            
            if existing_link:
                already_linked += 1
                continue
                
            new_link = AnalyticDevice(
                analytic_id=new_analytic.id,
                device_id=device_id
            )
            db.add(new_link)
            linked_count += 1
        
        db.commit()

        devices_info = []
        for device in existing_devices:
            devices_info.append({
                "device_id": device.id,
                "owner_name": device.owner_name,
                "phone_number": device.phone_number,
                "device_name": device.device_name
            })

        result = {
            "analytic": {
                "id": new_analytic.id,
                "analytic_name": new_analytic.analytic_name,
                "type": new_analytic.type,
                "method": new_analytic.method,
                "summary": new_analytic.summary,
                "created_at": str(new_analytic.created_at)
            },
            "linked_devices": {
                "total_devices": len(data.device_ids),
                "linked_count": linked_count,
                "already_linked": already_linked,
                "devices": devices_info
            }
        }

        return {
            "status": 200,
            "message": f"Analytics created and {linked_count} devices linked successfully",
            "data": result
        }

    except Exception as e:
        db.rollback()
        return {
            "status": 500,
            "message": f"Gagal membuat analytic dengan devices: {str(e)}",
            "data": []
        }

