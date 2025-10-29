from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Device, AnalyticDevice, Analytic
from app.analytics.device_management.models import ChatMessage
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
@router.get("/analytics/{analytic_id}/deep-communication")
def get_deep_communication_by_analytic(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        return JSONResponse(
            {
                "status": 404,
                "message": f"Analytic with ID {analytic_id} not found",
                "data": []
            },
            status_code=404
        )

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).all()
    
    device_ids = []
    for link in device_links:
        device_ids.extend(link.device_ids)
    device_ids = list(set(device_ids))
    
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()

    if not devices:
        return JSONResponse(
            {
                "status": 200,
                "message": f"No devices found for analytic '{analytic.analytic_name}'",
                "data": []
            },
            status_code=200
        )

    correlations = []
    devices_list = []

    # Konversi ke snake_case
    def normalize_platform_name(name: str) -> str:
        return name.lower().replace(" ", "_")

    for device in devices:
        devices_list.append({
            "device_id": device.id,
            "device_name": device.device_name,
            "owner_name": device.owner_name,
            "phone_number": device.phone_number,
        })

        platforms = (
            db.query(ChatMessage.platform)
            .filter(ChatMessage.device_id == device.id)
            .distinct()
            .all()
        )
        platforms = [p[0] for p in platforms if p[0]]

        platform_map = {normalize_platform_name(p): [] for p in ALLOWED_SOURCES}

        for plat in platforms:
            plat_key = normalize_platform_name(plat)
            thread_ids = (
                db.query(ChatMessage.thread_id)
                .filter(ChatMessage.device_id == device.id)
                .filter(ChatMessage.platform == plat)
                .distinct()
                .all()
            )
            thread_ids = [t[0] for t in thread_ids if t[0]]

            thread_list = []

            for tid in thread_ids:
                msgs = (
                    db.query(
                        ChatMessage.direction,
                        ChatMessage.sender_name.label("sender"),
                        ChatMessage.receiver_name.label("receiver"),
                        ChatMessage.timestamp,
                        ChatMessage.platform.label("platform")
                    )
                    .filter(ChatMessage.device_id == device.id)
                    .filter(ChatMessage.thread_id == tid)
                    .filter(ChatMessage.platform == plat)
                    .all()
                )

                if not msgs:
                    continue

                has_incoming = any(
                    (m.direction or "").lower().startswith("in") for m in msgs
                )
                if not has_incoming:
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
                    "platform": plat_key
                })

            thread_list.sort(key=lambda x: x["intensity"], reverse=True)
            platform_map[plat_key] = thread_list

        correlations.append({
            "device_id": device.id,
            "platforms": platform_map
        })

    return JSONResponse(
        {
            "status": 200,
            "message": f"Retrieved deep communication data for analytic '{analytic.analytic_name}' successfully",
            "data": {
                "analytic_id": analytic.id,
                "analytic_name": analytic.analytic_name,
                "total_devices": len(devices),
                "devices": devices_list,
                "correlations": correlations
            }
        },
        status_code=200
    )



@router.get("/analytics/deep-communication/{device_id}/chat/{thread_id}")
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
            ChatMessage.id,
            ChatMessage.timestamp,
            ChatMessage.direction,
            ChatMessage.sender_name.label("sender"),
            ChatMessage.receiver_name.label("receiver"),
            ChatMessage.message_text.label("text"),
            ChatMessage.message_type.label("type"),
            ChatMessage.platform.label("source")
        )
        .filter(ChatMessage.device_id == device.id)
        .filter(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.id.asc())
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
