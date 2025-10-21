from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Device, Message
from app.analytics.utils.parser_xlsx import normalize_str, _to_str

router = APIRouter()

@router.get("/analytics/deep-communication/device/{device_id}")
def get_device_threads_by_platform(
    device_id: int,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    platforms = (
        db.query(Message.type)
        .filter(Message.device_id == device.id)
        .distinct()
        .order_by(Message.type)
        .all()
    )
    platforms = [p[0] or "General" for p in platforms]

    if not platforms:
        return JSONResponse(
            content={"status": 200, "message": "No messages", "data": []},
            status_code=200
        )

    platform_map = {}

    for plat in platforms:
        thread_ids = (
            db.query(Message.thread_id)
            .filter(Message.device_id == device.id)
            .filter(Message.type == plat)
            .distinct()
            .order_by(Message.thread_id)
            .all()
        )
        thread_ids = [t[0] for t in thread_ids if t[0]]

        thread_list = []

        for tid in thread_ids:
            msgs = (
                db.query(
                    Message.direction,
                    Message.sender,
                    Message.receiver,
                    Message.timestamp,
                    Message.type.label("platform")
                )
                .filter(Message.device_id == device.id)
                .filter(Message.thread_id == tid)
                .filter(Message.type == plat)
                .order_by(Message.id)
                .all()
            )

            if not msgs:
                continue

            incoming_msg = next(
                (m for m in msgs if (m.direction or "").lower().startswith("in")), None
            )

            if incoming_msg:
                peer_name = (incoming_msg.sender or incoming_msg.receiver or "Anonymous").strip()
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
                peer_name = peer_name or "Anonymous"

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
                "platform": plat or "General"
            })

        thread_list.sort(key=lambda x: x["intensity"], reverse=True)
        platform_map[plat.lower()] = thread_list

    return JSONResponse(
        content={
            "status": 200,
            "message": "Success",
            "data": {
                "device_id": device.id,
                "owner_name": device.owner_name,
                "phone_number": device.phone_number,
                "platforms": platform_map
            }
        },
        status_code=200
    )

@router.get("/analytics/deep-communication/thread/{device_id}/{thread_id}")
def get_thread_messages(
    device_id: int,
    thread_id: str,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    messages = (
        db.query(
            Message.id,
            Message.timestamp,
            Message.direction,
            Message.sender,
            Message.receiver,
            Message.text,
            Message.type,
            Message.source
        )
        .filter(Message.device_id == device.id)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.id.asc())
        .all()
    )

    if not messages:
        return JSONResponse(
            content={
                "status": 200,
                "message": "No messages in this thread",
                "data": []
            },
            status_code=200
        )

    return JSONResponse(
        content={
            "status": 200,
            "message": "Success",
            "data": [m._asdict() for m in messages]
        },
        status_code=200
    )
