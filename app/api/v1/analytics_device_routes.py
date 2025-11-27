from fastapi import APIRouter, Depends, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Device, File, Analytic, AnalyticDevice
from app.utils.timezone import get_indonesia_time
from typing import Optional
from sqlalchemy import or_
from app.auth.models import User
from app.api.deps import get_current_user
from app.api.v1.analytics_management_routes import check_analytic_access

router = APIRouter()

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

@router.post("/analytics/add-device")
async def add_device(
    file_id: int = Form(...),
    analytic_id: int = Form(...),
    name: str = Form(...),
    phone_number: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
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
                        "instruction": "The specified analytic was not found. Please create a new analytic."
                    }
                },
                status_code=404
            )
        
        if current_user is not None and not check_analytic_access(analytic, current_user):
            return JSONResponse(
                {"status": 403, "message": "You do not have permission to access this analytic", "data": []},
                status_code=403
            )
        
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return JSONResponse(
                {"status": 404, "message": "File not found", "data": []},
                status_code=404
            )
        
        file_method = str(file_record.method) if file_record.method is not None else ""
        analytic_method = str(analytic.method) if analytic.method is not None else ""
        if file_method != analytic_method:
            return JSONResponse(
                {
                    "status": 400, 
                    "message": f"File method '{file_method}' does not match analytic method '{analytic_method}'", 
                    "data": {
                        "file_info": {
                            "file_id": file_id,
                            "file_name": getattr(file_record, 'file_name', 'Unknown'),
                            "file_method": file_method
                        },
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": getattr(analytic, 'analytic_name', 'Unknown'),
                            "analytic_method": analytic_method
                        },
                        "next_action": "select_file",
                        "redirect_to": "/analytics/devices",
                        "instruction": f"File method '{file_method}' does not match current analytic method '{analytic_method}'. Please select a file with method '{analytic_method}' for this analytic, or create a new analytic with method '{file_method}'."
                    }
                },
                status_code=400
            )
        
        existing_links = db.query(AnalyticDevice).filter(AnalyticDevice.analytic_id == analytic_id).all()
        linked_device_ids_check = []
        for l in existing_links:
            linked_device_ids_check.extend(l.device_ids or [])
        if linked_device_ids_check:
            conflict_device = db.query(Device).filter(Device.id.in_(linked_device_ids_check), Device.file_id == file_id).first()
            if conflict_device:
                return JSONResponse(
                    {
                        "status": 400,
                        "message": "This file is already used by another device in this analytic",
                        "data": {
                            "device_id": conflict_device.id,
                            "owner_name": conflict_device.owner_name,
                            "phone_number": conflict_device.phone_number
                        }
                    },
                    status_code=400
                )

        new_device = Device(
            file_id=file_id,
            owner_name=name,
            phone_number=phone_number,
            device_name=f"{name} Device",
            created_at=get_indonesia_time()
        )
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        device = new_device
        
        existing_link = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).first()

        if existing_link:
            current_ids = list(existing_link.device_ids or [])
            device_id_value = int(device.id) if device.id is not None else None
            if device_id_value is not None and device_id_value not in current_ids:
                current_ids.append(device_id_value)
                setattr(existing_link, 'device_ids', current_ids)  
                setattr(existing_link, 'updated_at', get_indonesia_time())  
                db.add(existing_link)
        else:
            new_link = AnalyticDevice(
                analytic_id=analytic_id,
                device_ids=[device.id]
            )
            db.add(new_link)
        
        db.commit()
        
        device_links = db.query(AnalyticDevice).filter(AnalyticDevice.analytic_id == analytic_id).all()
        linked_device_ids = []
        for link in device_links:
            linked_device_ids.extend(link.device_ids or [])
        linked_device_ids = list(dict.fromkeys(linked_device_ids))

        device_item = None
        if linked_device_ids:
            devices_q = db.query(Device).filter(Device.id.in_(linked_device_ids)).order_by(Device.id).all()
            labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
            device_id_value = int(device.id) if device.id is not None else None
            if device_id_value is not None:
                idx = next((i for i, d in enumerate(devices_q) if d.id is not None and int(d.id) == device_id_value), None)
            else:
                idx = None
            if idx is not None:
                if idx < len(labels):
                    label = labels[idx]
                else:
                    first_char = chr(65 + (idx - 26) // 26)
                    second_char = chr(65 + (idx - 26) % 26)
                    label = f"{first_char}{second_char}"
                device_item = {
                    "device_label": label,
                    "device_id": device.id,
                    "owner_name": device.owner_name,
                    "phone_number": device.phone_number,
                }

        analytics_payload = [{
            "analytic_id": analytic.id,
            "analytic_name": analytic.analytic_name,
            "method": analytic.method,
            "summary": getattr(analytic, 'summary', None),
            "date": analytic.created_at.strftime("%d/%m/%Y") if getattr(analytic, 'created_at', None) else None,
            "device": [device_item] if device_item else [],
            "file_info": {
                "file_id": file_record.id,
                "file_name": file_record.file_name,
                "file_type": file_record.type,
                "notes": file_record.notes,
                "tools": file_record.tools,
                "method": file_record.method,
                "total_size": file_record.total_size,
                "total_size_formatted": format_file_size(file_record.total_size) if file_record.total_size is not None else None
            }
        }]

        return JSONResponse(
            {
                "status": 200,
                "message": "Device added successfully",
                "data": {
                    "analytics": analytics_payload
                }
            },
            status_code=200
        )
        
    except Exception as e:
        db.rollback()
        return JSONResponse(
            {"status": 500, "message": f"Failed to add device: {str(e)}", "data": []},
            status_code=500
        )

@router.get("/analytics/get-devices")
def get_devices_by_analytic_id(
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
        
        user_role = getattr(current_user, 'role', None)
        if user_role != "admin":
            user_fullname = getattr(current_user, 'fullname', '') or ''
            user_email = getattr(current_user, 'email', '') or ''
            analytic_name = analytic.analytic_name or ''
            analytic_summary = analytic.summary or ''
            analytic_created_by = analytic.created_by or ''
            if not (user_fullname.lower() in analytic_name.lower() or 
                    user_email.lower() in analytic_name.lower() or
                    user_fullname.lower() in analytic_summary.lower() or 
                    user_email.lower() in analytic_summary.lower() or
                    user_fullname.lower() in analytic_created_by.lower() or 
                    user_email.lower() in analytic_created_by.lower()):
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
        
        if not device_ids:
            return JSONResponse(
                {
                    "status": 200,
                    "message": "No devices linked to this analytic yet",
                    "data": {
                        "analytic": {
                            "id": analytic.id,
                            "analytic_name": analytic.analytic_name,
                            "method": analytic.method
                        },
                        "devices": [],
                        "device_count": 0
                    }
                },
                status_code=200
            )
        
        devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
        
        device_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        device_cards = []
        
        for i, device in enumerate(devices):
            file_record = db.query(File).filter(File.id == device.file_id).first()
            
            if i < len(device_labels):
                device_label = f"Device {device_labels[i]}"
            else:
                first_char = chr(65 + (i - 26) // 26)
                second_char = chr(65 + (i - 26) % 26)
                device_label = f"Device {first_char}{second_char}"
            
            device_card = {
                "label": device_label,
                "device_id": str(device.id) if device.id is not None else "",
                "name": device.owner_name or "",
                "phone_number": device.phone_number or "",
                "file_name": file_record.file_name if file_record else "Unknown",
                "file_size": format_file_size(file_record.total_size) if file_record is not None and file_record.total_size is not None else "0 B"
            }
            
            device_cards.append(device_card)
        
        return JSONResponse(
            {
                "status": 200,
                "message": f"Retrieved {len(device_cards)} devices for {analytic.method}" if len(device_cards) != 1 else f"Retrieved {len(device_cards)} device for {analytic.method}",
                "data": {
                    "analytic": {
                        "id": analytic.id,
                        "analytic_name": analytic.analytic_name,
                        "method": analytic.method
                    },
                    "devices": device_cards,
                    "device_count": len(device_cards)
                }
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Failed to get devices: {str(e)}", "data": []},
            status_code=500
        )