from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Device, File
from app.utils.timezone import get_indonesia_time

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
    owner_name: str = Form(...),
    phone_number: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return JSONResponse(
                {"status": 404, "message": "File not found", "data": []},
                status_code=404
            )
        
        existing_device = db.query(Device).filter(Device.file_id == file_id).first()
        
        if existing_device:
            existing_device.owner_name = owner_name
            existing_device.phone_number = phone_number
            existing_device.device_name = f"{owner_name} Device"
            existing_device.updated_at = get_indonesia_time()
            
            db.commit()
            db.refresh(existing_device)
            device = existing_device
        else:
            new_device = Device(
                file_id=file_id,
                owner_name=owner_name,
                phone_number=phone_number,
                device_name=f"{owner_name} Device",
                created_at=get_indonesia_time()
            )
            
            db.add(new_device)
            db.commit()
            db.refresh(new_device)
            device = new_device
        
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
                    "file_name": file_record.file_name,
                    "created_at": str(device.created_at),
                    "file_info": {
                        "file_name": file_record.file_name,
                        "file_type": file_record.type,
                        "notes": file_record.notes,
                        "tools": file_record.tools,
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



@router.get("/analytics/device/get-all-devices")
def get_all_devices(db: Session = Depends(get_db)):
    try:
        devices = db.query(Device).order_by(Device.id).all()
        
        if not devices:
            return JSONResponse(
                {"status": 200, "message": "No devices found", "data": []},
                status_code=200
            )
        
        # Group devices by device_label (Device A, Device B, etc.)
        grouped_devices = []
        device_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        
        for i, device in enumerate(devices):
            file_record = db.query(File).filter(File.id == device.file_id).first()
            
            contacts_count = len(device.contacts) if device.contacts else 0
            messages_count = len(device.deep_communications) if device.deep_communications else 0
            calls_count = len(device.calls) if device.calls else 0
            hash_files_count = len(device.hash_files) if device.hash_files else 0
            social_media_count = 0  # social_media_accounts relationship removed
            
            device_data = {
                "device_id": device.id,
                "owner_name": device.owner_name,
                "phone_number": device.phone_number,
                "device_name": device.device_name,
                "file_name": file_record.file_name if file_record else None,
                "created_at": str(device.created_at),
                "file_info": {
                    "file_id": file_record.id if file_record else None,
                    "file_name": file_record.file_name if file_record else None,
                    "file_type": file_record.type if file_record else None,
                    "notes": file_record.notes if file_record else None,
                    "tools": file_record.tools if file_record else None,
                    "total_size": file_record.total_size if file_record else None,
                    "total_size_formatted": format_file_size(file_record.total_size) if file_record and file_record.total_size else None
                }
            }
            
            # Create device label (Device A, Device B, etc.)
            if i < len(device_labels):
                device_label = f"Device {device_labels[i]}"
            else:
                # For devices beyond Z, use AA, AB, AC, etc.
                first_char = chr(65 + (i - 26) // 26)
                second_char = chr(65 + (i - 26) % 26)
                device_label = f"Device {first_char}{second_char}"
            
            grouped_devices.append({
                "device_label": device_label,
                "data_device": [device_data]
            })
        
        return JSONResponse(
            {
                "status": 200,
                "message": f"Retrieved {len(devices)} devices successfully",
                "data": grouped_devices
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Failed to get all devices: {str(e)}", "data": []},
            status_code=500
        )


@router.get("/analytics/device/{device_id}")
def get_device_by_id(device_id: int, db: Session = Depends(get_db)):
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        
        if not device:
            return JSONResponse(
                {"status": 404, "message": "Device not found", "data": []},
                status_code=404
            )
        
        file_record = db.query(File).filter(File.id == device.file_id).first()
        
        contacts_count = len(device.contacts) if device.contacts else 0
        messages_count = len(device.deep_communications) if device.deep_communications else 0
        calls_count = len(device.calls) if device.calls else 0
        hash_files_count = len(device.hash_files) if device.hash_files else 0
        social_media_count = 0  # social_media_accounts relationship removed
        
        device_data = {
            "device_id": device.id,
            "owner_name": device.owner_name,
            "phone_number": device.phone_number,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "device_model": device.device_model,
            "os_version": device.os_version,
            "imei": device.imei,
            "serial_number": device.serial_number,
            "extraction_tool": device.extraction_tool,
            "extraction_method": device.extraction_method,
            "extraction_date": str(device.extraction_date) if device.extraction_date else None,
            "is_encrypted": device.is_encrypted,
            "encryption_type": device.encryption_type,
            "is_rooted": device.is_rooted,
            "is_jailbroken": device.is_jailbroken,
            "file_name": file_record.file_name if file_record else None,
            "created_at": str(device.created_at),
            "updated_at": str(device.updated_at) if device.updated_at else None,
            "file_info": {
                "file_id": file_record.id if file_record else None,
                "file_name": file_record.file_name if file_record else None,
                "file_type": file_record.type if file_record else None,
                "notes": file_record.notes if file_record else None,
                "tools": file_record.tools if file_record else None,
                "total_size": file_record.total_size if file_record else None,
                "total_size_formatted": format_file_size(file_record.total_size) if file_record and file_record.total_size else None
            },
            "data_extraction_status": {
                "contacts_count": contacts_count,
                "messages_count": messages_count,
                "calls_count": calls_count,
                "hash_files_count": hash_files_count,
                "social_media_count": social_media_count,
                "total_extracted": contacts_count + messages_count + calls_count + hash_files_count + social_media_count,
                "is_extracted": device.extraction_date is not None
            }
        }
        
        return JSONResponse(
            {
                "status": 200,
                "message": "Device retrieved successfully",
                "data": device_data
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Failed to get device: {str(e)}", "data": []},
            status_code=500
        )


