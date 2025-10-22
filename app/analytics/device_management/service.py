from sqlalchemy.orm import Session
from app.analytics.device_management.models import Device, File, Contact, DeepCommunication, Call, HashFile
from app.db.init_db import SessionLocal
from app.analytics.utils.parser_xlsx import normalize_str, _to_str
from typing import List, Dict, Any
import os
from app.utils.timezone import get_indonesia_time

def create_file_record(file_name: str, file_path: str, notes: str, type: str, tools: str):
    db = SessionLocal()
    try:
        new_file = File(
            file_name=file_name,
            file_path=file_path,
            notes=notes,
            type=type,
            tools=tools
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        return new_file
    finally:
        db.close()

def get_all_files(db: Session):
    try:
        files = db.query(File).order_by(File.id.desc()).all()

        result = [
            {
                "id": f.id,
                "file_name": f.file_name,
                "file_path": f.file_path,
                "notes": f.notes,
                "type": f.type,
                "tools": f.tools,
                "total_size": f.total_size,
                "total_size_formatted": format_file_size(f.total_size) if f.total_size else None,
                "created_at": f.created_at
            }
            for f in files
        ]

        return {
            "status": 200,
            "message": "File uploaded successfully.",
            "data": result
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal mengambil data file: {str(e)}",
            "data": []
        }

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

def create_device(
    device_data: Dict[str, Any],
    contacts: List[dict],
    messages: List[dict],
    calls: List[dict],
    existing_device_id: int = None
) -> int:
    db = SessionLocal()
    try:
        if existing_device_id:
            device_id = existing_device_id
        else:
            device = Device(
                owner_name=device_data.get("owner_name"),
                phone_number=device_data.get("phone_number"),
                file_id=device_data.get("file_id"),
                created_at=get_indonesia_time(),
            )

            db.add(device)
            db.commit()
            db.refresh(device)
            device_id = device.id

        if device_data.get("file_path"):
            db.add(HashFile(
                device_id=device_id,
                file_path=device_data["file_path"],
                created_at=get_indonesia_time(),
            ))

        # Save contacts with enhanced duplicate checking
        saved_contacts = 0
        skipped_contacts = 0
        seen_phones = set()  # Track phone numbers in current batch
        
        for c in contacts:
            phone_number = c.get("phone_number")
            display_name = c.get("display_name")
            
            # Skip if no phone number
            if not phone_number:
                skipped_contacts += 1
                continue
            
            # Skip if phone number already seen in current batch
            if phone_number in seen_phones:
                skipped_contacts += 1
                continue
            
            # Check if contact with same phone_number and device_id already exists in database
            existing_contact = db.query(Contact).filter(
                Contact.device_id == device_id,
                Contact.phone_number == phone_number
            ).first()
            
            if existing_contact:
                skipped_contacts += 1
                continue
            
            # Add to seen phones and save contact
            seen_phones.add(phone_number)
            db.add(Contact(
                device_id=device_id,
                file_id=device_data.get("file_id"),
                display_name=display_name,
                phone_number=phone_number,
                type=c.get("type"),
                last_time_contacted=c.get("last_time_contacted")
            ))
            saved_contacts += 1

        for m in messages:
            db.add(DeepCommunication(
                device_id=device_id,
                file_id=device_data.get("file_id"),
                index_row=m.get("index"),
                direction=_to_str(m.get("Direction")),
                source=_to_str(m.get("Source")),
                type=_to_str(m.get("Type")),
                timestamp=normalize_str(_to_str(m.get("Time stamp (UTC 0)"))),
                text=_to_str(m.get("Text")),
                sender=_to_str(m.get("From")),
                receiver=_to_str(m.get("To")),
                details=_to_str(m.get("Details")),
                thread_id=normalize_str(_to_str(m.get("Thread id"))),
                attachment=_to_str(m.get("Attachment")),
            ))

        for c in calls:
            db.add(Call(
                device_id=device_id,
                file_id=device_data.get("file_id"),
                index_row=c.get("index"),
                direction=_to_str(c.get("Direction")),
                source=_to_str(c.get("Source")),
                type=_to_str(c.get("Type")),
                timestamp=normalize_str(_to_str(c.get("Time stamp (UTC 0)"))),
                duration=_to_str(c.get("Duration")),
                caller=_to_str(c.get("From")),
                receiver=_to_str(c.get("To")),
                details=_to_str(c.get("Details")),
                thread_id=normalize_str(_to_str(c.get("Thread id"))),
            ))

        db.commit()
        return device_id

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_device_by_id(db: Session, device_id: int):
    return db.query(Device).filter(Device.id == device_id).first()

def get_device_messages(db: Session, device_id: int):
    return db.query(DeepCommunication).filter(DeepCommunication.device_id == device_id).all()

def get_device_contacts(db: Session, device_id: int):
    return db.query(Contact).filter(Contact.device_id == device_id).all()

def get_device_calls(db: Session, device_id: int):
    return db.query(Call).filter(Call.device_id == device_id).all()
