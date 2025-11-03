from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Device, Contact, Analytic, AnalyticDevice
from collections import defaultdict
import re
from typing import Optional, List

router = APIRouter()

@router.get("/analytic/{analytic_id}/deep-communication-analytics")
def get_deep_communication_analytics(
    analytic_id: int,
    device_id: Optional[int] = Query(None),
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")
    
    if analytic.method != "Deep communication analytics":
        return JSONResponse(
            content={
                "status": 400, 
                "message": f"This endpoint is only for Deep Communication Analytics. Current analytic method is '{analytic.method}'", 
                "data": None
            },
            status_code=400,
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
            content={"status": 200, "message": "No devices linked", "data": []},
            status_code=200
        )

    if device_id:
        if device_id not in device_ids:
            raise HTTPException(status_code=404, detail="Device not found in this analytic")
        device_ids = [device_id]

    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    device_info = {
        d.id: {
            "device_id": d.id,
            "device_name": d.owner_name,
            "phone_number": d.phone_number
        }
        for d in devices
    }

    messages = []

    platform_mapping = {
        'whatsapp': ['whatsapp', 'wa'],
        'telegram': ['telegram', 'tg'],
        'instagram': ['instagram', 'ig'],
        'tiktok': ['tiktok'],
        'facebook': ['facebook', 'fb', 'messenger']
    }

    platform_analysis = {}
    
    for platform_name, keywords in platform_mapping.items():
        if platform and platform.lower() != platform_name:
            continue
            
        platform_data = []
        person_intensity = defaultdict(int)
        
        for msg in messages:
            if not msg.text:
                continue
                
            text_lower = msg.text.lower()
            sender = msg.sender or ""
            receiver = msg.receiver or ""
            
            is_platform_message = any(keyword in text_lower for keyword in keywords)
            
            if is_platform_message:
                person_name = sender if sender else receiver
                if person_name:
                    person_intensity[person_name] += 1
        
        for person, intensity in person_intensity.items():
            platform_data.append({
                "person": person,
                "intensity": intensity
            })
        
        platform_data.sort(key=lambda x: x["intensity"], reverse=True)
        
        platform_analysis[platform_name] = platform_data

    device_tabs = []
    for device in devices:
        device_tabs.append({
            "device_id": device.id,
            "device_name": device.owner_name,
            "phone_number": device.phone_number
        })

    return JSONResponse(
        content={
            "status": 200,
            "message": "Deep communication analytics retrieved successfully",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "device_tabs": device_tabs,
                "platform_analysis": platform_analysis,
                "summary": {
                    "total_devices": len(devices),
                    "total_messages": len(messages),
                    "platforms_analyzed": list(platform_analysis.keys())
                }
            }
        },
        status_code=200
    )

@router.get("/analytic/{analytic_id}/communication-chat-details")
def get_communication_chat_details(
    analytic_id: int,
    person_name: str = Query(...),
    platform: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()
    device_ids = []
    for link in device_links:
        device_ids.extend(link.device_ids)
    device_ids = list(set(device_ids))
    
    if device_id and device_id in device_ids:
        device_ids = [device_id]

    messages = []

    if platform:
        platform_keywords = {
            'whatsapp': ['whatsapp', 'wa'],
            'telegram': ['telegram', 'tg'],
            'instagram': ['instagram', 'ig'],
            'tiktok': ['tiktok'],
            'facebook': ['facebook', 'fb', 'messenger']
        }
        
        if platform.lower() in platform_keywords:
            keywords = platform_keywords[platform.lower()]
            messages = [
                msg for msg in messages 
                if msg.text and any(keyword in msg.text.lower() for keyword in keywords)
            ]

    chat_messages = []
    for msg in messages:
        chat_messages.append({
            "message_id": msg.id,
            "sender": msg.sender,
            "receiver": msg.receiver,
            "text": msg.text,
            "timestamp": msg.timestamp,
            "direction": msg.direction,
            "platform": msg.type,
            "device_id": msg.device_id
        })

    chat_messages.sort(key=lambda x: x["timestamp"] or "", reverse=True)

    return JSONResponse(
        content={
            "status": 200,
            "message": "Chat details retrieved successfully",
            "data": {
                "person_name": person_name,
                "platform": platform,
                "chat_messages": chat_messages,
                "summary": {
                    "total_messages": len(chat_messages),
                    "devices_involved": list(set(msg["device_id"] for msg in chat_messages))
                }
            }
        },
        status_code=200
    )

@router.get("/analytic/{analytic_id}/communication-search")
def search_communication_data(
    analytic_id: int,
    query: str = Query(...),
    platform: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()
    device_ids = []
    for link in device_links:
        device_ids.extend(link.device_ids)
    device_ids = list(set(device_ids))
    
    if device_id and device_id in device_ids:
        device_ids = [device_id]

    messages = []

    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    file_ids = [d.file_id for d in devices]
    
    contacts = (
        db.query(Contact)
        .filter(Contact.file_id.in_(file_ids))
        .filter(Contact.display_name.ilike(f"%{query}%"))
        .all()
    )

    if platform:
        platform_keywords = {
            'whatsapp': ['whatsapp', 'wa'],
            'telegram': ['telegram', 'tg'],
            'instagram': ['instagram', 'ig'],
            'tiktok': ['tiktok'],
            'facebook': ['facebook', 'fb', 'messenger']
        }
        
        if platform.lower() in platform_keywords:
            keywords = platform_keywords[platform.lower()]
            messages = [
                msg for msg in messages 
                if msg.text and any(keyword in msg.text.lower() for keyword in keywords)
            ]

    search_results = {
        "messages": [
            {
                "message_id": msg.id,
                "sender": msg.sender,
                "receiver": msg.receiver,
                "text": msg.text,
                "timestamp": msg.timestamp,
                "platform": msg.type,
                "device_id": msg.device_id
            }
            for msg in messages
        ],
        "contacts": [
            {
                "contact_id": contact.id,
                "display_name": contact.display_name,
                "phone_number": contact.phone_number,
                "type": contact.type,
                "file_id": contact.file_id
            }
            for contact in contacts
        ]
    }

    return JSONResponse(
        content={
            "status": 200,
            "message": "Search completed successfully",
            "data": {
                "query": query,
                "platform": platform,
                "results": search_results,
                "summary": {
                    "total_messages_found": len(messages),
                    "total_contacts_found": len(contacts),
                    "devices_searched": len(device_ids)
                }
            }
        },
        status_code=200
    )

@router.post("/analytic/{analytic_id}/add-notes")
def add_notes_to_analytic(
    analytic_id: int,
    notes: str,
    db: Session = Depends(get_db)
):

    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    if analytic.notes:
        analytic.notes += f"\n\n{notes}"
    else:
        analytic.notes = notes
    
    db.commit()
    db.refresh(analytic)

    return JSONResponse(
        content={
            "status": 200,
            "message": "Notes added successfully",
            "data": {
                "analytic_id": analytic_id,
                "notes": analytic.notes
            }
        },
        status_code=200
    )
