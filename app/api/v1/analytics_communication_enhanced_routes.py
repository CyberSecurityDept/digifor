from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from app.db.session import get_db
from app.analytics.shared.models import Device, Contact, Analytic, AnalyticDevice
from app.analytics.device_management.models import ChatMessage
from collections import defaultdict
from typing import Optional, List
from datetime import datetime
import traceback, re, logging
from app.auth.models import User
from app.api.deps import get_current_user
from app.api.v1.analytics_management_routes import check_analytic_access

logger = logging.getLogger(__name__)

router = APIRouter()

PLATFORM_MAPPING = {
    'instagram': ['Instagram', 'instagram'],
    'telegram': ['Telegram', 'telegram'],
    'whatsapp': ['WhatsApp', 'whatsapp', 'WA'],
    'facebook': ['Facebook', 'facebook', 'Messenger', 'messenger'],
    'x': ['X', 'x', 'Twitter', 'twitter'],
    'tiktok': ['TikTok', 'tiktok', 'TikTok']
}

def normalize_platform_name(platform: str) -> str:
    if not platform:
        return ''
    platform_lower = platform.lower().strip()
    
    for normalized, variants in [
        ('instagram', ['instagram', 'ig']),
        ('telegram', ['telegram', 'tg']),
        ('whatsapp', ['whatsapp', 'wa']),
        ('facebook', ['facebook', 'fb', 'messenger']),
        ('x', ['x', 'twitter']),
        ('tiktok', ['tiktok'])
    ]:
        if platform_lower in variants:
            return normalized
    return platform_lower


def clean_message_text(text: str) -> str:
    if not text:
        return ""
    
    cleaned = re.sub(r'[\u200B-\u200D\uFEFF\u00A0\u2060\u200E\u200F]', '', text)
 
    cleaned = cleaned.replace('\\\\\\\\', '\\\\') 
    cleaned = cleaned.replace('\\\\n', '\n')
    cleaned = cleaned.replace('\\\\r', '\r')
    cleaned = cleaned.replace('\\\\t', ' ')
    cleaned = cleaned.replace('\\n', '\n') 
    cleaned = cleaned.replace('\\r', '\r')
    cleaned = cleaned.replace('\\t', ' ')
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    cleaned = cleaned.replace('\n', ' ')
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    cleaned = cleaned.strip()

    result = re.sub(r'\\(?![\'"nrtbfvxuU0-7\\])', '', cleaned)
    if result.endswith('\\') and (len(result) < 2 or result[-2] != '\\'):
        result = result[:-1]
    
    return result

def extract_time_from_timestamp(timestamp: str) -> str:
    if not timestamp:
        return ""
    try:
        time_match = re.search(r'(\d{1,2}):(\d{2})(?::\d{2})?', timestamp)
        if time_match:
            hour = time_match.group(1).zfill(2)
            minute = time_match.group(2)
            return f"{hour}:{minute}"
        
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"]:
            try:
                dt = datetime.strptime(timestamp, fmt)
                return dt.strftime("%H:%M")
            except ValueError:
                continue
    except Exception:
        pass
    
    return ""

def is_valid_person_name(name: str) -> bool:
    if not name:
        return False
    
    stripped = re.sub(r'[\u200B-\u200D\uFEFF\u00A0\u2060\u200E\u200F\u3164]', '', name).strip()
    if not stripped:
        return False
    
    if len(stripped) == 1:
        return False
    
    if re.search(r'[a-zA-Z0-9]', stripped):
        return True
    
    meaningful_chars = re.sub(r'[\s\W_]', '', stripped)
    if not meaningful_chars:
        return False
    
    if len(stripped) < 2:
        return False
    
    return True

def get_chat_messages_for_analytic(
    db: Session,
    analytic_id: int,
    device_id: Optional[int] = None,
    platform: Optional[str] = None,
    file_ids: Optional[List[int]] = None
) -> List[ChatMessage]:
    query = db.query(ChatMessage)
    
    if file_ids:
        valid_file_ids = [fid for fid in file_ids if fid is not None]
        if valid_file_ids:
            query = query.filter(ChatMessage.file_id.in_(valid_file_ids))
            logger.debug(f"Filtering ChatMessage by file_ids: {valid_file_ids}")
        else:
            logger.warning(f"All file_ids are None, returning empty result")
            return []

    if platform:
        normalized_platform = normalize_platform_name(platform)
        if normalized_platform == 'x':
            query = query.filter(
                or_(
                    func.lower(ChatMessage.platform) == 'x',
                    func.lower(ChatMessage.platform) == 'twitter',
                    func.lower(ChatMessage.platform).like('%x%'),
                    func.lower(ChatMessage.platform).like('%twitter%')
                )
            )
        else:
            query = query.filter(
                or_(
                    func.lower(ChatMessage.platform) == normalized_platform,
                    func.lower(ChatMessage.platform).like(f"%{normalized_platform}%")
                )
            )
    
    messages = query.all()
    logger.debug(f"get_chat_messages_for_analytic: Found {len(messages)} messages (analytic_id={analytic_id}, device_id={device_id}, platform={platform}, file_ids={file_ids})")
    return messages

