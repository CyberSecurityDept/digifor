from fastapi import APIRouter, Depends, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Device, File, Analytic, AnalyticDevice
from app.utils.timezone import get_indonesia_time
from typing import Optional
from sqlalchemy import or_

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
    name: str = Form(...),
    phone_number: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Automatically get the latest analytic (from workflow: create analytic then add device)
        latest_analytic = db.query(Analytic).order_by(Analytic.created_at.desc()).first()
        
        if not latest_analytic:
            return JSONResponse(
                {"status": 404, "message": "No analytic found. Please create an analytic first.", "data": []},
                status_code=404
            )
        
        analytic_id = latest_analytic.id
        analytic = latest_analytic
        
        # Validate file
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return JSONResponse(
                {"status": 404, "message": "File not found", "data": []},
                status_code=404
            )
        
        # Validate method match (file method must match analytic method)
        if file_record.method != analytic.method:
            return JSONResponse(
                {
                    "status": 400, 
                    "message": f"File method '{file_record.method}' does not match analytic method '{analytic.method}'", 
                    "data": []
                },
                status_code=400
            )
        
        # Check if device already exists for this file
        existing_device = db.query(Device).filter(Device.file_id == file_id).first()
        
        if existing_device:
            existing_device.owner_name = name
            existing_device.phone_number = phone_number
            existing_device.device_name = f"{name} Device"
            existing_device.updated_at = get_indonesia_time()
            
            db.commit()
            db.refresh(existing_device)
            device = existing_device
        else:
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
        
        # Link device to analytic (required for workflow)
        existing_link = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).first()
        
        if existing_link:
            # Add device_id to array if not already present
            if device.id not in existing_link.device_ids:
                existing_link.device_ids.append(device.id)
                existing_link.updated_at = get_indonesia_time()
        else:
            # Create new AnalyticDevice link
            new_link = AnalyticDevice(
                analytic_id=analytic_id,
                device_ids=[device.id]
            )
            db.add(new_link)
        
        db.commit()
        
        return JSONResponse(
            {
                "status": 200,
                "message": "Device added successfully",
                "data": {
                    "device_id": device.id,
                    "file_id": device.file_id,
                    "owner_name": device.owner_name,
                    "phone_number": device.phone_number,
                    "device_name": device.device_name,
                    "name": device.owner_name,
                    "file_name": file_record.file_name,
                    "analytic_id": analytic_id,
                    "created_at": str(device.created_at),
                    "file_info": {
                        "file_name": file_record.file_name,
                        "file_type": file_record.type,
                        "notes": file_record.notes,
                        "tools": file_record.tools,
                        "method": file_record.method,
                        "total_size": file_record.total_size,
                        "total_size_formatted": format_file_size(file_record.total_size) if file_record.total_size else None
                    }
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

@router.get("/analytics/latest/files")
def get_files_by_latest_analytic_method(
    search: Optional[str] = Query(None, description="Search by file_name, notes, tools, or method"),
    dropdown: Optional[str] = Query("All", description='Method filter: "Deep Communication", "Social Media Correlation", "Contact Correlation", "Hashfile Analytics", "All"'),
    db: Session = Depends(get_db)
):
    try:
        allowed_methods = {"Deep Communication", "Social Media Correlation", "Contact Correlation", "Hashfile Analytics", "All"}

        query = db.query(File)

        if dropdown and dropdown in allowed_methods and dropdown != "All":
            query = query.filter(File.method == dropdown)

        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    File.file_name.ilike(term),
                    File.notes.ilike(term),
                    File.tools.ilike(term),
                    File.method.ilike(term),
                )
            )

        files = query.order_by(File.created_at.desc()).all()

        files_data = []
        for file_record in files:
            files_data.append({
                "id": file_record.id,
                "file_name": file_record.file_name,
                "notes": file_record.notes,
                "type": file_record.type,
                "tools": file_record.tools,
                "method": file_record.method,
                "total_size": file_record.total_size,
                "total_size_formatted": format_file_size(file_record.total_size) if file_record.total_size else None,
                "amount_of_data": file_record.amount_of_data,
                "created_at": str(file_record.created_at),
                "date": file_record.created_at.strftime("%d/%m/%Y") if file_record.created_at else None
            })

        return JSONResponse(
            {
                "status": 200,
                "message": f"Retrieved {len(files_data)} files",
                "data": {
                    "filters": {
                        "search": search,
                        "dropdown": dropdown if dropdown in allowed_methods else None
                    },
                    "files": files_data
                }
            },
            status_code=200
        )

    except Exception as e:
        return JSONResponse(
            {
                "status": 500,
                "message": f"Failed to get files: {str(e)}",
                "data": []
            },
            status_code=500
        )

@router.get("/analytics/{analytic_id}/get-devices")
def get_devices_by_analytic_id(
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
                "device_id": device.id,
                "device_label": device_label,
                "name": device.owner_name or "",
                "phone_number": device.phone_number or "",
                "file_name": file_record.file_name if file_record else "Unknown",
                "file_size": format_file_size(file_record.total_size) if file_record and file_record.total_size else "0 B",
                "file_id": file_record.id if file_record else None,
                "id": str(device.id) if device.id else "",
                "created_at": str(device.created_at) if device.created_at else ""
            }
            
            device_cards.append(device_card)
        
        return JSONResponse(
            {
                "status": 200,
                "message": f"Retrieved {len(device_cards)} devices for analytic",
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