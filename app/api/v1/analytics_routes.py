from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
import tempfile
import json
import os
from pydantic import BaseModel
from app.db.session import get_db
from app.analytics.service import create_group, get_all_groups, create_device, create_group_device, encrypt_and_store_file
from pathlib import Path
from app.analytics.utils.parser_xlsx import parse_sheet

router = APIRouter(prefix="/analytics", tags=["Analytics"])

class GroupCreate(BaseModel):
    analytic_name: str
    type: Optional[str] = None
    notes: Optional[str] = None


class GroupResponse(BaseModel):
    id: int
    analytic_name: str
    type: Optional[str]
    notes: Optional[str]
    created_at: str

    class Config:
        orm_mode = True
        
class AddDevice(BaseModel):
    owner_name: str
    phone_number: str

@router.get("/get-all-analytic")
def get_all_analytic(db: Session = Depends(get_db)):
    try:
        groups = get_all_groups(db)
        return {
            "status": 200,
            "message": "Success",
            "data": groups
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal mengambil data: {str(e)}",
            "data": []
        }

@router.post("/create-analytic")
def create_analytic(data: GroupCreate, db: Session = Depends(get_db)):
    try:
        if not data.analytic_name.strip():
            return {
                "status": 400,
                "message": "analytic_name wajib diisi",
                "data": []
            }

        new_group = create_group(
            db=db,
            analytic_name=data.analytic_name,
            type=data.type,
            notes=data.notes,
        )

        result = {
            "id": new_group.id,
            "analytic_name": new_group.analytic_name,
            "type": new_group.type,
            "notes": new_group.notes,
            "created_at": str(new_group.created_at)
        }

        return {
            "status": 200,
            "message": "Analytics created successfully",
            "data": result
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal membuat analytic: {str(e)}",
            "data": []
        }
        
@router.post("/add-device")
async def add_device(
    file: UploadFile = File(...),
    group_id: int = Form(...),
    owner_name: str = Form(...),
    phone_number: str = Form(...),
    social_media: Optional[str] = Form(None),
):
    """
    Upload file XLSX → enkripsi dengan nama asli → simpan ke uploads → buat device → link ke group
    """
    # --- Parse social media JSON ---
    try:
        social_media_obj: Dict[str, Any] = json.loads(social_media) if social_media else {}
    except Exception as e:
        return {"status": 422, "message": f"Invalid social_media JSON: {str(e)}"}

    # --- Baca konten file upload ---
    file_bytes = await file.read()
    original_filename = file.filename

    # --- Parse isi Excel sementara ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    contacts = parse_sheet(tmp_path, "contacts") or []
    messages = parse_sheet(tmp_path, "messages") or []
    calls = parse_sheet(tmp_path, "calls") or []

    # --- Enkripsi file dan simpan ke uploads/ dengan nama asli ---
    public_key_path = os.path.join(os.getcwd(), "keys", "public.key")
    encrypted_path = encrypt_and_store_file(original_filename, file_bytes, public_key_path)

    # --- Siapkan data untuk Device ---
    device_data = {
        "owner_name": owner_name,
        "phone_number": phone_number,
        "social_media": social_media_obj,
        "file_path": encrypted_path,
    }

    # --- Simpan device dan relasi ke group ---
    device_id = create_device(
        device_data=device_data,
        contacts=contacts,
        messages=messages,
        calls=calls,
    )

    create_group_device(group_id=group_id, device_id=device_id)

    return {
        "status": 200,
        "message": "Device added, encrypted, and linked to group successfully",
        "data": {
            "group_id": group_id,
            "device_id": device_id,
            "owner_name": owner_name,
            "phone_number": phone_number,
            "social_media": social_media_obj,
            "file_path": encrypted_path
        }
    }
