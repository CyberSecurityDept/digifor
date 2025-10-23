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
                direction=_to_str(m.get("Direction")),
                source=_to_str(m.get("Source")),
                type=_to_str(m.get("Type")),
                timestamp=normalize_str(_to_str(m.get("Time stamp (UTC 0)"))),
                text=_to_str(m.get("Text")),
                sender=_to_str(m.get("From")),
                receiver=_to_str(m.get("To")),
                details=_to_str(m.get("Details")),
                thread_id=normalize_str(_to_str(m.get("Thread id"))),
            ))

        for c in calls:
            db.add(Call(
                device_id=device_id,
                file_id=device_data.get("file_id"),
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

def save_hashfiles_to_database(device_id: int, hashfiles: List[Dict[str, Any]], source_tool: str = "Unknown"):
    db = SessionLocal()
    try:
        saved_count = 0
        for hf in hashfiles:
            # Determine file extension
            file_extension = None
            if hf.get('name'):
                if '.' in hf['name']:
                    file_extension = hf['name'].split('.')[-1].lower()
            
            # Determine file type based on extension
            file_type = "Unknown"
            if file_extension:
                if file_extension in ['exe', 'bat', 'cmd', 'scr', 'pif', 'com']:
                    file_type = "Executable"
                elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                    file_type = "Image"
                elif file_extension in ['mp4', 'avi', 'mov', 'wmv', 'flv']:
                    file_type = "Video"
                elif file_extension in ['mp3', 'wav', 'flac', 'aac']:
                    file_type = "Audio"
                elif file_extension in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
                    file_type = "Document"
                elif file_extension in ['zip', 'rar', '7z', 'tar', 'gz']:
                    file_type = "Archive"
            
            # Determine if suspicious
            is_suspicious = "False"
            suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.vbs', '.js']
            if file_extension and file_extension in suspicious_extensions:
                is_suspicious = "True"
            
            # Determine risk level
            risk_level = "Low"
            if is_suspicious == "True":
                risk_level = "High"
            elif file_extension in ['.dll', '.sys', '.drv']:
                risk_level = "Medium"
            
            # Get required fields with defaults
            file_name = normalize_str(hf.get('name', 'Unknown'))
            file_path = normalize_str(hf.get('path', f'/unknown/{file_name}'))
            file_hash = normalize_str(hf.get('md5') or hf.get('sha1') or hf.get('hash', ''))
            
            # Skip if no hash value
            if not file_hash:
                continue
                
            hashfile_record = HashFile(
                device_id=device_id,
                name=file_name,
                file_path=file_path,
                file_hash=file_hash,
                hash_algorithm=normalize_str(hf.get('algorithm', 'MD5')),
                file_size=int(hf.get('size', 0)) if hf.get('size') else None,
                source_type=normalize_str(hf.get('source_type', 'File System')),
                source_tool=source_tool,
                file_type=file_type,
                file_extension=file_extension,
                is_duplicate="False",  # Will be updated later if needed
                is_suspicious=is_suspicious,
                malware_detection=normalize_str(hf.get('malware_detection', '')),
                risk_level=risk_level,
                created_at=get_indonesia_time()
            )
            
            db.add(hashfile_record)
            saved_count += 1
        
        db.commit()
        return saved_count
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_device_hashfiles(db: Session, device_id: int):
    return db.query(HashFile).filter(HashFile.device_id == device_id).all()
