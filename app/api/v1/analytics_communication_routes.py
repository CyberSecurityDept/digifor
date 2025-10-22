from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Device, DeepCommunication
from app.analytics.utils.parser_xlsx import normalize_str, _to_str

router = APIRouter()

ALLOWED_SOURCES = [
    "Facebook Messenger",
    "Telegram",
    "WhatsApp Messenger",
    "X (Twitter)",
    "Instagram",
    "TikTok"
]

@router.get("/analytics/deep-communication/device/{device_id}")
def get_device_threads_by_platform(
    device_id: int,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return {"status": 404, "message": "Device not found", "data": []}

    platforms = (
        db.query(DeepCommunication.source)
        .filter(DeepCommunication.device_id == device.id)
        .distinct()
        .all()
    )
    platforms = [p[0] for p in platforms if p[0] in ALLOWED_SOURCES]

    if not platforms:
        return {"status": 200, "message": "No messages for allowed platforms", "data": []}

    platform_map = {}

    for plat in platforms:
        thread_ids = (
            db.query(DeepCommunication.thread_id)
            .filter(DeepCommunication.device_id == device.id)
            .filter(DeepCommunication.source == plat)
            .distinct()
            .all()
        )
        thread_ids = [t[0] for t in thread_ids if t[0]]

        thread_list = []

        for tid in thread_ids:
            msgs = (
                db.query(
                    DeepCommunication.direction,
                    DeepCommunication.sender,
                    DeepCommunication.receiver,
                    DeepCommunication.timestamp,
                    DeepCommunication.source.label("platform")
                )
                .filter(DeepCommunication.device_id == device.id)
                .filter(DeepCommunication.thread_id == tid)
                .filter(DeepCommunication.source == plat)
                .all()
            )

            if not msgs:
                continue

            incoming_msg = next(
                (m for m in msgs if (m.direction or "").lower().startswith("in")), None
            )

            if incoming_msg:
                peer_name = (incoming_msg.sender or incoming_msg.receiver or "Unknown").strip()
            else:
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
                "platform": plat
            })

        thread_list.sort(key=lambda x: x["intensity"], reverse=True)
        platform_map[plat] = thread_list

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

@router.get("/analytics/deep-communication/thread/{device_id}/{thread_id}")
def get_thread_messages(
    device_id: int,
    thread_id: str,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return {"status": 404, "message": "Device not found", "data": []}

    messages = (
        db.query(
            DeepCommunication.id,
            DeepCommunication.timestamp,
            DeepCommunication.direction,
            DeepCommunication.sender,
            DeepCommunication.receiver,
            DeepCommunication.text,
            DeepCommunication.type,
            DeepCommunication.source
        )
        .filter(DeepCommunication.device_id == device.id)
        .filter(DeepCommunication.thread_id == thread_id)
        .order_by(DeepCommunication.id.asc())
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
