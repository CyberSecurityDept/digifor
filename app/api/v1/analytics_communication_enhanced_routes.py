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
import re
import traceback

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
        query = query.filter(ChatMessage.file_id.in_(file_ids))

    if platform:
        normalized_platform = normalize_platform_name(platform)
        query = query.filter(
            or_(
                func.lower(ChatMessage.platform) == normalized_platform,
                func.lower(ChatMessage.platform).like(f"%{normalized_platform}%")
            )
        )
    
    return query.all()


@router.get("/analytic/deep-communication-analytics")
def get_deep_communication_analytics(  # type: ignore[reportGeneralTypeIssues]
    analytic_id: int = Query(..., description="Analytic ID"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    db: Session = Depends(get_db)
):
    try:
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                content={
                    "status": 404,
                    "message": "Analytic not found"
                },
                status_code=404
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
                    "message": "No devices linked to this analytic",
                    "data": {
                        "analytic_info": {
                            "analytic_id": analytic_id,
                            "analytic_name": analytic.analytic_name or "Unknown"
                        },
                        "devices": [],
                        "summary": analytic.summary if analytic.summary else None
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
            
        all_file_ids = [d.file_id for d in devices]
        all_messages = get_chat_messages_for_analytic(db, analytic_id, None, None, all_file_ids)
        
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
            device_file_ids = [device.file_id]
            device_messages = [msg for msg in all_messages if msg.file_id == device.file_id]
            
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
  
                thread_person_messages = defaultdict(lambda: defaultdict(list))
                person_info = {}
                device_owner_name = (device.owner_name or "").strip().lower()
                
                thread_person_map = {}
                
                for msg in platform_messages:
                    direction = (msg.direction or "").strip()
                    direction_lower = direction.lower()
                    
                    if direction_lower in ['incoming', 'received']:
                        sender_name = msg.from_name or ""
                        sender_id = msg.sender_number or ""
                        thread_id = (msg.thread_id or msg.chat_id or "").strip()
                        
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
                            sender_name_lower = person_name.strip().lower()
                            is_not_device_owner = True
                            if device_owner_name:
                                is_not_device_owner = (
                                    sender_name_lower != device_owner_name and
                                    device_owner_name not in sender_name_lower and
                                    sender_name_lower not in device_owner_name and
                                    not (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                                )
                            
                            if is_not_device_owner and thread_id not in thread_person_map:
                                thread_person_map[thread_id] = {
                                    "name": person_name,
                                    "id": person_id
                                }
                
                for msg in platform_messages:
                    sender_name = msg.from_name or ""
                    sender_id = msg.sender_number or ""
                    recipient_name = msg.to_name or ""
                    recipient_id = msg.recipient_number or ""
                    
                    sender_name_lower = (sender_name or "").strip().lower()
                    recipient_name_lower = (recipient_name or "").strip().lower()
                    
                    direction = (msg.direction or "").strip()
                    direction_lower = direction.lower()
                    
                    person_name = None
                    person_id = None
                    thread_id = (msg.thread_id or msg.chat_id or "").strip()
                    
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
                    else:
                        sender_name_lower = (sender_name or "").strip().lower()
                        if sender_name and (not device_owner_name or sender_name_lower != device_owner_name):
                            person_name = sender_name
                            person_id = sender_id
                        elif recipient_name and (not device_owner_name or recipient_name_lower != device_owner_name):
                            person_name = recipient_name
                            person_id = recipient_id
                        elif recipient_name:
                            person_name = recipient_name
                            person_id = recipient_id
                        elif sender_name:
                            person_name = sender_name
                            person_id = sender_id
                    
                    if person_name and device_owner_name:
                        person_name_lower = person_name.strip().lower()
                        device_owner_lower = device_owner_name.lower()
                        if (person_name_lower == device_owner_lower or
                            device_owner_lower in person_name_lower or
                            person_name_lower in device_owner_lower or
                            (len(set(device_owner_lower.split()) & set(person_name_lower.split())) > 0)):
                            continue
                    
                    if person_name:
                        person_key = person_name.strip()
                        if person_key:
                            thread_person_messages[thread_id][person_key].append(msg)
                            if person_key not in person_info:
                                stored_person_id = ""
                                if direction_lower in ['incoming', 'received']:
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
                                
                                person_info[person_key] = {
                                    "name": person_name,
                                    "id": stored_person_id
                                }
                            else:
                                if not person_info[person_key]["id"] and direction_lower in ['incoming', 'received']:
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
                                            person_info[person_key]["id"] = person_id
                                    elif not device_owner_name and person_id:
                                        person_info[person_key]["id"] = person_id
                
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
                        
                        for person_key in person_keys_in_thread:
                            messages = persons[person_key]
                            all_messages_in_thread.extend(messages)
                            person_data = person_info.get(person_key, {})
                            name_val = person_data.get("name", person_key)
                            if not merged_name or (name_val and not name_val.strip().isdigit() and len(name_val.strip()) > 3):
                                merged_name = name_val if name_val else merged_name
                        
                        for msg in all_messages_in_thread:
                            direction = (msg.direction or "").strip().lower()
                            if direction in ['incoming', 'received']:
                                sender_id = msg.sender_number or ""
                                sender_name = (msg.from_name or "").strip()
                                if sender_name:
                                    sender_name_lower = sender_name.strip().lower()
                                    is_person = True
                                    if device_owner_name:
                                        is_person = (
                                            sender_name_lower != device_owner_name and
                                            device_owner_name not in sender_name_lower and
                                            sender_name_lower not in device_owner_name and
                                            not (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                                        )
                                    if is_person and sender_id and sender_id.strip():
                                        sender_id_clean = sender_id.strip()
                                        if len(sender_id_clean) <= 50:
                                            if not merged_id:
                                                merged_id = sender_id_clean
                                            elif merged_id.strip().isdigit() and not sender_id_clean.strip().isdigit():
                                                merged_id = sender_id_clean
                                            break
                        
                        if primary_key in person_info:
                            if not person_info[primary_key]["name"] or person_info[primary_key]["name"].strip().isdigit():
                                if merged_name and not merged_name.strip().isdigit():
                                    person_info[primary_key]["name"] = merged_name
                            if not person_info[primary_key]["id"] and merged_id:
                                person_info[primary_key]["id"] = merged_id
                        else:
                            person_info[primary_key] = {
                                "name": merged_name or primary_key,
                                "id": merged_id or ""
                            }
                        
                        person_intensity[primary_key] += len(all_messages_in_thread)
                
                intensity_list = []
                for person_key, intensity_value in sorted(person_intensity.items(), key=lambda x: x[1], reverse=True):
                    person_data = person_info.get(person_key, {})
                    person_name = person_data.get("name", person_key)
                    person_id_value = person_data.get("id", "")
                    
                    if (not person_name or person_name.strip() == "") and person_id_value:
                        person_name = person_id_value
                    
                    if not person_id_value or not person_id_value.strip():
                        person_id_value = None
                    else:
                        person_id_value = person_id_value.strip()
                    
                    intensity_list.append({
                        "person": person_name,
                        "intensity": intensity_value
                    })
                
                platform_card = {
                    "platform": platform_display,
                    "platform_key": platform_key,
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
                    "message": "Analytic not found"
                },
                status_code=404
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
                        "message": "Device not found in this analytic"
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
        
        for msg in platform_messages:
            direction = (msg.direction or "").strip()
            direction_lower = direction.lower()
            if direction_lower in ['incoming', 'received']:
                sender_name = msg.from_name or ""
                sender_id = msg.sender_number or ""
                thread_id = (msg.thread_id or msg.chat_id or "").strip()
                
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
            
            device_owner_name = None
            device_owner_id = None
            for d in devices:
                if d.file_id == msg.file_id:
                    device_owner_name = (d.owner_name or "").strip().lower()
                    device_owner_id = (d.phone_number or "").strip()
                    break
            
            sender_name_lower = (sender_name or "").strip().lower()
            recipient_name_lower = (recipient_name or "").strip().lower()
            
            
            direction = (msg.direction or "").strip()
            direction_lower = direction.lower()
            
            person_name = None
            person_id = None
            
            thread_id = (msg.thread_id or msg.chat_id or "").strip()
            
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
                
                if person_name_lower == device_owner_lower:
                    continue
                
                if (device_owner_lower in person_name_lower or 
                    person_name_lower in device_owner_lower or
                    (len(set(device_owner_lower.split()) & set(person_name_lower.split())) > 0)):
                    continue
            
            if person_name:
                person_key = person_name.strip()
                if person_key:
                    thread_id = (msg.thread_id or msg.chat_id or "").strip()
                    
                    thread_person_messages[thread_id][person_key].append(msg)
                    
                    stored_person_id = ""
                    if direction_lower in ['incoming', 'received']:
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
                    
                    if person_key not in person_info:
                        person_info[person_key] = {
                            "name": person_name,
                            "id": stored_person_id
                        }
                    else:
                        if not person_info[person_key]["id"] and stored_person_id:
                            person_info[person_key]["id"] = stored_person_id
        
        person_intensity = defaultdict(int)
        person_thread_info = defaultdict(list)
        
        thread_primary_person = {}
        
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
                
                thread_primary_person[thread_id] = primary_key
                all_messages_in_thread = []
                merged_name = None
                merged_id = None
                
                for person_key in person_keys_in_thread:
                    messages = persons[person_key]
                    all_messages_in_thread.extend(messages)
                    
                    person_data = person_info.get(person_key, {})
                    name_val = person_data.get("name", person_key)
                    id_val = person_data.get("id", "")
                    if not merged_name or (name_val and not name_val.strip().isdigit() and len(name_val.strip()) > 3):
                        merged_name = name_val if name_val else merged_name
                
                for msg in all_messages_in_thread:
                    direction = (msg.direction or "").strip().lower()
                    if direction in ['incoming', 'received']:
                        sender_id = msg.sender_number or ""
                        sender_name = (msg.from_name or "").strip()
                        
                        device_owner_name = None
                        for d in devices:
                            if d.file_id == msg.file_id:
                                device_owner_name = (d.owner_name or "").strip().lower()
                                break
                        
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
                
                if primary_key in person_info:
                    if not person_info[primary_key]["name"] or person_info[primary_key]["name"].strip().isdigit():
                        if merged_name and not merged_name.strip().isdigit():
                            person_info[primary_key]["name"] = merged_name
                    if not person_info[primary_key]["id"] and merged_id:
                        person_info[primary_key]["id"] = merged_id
                else:
                    person_info[primary_key] = {
                        "name": merged_name or primary_key,
                        "id": merged_id or ""
                    }
                
                message_count = len(all_messages_in_thread)
                person_intensity[primary_key] += message_count
                person_thread_info[primary_key].append({
                    "thread_id": thread_id,
                    "count": message_count
                })
                
                if not person_info[primary_key]["id"]:
                    for msg in all_messages_in_thread:
                        direction = (msg.direction or "").strip().lower()
                        
                        if direction not in ['incoming', 'received']:
                            continue
                        
                        device_owner_name = None
                        for d in devices:
                            if d.file_id == msg.file_id:
                                device_owner_name = (d.owner_name or "").strip().lower()
                                break
                        
                        sender_name = (msg.from_name or "").strip()
                        sender_id = msg.sender_number or ""
                        
                        if sender_name:
                            sender_name_lower = sender_name.strip().lower()
                            is_person_sender = False
                            
                            if device_owner_name:
                                is_person_sender = (
                                    sender_name_lower != device_owner_name and
                                    device_owner_name not in sender_name_lower and
                                    sender_name_lower not in device_owner_name and
                                    not (len(set(device_owner_name.split()) & set(sender_name_lower.split())) > 0)
                                )
                            else:
                                is_person_sender = True
                            
                            if is_person_sender and sender_id and sender_id.strip():
                                sender_id_clean = sender_id.strip()
                                if len(sender_id_clean) <= 50:
                                    person_info[primary_key]["id"] = sender_id_clean
                                    break
        
        intensity_list = []
        for person_key, intensity in sorted(person_intensity.items(), key=lambda x: x[1], reverse=True):
            person_data = person_info.get(person_key, {})
            person_name = person_data.get("name", person_key)
            person_id_value = person_data.get("id", "")
            
            if (not person_name or person_name.strip() == "") and person_id_value:
                person_name = person_id_value
            
            is_device_owner = False
            person_name_lower = (person_name or "").strip().lower()
            for d in devices:
                device_owner_name = (d.owner_name or "").strip().lower()
                if device_owner_name:
                    if person_name_lower == device_owner_name:
                        is_device_owner = True
                        break
                    if (device_owner_name in person_name_lower or 
                        person_name_lower in device_owner_name or
                        (len(set(device_owner_name.split()) & set(person_name_lower.split())) > 0)):
                        is_device_owner = True
                        break
            
            if is_device_owner:
                continue
            
            if not person_id_value or not person_id_value.strip():
                person_id_value = None
            else:
                person_id_value = person_id_value.strip()
            
            intensity_list.append({
                "person": person_name,
                "person_id": person_id_value,
                "intensity": intensity
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
                    "message": "Analytic not found"
                },
                status_code=404
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
        normalized_platform = normalize_platform_name(platform) if platform else None
        person_name_normalized = person_name.strip().lower() if person_name else None
        search_lower = search.lower() if search else None
        
        thread_person_map = {}
        
        if person_name_normalized:
            for msg in messages:
                if normalized_platform:
                    msg_platform_normalized = normalize_platform_name(msg.platform or '')
                    if msg_platform_normalized != normalized_platform:
                        continue
                
                direction = (msg.direction or "").strip().lower()
                if direction in ['incoming', 'received']:
                    sender_name = (msg.from_name or "").strip().lower()
                    if sender_name == person_name_normalized or person_name_normalized in sender_name:
                        thread_id = (msg.thread_id or msg.chat_id or "").strip()
                        if thread_id:
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
                
                sender_match = sender_name == person_name_normalized
                recipient_match = recipient_name == person_name_normalized
                
                if not sender_match:
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
                
                if not recipient_match:
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
                
                thread_match = False
                if thread_id and thread_id in thread_person_map:
                    thread_match = True
                
                if not sender_match and not recipient_match and not thread_match:
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
            
            chat_messages.append({
                "message_id": msg.id,
                "timestamp": msg.timestamp,
                "times": times_value,
                "direction": direction or "Unknown",
                "sender": msg.from_name or msg.sender_number or "Unknown",
                "recipient": msg.to_name or msg.recipient_number or "Unknown",
                "sender_id": sender_id_value,
                "recipient_id": recipient_id_value,
                "message_text": cleaned_message_text,
                "message_type": msg.message_type or "text",
                "platform": msg.platform,
                "thread_id": msg.thread_id or "",
                "chat_id": msg.chat_id or ""
            })
        
        if person_name:
            chat_messages.sort(key=lambda x: x["timestamp"] or "", reverse=False)
        else:
            chat_messages.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        
        intensity = len(chat_messages)
        
        actual_person_name = person_name
        person_id = None
        
        if person_name_normalized and chat_messages:
            for msg in chat_messages:
                sender_lower = msg.get("sender", "").lower()
                recipient_lower = msg.get("recipient", "").lower()
                direction = msg.get("direction", "").strip()
                
                sender_matches = sender_lower == person_name_normalized
                if not sender_matches:
                    sender_matches = (
                        person_name_normalized in sender_lower or
                        sender_lower in person_name_normalized or
                        (len(set(person_name_normalized.split()) & set(sender_lower.split())) > 0)
                    )
                
                recipient_matches = recipient_lower == person_name_normalized
                if not recipient_matches:
                    recipient_matches = (
                        person_name_normalized in recipient_lower or
                        recipient_lower in person_name_normalized or
                        (len(set(person_name_normalized.split()) & set(recipient_lower.split())) > 0)
                    )
                
                if sender_matches and direction.lower() in ['incoming', 'received']:
                    actual_person_name = msg.get("sender", person_name)
                    sender_id_val = msg.get("sender_id", "")
                    if sender_id_val and sender_id_val.strip():
                        person_id = sender_id_val.strip()
                    break
                elif sender_matches:
                    actual_person_name = msg.get("sender", person_name)
                    sender_id_val = msg.get("sender_id", "")
                    if sender_id_val and sender_id_val.strip():
                        person_id = sender_id_val.strip()
                elif recipient_matches:
                    actual_person_name = msg.get("recipient", person_name)
                    if not person_id and direction.lower() in ['outgoing', 'sent']:
                        recipient_id_val = msg.get("recipient_id", "")
                        if recipient_id_val and recipient_id_val.strip() and len(recipient_id_val.strip()) <= 50:
                            person_id = recipient_id_val.strip()
        
        if not person_id or not person_id.strip():
            person_id = None
        else:
            person_id = person_id.strip()
        
        summary_value = analytic.summary if analytic.summary else None

        return JSONResponse(
            content={
                "status": 200,
                "message": "Chat detail retrieved successfully",
                "data": {
                    "person_name": actual_person_name,
                    "person_id": person_id,
                    "platform": platform,
                    "intensity": intensity,
                    "chat_messages": chat_messages,
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
                "message": "Internal server error: Failed to retrieve chat detail",
                "data": None
            },
            status_code=500
        )

