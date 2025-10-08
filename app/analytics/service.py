from sqlalchemy.orm import Session
from app.analytics.models import Group
from datetime import datetime
from typing import List, Dict, Any
from app.db.init_db import SessionLocal
from app.analytics.models import Device, Contact, Message, Call, HashFile
from app.analytics.utils.parser_xlsx import normalize_str,_to_str
import os
from app.analytics.utils.sdp_crypto import encrypt_to_sdp, generate_keypair
import tempfile

def create_group(db: Session, analytic_name: str, type: str = None, notes: str = None):
    """Buat group baru dan simpan ke database"""
    new_group = Group(
        analytic_name=analytic_name,
        type=type,
        notes=notes,
        created_at=datetime.utcnow()
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


def get_all_groups(db: Session):
    """Ambil semua data group"""
    groups = db.query(Group).order_by(Group.created_at.desc()).all()
    return groups


UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
KEY_DIR = os.path.join(os.getcwd(), "keys")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KEY_DIR, exist_ok=True)


def encrypt_and_store_file(original_filename: str, file_bytes: bytes, public_key_path: str) -> str:
    public_key_path = os.path.join(KEY_DIR, "public.key")
    private_key_path = os.path.join(KEY_DIR, "private.key")

    # 🔐 Generate keypair kalau belum ada
    if not (os.path.exists(public_key_path) and os.path.exists(private_key_path)):
        print("⚙️  Keypair belum ada — generate baru...")
        private_key, public_key = generate_keypair()
        with open(private_key_path, "wb") as f:
            f.write(private_key)
        with open(public_key_path, "wb") as f:
            f.write(public_key)
        print(f"✅ Keypair dibuat: {public_key_path}, {private_key_path}")

    # Tentukan nama file hasil enkripsi
    encrypted_filename = f"{original_filename}.sdp"
    encrypted_path = os.path.join(UPLOAD_DIR, encrypted_filename)

    # Buat file sementara untuk proses enkripsi
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # Baca public key
        with open(public_key_path, "rb") as f:
            pub_key = f.read()

        # Enkripsi file sementara → hasil di folder uploads/
        encrypt_to_sdp(pub_key, tmp_path, encrypted_path)

    finally:
        # Hapus file sementara setelah enkripsi selesai
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # ✅ Kembalikan path RELATIF, bukan full absolute path
    return os.path.join("uploads", encrypted_filename)


def create_device(device_data: Dict[str, Any], contacts: List[dict], messages: List[dict], calls: List[dict]) -> int:
    """Simpan data Device + HasFile + detail lain ke DB."""
    db = SessionLocal()
    try:
        social_media = device_data.get("social_media", {}) or {}

        device = Device(
            group_id=device_data.get("group_id"), 
            owner_name=device_data.get("owner_name"),
            phone_number=device_data.get("phone_number"),
            instagram=social_media.get("instagram"),
            whatsapp=social_media.get("whatsapp"),
            x=social_media.get("x"),
            facebook=social_media.get("facebook"),
            tiktok=social_media.get("tiktok"),
            telegram=social_media.get("telegram"),
        )

        db.add(device)
        db.commit()
        db.refresh(device)

        device_id = device.id

        # --- 1️⃣ Simpan file info ke HasFile ---
        if device_data.get("file_path"):
            db.add(HashFile(
                device_id=device_id,
                file_path=device_data["file_path"],
                created_at=datetime.utcnow(),
            ))

        # --- 2️⃣ Simpan Contacts ---
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

        # --- 3️⃣ Simpan Messages ---
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

        # --- 4️⃣ Simpan Calls ---
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

        # --- 5️⃣ Commit semua perubahan ---
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