@router.get("/analytic/deep-communication-analytics")
def get_deep_communication_analytics(  # type: ignore[reportGeneralTypeIssues]
    analytic_id: int = Query(..., description="Analytic ID"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"getDeepCommunication called with analytic_id={analytic_id}, device_id={device_id}")
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            logger.warning(f"Analytic not found: analytic_id={analytic_id}")
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Analytic with ID {analytic_id} not found",
                    "data": {
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": "Unknown"
                        },
                        "next_action": "create_analytic",
                        "redirect_to": "/analytics/start-analyzing",
                        "instruction": "Please create a new analytic with method 'Deep Communication Analytics'"
                    }
                },
                status_code=404
            )
        
        if current_user is not None and not check_analytic_access(analytic, current_user):
            logger.warning(f"Access denied for user {current_user.id} to analytic {analytic_id}")
            return JSONResponse(
                content={
                    "status": 403,
                    "message": "You do not have permission to access this analytic"
                },
                status_code=403
            )

        method_value = analytic.method
        logger.info(f"Analytic method: {method_value}, expected: 'Deep Communication Analytics'")
        if method_value is None or str(method_value) != "Deep Communication Analytics":
            logger.warning(f"Invalid method for analytic {analytic_id}: {method_value}")
            return JSONResponse(
                content={
                    "status": 400,
                    "message": f"This endpoint is only for Deep Communication Analytics. Current analytic method is '{method_value}'",
                    "data": {
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": analytic.analytic_name or "Unknown",
                            "current_method": str(method_value) if method_value else None
                        },
                        "next_action": "create_analytic",
                        "redirect_to": "/analytics/start-analyzing",
                        "instruction": "Please create a new analytic with method 'Deep Communication Analytics'"
                    }
                },
                status_code=400
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).order_by(AnalyticDevice.id).all()
            
        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        device_ids = list(set(device_ids))
        
        if not device_ids:
            logger.warning(f"No devices linked to analytic {analytic_id}")
            analytic_name_value = getattr(analytic, 'analytic_name', None) or "Unknown"
            return JSONResponse(
                content={
                    "status": 404,
                    "message": "No devices linked to this analytic",
                    "data": {
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": analytic_name_value
                        },
                        "device_count": 0,
                        "required_minimum": 2,
                        "next_action": "add_device",
                        "redirect_to": "/analytics/devices",
                        "instruction": "Please add at least 2 devices to continue with Deep Communication Analytics"
                    }
                },
                status_code=404
            )
            
        total_device_count = len(device_ids)
        logger.info(f"Total device count for analytic {analytic_id}: {total_device_count}")
        if total_device_count < 2:
            logger.warning(f"Insufficient devices for analytic {analytic_id}: {total_device_count} < 2")
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Deep Communication Analytics requires minimum 2 devices. Current analytic has {total_device_count} device(s).",
                    "data": {
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": getattr(analytic, 'analytic_name', None) or "Unknown"
                        },
                        "device_count": total_device_count,
                        "required_minimum": 2,
                        "next_action": "add_device",
                        "redirect_to": "/analytics/devices",
                        "instruction": "Please add at least 2 devices to continue with Deep Communication Analytics"
                    }
                },
                status_code=404
            )

        if device_id is not None:
            if device_id not in device_ids:
                logger.warning(f"Device {device_id} not found in analytic {analytic_id}")
                return JSONResponse(
                    content={
                        "status": 404,
                        "message": f"Device with ID {device_id} not found in this analytic",
                        "data": {
                            "analytic_info": {
                                "analytic_id": analytic_id,
                                "analytic_name": getattr(analytic, 'analytic_name', None) or "Unknown"
                            },
                            "device_id": device_id,
                            "device_count": total_device_count,
                            "required_minimum": 2,
                            "next_action": "add_device",
                            "redirect_to": "/analytics/devices",
                            "instruction": "The specified device is not linked to this analytic. Please add the device or ensure you have at least 2 devices to continue with Deep Communication Analytics"
                        }
                    },
                    status_code=404
                )
            device_ids = [device_id]

        devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
        
        if not devices:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": "Devices not found for this analytic",
                    "data": {
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": analytic.analytic_name or "Unknown"
                        },
                        "device_count": 0,
                        "required_minimum": 2,
                        "next_action": "add_device",
                        "redirect_to": "/analytics/devices",
                        "instruction": "Please add at least 2 devices to continue with Deep Communication Analytics"
                    }
                },
                status_code=404
            )
            
        all_file_ids = [d.file_id for d in devices if d.file_id]
        logger.info(f"Retrieving messages for file_ids: {all_file_ids}")
        all_messages = get_chat_messages_for_analytic(db, analytic_id, None, None, all_file_ids)
        logger.info(f"Found {len(all_messages)} total messages for analytic {analytic_id}")
        
        all_platforms = [
            {'key': 'instagram', 'display': 'Instagram'},
            {'key': 'telegram', 'display': 'Telegram'},
            {'key': 'whatsapp', 'display': 'WhatsApp'},
            {'key': 'facebook', 'display': 'Facebook'},
            {'key': 'x', 'display': 'X'},
            {'key': 'tiktok', 'display': 'TikTok'}
        ]
        
        devices_with_platforms = []
        
        for device in devices:
            if not device.file_id:
                logger.warning(f"Device {device.id} has no file_id")
                continue
                
            device_file_ids = [device.file_id]
            device_messages = [msg for msg in all_messages if msg.file_id == device.file_id]
            logger.info(f"Device {device.id} (file_id={device.file_id}): Found {len(device_messages)} messages")
            
            platform_cards = []
            
            for platform_info in all_platforms:
                platform_key = platform_info['key']
                platform_display = platform_info['display']
                
                platform_messages = [
                    msg for msg in device_messages 
                    if normalize_platform_name(msg.platform or '') == platform_key
                ]
                
                message_count = len(platform_messages)
                has_data = message_count > 0
                
                if has_data:
                    logger.info(f"Device {device.id}, Platform {platform_display}: Found {message_count} messages")
                else:
                    # Log available platforms for debugging
                    available_platforms = set([normalize_platform_name(msg.platform or '') for msg in device_messages])
                    if available_platforms:
                        logger.debug(f"Device {device.id}, Platform {platform_display}: No messages. Available platforms: {available_platforms}")
  
                thread_person_messages = defaultdict(lambda: defaultdict(list))
                person_info = {}
                device_owner_name = (device.owner_name or "").strip().lower()
                
                thread_person_map = {}
                thread_group_map = {}
                
                for msg in platform_messages:
                    thread_id = (msg.thread_id or msg.chat_id or "").strip()
                    if thread_id:
                        chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
                        if chat_type:
                            chat_type_lower = chat_type.lower()
                            if chat_type_lower in ["group", "broadcast"]:
                                group_name = (msg.group_name or "").strip() if msg.group_name else None
                                if group_name and group_name.strip():
                                    if thread_id not in thread_group_map:
                                        thread_group_map[thread_id] = {
                                            "name": group_name.strip(),
                                            "id": (msg.group_id or "").strip() if msg.group_id else None
                                        }
                
                for msg in platform_messages:
                    direction = (msg.direction or "").strip()
                    direction_lower = direction.lower()
                    if direction_lower in ['incoming', 'received']:
                        sender_name = msg.from_name or ""
                        sender_id = msg.sender_number or ""
                        thread_id = (msg.thread_id or msg.chat_id or "").strip()
                        chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
                        group_name = (msg.group_name or "").strip() if msg.group_name else None
                        
                        person_name = None
                        person_id = None
                        
                        if chat_type:
                            chat_type_lower = chat_type.lower()
                            if chat_type_lower in ["group", "broadcast"]:
                                if group_name and group_name.strip():
                                    person_name = group_name.strip()
                                    person_id = (msg.group_id or "").strip() if msg.group_id else None
                                elif thread_id and thread_id in thread_group_map:
                                    person_name = thread_group_map[thread_id]["name"]
                                    person_id = thread_group_map[thread_id].get("id")
                            elif chat_type_lower == "one on one":
                                if sender_name and sender_name.strip():
                                    person_name = sender_name.strip()
                                    person_id = sender_id if sender_id and sender_id.strip() else None
                        
                        if not person_name:
                            if sender_name and sender_name.strip():
                                person_name = sender_name.strip()
                                person_id = sender_id if sender_id and sender_id.strip() else None
                            elif sender_id and sender_id.strip():
                                sender_id_clean = sender_id.strip()
                                if len(sender_id_clean) <= 50:
                                    person_name = sender_id_clean
                                    person_id = sender_id_clean
                                else:
                                    continue
                            else:
                                continue
                        
                        if thread_id and person_name:
                            if thread_id not in thread_person_map:
                                thread_person_map[thread_id] = {
                                    "name": person_name,
                                    "id": person_id
                                }
                
                for msg in platform_messages:
                    sender_name = msg.from_name or ""
                    sender_id = msg.sender_number or ""
                    recipient_name = msg.to_name or ""
                    recipient_id = msg.recipient_number or ""
                    chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
                    group_name = (msg.group_name or "").strip() if msg.group_name else None
                    
                    sender_name_lower = (sender_name or "").strip().lower()
                    recipient_name_lower = (recipient_name or "").strip().lower()
                    
                    direction = (msg.direction or "").strip()
                    direction_lower = direction.lower()
                    
                    person_name = None
                    person_id = None
                    
                    thread_id = (msg.thread_id or msg.chat_id or "").strip()
                    
                    if thread_id and thread_id in thread_group_map:
                        person_name = thread_group_map[thread_id]["name"]
                        person_id = thread_group_map[thread_id].get("id")
                    elif chat_type:
                        chat_type_lower = chat_type.lower()
                        if chat_type_lower in ["group", "broadcast"]:
                            if group_name and group_name.strip():
                                person_name = group_name.strip()
                                person_id = (msg.group_id or "").strip() if msg.group_id else None
                            elif thread_id and thread_id in thread_group_map:
                                person_name = thread_group_map[thread_id]["name"]
                                person_id = thread_group_map[thread_id].get("id")
                        elif chat_type_lower == "one on one":
                            if direction_lower in ['outgoing', 'sent']:
                                if recipient_name and recipient_name.strip():
                                    person_name = recipient_name.strip()
                                    person_id = recipient_id if recipient_id and recipient_id.strip() else None
                                elif recipient_id and recipient_id.strip():
                                    person_name = recipient_id.strip()
                                    person_id = recipient_id.strip()
                            else:
                                if sender_name and sender_name.strip():
                                    person_name = sender_name.strip()
                                    person_id = sender_id if sender_id and sender_id.strip() else None
                    
                    if not person_name:
                        if direction_lower in ['outgoing', 'sent']:
                            if recipient_name and recipient_name.strip():
                                recipient_name_clean = recipient_name.strip()
                                if len(recipient_name_clean) > 50 or (recipient_name_clean.isdigit() and len(recipient_name_clean) > 20):
                                    if recipient_id and recipient_id.strip() and len(recipient_id.strip()) <= 50:
                                        person_name = recipient_id.strip()
                                        person_id = recipient_id.strip()
                                    elif thread_id and thread_id in thread_person_map:
                                        person_name = thread_person_map[thread_id]["name"]
                                        person_id = thread_person_map[thread_id].get("id")
                                    else:
                                        continue
                                else:
                                    person_name = recipient_name_clean
                                    person_id = recipient_id if recipient_id and recipient_id.strip() else None
                            elif recipient_id and recipient_id.strip():
                                recipient_id_clean = recipient_id.strip()
                                if len(recipient_id_clean) > 50:
                                    if thread_id and thread_id in thread_person_map:
                                        person_name = thread_person_map[thread_id]["name"]
                                        person_id = thread_person_map[thread_id].get("id")
                                    else:
                                        continue
                                else:
                                    person_name = recipient_id_clean
                                    person_id = recipient_id_clean
                            else:
                                if thread_id and thread_id in thread_person_map:
                                    person_name = thread_person_map[thread_id]["name"]
                                    person_id = thread_person_map[thread_id].get("id")
                                else:
                                    continue
                        elif direction_lower in ['incoming', 'received']:
                            if sender_name and sender_name.strip():
                                person_name = sender_name.strip()
                                person_id = sender_id if sender_id and sender_id.strip() else None
                            elif sender_id and sender_id.strip():
                                sender_id_clean = sender_id.strip()
                                if len(sender_id_clean) > 50:
                                    continue
                                person_name = sender_id_clean
                                person_id = sender_id_clean
                            else:
                                continue
                    
                    if thread_id and person_name:
                        if thread_id not in thread_person_map:
                            thread_person_map[thread_id] = {
                                "name": person_name,
                                "id": person_id
                            }
                    else:
                        if direction_lower in ['outgoing', 'sent']:
                            if recipient_name and recipient_name.strip():
                                person_name = recipient_name.strip()
                                person_id = recipient_id if recipient_id and recipient_id.strip() else None
                            elif recipient_id and recipient_id.strip():
                                person_name = recipient_id.strip()
                                person_id = recipient_id.strip()
                            else:
                                continue
                        elif direction_lower in ['incoming', 'received']:
                            is_device_owner_sender = False
                            is_device_owner_recipient = False
                            
                            if device_owner_name:
                                is_device_owner_sender = sender_name_lower == device_owner_name
                                if not is_device_owner_sender:
                                    is_device_owner_sender = (
                                        device_owner_name in sender_name_lower or
                                        sender_name_lower in device_owner_name or
                                        (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                                    )
                                
                                is_device_owner_recipient = recipient_name_lower == device_owner_name
                                if not is_device_owner_recipient:
                                    is_device_owner_recipient = (
                                        device_owner_name in recipient_name_lower or
                                        recipient_name_lower in device_owner_name or
                                        (len(set(device_owner_name.split()) & set(recipient_name_lower.split())) > 0)
                                    )
                            
                            if is_device_owner_sender and is_device_owner_recipient:
                                continue
                            
                            if is_device_owner_sender:
                                if recipient_name and recipient_name.strip():
                                    recipient_lower = recipient_name.strip().lower()
                                    if not device_owner_name or recipient_lower != device_owner_name.lower():
                                        person_name = recipient_name
                                        person_id = recipient_id
                            elif is_device_owner_recipient:
                                if sender_name and sender_name.strip():
                                    sender_lower = sender_name.strip().lower()
                                    if not device_owner_name or sender_lower != device_owner_name.lower():
                                        person_name = sender_name
                                        person_id = sender_id
                            else:
                                if device_owner_name:
                                    if sender_name and sender_name.strip():
                                        sender_lower = sender_name.strip().lower()
                                        if sender_lower != device_owner_name.lower():
                                            person_name = sender_name
                                            person_id = sender_id
                                        elif recipient_name and recipient_name.strip():
                                            recipient_lower = recipient_name.strip().lower()
                                            if recipient_lower != device_owner_name.lower():
                                                person_name = recipient_name
                                                person_id = recipient_id
                                    elif recipient_name and recipient_name.strip():
                                        recipient_lower = recipient_name.strip().lower()
                                        if recipient_lower != device_owner_name.lower():
                                            person_name = recipient_name
                                            person_id = recipient_id
                                else:
                                    if sender_name and sender_name.strip():
                                        person_name = sender_name
                                        person_id = sender_id
                                    elif recipient_name and recipient_name.strip():
                                        person_name = recipient_name
                                        person_id = recipient_id
                        else:
                            is_device_owner_sender = False
                            is_device_owner_recipient = False
                            
                            if device_owner_name:
                                is_device_owner_sender = sender_name_lower == device_owner_name
                                if not is_device_owner_sender:
                                    is_device_owner_sender = (
                                        device_owner_name in sender_name_lower or
                                        sender_name_lower in device_owner_name or
                                        (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                                    )
                                
                                is_device_owner_recipient = recipient_name_lower == device_owner_name
                                if not is_device_owner_recipient:
                                    is_device_owner_recipient = (
                                        device_owner_name in recipient_name_lower or
                                        recipient_name_lower in device_owner_name or
                                        (len(set(device_owner_name.split()) & set(recipient_name_lower.split())) > 0)
                                    )
                            
                            if is_device_owner_sender and is_device_owner_recipient:
                                continue
                            
                            if is_device_owner_sender:
                                if recipient_name and recipient_name.strip():
                                    recipient_lower = recipient_name.strip().lower()
                                    if not device_owner_name or recipient_lower != device_owner_name.lower():
                                        person_name = recipient_name
                                        person_id = recipient_id
                            elif is_device_owner_recipient:
                                if sender_name and sender_name.strip():
                                    sender_lower = sender_name.strip().lower()
                                    if not device_owner_name or sender_lower != device_owner_name.lower():
                                        person_name = sender_name
                                        person_id = sender_id
                            else:
                                if device_owner_name:
                                    if sender_name and sender_name.strip():
                                        sender_lower = sender_name.strip().lower()
                                        if sender_lower != device_owner_name.lower():
                                            person_name = sender_name
                                            person_id = sender_id
                                        elif recipient_name and recipient_name.strip():
                                            recipient_lower = recipient_name.strip().lower()
                                            if recipient_lower != device_owner_name.lower():
                                                person_name = recipient_name
                                                person_id = recipient_id
                                    elif recipient_name and recipient_name.strip():
                                        recipient_lower = recipient_name.strip().lower()
                                        if recipient_lower != device_owner_name.lower():
                                            person_name = recipient_name
                                            person_id = recipient_id
                                else:
                                    if sender_name and sender_name.strip():
                                        person_name = sender_name
                                        person_id = sender_id
                                    elif recipient_name and recipient_name.strip():
                                        person_name = recipient_name
                                        person_id = recipient_id
                    
                    if person_name and device_owner_name:
                        person_name_lower = person_name.strip().lower()
                        device_owner_lower = device_owner_name.lower()
                        person_name_len = len(person_name_lower.strip())
                        device_owner_len = len(device_owner_lower.strip())
                        
                        if person_name_len <= 2 or device_owner_len <= 2:
                            if person_name_lower == device_owner_lower:
                                continue
                        else:
                            if (person_name_lower == device_owner_lower or
                                device_owner_lower in person_name_lower or
                                person_name_lower in device_owner_lower or
                                (len(set(device_owner_lower.split()) & set(person_name_lower.split())) > 0)):
                                continue
                    
                    if person_name:
                        person_key = person_name.strip()
                        if person_key:
                            thread_id = (msg.thread_id or msg.chat_id or "").strip()
                            if thread_id and thread_id in thread_group_map:
                                person_key = thread_group_map[thread_id]["name"].strip()
                                person_name = person_key
                            thread_person_messages[thread_id][person_key].append(msg)
                            stored_person_id = ""
                            
                            if chat_type and chat_type.lower() in ["group", "broadcast"]:
                                if msg.group_id:
                                    stored_person_id = (msg.group_id or "").strip()
                            elif chat_type and chat_type.lower() == "one on one":
                                if person_id:
                                    stored_person_id = person_id
                            elif direction_lower in ['outgoing', 'sent']:
                                if recipient_id and recipient_id.strip():
                                    stored_person_id = recipient_id.strip()
                            elif direction_lower in ['incoming', 'received']:
                                    sender_check = msg.from_name or ""
                                    if sender_check and device_owner_name:
                                        sender_check_lower = sender_check.strip().lower()
                                        is_not_device_owner = (
                                            sender_check_lower != device_owner_name and
                                            device_owner_name not in sender_check_lower and
                                            sender_check_lower not in device_owner_name and
                                            not (len(set(device_owner_name.split()) & set(sender_check_lower.split())) > 0)
                                        )
                                        if is_not_device_owner and person_id:
                                            stored_person_id = person_id
                                    elif not device_owner_name and person_id:
                                        stored_person_id = person_id
                                
                            person_direction = None
                            if direction_lower in ['outgoing', 'sent']:
                                person_direction = "Outgoing"
                            elif direction_lower in ['incoming', 'received']:
                                person_direction = "Incoming"
                            else:
                                person_direction = "Unknown"
                            
                            cleaned_person_name = None
                            if person_name:
                                person_name_stripped = person_name.strip()
                                cleaned_check = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', person_name_stripped)
                                if cleaned_check and cleaned_check.strip():
                                    cleaned_person_name = person_name_stripped
                            
                            if not cleaned_person_name and stored_person_id:
                                cleaned_person_name = stored_person_id.strip() if stored_person_id else None
                            
                            if person_key not in person_info:
                                person_info[person_key] = {
                                    "name": cleaned_person_name or person_key,
                                    "id": stored_person_id,
                                    "direction": person_direction
                                }
                            else:
                                if not person_info[person_key]["id"] and stored_person_id:
                                    person_info[person_key]["id"] = stored_person_id
                                
                                current_name = person_info[person_key].get("name", "")
                                current_name_cleaned = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', current_name) if current_name else ""
                                if (not current_name or not current_name_cleaned or not current_name_cleaned.strip()) and cleaned_person_name:
                                    person_info[person_key]["name"] = cleaned_person_name
                                elif not person_info[person_key].get("name") and cleaned_person_name:
                                    person_info[person_key]["name"] = cleaned_person_name
                                if not person_info[person_key].get("direction") or person_direction != "Unknown":
                                    person_info[person_key]["direction"] = person_direction
                
                person_intensity = defaultdict(int)
                
                for thread_id, persons in thread_person_messages.items():
                    person_keys_in_thread = list(persons.keys())
                    if person_keys_in_thread:
                        primary_key = None
                        for pk in person_keys_in_thread:
                            person_data = person_info.get(pk, {})
                            person_name_val = person_data.get("name", pk)
                            if person_name_val and not person_name_val.strip().isdigit() and len(person_name_val.strip()) > 3:
                                primary_key = pk
                                break
                        
                        if not primary_key:
                            primary_key = max(person_keys_in_thread, key=lambda pk: len(persons[pk]))
                        
                        all_messages_in_thread = []
                        merged_name = None
                        merged_id = None
                        
                        thread_chat_type = None
                        thread_group_name = None
                        thread_group_id = None
                        
                        if thread_id and thread_id in thread_group_map:
                            thread_chat_type = "group"
                            thread_group_name = thread_group_map[thread_id]["name"]
                            thread_group_id = thread_group_map[thread_id].get("id")
                        elif person_keys_in_thread:
                            first_person_messages = persons[person_keys_in_thread[0]]
                            if first_person_messages:
                                first_msg = first_person_messages[0]
                                msg_chat_type = (first_msg.chat_type or "").strip() if first_msg.chat_type else None
                                if msg_chat_type:
                                    msg_chat_type_lower = msg_chat_type.lower()
                                    if msg_chat_type_lower in ["group", "broadcast"]:
                                        thread_chat_type = msg_chat_type_lower
                                        thread_group_name = (first_msg.group_name or "").strip() if first_msg.group_name else None
                                        thread_group_id = (first_msg.group_id or "").strip() if first_msg.group_id else None
                        
                        for person_key in person_keys_in_thread:
                            messages = persons[person_key]
                            all_messages_in_thread.extend(messages)
                            
                            person_data = person_info.get(person_key, {})
                            name_val = person_data.get("name", person_key)
                            id_val = person_data.get("id", "")
                            
                            if thread_chat_type in ["group", "broadcast"] and thread_group_name:
                                if not merged_name or (thread_group_name and not thread_group_name.strip().isdigit() and len(thread_group_name.strip()) > 3):
                                    merged_name = thread_group_name
                            elif not merged_name or (name_val and not name_val.strip().isdigit() and len(name_val.strip()) > 3):
                                merged_name = name_val if name_val else merged_name
                        
                        for msg in all_messages_in_thread:
                            msg_direction = (msg.direction or "").strip().lower()
                            if msg_direction in ['outgoing', 'sent']:
                                to_name_val = (msg.to_name or "").strip()
                                if to_name_val and not to_name_val.strip().isdigit() and len(to_name_val.strip()) > 3:
                                    if not merged_name or merged_name.strip().isdigit() or len(merged_name.strip()) <= 3:
                                        merged_name = to_name_val
                                    break
                        
                        for msg in all_messages_in_thread:
                            direction = (msg.direction or "").strip().lower()
                            
                            if thread_chat_type in ["group", "broadcast"] and thread_group_id:
                                if not merged_id:
                                    merged_id = thread_group_id
                                break
                            
                            device_owner_name_local = None
                            if device.file_id == msg.file_id:
                                device_owner_name_local = (device.owner_name or "").strip().lower()
                            else:
                                for d in devices:
                                    if d.file_id == msg.file_id:
                                        device_owner_name_local = (d.owner_name or "").strip().lower()
                                        break
                            
                            if direction in ['outgoing', 'sent']:
                                recipient_id = msg.recipient_number or ""
                                recipient_name = (msg.to_name or "").strip()
                                
                                if recipient_name:
                                    recipient_name_lower = recipient_name.strip().lower()
                                    if device_owner_name:
                                        is_person = (
                                            recipient_name_lower != device_owner_name and
                                            device_owner_name not in recipient_name_lower and
                                            recipient_name_lower not in device_owner_name and
                                            not (len(set(device_owner_name.split()) & set(recipient_name_lower.split())) > 0)
                                        )
                                    else:
                                        is_person = True
                                    
                                    if is_person and recipient_id and recipient_id.strip():
                                        recipient_id_clean = recipient_id.strip()
                                        if len(recipient_id_clean) <= 50:
                                            if not merged_id:
                                                merged_id = recipient_id_clean
                                            elif merged_id.strip().isdigit() and not recipient_id_clean.strip().isdigit():
                                                merged_id = recipient_id_clean
                                            break
                            
                            elif direction in ['incoming', 'received']:
                                sender_id = msg.sender_number or ""
                                sender_name = (msg.from_name or "").strip()
                                
                                if sender_name:
                                    sender_name_lower = sender_name.strip().lower()
                                    if device_owner_name:
                                        is_person = (
                                            sender_name_lower != device_owner_name and
                                            device_owner_name not in sender_name_lower and
                                            sender_name_lower not in device_owner_name and
                                            not (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                                        )
                                    else:
                                        is_person = True
                                    
                                    if is_person and sender_id and sender_id.strip():
                                        sender_id_clean = sender_id.strip()
                                        if len(sender_id_clean) <= 50:
                                            if not merged_id:
                                                merged_id = sender_id_clean
                                            elif merged_id.strip().isdigit() and not sender_id_clean.strip().isdigit():
                                                merged_id = sender_id_clean
                                            break
                        
                        outgoing_count = 0
                        incoming_count = 0
                        for msg in all_messages_in_thread:
                            msg_direction = (msg.direction or "").strip().lower()
                            if msg_direction in ['outgoing', 'sent']:
                                outgoing_count += 1
                            elif msg_direction in ['incoming', 'received']:
                                incoming_count += 1
                        
                        thread_direction = None
                        if outgoing_count > incoming_count:
                            thread_direction = "Outgoing"
                        elif incoming_count > outgoing_count:
                            thread_direction = "Incoming"
                        else:
                            thread_direction = "Unknown"
                        
                        cleaned_merged_name = None
                        if merged_name:
                            merged_name_stripped = merged_name.strip()
                            cleaned_check = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', merged_name_stripped)
                            if cleaned_check and cleaned_check.strip():
                                cleaned_merged_name = merged_name_stripped
                        
                        if not cleaned_merged_name and merged_id:
                            cleaned_merged_name = merged_id.strip() if merged_id else None
                        
                        if primary_key in person_info:
                            current_name = person_info[primary_key].get("name", "")
                            current_name_cleaned = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', current_name) if current_name else ""
                            current_name_is_empty = not current_name or not current_name_cleaned or not current_name_cleaned.strip()
                            if current_name_is_empty or (current_name.strip().isdigit() and cleaned_merged_name and not cleaned_merged_name.strip().isdigit()):
                                if cleaned_merged_name:
                                    person_info[primary_key]["name"] = cleaned_merged_name
                            elif current_name_is_empty and cleaned_merged_name:
                                person_info[primary_key]["name"] = cleaned_merged_name
                            if not person_info[primary_key]["id"] and merged_id:
                                person_info[primary_key]["id"] = merged_id
                            if not person_info[primary_key].get("direction") or thread_direction != "Unknown":
                                person_info[primary_key]["direction"] = thread_direction
                        else:
                            person_info[primary_key] = {
                                "name": cleaned_merged_name or primary_key,
                                "id": merged_id or "",
                                "direction": thread_direction
                            }
                        
                        person_intensity[primary_key] += len(persons.get(primary_key, []))
                
                intensity_list = []
                for person_key, intensity_value in sorted(person_intensity.items(), key=lambda x: x[1], reverse=True):
                    person_data = person_info.get(person_key, {})
                    person_name = person_data.get("name", person_key)
                    person_id_value = person_data.get("id", "")
                    person_direction = person_data.get("direction", "Unknown")
                    
                    def is_empty_or_whitespace(s):
                        if not s:
                            return True
                        cleaned = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', s)
                        if len(cleaned) == 0:
                            return True
                        if not cleaned.strip():
                            return True
                        return False
                    
                    if person_name:
                        person_name_cleaned = person_name.strip()
                        if is_empty_or_whitespace(person_name_cleaned):
                            person_name = None
                        else:
                            person_name = person_name_cleaned
                    else:
                        person_name = None
                    
                    if not person_id_value or not person_id_value.strip():
                        person_id_value = None
                    else:
                        person_id_value = person_id_value.strip()
                    
                    if not person_name and person_id_value:
                        person_name = person_id_value
                    
                    if not person_name:
                        person_key_cleaned = None
                        if person_key:
                            person_key_stripped = person_key.strip()
                            person_key_cleaned_check = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', person_key_stripped)
                            if person_key_cleaned_check and person_key_cleaned_check.strip():
                                person_key_cleaned = person_key_stripped
                        
                        if person_key_cleaned:
                            person_name = person_key_cleaned
                    
                    if not person_name or person_name.strip() == "":
                        person_name = "Unknown"
                    
                    if person_name and person_id_value and person_name == person_id_value:
                        pass
                    elif person_name and not person_id_value:
                        if person_name.isdigit() or (len(person_name) > 10 and person_name.replace('+', '').replace('-', '').isdigit()):
                            person_id_value = person_name
                    
                    intensity_list.append({
                        "person": person_name,
                        "person_id": person_id_value,
                        "intensity": intensity_value,
                        "direction": person_direction
                    })
                
                platform_card = {
                    "platform": platform_display,
                    "has_data": has_data,
                    "message_count": message_count
                }
                
                if has_data:
                    platform_card["intensity_list"] = intensity_list
                else:
                    platform_card["person"] = None
                    platform_card["intensity"] = 0
                
                platform_cards.append(platform_card)
            
            devices_with_platforms.append({
                "device_id": device.id,
                "device_name": device.owner_name or "Unknown",
                "phone_number": device.phone_number or "",
                "platform_cards": platform_cards
            })
        
        if device_id:
            devices_with_platforms = [
                d for d in devices_with_platforms if d["device_id"] == device_id
            ]
        
        summary_value = analytic.summary if analytic.summary else None

        return JSONResponse(
            content={
                "status": 200,
                "message": "Deep Communication Analytics retrieved successfully",
                "data": {
                    "analytic_info": {
                        "analytic_id": analytic_id,
                        "analytic_name": analytic.analytic_name or "Unknown"
                    },
                    "devices": devices_with_platforms,
                    "summary": summary_value
                }
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        return JSONResponse(
            content={
                "status": 500,
                "message": "Internal server error: Failed to retrieve deep communication analytics",
                "data": None
            },
            status_code=500
        )

@router.get("/analytic/platform-cards/intensity")
def get_platform_cards_intensity(  # type: ignore[reportGeneralTypeIssues]
    analytic_id: int = Query(..., description="Analytic ID"),
    platform: str = Query(..., description="Platform name (Instagram, Telegram, WhatsApp, Facebook, X, TikTok)"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not platform or not platform.strip():
            return JSONResponse(
                content={
                    "status": 400,
                    "message": "Platform parameter is required"
                },
                status_code=400
            )
        
        normalized = normalize_platform_name(platform)
        valid_platforms = ['instagram', 'telegram', 'whatsapp', 'facebook', 'x', 'tiktok']
        if normalized not in valid_platforms:
            return JSONResponse(
                content={
                    "status": 400,
                    "message": f"Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok"
                },
                status_code=400
            )
        
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Analytic with ID {analytic_id} not found",
                    "data": {
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": "Unknown"
                        },
                        "next_action": "create_analytic",
                        "redirect_to": "/analytics/start-analyzing",
                        "instruction": "Please create a new analytic with method 'Deep Communication Analytics'"
                    }
                },
                status_code=404
            )
        
        if current_user is not None and not check_analytic_access(analytic, current_user):
            return JSONResponse(
                content={
                    "status": 403,
                    "message": "You do not have permission to access this analytic"
                },
                status_code=403
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).order_by(AnalyticDevice.id).all()
            
        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        device_ids = list(set(device_ids))
        
        if not device_ids:
            summary_value = analytic.summary if analytic.summary else None
            
            return JSONResponse(
                content={
                    "status": 200,
                    "message": "Platform cards intensity retrieved successfully",
                    "data": {
                        "analytic_id": analytic_id,
                        "platform": platform,
                        "device_id": device_id,
                        "intensity_list": [],
                        "summary": summary_value
                    }
                },
                status_code=200
            )
        
        if device_id:
            if device_id not in device_ids:
                return JSONResponse(
                    content={
                        "status": 404,
                        "message": "Device not found in this analytic",
                        "data": {
                            "analytic_info": {
                                "analytic_id": analytic_id,
                                "analytic_name": analytic.analytic_name or "Unknown"
                            },
                            "device_id": device_id,
                            "next_action": "add_device",
                            "redirect_to": "/analytics/devices",
                            "instruction": "The specified device is not linked to this analytic. Please add the device first."
                        }
                    },
                    status_code=404
                )
            device_ids = [device_id]

        devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
        file_ids = [d.file_id for d in devices]
        
        if not file_ids:
            summary_value = analytic.summary if analytic.summary else None
            return JSONResponse(
                content={
                    "status": 200,
                    "message": "Platform cards intensity retrieved successfully",
                    "data": {
                        "analytic_id": analytic_id,
                        "platform": platform,
                        "device_id": device_id,
                        "intensity_list": [],
                        "summary": summary_value
                    }
                },
                status_code=200
            )
        
        normalized_platform = normalize_platform_name(platform)
        messages = get_chat_messages_for_analytic(db, analytic_id, device_id, platform, file_ids)
        
        platform_messages = [
                msg for msg in messages 
            if normalize_platform_name(msg.platform or '') == normalized_platform
        ]
        
        thread_person_messages = defaultdict(lambda: defaultdict(list))
        person_info = {}
        
        thread_person_map = {}
        thread_group_map = {}
        
        for msg in platform_messages:
            thread_id = (msg.thread_id or msg.chat_id or "").strip()
            if thread_id:
                chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
                if chat_type:
                    chat_type_lower = chat_type.lower()
                    if chat_type_lower in ["group", "broadcast"]:
                        group_name = (msg.group_name or "").strip() if msg.group_name else None
                        if group_name and group_name.strip():
                            if thread_id not in thread_group_map:
                                thread_group_map[thread_id] = {
                                    "name": group_name.strip(),
                                    "id": (msg.group_id or "").strip() if msg.group_id else None
                                }
        
        for msg in platform_messages:
            sender_name = msg.from_name or ""
            sender_id = msg.sender_number or ""
            recipient_name = msg.to_name or ""
            recipient_id = msg.recipient_number or ""
            chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
            group_name = (msg.group_name or "").strip() if msg.group_name else None
            
            sender_name_lower = (sender_name or "").strip().lower()
            recipient_name_lower = (recipient_name or "").strip().lower()
            
            direction = (msg.direction or "").strip()
            direction_lower = direction.lower()
            
            person_name = None
            person_id = None
            
            thread_id = (msg.thread_id or msg.chat_id or "").strip()
            
            if thread_id and thread_id in thread_group_map:
                person_name = thread_group_map[thread_id]["name"]
                person_id = thread_group_map[thread_id].get("id")
            elif chat_type:
                chat_type_lower = chat_type.lower()
                if chat_type_lower in ["group", "broadcast"]:
                    if group_name and group_name.strip():
                        person_name = group_name.strip()
                        person_id = (msg.group_id or "").strip() if msg.group_id else None
                    elif thread_id and thread_id in thread_group_map:
                        person_name = thread_group_map[thread_id]["name"]
                        person_id = thread_group_map[thread_id].get("id")
                elif chat_type_lower == "one on one":
                    if direction_lower in ['outgoing', 'sent']:
                       
                        if recipient_name and recipient_name.strip():
                            person_name = recipient_name.strip()
                            person_id = recipient_id if recipient_id and recipient_id.strip() else None
                        elif recipient_id and recipient_id.strip():
                            person_name = recipient_id.strip()
                            person_id = recipient_id.strip()
                    else:
                        if sender_name and sender_name.strip():
                            person_name = sender_name.strip()
                            person_id = sender_id if sender_id and sender_id.strip() else None
            
            if not person_name:
                if direction_lower in ['outgoing', 'sent']:
                   
                    if recipient_name and recipient_name.strip():
                        recipient_name_clean = recipient_name.strip()
                        if len(recipient_name_clean) > 50 or (recipient_name_clean.isdigit() and len(recipient_name_clean) > 20):
                            if recipient_id and recipient_id.strip() and len(recipient_id.strip()) <= 50:
                                person_name = recipient_id.strip()
                                person_id = recipient_id.strip()
                            elif thread_id and thread_id in thread_person_map:
                                person_name = thread_person_map[thread_id]["name"]
                                person_id = thread_person_map[thread_id].get("id")
                            else:
                                continue
                        else:
                            person_name = recipient_name_clean
                            person_id = recipient_id if recipient_id and recipient_id.strip() else None
                    elif recipient_id and recipient_id.strip():
                        recipient_id_clean = recipient_id.strip()
                        if len(recipient_id_clean) > 50:
                            if thread_id and thread_id in thread_person_map:
                                person_name = thread_person_map[thread_id]["name"]
                                person_id = thread_person_map[thread_id].get("id")
                            else:
                                continue
                        else:
                            person_name = recipient_id_clean
                            person_id = recipient_id_clean
                    else:
                        if thread_id and thread_id in thread_person_map:
                            person_name = thread_person_map[thread_id]["name"]
                            person_id = thread_person_map[thread_id].get("id")
                        else:
                            continue
                elif direction_lower in ['incoming', 'received']:
                    if sender_name and sender_name.strip():
                        person_name = sender_name.strip()
                        person_id = sender_id if sender_id and sender_id.strip() else None
                    elif sender_id and sender_id.strip():
                        sender_id_clean = sender_id.strip()
                        if len(sender_id_clean) > 50:
                            continue
                        person_name = sender_id_clean
                        person_id = sender_id_clean
                    else:
                        continue
            
            if thread_id and person_name:
                if thread_id not in thread_person_map:
                    thread_person_map[thread_id] = {
                        "name": person_name,
                        "id": person_id
                    }
            else:
                if direction_lower in ['outgoing', 'sent']:
                   
                    if recipient_name and recipient_name.strip():
                        person_name = recipient_name.strip()
                        person_id = recipient_id if recipient_id and recipient_id.strip() else None
                    elif recipient_id and recipient_id.strip():
                        person_name = recipient_id.strip()
                        person_id = recipient_id.strip()
                    else:
                        continue
                elif direction_lower in ['incoming', 'received']:
                    device_owner_name = None
                    for d in devices:
                        if d.file_id == msg.file_id:
                            device_owner_name = (d.owner_name or "").strip().lower()
                            break
                    
                    is_device_owner_sender = False
                    is_device_owner_recipient = False
                    
                    if device_owner_name:
                        is_device_owner_sender = sender_name_lower == device_owner_name
                        if not is_device_owner_sender:
                            is_device_owner_sender = (
                                device_owner_name in sender_name_lower or
                                sender_name_lower in device_owner_name or
                                (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                            )
                        
                        is_device_owner_recipient = recipient_name_lower == device_owner_name
                        if not is_device_owner_recipient:
                            is_device_owner_recipient = (
                                device_owner_name in recipient_name_lower or
                                recipient_name_lower in device_owner_name or
                                (len(set(device_owner_name.split()) & set(recipient_name_lower.split())) > 0)
                            )
                    
                    if is_device_owner_sender and is_device_owner_recipient:
                        continue
                    
                    if is_device_owner_sender:
                        if recipient_name and recipient_name.strip():
                            recipient_lower = recipient_name.strip().lower()
                            if not device_owner_name or recipient_lower != device_owner_name.lower():
                                person_name = recipient_name
                                person_id = recipient_id
                    elif is_device_owner_recipient:
                        if sender_name and sender_name.strip():
                            sender_lower = sender_name.strip().lower()
                            if not device_owner_name or sender_lower != device_owner_name.lower():
                                person_name = sender_name
                                person_id = sender_id
                    else:
                        if device_owner_name:
                            if sender_name and sender_name.strip():
                                sender_lower = sender_name.strip().lower()
                                if sender_lower != device_owner_name.lower():
                                    person_name = sender_name
                                    person_id = sender_id
                                elif recipient_name and recipient_name.strip():
                                    recipient_lower = recipient_name.strip().lower()
                                    if recipient_lower != device_owner_name.lower():
                                        person_name = recipient_name
                                        person_id = recipient_id
                            elif recipient_name and recipient_name.strip():
                                recipient_lower = recipient_name.strip().lower()
                                if recipient_lower != device_owner_name.lower():
                                    person_name = recipient_name
                                    person_id = recipient_id
                        else:
                            if sender_name and sender_name.strip():
                                person_name = sender_name
                                person_id = sender_id
                            elif recipient_name and recipient_name.strip():
                                person_name = recipient_name
                                person_id = recipient_id
                else:
                    device_owner_name = None
                    for d in devices:
                        if d.file_id == msg.file_id:
                            device_owner_name = (d.owner_name or "").strip().lower()
                            break
                    
                    is_device_owner_sender = False
                    is_device_owner_recipient = False
                    
                    if device_owner_name:
                        is_device_owner_sender = sender_name_lower == device_owner_name
                        if not is_device_owner_sender:
                            is_device_owner_sender = (
                                device_owner_name in sender_name_lower or
                                sender_name_lower in device_owner_name or
                                (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                            )
                        
                        is_device_owner_recipient = recipient_name_lower == device_owner_name
                        if not is_device_owner_recipient:
                            is_device_owner_recipient = (
                                device_owner_name in recipient_name_lower or
                                recipient_name_lower in device_owner_name or
                                (len(set(device_owner_name.split()) & set(recipient_name_lower.split())) > 0)
                            )
                    
                    if is_device_owner_sender and is_device_owner_recipient:
                        continue
                    
                    if is_device_owner_sender:
                        if recipient_name and recipient_name.strip():
                            recipient_lower = recipient_name.strip().lower()
                            if not device_owner_name or recipient_lower != device_owner_name.lower():
                                person_name = recipient_name
                                person_id = recipient_id
                    elif is_device_owner_recipient:
                        if sender_name and sender_name.strip():
                            sender_lower = sender_name.strip().lower()
                            if not device_owner_name or sender_lower != device_owner_name.lower():
                                person_name = sender_name
                                person_id = sender_id
                    else:
                        if device_owner_name:
                            if sender_name and sender_name.strip():
                                sender_lower = sender_name.strip().lower()
                                if sender_lower != device_owner_name.lower():
                                    person_name = sender_name
                                    person_id = sender_id
                                elif recipient_name and recipient_name.strip():
                                    recipient_lower = recipient_name.strip().lower()
                                    if recipient_lower != device_owner_name.lower():
                                        person_name = recipient_name
                                        person_id = recipient_id
                            elif recipient_name and recipient_name.strip():
                                recipient_lower = recipient_name.strip().lower()
                                if recipient_lower != device_owner_name.lower():
                                    person_name = recipient_name
                                    person_id = recipient_id
                        else:
                            if sender_name and sender_name.strip():
                                person_name = sender_name
                                person_id = sender_id
                            elif recipient_name and recipient_name.strip():
                                person_name = recipient_name
                                person_id = recipient_id
            
            device_owner_name = None
            for d in devices:
                if d.file_id == msg.file_id:
                    device_owner_name = (d.owner_name or "").strip().lower()
                    break
            
            if person_name and device_owner_name:
                person_name_lower = person_name.strip().lower()
                device_owner_lower = device_owner_name.lower()
                person_name_len = len(person_name_lower.strip())
                device_owner_len = len(device_owner_lower.strip())
                
                if person_name_len <= 2 or device_owner_len <= 2:
                    if person_name_lower == device_owner_lower:
                        continue
                else:
                    if (person_name_lower == device_owner_lower or
                        device_owner_lower in person_name_lower or
                        person_name_lower in device_owner_lower or
                        (len(set(device_owner_lower.split()) & set(person_name_lower.split())) > 0)):
                        continue
            
            if person_name:
                person_key = person_name.strip()
                if person_key:
                    thread_id = (msg.thread_id or msg.chat_id or "").strip()
                    if thread_id and thread_id in thread_group_map:
                        person_key = thread_group_map[thread_id]["name"].strip()
                        person_name = person_key
                    thread_person_messages[thread_id][person_key].append(msg)
                    stored_person_id = ""
                    
                    if chat_type and chat_type.lower() in ["group", "broadcast"]:
                        if msg.group_id:
                            stored_person_id = (msg.group_id or "").strip()
                    elif chat_type and chat_type.lower() == "one on one":
                        if person_id:
                            stored_person_id = person_id
                    elif direction_lower in ['outgoing', 'sent']:
                        if recipient_id and recipient_id.strip():
                            stored_person_id = recipient_id.strip()
                    elif direction_lower in ['incoming', 'received']:
                        sender_check = msg.from_name or ""
                        if sender_check and device_owner_name:
                            sender_check_lower = sender_check.strip().lower()
                            is_not_device_owner = (
                                sender_check_lower != device_owner_name and
                                device_owner_name not in sender_check_lower and
                                sender_check_lower not in device_owner_name and
                                not (len(set(device_owner_name.split()) & set(sender_check_lower.split())) > 0)
                            )
                            if is_not_device_owner and person_id:
                                stored_person_id = person_id
                        elif not device_owner_name and person_id:
                            stored_person_id = person_id
                    
                    person_direction = None
                    if direction_lower in ['outgoing', 'sent']:
                        person_direction = "Outgoing"
                    elif direction_lower in ['incoming', 'received']:
                        person_direction = "Incoming"
                    else:
                        person_direction = "Unknown"
                    
                    cleaned_person_name = None
                    if person_name:
                        person_name_stripped = person_name.strip()
                        cleaned_check = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', person_name_stripped)
                        if cleaned_check and cleaned_check.strip():
                            cleaned_person_name = person_name_stripped
                    
                    if not cleaned_person_name and stored_person_id:
                        cleaned_person_name = stored_person_id.strip() if stored_person_id else None
                    
                    if person_key not in person_info:
                        person_info[person_key] = {
                            "name": cleaned_person_name or person_key,
                            "id": stored_person_id,
                            "direction": person_direction
                        }
                    else:
                        if not person_info[person_key]["id"] and stored_person_id:
                            person_info[person_key]["id"] = stored_person_id
        
                        current_name = person_info[person_key].get("name", "")

                        current_name_cleaned = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', current_name) if current_name else ""
                        if (not current_name or not current_name_cleaned or not current_name_cleaned.strip()) and cleaned_person_name:
                            person_info[person_key]["name"] = cleaned_person_name
                        elif not person_info[person_key].get("name") and cleaned_person_name:
                            person_info[person_key]["name"] = cleaned_person_name
                        if not person_info[person_key].get("direction") or person_direction != "Unknown":
                            person_info[person_key]["direction"] = person_direction
        
        person_intensity = defaultdict(int)
        for thread_id, persons in thread_person_messages.items():
            person_keys_in_thread = list(persons.keys())
            if person_keys_in_thread:
                primary_key = None
                for pk in person_keys_in_thread:
                    person_data = person_info.get(pk, {})
                    person_name_val = person_data.get("name", pk)
                    person_id_val = person_data.get("id", "")
                    
                    if person_name_val and not person_name_val.strip().isdigit() and len(person_name_val.strip()) > 3:
                        primary_key = pk
                        break
                
                if not primary_key:
                    primary_key = max(person_keys_in_thread, key=lambda pk: len(persons[pk]))
                
                all_messages_in_thread = []
                merged_name = None
                merged_id = None
                
                thread_chat_type = None
                thread_group_name = None
                thread_group_id = None
                
                if thread_id and thread_id in thread_group_map:
                    thread_chat_type = "group"
                    thread_group_name = thread_group_map[thread_id]["name"]
                    thread_group_id = thread_group_map[thread_id].get("id")
                elif person_keys_in_thread:
                    first_person_messages = persons[person_keys_in_thread[0]]
                    if first_person_messages:
                        first_msg = first_person_messages[0]
                        msg_chat_type = (first_msg.chat_type or "").strip() if first_msg.chat_type else None
                        if msg_chat_type:
                            msg_chat_type_lower = msg_chat_type.lower()
                            if msg_chat_type_lower in ["group", "broadcast"]:
                                thread_chat_type = msg_chat_type_lower
                                thread_group_name = (first_msg.group_name or "").strip() if first_msg.group_name else None
                                thread_group_id = (first_msg.group_id or "").strip() if first_msg.group_id else None
                
                for person_key in person_keys_in_thread:
                    messages = persons[person_key]
                    all_messages_in_thread.extend(messages)
                    
                    person_data = person_info.get(person_key, {})
                    name_val = person_data.get("name", person_key)
                    id_val = person_data.get("id", "")
                    
                    if thread_chat_type in ["group", "broadcast"] and thread_group_name:
                        if not merged_name or (thread_group_name and not thread_group_name.strip().isdigit() and len(thread_group_name.strip()) > 3):
                            merged_name = thread_group_name
                    elif not merged_name or (name_val and not name_val.strip().isdigit() and len(name_val.strip()) > 3):
                        merged_name = name_val if name_val else merged_name
                
                for msg in all_messages_in_thread:
                    msg_direction = (msg.direction or "").strip().lower()
                    if msg_direction in ['outgoing', 'sent']:
                        to_name_val = (msg.to_name or "").strip()
                        if to_name_val and not to_name_val.strip().isdigit() and len(to_name_val.strip()) > 3:
                            if not merged_name or merged_name.strip().isdigit() or len(merged_name.strip()) <= 3:
                                merged_name = to_name_val
                            break
                
                for msg in all_messages_in_thread:
                    direction = (msg.direction or "").strip().lower()

                    if thread_chat_type in ["group", "broadcast"] and thread_group_id:
                        if not merged_id:
                            merged_id = thread_group_id
                        break
                    
                    device_owner_name = None
                    for d in devices:
                        if d.file_id == msg.file_id:
                            device_owner_name = (d.owner_name or "").strip().lower()
                            break
                    
                    if direction in ['outgoing', 'sent']:
                        recipient_id = msg.recipient_number or ""
                        recipient_name = (msg.to_name or "").strip()
                        
                        if recipient_name:
                            recipient_name_lower = recipient_name.strip().lower()
                            if device_owner_name:
                                is_person = (
                                    recipient_name_lower != device_owner_name and
                                    device_owner_name not in recipient_name_lower and
                                    recipient_name_lower not in device_owner_name and
                                    not (len(set(device_owner_name.split()) & set(recipient_name_lower.split())) > 0)
                                )
                            else:
                                is_person = True
                            
                            if is_person and recipient_id and recipient_id.strip():
                                recipient_id_clean = recipient_id.strip()
                                if len(recipient_id_clean) <= 50:
                                    if not merged_id:
                                        merged_id = recipient_id_clean
                                    elif merged_id.strip().isdigit() and not recipient_id_clean.strip().isdigit():
                                        merged_id = recipient_id_clean
                                    break

                    elif direction in ['incoming', 'received']:
                        sender_id = msg.sender_number or ""
                        sender_name = (msg.from_name or "").strip()
                        
                        if sender_name:
                            sender_name_lower = sender_name.strip().lower()
                            if device_owner_name:
                                is_person = (
                                    sender_name_lower != device_owner_name and
                                    device_owner_name not in sender_name_lower and
                                    sender_name_lower not in device_owner_name and
                                    not (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                                )
                            else:
                                is_person = True
                            
                            if is_person and sender_id and sender_id.strip():
                                sender_id_clean = sender_id.strip()
                                if len(sender_id_clean) <= 50:
                                    if not merged_id:
                                        merged_id = sender_id_clean
                                    elif merged_id.strip().isdigit() and not sender_id_clean.strip().isdigit():
                                        merged_id = sender_id_clean
                                    break
                
                outgoing_count = 0
                incoming_count = 0
                for msg in all_messages_in_thread:
                    msg_direction = (msg.direction or "").strip().lower()
                    if msg_direction in ['outgoing', 'sent']:
                        outgoing_count += 1
                    elif msg_direction in ['incoming', 'received']:
                        incoming_count += 1
                
                thread_direction = None
                if outgoing_count > incoming_count:
                    thread_direction = "Outgoing"
                elif incoming_count > outgoing_count:
                    thread_direction = "Incoming"
                else:
                    thread_direction = "Unknown"

                cleaned_merged_name = None
                if merged_name:
                    merged_name_stripped = merged_name.strip()

                    cleaned_check = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', merged_name_stripped)
                    if cleaned_check and cleaned_check.strip():
                        cleaned_merged_name = merged_name_stripped
                
                if not cleaned_merged_name and merged_id:
                    cleaned_merged_name = merged_id.strip() if merged_id else None
                
                if primary_key in person_info:
                    current_name = person_info[primary_key].get("name", "")
                    current_name_cleaned = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', current_name) if current_name else ""
                    current_name_is_empty = not current_name or not current_name_cleaned or not current_name_cleaned.strip()
                    if current_name_is_empty or (current_name.strip().isdigit() and cleaned_merged_name and not cleaned_merged_name.strip().isdigit()):
                        if cleaned_merged_name:
                            person_info[primary_key]["name"] = cleaned_merged_name
                    elif current_name_is_empty and cleaned_merged_name:
                        person_info[primary_key]["name"] = cleaned_merged_name
                    if not person_info[primary_key]["id"] and merged_id:
                        person_info[primary_key]["id"] = merged_id
                    if not person_info[primary_key].get("direction") or thread_direction != "Unknown":
                        person_info[primary_key]["direction"] = thread_direction
                else:
                    person_info[primary_key] = {
                        "name": cleaned_merged_name or primary_key,
                        "id": merged_id or "",
                        "direction": thread_direction
                    }
                
                person_intensity[primary_key] += len(persons.get(primary_key, []))
        
        intensity_list = []
        for person_key, intensity_value in sorted(person_intensity.items(), key=lambda x: x[1], reverse=True):
            person_data = person_info.get(person_key, {})
            person_name = person_data.get("name", person_key)
            person_id_value = person_data.get("id", "")
            person_direction = person_data.get("direction", "Unknown")
            
            def is_empty_or_whitespace(s):
                if not s:
                    return True

                cleaned = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', s)
                if len(cleaned) == 0:
                    return True
        
                if not cleaned.strip():
                    return True
                return False
            
            if person_name:
                person_name_cleaned = person_name.strip()
                if is_empty_or_whitespace(person_name_cleaned):
                    person_name = None
                else:
                    person_name = person_name_cleaned
            else:
                person_name = None
            
            if not person_id_value or not person_id_value.strip():
                person_id_value = None
            else:
                person_id_value = person_id_value.strip()
            
            if not person_name and person_id_value:
                person_name = person_id_value
            
            if not person_name:
                person_key_cleaned = None
                if person_key:
                    person_key_stripped = person_key.strip()
                    person_key_cleaned_check = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', person_key_stripped)
                    if person_key_cleaned_check and person_key_cleaned_check.strip():
                        person_key_cleaned = person_key_stripped
                
                if person_key_cleaned:
                    person_name = person_key_cleaned
            
            if not person_name or person_name.strip() == "":
                person_name = "Unknown"
            
            if person_name and person_id_value and person_name == person_id_value:
                pass
            elif person_name and not person_id_value:
                if person_name.isdigit() or (len(person_name) > 10 and person_name.replace('+', '').replace('-', '').isdigit()):
                    person_id_value = person_name
            
            intensity_list.append({
                "person": person_name,
                "person_id": person_id_value,
                "intensity": intensity_value,
                "direction": person_direction
            })
        
        platform_display = platform
        
        summary_value = analytic.summary if analytic.summary else None

        return JSONResponse(
            content={
                "status": 200,
                "message": "Platform cards intensity retrieved successfully",
                "data": {
                    "analytic_id": analytic_id,
                    "platform": platform_display,
                    "device_id": device_id,
                    "intensity_list": intensity_list,
                    "summary": summary_value
                }
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        return JSONResponse(
            content={
                "status": 500,
                "message": "Internal server error: Failed to retrieve platform cards intensity",
                "data": None
            },
            status_code=500
        )

@router.get("/analytic/chat-detail")
def get_chat_detail(  # type: ignore[reportGeneralTypeIssues]
    analytic_id: int = Query(..., description="Analytic ID"),
    person_name: Optional[str] = Query(None, description="Person name to filter chat details (optional if using search only)"),
    platform: Optional[str] = Query(None, description="Platform name (optional, can filter by search only)"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    search: Optional[str] = Query(None, description="Search text in messages (optional)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not person_name and not search:
            return JSONResponse(
                content={
                    "status": 400,
                    "message": "Either person_name or search parameter must be provided"
                },
                status_code=400
            )
        
        if platform:
            if not platform.strip():
                return JSONResponse(
                    content={
                        "status": 400,
                        "message": "Platform parameter cannot be empty"
                    },
                    status_code=400
                )
            
            normalized = normalize_platform_name(platform)
            valid_platforms = ['instagram', 'telegram', 'whatsapp', 'facebook', 'x', 'tiktok']
            if normalized not in valid_platforms:
                return JSONResponse(
                    content={
                        "status": 400,
                    "message": f"Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok"
                },
                status_code=400
            )
        
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": f"Analytic with ID {analytic_id} not found",
                    "data": {
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": "Unknown"
                        },
                        "next_action": "create_analytic",
                        "redirect_to": "/analytics/start-analyzing",
                        "instruction": "Please create a new analytic with method 'Deep Communication Analytics'"
                    }
                },
                status_code=404
            )
        
        if current_user is not None and not check_analytic_access(analytic, current_user):
            return JSONResponse(
                content={
                    "status": 403,
                    "message": "You do not have permission to access this analytic"
                },
                status_code=403
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).order_by(AnalyticDevice.id).all()
            
        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        device_ids = list(set(device_ids))
        
        if not device_ids:
            return JSONResponse(
                content={
                    "status": 200,
                    "message": "No devices linked",
                    "data": {
                        "person_name": person_name,
                        "platform": platform,
                        "chat_messages": []
                    }
                },
                status_code=200
            )

        if device_id:
            if device_id not in device_ids:
                return JSONResponse(
                    content={
                        "status": 404,
                        "message": "Device not found in this analytic"
                    },
                    status_code=404
                )
            device_ids = [device_id]

        devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
        file_ids = [d.file_id for d in devices]
        
        messages = get_chat_messages_for_analytic(db, analytic_id, device_id, platform, file_ids)
        
        chat_messages = []
        filtered_messages = []
        normalized_platform = normalize_platform_name(platform) if platform else None
        person_name_normalized = person_name.strip().lower() if person_name else None
        search_lower = search.lower() if search else None
        
        thread_person_map = {}
        thread_group_map = {}
        
        if person_name_normalized:
            for msg in messages:
                if normalized_platform:
                    msg_platform_normalized = normalize_platform_name(msg.platform or '')
                    if msg_platform_normalized != normalized_platform:
                        continue
                
                thread_id = (msg.thread_id or msg.chat_id or "").strip()
                if thread_id:
                    chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
                    if chat_type:
                        chat_type_lower = chat_type.lower()
                        if chat_type_lower in ["group", "broadcast"]:
                            group_name = (msg.group_name or "").strip() if msg.group_name else None
                            if group_name and group_name.strip():
                                group_name_lower = group_name.strip().lower()
                                person_name_len = len(person_name_normalized.strip())
                                if person_name_len <= 2:
                                    if group_name_lower == person_name_normalized:
                                        if thread_id not in thread_group_map:
                                            thread_group_map[thread_id] = group_name.strip()
                                else:
                                    if group_name_lower == person_name_normalized or person_name_normalized in group_name_lower:
                                        if thread_id not in thread_group_map:
                                            thread_group_map[thread_id] = group_name.strip()
        
        if person_name_normalized:
            for msg in messages:
                if normalized_platform:
                    msg_platform_normalized = normalize_platform_name(msg.platform or '')
                    if msg_platform_normalized != normalized_platform:
                        continue
                
                thread_id = (msg.thread_id or msg.chat_id or "").strip()
                chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
                
                if thread_id and thread_id in thread_group_map:
                        continue
                
                direction = (msg.direction or "").strip().lower()
                if direction in ['incoming', 'received']:
                    sender_name = (msg.from_name or "").strip().lower()
                    sender_number = (msg.sender_number or "").strip()
                    person_name_len = len(person_name_normalized.strip())
                    
                    is_likely_id = person_name_normalized.isdigit() or (len(person_name_normalized) >= 5 and person_name_normalized.replace(' ', '').isdigit())
                    
                    name_matched = False
                    if person_name_len == 1:
                        if sender_name == person_name_normalized:
                            name_matched = True
                    elif person_name_len == 2:
                        if sender_name == person_name_normalized:
                            name_matched = True
                        else:
                            sender_words = sender_name.split()
                            for word in sender_words:
                                if word.strip().lower() == person_name_normalized:
                                    name_matched = True
                                    break
                    else:
                        if sender_name == person_name_normalized or person_name_normalized in sender_name:
                            name_matched = True
                    
                    number_matched = False
                    if is_likely_id and sender_number and sender_number.strip():
                        sender_number_normalized = sender_number.strip().lower()
                        if sender_number_normalized == person_name_normalized:
                            number_matched = True
                    
                    if (name_matched or number_matched) and thread_id:
                        thread_person_map[thread_id] = person_name_normalized
        
        for msg in messages:
            if normalized_platform:
                msg_platform_normalized = normalize_platform_name(msg.platform or '')
                if msg_platform_normalized != normalized_platform:
                    continue
            
            device_owner_name = None
            for d in devices:
                if d.file_id == msg.file_id:
                    device_owner_name = (d.owner_name or "").strip().lower()
                    break
            
            if person_name_normalized:
                sender_name = (msg.from_name or "").strip().lower()
                recipient_name = (msg.to_name or "").strip().lower()
                thread_id = (msg.thread_id or msg.chat_id or "").strip()
                chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
                group_name = (msg.group_name or "").strip() if msg.group_name else None
                
                group_match = False
                person_name_len = len(person_name_normalized.strip()) if person_name_normalized else 0
                if thread_id and thread_id in thread_group_map:
                    group_name_from_map = thread_group_map[thread_id].lower()
                    if person_name_len == 1:
                        if group_name_from_map == person_name_normalized:
                            group_match = True
                    elif person_name_len == 2:
                        if group_name_from_map == person_name_normalized:
                            group_match = True
                    else:
                        if group_name_from_map == person_name_normalized or person_name_normalized in group_name_from_map:
                            group_match = True
                elif chat_type and chat_type.lower() in ["group", "broadcast"]:
                    if group_name:
                        group_name_lower = group_name.strip().lower()
                        if person_name_len == 1:
                            if group_name_lower == person_name_normalized:
                                group_match = True
                        elif person_name_len == 2:
                            if group_name_lower == person_name_normalized:
                                group_match = True
                        else:
                            if group_name_lower == person_name_normalized or person_name_normalized in group_name_lower:
                                group_match = True
                
                sender_match = sender_name == person_name_normalized
                recipient_match = recipient_name == person_name_normalized
                
                sender_number = (msg.sender_number or "").strip()
                recipient_number = (msg.recipient_number or "").strip()
                
                is_likely_id = person_name_normalized.isdigit() or (len(person_name_normalized) >= 5 and person_name_normalized.replace(' ', '').isdigit())
                
                if is_likely_id:
                    if sender_number and sender_number.strip():
                        sender_number_normalized = sender_number.strip().lower()
                        if sender_number_normalized == person_name_normalized:
                            sender_match = True
                    if recipient_number and recipient_number.strip():
                        recipient_number_normalized = recipient_number.strip().lower()
                        if recipient_number_normalized == person_name_normalized:
                            recipient_match = True
                
                if person_name_normalized:
                    person_name_len = len(person_name_normalized.strip())
                else:
                    person_name_len = 0
                
                if not sender_match and person_name_len > 2:
                    if person_name_normalized in sender_name:
                        sender_match = True
                    elif sender_name in person_name_normalized and len(sender_name) >= 3:
                        sender_match = True
                    elif person_name_normalized and sender_name:
                        query_words = [w for w in person_name_normalized.split() if len(w) >= 2]
                        sender_words = [w for w in sender_name.split() if len(w) >= 2]
                        if len(query_words) >= 2 and len(sender_words) >= 1:
                            query_words_set = set(query_words)
                            sender_words_set = set(sender_words)
                            common_words = query_words_set & sender_words_set
                            if len(common_words) >= 2 or (len(query_words) == 2 and len(common_words) == 2):
                                sender_match = True
                elif not sender_match and person_name_len == 1:
                    pass
                elif not sender_match and person_name_len == 2:
                    sender_words = sender_name.split()
                    for word in sender_words:
                        if word.strip().lower() == person_name_normalized:
                            sender_match = True
                            break
                
                if not recipient_match and person_name_len > 2:
                    if person_name_normalized in recipient_name:
                        recipient_match = True
                    elif recipient_name in person_name_normalized and len(recipient_name) >= 3:
                        recipient_match = True
                    elif person_name_normalized and recipient_name:
                        query_words = [w for w in person_name_normalized.split() if len(w) >= 2]
                        recipient_words = [w for w in recipient_name.split() if len(w) >= 2]
                        if len(query_words) >= 2 and len(recipient_words) >= 1:
                            query_words_set = set(query_words)
                            recipient_words_set = set(recipient_words)
                            common_words = query_words_set & recipient_words_set
                            if len(common_words) >= 2 or (len(query_words) == 2 and len(common_words) == 2):
                                recipient_match = True
                elif not recipient_match and person_name_len == 1:
                    pass
                elif not recipient_match and person_name_len == 2:
                    recipient_words = recipient_name.split()
                    for word in recipient_words:
                        if word.strip().lower() == person_name_normalized:
                            recipient_match = True
                            break
                
                thread_match = False
                if thread_id and thread_id in thread_person_map:
                    thread_match = True
                
                if not group_match and not sender_match and not recipient_match and not thread_match:
                    continue
                
                if device_owner_name:
                    is_device_owner_sender = sender_name == device_owner_name
                    if not is_device_owner_sender:
                        is_device_owner_sender = (
                            device_owner_name in sender_name or
                            sender_name in device_owner_name or
                            (len(set(device_owner_name.split()) & set(sender_name.split())) > 0)
                        )
                    
                    is_device_owner_recipient = recipient_name == device_owner_name
                    if not is_device_owner_recipient:
                        is_device_owner_recipient = (
                            device_owner_name in recipient_name or
                            recipient_name in device_owner_name or
                            (len(set(device_owner_name.split()) & set(recipient_name.split())) > 0)
                        )
                    
                    if is_device_owner_sender and is_device_owner_recipient:
                        continue
            
            if search_lower:
                message_text = (msg.message_text or "").lower()
                if search_lower not in message_text:
                    continue
            
            direction = None
            
            if person_name_normalized and device_owner_name:
                is_device_owner_sender = sender_name == device_owner_name
                if not is_device_owner_sender:
                    is_device_owner_sender = (
                        device_owner_name in sender_name or
                        sender_name in device_owner_name or
                        (len(set(device_owner_name.split()) & set(sender_name.split())) > 0)
                    )
                
                is_device_owner_recipient = recipient_name == device_owner_name
                if not is_device_owner_recipient:
                    is_device_owner_recipient = (
                        device_owner_name in recipient_name or
                        recipient_name in device_owner_name or
                        (len(set(device_owner_name.split()) & set(recipient_name.split())) > 0)
                    )
                
                is_person_sender = sender_match
                is_person_recipient = recipient_match
                
                if is_person_sender and not is_device_owner_sender:
                    direction = "Incoming"
                elif is_device_owner_sender and not is_person_sender:
                    direction = "Outgoing"
                elif is_person_recipient and is_device_owner_sender:
                    direction = "Outgoing"
                elif is_person_recipient and not is_device_owner_sender:
                    direction = "Incoming"
                elif is_person_sender:
                    direction = "Incoming"
                elif is_person_recipient:
                    direction = "Outgoing"
                else:
                    direction = "Unknown"
            elif person_name_normalized:
                if sender_match:
                    direction = "Incoming"
                elif recipient_match:
                    direction = "Outgoing"
                else:
                    direction = "Unknown"
            
            if msg.direction:
                direction = msg.direction
            
            raw_message_text = msg.message_text or ""
            cleaned_message_text = clean_message_text(raw_message_text)
            
            times_value = extract_time_from_timestamp(msg.timestamp or "")
            
            sender_id_value = msg.sender_number or ""
            if not sender_id_value and msg.from_name:
                from_name = msg.from_name.strip()
                if from_name and (from_name.isdigit() or (len(from_name) > 15 and ' ' not in from_name)):
                    sender_id_value = from_name
            
            recipient_id_value = msg.recipient_number or ""
            if not recipient_id_value and msg.to_name:
                to_name = msg.to_name.strip()
                if to_name and (to_name.isdigit() or (len(to_name) > 15 and ' ' not in to_name)):
                    recipient_id_value = to_name
            
            chat_type_value = (msg.chat_type or "").strip() if msg.chat_type else None
            group_name_value = (msg.group_name or "").strip() if msg.group_name else None
            group_id_value = (msg.group_id or "").strip() if msg.group_id else None
            
            recipient_array = []
            if recipient_id_value or (msg.to_name and msg.to_name.strip() and msg.to_name.strip() != "Unknown"):
                recipient_array.append({
                    "recipient_name": msg.to_name or "Unknown",
                    "recipient_id": recipient_id_value or ""
                })
            
            from_array = []
            sender_name_value = msg.from_name or msg.sender_number or "Unknown"
            if sender_name_value and sender_name_value != "Unknown":
                cleaned_sender = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', sender_name_value)
                if cleaned_sender:
                    sender_name_value = sender_name_value.strip()
                else:
                    sender_name_value = None
            elif sender_name_value == "Unknown":
                sender_name_value = None
            
            from_item = {
                "message_id": msg.id,
                "thread_id": msg.thread_id or "",
                "sender": sender_name_value,
                "sender_id": sender_id_value or "",
                "direction": direction or "Unknown",
                "message_text": cleaned_message_text
            }
            from_array.append(from_item)
            
            chat_messages.append({
                "message_id": msg.id,
                "chat_id": msg.chat_id or "",
                "timestamp": msg.timestamp,
                "times": times_value,
                "direction": direction or "Unknown",
                "recipient": recipient_array,
                "from": from_array,
                "_chat_type": chat_type_value
            })
            
            filtered_messages.append(msg)
        
        chat_type_determined = None
        group_name_determined = None
        group_id_determined = None
        person_name_determined = person_name
        person_id_determined = None
        
        if filtered_messages:
            for msg in filtered_messages:
                msg_chat_type = (msg.chat_type or "").strip() if msg.chat_type else None
                msg_group_name = (msg.group_name or "").strip() if msg.group_name else None
                msg_group_id = (msg.group_id or "").strip() if msg.group_id else None
                
                if msg_chat_type and msg_chat_type.lower() in ["group", "broadcast"]:
                    if msg_group_name:
                        if person_name_normalized:
                            group_name_lower = msg_group_name.strip().lower()
                            person_name_len = len(person_name_normalized.strip())
                            
                            if person_name_len == 1:
                                if group_name_lower == person_name_normalized:
                                    chat_type_determined = msg_chat_type
                                    group_name_determined = msg_group_name.strip()
                                    if msg_group_id and msg_group_id.strip():
                                        group_id_determined = msg_group_id.strip()
                                    break
                            elif person_name_len == 2:
                                if group_name_lower == person_name_normalized:
                                    chat_type_determined = msg_chat_type
                                    group_name_determined = msg_group_name.strip()
                                    if msg_group_id and msg_group_id.strip():
                                        group_id_determined = msg_group_id.strip()
                                    break
                            else:
                                if group_name_lower == person_name_normalized or person_name_normalized in group_name_lower:
                                    chat_type_determined = msg_chat_type
                                    group_name_determined = msg_group_name.strip()
                                    if msg_group_id and msg_group_id.strip():
                                        group_id_determined = msg_group_id.strip()
                                    break
                        else:
                            chat_type_determined = msg_chat_type
                            group_name_determined = msg_group_name.strip()
                            if msg_group_id and msg_group_id.strip():
                                group_id_determined = msg_group_id.strip()
                            break
                elif person_name_normalized:
                    sender_name_val = (msg.from_name or "").strip().lower()
                    recipient_name_val = (msg.to_name or "").strip().lower()
                    sender_number_val = (msg.sender_number or "").strip()
                    recipient_number_val = (msg.recipient_number or "").strip()
                    person_name_len = len(person_name_normalized.strip())
                    
                    is_likely_id = person_name_normalized.isdigit() or (len(person_name_normalized) >= 5 and person_name_normalized.replace(' ', '').isdigit())
                    
                    sender_matches = sender_name_val == person_name_normalized
                    if not sender_matches and person_name_len > 2:
                        sender_matches = (
                            person_name_normalized in sender_name_val or
                            sender_name_val in person_name_normalized or
                            (len(set(person_name_normalized.split()) & set(sender_name_val.split())) > 0)
                        )
                    elif not sender_matches and person_name_len == 1:
                        pass
                    elif not sender_matches and person_name_len == 2:
                        sender_words = sender_name_val.split()
                        for word in sender_words:
                            if word.strip().lower() == person_name_normalized:
                                sender_matches = True
                                break
                    
                    if is_likely_id and not sender_matches and sender_number_val and sender_number_val.strip():
                        sender_number_normalized = sender_number_val.strip().lower()
                        if sender_number_normalized == person_name_normalized:
                            sender_matches = True
                    
                    recipient_matches = recipient_name_val == person_name_normalized
                    if not recipient_matches and person_name_len > 2:
                        recipient_matches = (
                            person_name_normalized in recipient_name_val or
                            recipient_name_val in person_name_normalized or
                            (len(set(person_name_normalized.split()) & set(recipient_name_val.split())) > 0)
                        )
                    elif not recipient_matches and person_name_len == 1:
                        pass
                    elif not recipient_matches and person_name_len == 2:
                        recipient_words = recipient_name_val.split()
                        for word in recipient_words:
                            if word.strip().lower() == person_name_normalized:
                                recipient_matches = True
                                break
                    
                    if is_likely_id and not recipient_matches and recipient_number_val and recipient_number_val.strip():
                        recipient_number_normalized = recipient_number_val.strip().lower()
                        if recipient_number_normalized == person_name_normalized:
                            recipient_matches = True
                    
                    if sender_matches:
                        chat_type_determined = msg_chat_type or "One On One"
                        person_name_determined = msg.from_name or person_name
                        if msg.sender_number and msg.sender_number.strip():
                            person_id_determined = msg.sender_number.strip()
                        break
                    elif recipient_matches:
                        chat_type_determined = msg_chat_type or "One On One"
                        person_name_determined = msg.to_name or person_name
                        if msg.recipient_number and msg.recipient_number.strip():
                            person_id_determined = msg.recipient_number.strip()
                        break
                    else:
                        chat_type_determined = msg_chat_type or "One On One"
                        if msg.from_name and msg.from_name.strip() and msg.from_name.strip() != "Unknown":
                            person_name_determined = msg.from_name.strip()
                        elif msg.to_name and msg.to_name.strip() and msg.to_name.strip() != "Unknown":
                            person_name_determined = msg.to_name.strip()
                        if msg.sender_number and msg.sender_number.strip():
                            person_id_determined = msg.sender_number.strip()
                        elif msg.recipient_number and msg.recipient_number.strip():
                            person_id_determined = msg.recipient_number.strip()
                        break
        
        
        if not person_id_determined or not person_id_determined.strip():
            person_id_determined = None
        else:
            person_id_determined = person_id_determined.strip()
        
        filtered_chat_messages = []
        if chat_type_determined:
            chat_type_determined_lower = chat_type_determined.lower()
            for msg_dict in chat_messages:
                msg_chat_type = msg_dict.get("_chat_type")
                if msg_chat_type:
                    msg_chat_type = msg_chat_type.strip() if isinstance(msg_chat_type, str) else None
                
                if chat_type_determined_lower == "one on one":
                    if msg_chat_type:
                        msg_chat_type_lower = msg_chat_type.lower()
                        if msg_chat_type_lower == "one on one":
                            msg_dict_clean = {k: v for k, v in msg_dict.items() if k != "_chat_type"}
                            filtered_chat_messages.append(msg_dict_clean)
                    else:
                        msg_dict_clean = {k: v for k, v in msg_dict.items() if k != "_chat_type"}
                        filtered_chat_messages.append(msg_dict_clean)
                elif chat_type_determined_lower in ["group", "broadcast"]:
                    if msg_chat_type and msg_chat_type.lower() == chat_type_determined_lower:
                        msg_dict_clean = {k: v for k, v in msg_dict.items() if k != "_chat_type"}
                        filtered_chat_messages.append(msg_dict_clean)
                else:
                    msg_dict_clean = {k: v for k, v in msg_dict.items() if k != "_chat_type"}
                    filtered_chat_messages.append(msg_dict_clean)
        else:
            filtered_chat_messages = [{k: v for k, v in msg_dict.items() if k != "_chat_type"} for msg_dict in chat_messages]

        if person_name:
            filtered_chat_messages.sort(key=lambda x: x["timestamp"] or "", reverse=False)
        else:
            filtered_chat_messages.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        
        grouped_messages = {}
        for msg in filtered_chat_messages:
            chat_id = msg.get("chat_id", "") or msg.get("thread_id", "")
            
            if chat_id not in grouped_messages:
                recipient_obj = {}
                recipient_array = msg.get("recipient", [])
                if recipient_array and len(recipient_array) > 0:
                    recipient_obj = recipient_array[0]
                elif not recipient_array:
                    recipient_obj = {
                        "recipient_name": "Unknown",
                        "recipient_id": ""
                    }
                
                grouped_messages[chat_id] = {
                    "chat_id": chat_id,
                    "timestamp": msg.get("timestamp", ""),
                    "times": msg.get("times", ""),
                    "direction": msg.get("direction", "Unknown"),
                    "recipient": recipient_obj,
                    "messages": []
                }
            
            from_array = msg.get("from", [])
            if from_array and len(from_array) > 0:
                from_item = from_array[0].copy()
                if "message_id" not in from_item:
                    from_item["message_id"] = msg.get("message_id")
                if "direction" not in from_item:
                    from_item["direction"] = msg.get("direction", "Unknown")
                grouped_messages[chat_id]["messages"].append(from_item)
        
        final_chat_messages = list(grouped_messages.values())
        
        if person_name:
            final_chat_messages.sort(key=lambda x: x.get("timestamp") or "", reverse=False)
        else:
            final_chat_messages.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        
        intensity = len(final_chat_messages)
        
        summary_value = analytic.summary if analytic.summary else None

        response_data = {
            "platform": platform,
            "intensity": intensity,
            "chat_type": chat_type_determined,
            "conversation_history": final_chat_messages,
            "summary": summary_value
        }

        if chat_type_determined and chat_type_determined.lower() in ["group", "broadcast"]:
            response_data["group_name"] = group_name_determined
            response_data["group_id"] = group_id_determined
        elif chat_type_determined and chat_type_determined.lower() == "one on one":
            if person_name_determined:
                person_name_cleaned = re.sub(r'[\s\u200B-\u200D\uFEFF\u00A0\u1680\u180E\u2000-\u2029\u202F-\u205F\u3000\u3164]+', '', person_name_determined)
                if person_name_cleaned:
                    response_data["person_name"] = person_name_determined.strip()
                else:
                    response_data["person_name"] = None
            if person_id_determined:
                response_data["person_id"] = person_id_determined

        return JSONResponse(
            content={
                "status": 200,
                "message": "Chat detail retrieved successfully",
                "data": response_data
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        return JSONResponse(
            content={
                "status": 500,
                "message": "Internal server error: Failed to retrieve chat detail",
                "data": None
            },
            status_code=500
        )