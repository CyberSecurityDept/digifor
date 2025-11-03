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


@router.get("/analytic/{analytic_id}/deep-communication-analytics")
def get_deep_communication_analytics(
    analytic_id: int,
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    platform: Optional[str] = Query(None, description="Filter by platform (Instagram, Telegram, WhatsApp, Facebook, X, TikTok)"),
    db: Session = Depends(get_db)
):
    try:
        if platform:
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
                    "message": "No devices linked to this analytic",
                    "data": {
                        "device_tabs": [],
                        "platform_analysis": {}
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
        
        # Build device tabs
        device_tabs = []
        for device in devices:
            device_tabs.append({
                "device_id": device.id,
                "device_name": device.owner_name or "Unknown",
                "phone_number": device.phone_number or ""
            })
        
        # Get all messages for all devices (no platform filter for initial view)
        all_file_ids = [d.file_id for d in devices]
        all_messages = get_chat_messages_for_analytic(db, analytic_id, None, None, all_file_ids)
        
        # Define all supported platforms with display names
        all_platforms = [
            {'key': 'instagram', 'display': 'Instagram'},
            {'key': 'telegram', 'display': 'Telegram'},
            {'key': 'whatsapp', 'display': 'WhatsApp'},
            {'key': 'facebook', 'display': 'Facebook'},
            {'key': 'x', 'display': 'X'},
            {'key': 'tiktok', 'display': 'TikTok'}
        ]
        
        # Build devices with platform cards
        devices_with_platforms = []
        
        for device in devices:
            device_file_ids = [device.file_id]
            device_messages = [msg for msg in all_messages if msg.file_id == device.file_id]
            
            # Build platform cards for this device
            platform_cards = []
            
            for platform_info in all_platforms:
                platform_key = platform_info['key']
                platform_display = platform_info['display']
                
                # Count messages for this platform and device
                platform_messages = [
                    msg for msg in device_messages 
                    if normalize_platform_name(msg.platform or '') == platform_key
                ]
                
                message_count = len(platform_messages)
                has_data = message_count > 0
                
                platform_cards.append({
                    "platform": platform_display,
                    "platform_key": platform_key,
                    "has_data": has_data,
                    "message_count": message_count
                })
            
            devices_with_platforms.append({
                "device_id": device.id,
                "device_name": device.owner_name or "Unknown",
                "phone_number": device.phone_number or "",
                "platform_cards": platform_cards
            })
        
        # If device_id specified, return only that device
        if device_id:
            devices_with_platforms = [
                d for d in devices_with_platforms if d["device_id"] == device_id
            ]
        
        # Build platform analysis if platform filter is specified
        platform_analysis = {}
        if platform:
            normalized_platform = normalize_platform_name(platform)
            file_ids = [d.file_id for d in devices]
            messages = get_chat_messages_for_analytic(db, analytic_id, device_id, platform, file_ids)
            
            platform_messages = [
                msg for msg in messages 
                if normalize_platform_name(msg.platform or '') == normalized_platform
            ]
            
            if platform_messages:
                person_intensity = defaultdict(int)
                person_info = {}
                
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
                    
                    person_name = None
                    person_id = None
                    
                    sender_name_lower = (sender_name or "").strip().lower()
                    if sender_name and (
                        not device_owner_name or 
                        sender_name_lower != device_owner_name
                    ):
                        person_name = sender_name
                        person_id = sender_id
                    
                    recipient_name_lower = (recipient_name or "").strip().lower()
                    if not person_name and recipient_name and (
                        not device_owner_name or 
                        recipient_name_lower != device_owner_name
                    ):
                        person_name = recipient_name
                        person_id = recipient_id
                    
                    if not person_name:
                        if recipient_name:
                            person_name = recipient_name
                            person_id = recipient_id
                        elif sender_name:
                            person_name = sender_name
                            person_id = sender_id
                    
                    if person_name:
                        person_key = person_name.strip()
                        person_intensity[person_key] += 1
                        
                        if person_key not in person_info:
                            person_info[person_key] = {
                                "name": person_name,
                                "id": person_id
                            }

                platform_data = []
                for person_key, intensity in sorted(person_intensity.items(), key=lambda x: x[1], reverse=True):
                    platform_data.append({
                        "person": person_info.get(person_key, {}).get("name", person_key),
                        "person_id": person_info.get(person_key, {}).get("id", ""),
                        "intensity": intensity
                    })
                
                if platform_data:
                    platform_analysis[normalized_platform] = platform_data
        
        return JSONResponse(
            content={
                "status": 200,
                "message": "Deep Communication Analytics retrieved successfully",
                "data": {
                    "analytic_info": {
                        "analytic_id": analytic_id,
                        "analytic_name": analytic.analytic_name or "Unknown"
                    },
                    "device_tabs": device_tabs,
                    "devices": devices_with_platforms,
                    "platform_analysis": platform_analysis,
                    "summary": {
                        "total_devices": len(devices),
                        "total_messages": len(all_messages),
                        "platforms_analyzed": list(platform_analysis.keys())
                    }
                }
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return JSONResponse(
            content={
                "status": 500,
                "message": "Internal server error: Failed to retrieve deep communication analytics",
                "error": str(e),
                "data": None
            },
            status_code=500
        )


@router.get("/analytic/{analytic_id}/interaction-intensity")
def get_interaction_intensity(
    analytic_id: int,
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
            return JSONResponse(
                content={
                    "status": 200,
                    "message": "No devices linked",
                    "data": {
                        "platform": platform,
                        "intensity_list": []
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

        person_intensity = defaultdict(int)
        person_info = {}
        
        normalized_platform = normalize_platform_name(platform)
        
        for msg in messages:
            msg_platform_normalized = normalize_platform_name(msg.platform or '')
            if msg_platform_normalized != normalized_platform:
                continue
            
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
            
            person_name = None
            person_id = None
            
            sender_name_lower = (sender_name or "").strip().lower()
            if sender_name and (
                not device_owner_name or 
                sender_name_lower != device_owner_name
            ):
                person_name = sender_name
                person_id = sender_id
            
            recipient_name_lower = (recipient_name or "").strip().lower()
            if not person_name and recipient_name and (
                not device_owner_name or 
                recipient_name_lower != device_owner_name
            ):
                person_name = recipient_name
                person_id = recipient_id
            
            if not person_name:
                person_name = recipient_name or sender_name
                person_id = recipient_id or sender_id
            
            if person_name:
                person_key = person_name.strip()
                person_intensity[person_key] += 1
                
                if person_key not in person_info:
                    person_info[person_key] = {
                        "name": person_name,
                        "id": person_id
                    }
        
        intensity_list = []
        for person_key, intensity in sorted(person_intensity.items(), key=lambda x: x[1], reverse=True):
            intensity_list.append({
                "person": person_info.get(person_key, {}).get("name", person_key),
                "person_id": person_info.get(person_key, {}).get("id", ""),
                "intensity": intensity
            })
        
        return JSONResponse(
            content={
                "status": 200,
                "message": "Interaction intensity retrieved successfully",
                "data": {
                    "platform": platform,
                    "intensity_list": intensity_list,
                    "summary": {
                        "total_persons": len(intensity_list),
                        "total_messages": len(messages)
                    }
                }
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return JSONResponse(
            content={
                "status": 500,
                "message": "Internal server error: Failed to retrieve interaction intensity",
                "error": str(e),
                "data": None
            },
            status_code=500
        )


@router.get("/analytic/{analytic_id}/chat-detail")
def get_chat_detail(
    analytic_id: int,
    person_name: Optional[str] = Query(None, description="Person name to filter chat details (optional if using search only)"),
    platform: Optional[str] = Query(None, description="Platform name (optional, can filter by search only)"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    search: Optional[str] = Query(None, description="Search text in messages (optional)"),
    db: Session = Depends(get_db)
):
    try:
        # Validate: either person_name or search must be provided
        if not person_name and not search:
            return JSONResponse(
                content={
                    "status": 400,
                    "message": "Either person_name or search parameter must be provided"
                },
                status_code=400
            )
        
        # Validate platform if provided
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
        
        for msg in messages:
            # Filter by platform if provided
            if normalized_platform:
                msg_platform_normalized = normalize_platform_name(msg.platform or '')
                if msg_platform_normalized != normalized_platform:
                    continue
            
            # Filter by person_name if provided
            if person_name_normalized:
                sender_name = (msg.from_name or "").strip()
                recipient_name = (msg.to_name or "").strip()
                
                sender_match = sender_name.lower() == person_name_normalized
                recipient_match = recipient_name.lower() == person_name_normalized
                
                if not sender_match and not recipient_match:
                    continue
            
            # Filter by search query if provided
            if search_lower:
                message_text = (msg.message_text or "").lower()
                if search_lower not in message_text:
                    continue
            
            # Determine direction
            direction = None
            device_owner_name = None
            for d in devices:
                if d.file_id == msg.file_id:
                    device_owner_name = (d.owner_name or "").strip().lower()
                    break
            
            if person_name_normalized:
                sender_name = (msg.from_name or "").strip()
                recipient_name = (msg.to_name or "").strip()
                
                if sender_name.lower() == person_name_normalized:
                    sender_name_lower = sender_name.lower()
                    if device_owner_name and sender_name_lower != device_owner_name:
                        direction = "Incoming"
                    else:
                        direction = "Outgoing"
                elif recipient_name.lower() == person_name_normalized:
                    recipient_name_lower = recipient_name.lower()
                    if device_owner_name and recipient_name_lower != device_owner_name:
                        direction = "Outgoing"
                    else:
                        direction = "Incoming"
            
            # Use existing direction if available
            if msg.direction:
                direction = msg.direction
            
            chat_messages.append({
                "message_id": msg.id,
                "timestamp": msg.timestamp,
                "direction": direction or "Unknown",
                "sender": msg.from_name or msg.sender_number or "Unknown",
                "recipient": msg.to_name or msg.recipient_number or "Unknown",
                "sender_id": msg.sender_number or "",
                "recipient_id": msg.recipient_number or "",
                "message_text": msg.message_text or "",
                "message_type": msg.message_type or "text",
                "platform": msg.platform,
                "thread_id": msg.thread_id or "",
                "chat_id": msg.chat_id or ""
            })
        
        # Sort by timestamp (oldest first for chat, newest first for search-only)
        if person_name:
            chat_messages.sort(key=lambda x: x["timestamp"] or "", reverse=False)
        else:
            chat_messages.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        
        intensity = len(chat_messages)
        
        # Extract person_id if person_name provided
        person_id = ""
        if person_name_normalized:
            for msg in chat_messages:
                if msg.get("sender", "").lower() == person_name_normalized:
                    person_id = msg.get("sender_id", "")
                    break
                elif msg.get("recipient", "").lower() == person_name_normalized:
                    person_id = msg.get("recipient_id", "")
                    break
        
        return JSONResponse(
            content={
                "status": 200,
                "message": "Chat detail retrieved successfully",
                "data": {
                    "person_name": person_name,
                    "person_id": person_id,
                    "platform": platform,
                    "intensity": intensity,
                    "chat_messages": chat_messages,
                    "search_query": search,
                    "summary": {
                        "total_messages": len(chat_messages),
                        "devices_involved": list(set([d.id for d in devices]))
                    }
                }
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return JSONResponse(
            content={
                "status": 500,
                "message": "Internal server error: Failed to retrieve chat detail",
                "error": str(e),
                "data": None
            },
            status_code=500
        )

