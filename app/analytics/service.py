from sqlalchemy.orm import Session
from app.analytics.models import Analytic
from datetime import datetime
from typing import List, Dict, Any
from app.db.init_db import SessionLocal
from app.analytics.models import Device, Contact, Message, Call, HashFile, File
from app.analytics.utils.parser_xlsx import normalize_str,_to_str
import os
from app.analytics.utils.sdp_crypto import encrypt_to_sdp, generate_keypair
import tempfile

def store_analytic(db: Session, analytic_name: str, type: str = None, notes: str = None):
    new_analytic = Analytic(
        analytic_name=analytic_name,
        type=type,
        notes=notes,
        created_at=datetime.utcnow()
    )
    db.add(new_analytic)
    db.commit()
    db.refresh(new_analytic)
    return new_analytic


def get_all_analytics(db: Session):
    analytics = db.query(Analytic).order_by(Analytic.created_at.desc()).all()
    return analytics

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
KEY_DIR = os.path.join(os.getcwd(), "keys")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KEY_DIR, exist_ok=True)

def encrypt_and_store_file(original_filename: str, file_bytes: bytes, public_key_path: str) -> str:
    public_key_path = os.path.join(KEY_DIR, "public.key")
    private_key_path = os.path.join(KEY_DIR, "private.key")
    if not (os.path.exists(public_key_path) and os.path.exists(private_key_path)):
        print("⚙️  Keypair belum ada — generate baru...")
        private_key, public_key = generate_keypair()
        with open(private_key_path, "wb") as f:
            f.write(private_key)
        with open(public_key_path, "wb") as f:
            f.write(public_key)
        print(f"Keypair dibuat: {public_key_path}, {private_key_path}")

    encrypted_filename = f"{original_filename}.sdp"
    encrypted_path = os.path.join(UPLOAD_DIR, encrypted_filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        with open(public_key_path, "rb") as f:
            pub_key = f.read()
        encrypt_to_sdp(pub_key, tmp_path, encrypted_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return os.path.join("uploads", encrypted_filename)


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

        if device_data.get("file_path"):
            db.add(HashFile(
                device_id=device_id,
                file_path=device_data["file_path"],
                created_at=datetime.utcnow(),
            ))

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

def format_bytes(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i, x = 0, float(n)
    while x >= 1024 and i < len(units) - 1:
        x /= 1024.0
        i += 1
    return f"{int(x)} {units[i]}" if i == 0 else f"{x:.2f} {units[i]}"

def infer_peer(msg, device_owner: str):
    d = (msg.direction or "").lower()
    sender = (msg.sender or "").strip() if msg.sender else None
    receiver = (msg.receiver or "").strip() if msg.receiver else None
    owner = (device_owner or "").strip().lower() if device_owner else None

    if "out" in d:
        return receiver or (sender if sender and sender.lower() != owner else None)
    elif "in" in d:
        return sender or (receiver if receiver and receiver.lower() != owner else None)
    else:
        if owner:
            if sender and sender.lower() != owner:
                return sender
            if receiver and receiver.lower() != owner:
                return receiver
        return receiver or sender or "Unknown"

def create_file_record(file_name: str, file_path: str, notes: str, type: str, tools: str):
    db = SessionLocal()
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
    db.close()
    return new_file

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