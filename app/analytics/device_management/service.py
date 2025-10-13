from sqlalchemy.orm import Session
from app.analytics.device_management.models import Device, File, Contact, Message, Call, HashFile
from app.db.init_db import SessionLocal
from app.analytics.utils.parser_xlsx import normalize_str, _to_str
from datetime import datetime
from typing import List, Dict, Any
import os

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
        files = db.query(File).order_by(File.created_at.desc()).all()

        result = [
            {
                "id": f.id,
                "file_name": f.file_name,
                "file_path": f.file_path,
                "notes": f.notes,
                "type": f.type,
                "tools": f.tools,
                "created_at": f.created_at
            }
            for f in files
        ]

        return {
            "status": 200,
            "message": "Success",
            "data": result
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal mengambil data file: {str(e)}",
            "data": []
        }

def create_device(
    device_data: Dict[str, Any],
    contacts: List[dict],
    messages: List[dict],
    calls: List[dict]
) -> int:
    db = SessionLocal()
    try:
        device = Device(
            owner_name=device_data.get("owner_name"),
            phone_number=device_data.get("phone_number"),
            file_id=device_data.get("file_id"),
            created_at=datetime.utcnow(),
        )

        db.add(device)
        db.commit()
        db.refresh(device)
        device_id = device.id

        # Simpan file info ke HashFile
        if device_data.get("file_path"):
            db.add(HashFile(
                device_id=device_id,
                file_path=device_data["file_path"],
                created_at=datetime.utcnow(),
            ))

        # Simpan Contacts
        for c in contacts:
            db.add(Contact(
                device_id=device_id,
                index_row=c.get("index"),
                type=_to_str(c.get("Type")),
                source=_to_str(c.get("Source")),
                contact=_to_str(c.get("Contact")),
                messages=_to_str(c.get("Messages")),
                phones_emails=_to_str(c.get("Phones & Emails")),
                internet=_to_str(c.get("Internet")),
                other=_to_str(c.get("Other")),
            ))

        # Simpan Messages
        for m in messages:
            db.add(Message(
                device_id=device_id,
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

        # Simpan Calls
        for c in calls:
            db.add(Call(
                device_id=device_id,
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
    return db.query(Message).filter(Message.device_id == device_id).all()

def get_device_contacts(db: Session, device_id: int):
    return db.query(Contact).filter(Contact.device_id == device_id).all()

def get_device_calls(db: Session, device_id: int):
    return db.query(Call).filter(Call.device_id == device_id).all()
