from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.db.session import get_db
from app.analytics.service import store_analytic, get_all_analytics, infer_peer, create_file_record,get_all_files
from app.analytics.utils.upload_pipeline import upload_service
from app.analytics.schemas import AnalyticCreate
from collections import defaultdict
from fastapi import Query
from app.analytics import models
import os

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/get-all-file")
def get_files(db: Session = Depends(get_db)):
    """
    Endpoint GET untuk mengambil semua file.
    """
    return get_all_files(db)

@router.post("/upload-data")
async def upload_data(
    file: UploadFile = File(...),
    notes: str = Form(...),
    type: str = Form(...),
    tools: str = Form(...)
):
    try:
        if not file.filename:
            return JSONResponse({"status": 400, "message": "File name is required"}, status_code=400)

        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return JSONResponse({"status": 400, "message": "Only Excel files (.xlsx, .xls) are allowed"}, status_code=400)

        save_dir = "uploads/data"
        os.makedirs(save_dir, exist_ok=True)
        file_path = f"{save_dir}/{file.filename}"

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        file_record = create_file_record(
            file_name=file.filename,
            file_path=file_path,
            notes=notes,
            type=type,
            tools=tools
        )

        return JSONResponse({
            "status": 200,
            "message": "File uploaded successfully",
            "data": {"file_id": file_record.id, "file_path": file_path}
        })

    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Upload error: {str(e)}"}, status_code=500)

@router.post("/add-device")
async def add_device(
    file_id: int = Form(...),
    owner_name: str = Form(...),
    phone_number: str = Form(...),
    upload_id: str = Form(...),
):
    try:
        resp = await upload_service.start_upload_and_process(
            file_id=file_id,
            owner_name=owner_name,
            phone_number=phone_number,
            upload_id=upload_id,
        )
        return JSONResponse(resp, status_code=resp.get("status", 200))
    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Unexpected error: {str(e)}"},
            status_code=500
        )

@router.get("/upload-progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    """Cek progres proses file."""
    data, status_code = upload_service.get_progress(upload_id)
    return JSONResponse(content=data, status_code=status_code)

@router.post("/upload-cancel/{upload_id}")
async def cancel_upload(upload_id: str):
    """Batalkan proses upload/analisis berjalan."""
    data, status_code = upload_service.cancel(upload_id)
    return JSONResponse(content=data, status_code=status_code)

@router.get("/get-all-analytic")
def get_all_analytic(db: Session = Depends(get_db)):
    try:
        analytics = get_all_analytics(db)
        return {
            "status": 200,
            "message": "Success",
            "data": analytics
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal mengambil data: {str(e)}",
            "data": []
        }

@router.post("/create-analytic")
def create_analytic(data: AnalyticCreate, db: Session = Depends(get_db)):
    try:
        if not data.analytic_name.strip():
            return {
                "status": 400,
                "message": "analytic_name wajib diisi",
                "data": []
            }

        new_analytic = store_analytic(
            db=db,
            analytic_name=data.analytic_name,
            type=data.type,
            notes=data.notes,
        )

        result = {
            "id": new_analytic.id,
            "analytic_name": new_analytic.analytic_name,
            "type": new_analytic.type,
            "notes": new_analytic.notes,
            "created_at": str(new_analytic.created_at)
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

@router.post("/link-device-analytic")
def link_device_to_analytic(device_id: int, analytic_id: int):
    db = next(get_db())
    device = db.query(models.Device).get(device_id)
    analytic = db.query(models.Analytic).get(analytic_id)
    if not device or not analytic:
        return {"status": 404, "message": "Device or Analytic not found"}

    analytic.devices.append(device)
    db.commit()
    return {"status": 200, "message": "Linked successfully"}


@router.get("/{analytic_id}/devices")
def get_analytic_devices(analytic_id: int, db: Session = Depends(get_db)):
    analytic = db.query(models.Analytic).filter(models.Analytic.id == analytic_id).first()
    if not analytic:
        return {"status": 404, "message": "Analytic not found", "data": []}

    devices = db.query(models.Device).filter(models.Device.analytic_id == analytic_id).all()

    return {
        "status": 200,
        "message": "Success",
        "data": [
            {
                "device_id": d.id,
                "owner_name": d.owner_name,
                "phone_number": d.phone_number,
                "created_at": d.created_at,
            }
            for d in devices
        ]
    }

@router.get("/deep-communication/device/{device_id}")
def get_device_threads_by_platform(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Ambil daftar thread komunikasi per platform (WhatsApp, Telegram, dll)
    - Tiap thread 1 record (tidak digabungkan per peer)
    - Nama peer diambil dari pesan 'Incoming'
    """
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        return {"status": 404, "message": "Device not found", "data": []}

    # ambil semua platform unik dari message device ini
    platforms = (
        db.query(models.Message.type)
        .filter(models.Message.device_id == device.id)
        .distinct()
        .all()
    )
    platforms = [p[0] or "Unknown" for p in platforms]

    if not platforms:
        return {"status": 200, "message": "No messages", "data": []}

    platform_map = {}

    for plat in platforms:
        # ambil semua thread unik di platform itu
        thread_ids = (
            db.query(models.Message.thread_id)
            .filter(models.Message.device_id == device.id)
            .filter(models.Message.type == plat)
            .distinct()
            .all()
        )
        thread_ids = [t[0] for t in thread_ids if t[0]]

        thread_list = []

        for tid in thread_ids:
            # ambil semua pesan dalam thread
            msgs = (
                db.query(
                    models.Message.direction,
                    models.Message.sender,
                    models.Message.receiver,
                    models.Message.timestamp,
                    models.Message.type.label("platform")
                )
                .filter(models.Message.device_id == device.id)
                .filter(models.Message.thread_id == tid)
                .filter(models.Message.type == plat)
                .all()
            )

            if not msgs:
                continue

            # tentukan siapa peer (prioritas dari pesan Incoming)
            incoming_msg = next(
                (m for m in msgs if (m.direction or "").lower().startswith("in")), None
            )

            if incoming_msg:
                peer_name = (incoming_msg.sender or incoming_msg.receiver or "Unknown").strip()
            else:
                # fallback: ambil siapa pun yang bukan owner
                owner = (device.owner_name or "").strip().lower()
                peer_name = None
                for m in msgs:
                    s = (m.sender or "").strip().lower()
                    r = (m.receiver or "").strip().lower()
                    if s and s != owner:
                        peer_name = s
                        break
                    if r and r != owner:
                        peer_name = r
                        break
                peer_name = peer_name or "Unknown"

            # hitung intensitas & waktu
            message_count = len(msgs)
            timestamps = [m.timestamp for m in msgs if m.timestamp]
            first_ts = min(timestamps) if timestamps else None
            last_ts = max(timestamps) if timestamps else None

            thread_list.append({
                "peer": peer_name,
                "thread_id": tid,
                "intensity": message_count,
                "first_timestamp": first_ts,
                "last_timestamp": last_ts,
                "platform": plat or "Unknown"
            })

        # urutkan thread berdasarkan intensitas terbesar
        thread_list.sort(key=lambda x: x["intensity"], reverse=True)
        platform_map[plat.lower()] = thread_list

    return {
        "status": 200,
        "message": "Success",
        "data": {
            "device_id": device.id,
            "owner_name": device.owner_name,
            "phone_number": device.phone_number,
            "platforms": platform_map
        }
    }


@router.get("/deep-communication/thread/{device_id}/{thread_id}")
def get_thread_messages(
    device_id: int,
    thread_id: str,
    db: Session = Depends(get_db)
):
    """
    Ambil semua message dari 1 thread_id di device tertentu.
    """
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        return {"status": 404, "message": "Device not found", "data": []}

    messages = (
        db.query(
            models.Message.id,
            models.Message.timestamp,
            models.Message.direction,
            models.Message.sender,
            models.Message.receiver,
            models.Message.text,
            models.Message.type,
            models.Message.source
        )
        .filter(models.Message.device_id == device.id)
        .filter(models.Message.thread_id == thread_id)
        .order_by(models.Message.id.asc())
        .all()
    )

    if not messages:
        return {
            "status": 200,
            "message": "No messages in this thread",
            "data": []
        }

    return {
        "status": 200,
        "message": "Success",
        "data": [m._asdict() for m in messages]
    }
