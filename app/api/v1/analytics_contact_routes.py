from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, Device, AnalyticDevice, Contact
from app.auth.models import User
from app.api.deps import get_current_user
from app.api.v1.analytics_management_routes import check_analytic_access
from collections import defaultdict
import re
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()

def normalize_phone_number(phone: str) -> str:
    if not phone:
        return ""
    
    phone = re.sub(r'[^\d+]', '', phone)
    
    phone = phone.replace('+', '')
    
    if phone.startswith('0'):
        phone = '62' + phone[1:]
    elif not phone.startswith('62'):
        phone = '62' + phone
    
    return phone

def _get_contact_correlation_data(analytic_id: int, db: Session, current_user=None):
    min_devices = 2
    
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        return JSONResponse(
            content={"status": 404, "message": "Analytic not found", "data": None},
            status_code=404,
        )
    
    if current_user is not None and not check_analytic_access(analytic, current_user):
        return JSONResponse(
            content={"status": 403, "message": "You do not have permission to access this analytic", "data": None},
            status_code=403,
        )
    
    method_value = analytic.method
    if method_value is None or str(method_value) != "Contact Correlation":
        return JSONResponse(
            content={
                "status": 400, 
                "message": f"This endpoint is only for Contact Correlation. Current analytic method is '{method_value}'", 
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
            content={"status": 200, "message": "No devices linked", "data": {"devices": [], "correlations": [], "total_correlations": 0}},
            status_code=200
        )

    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    
    file_ids = [d.file_id for d in devices]
    
    contacts = (
        db.query(Contact)
        .filter(Contact.file_id.in_(file_ids))
        .order_by(Contact.id)
        .all()
    )

    device_info = {}
    device_labels = {}
    
    for i, device in enumerate(devices, 1):
        device_info[device.id] = {
            "device_label": f"Device {chr(64 + i)}",
            "owner_name": device.owner_name,
            "phone_number": device.phone_number
        }
        device_labels[device.id] = f"Device {chr(64 + i)}"

    phone_patterns = [
        re.compile(r"(\+?\d{7,15})"),
        re.compile(r"Mobile:\s*(\+?\d{7,15})", re.IGNORECASE),
        re.compile(r"Phone number:\s*(\+?\d{7,15})", re.IGNORECASE),
    ]

    name_patterns = [
        re.compile(r"First name:\s*(.*)", re.IGNORECASE),
        re.compile(r"Display Name:\s*(.*)", re.IGNORECASE),
        re.compile(r"Contact:\s*(.*)", re.IGNORECASE),
    ]

    correlation_map = defaultdict(dict)

    for contact in contacts:
        contact_type = contact.type
        if contact_type is not None and "account" in str(contact_type).lower():
            display_name = contact.display_name if contact.display_name is not None else "Unknown"
            print(f"Skipped contact (account type): {display_name} — {contact_type}")
            continue

        phones_found = []
        names_found = []

        contact_text = str(contact.display_name) if contact.display_name is not None else ""
        phones_emails_text = str(contact.phone_number) if contact.phone_number is not None else ""

        for pattern in phone_patterns:
            phones_found.extend(pattern.findall(contact_text))
            phones_found.extend(pattern.findall(phones_emails_text))

        for pattern in name_patterns:
            match = pattern.search(contact_text)
            if match:
                name = match.group(1).strip()
                if name and name not in names_found:
                    names_found.append(name)

        if not names_found and contact_text and not re.search(r"\d{7,15}", contact_text):
            potential_name = contact_text.strip()
            if potential_name and potential_name != "(Unknown)":
                names_found.append(potential_name)

        for phone in phones_found:
            if not phone:
                continue

            normalized_phone = normalize_phone_number(phone)
            if len(normalized_phone) < 10:
                continue

            if names_found:
                contact_name = names_found[0]
            else:
                if re.match(r'^[\+\d\s\-\(\)]+$', contact_text.strip()):
                    contact_name = "Unknown"
                else:
                    contact_name = contact_text.strip() if contact_text.strip() else "Unknown"
            
            contact_name = re.sub(r"\s+", " ", contact_name).strip()
            
            if not contact_name or re.match(r'^[\+\d\s\-\(\)]+$', contact_name):
                contact_name = "Unknown"

            contact_device_id = None
            contact_file_id = contact.file_id
            contact_file_id_int = int(contact_file_id) if contact_file_id is not None else None
            for d in devices:
                device_file_id = d.file_id
                device_file_id_int = int(device_file_id) if device_file_id is not None else None
                if device_file_id_int is not None and contact_file_id_int is not None and device_file_id_int == contact_file_id_int:
                    device_id_value = d.id
                    if device_id_value is not None:
                        contact_device_id = int(device_id_value)
                    break
            if contact_device_id is not None:
                correlation_map[normalized_phone][contact_device_id] = contact_name

    filtered_correlations = {
        phone: devices_dict for phone, devices_dict in correlation_map.items()
        if len(devices_dict) >= min_devices
    }

    correlations = []
    for phone, devices_dict in filtered_correlations.items():
        devices_found_in = []
        
        for device_id in device_ids:
            if device_id in devices_dict:
                devices_found_in.append({
                    "device_label": device_labels[device_id],
                    "contact_name": devices_dict[device_id]
                })
        
        correlations.append({
            "contact_number": phone,
            "devices_found_in": devices_found_in
        })

    correlations.sort(key=lambda x: len(x["devices_found_in"]), reverse=True)

    if not correlations:
        correlations = []

    total_correlations = len(correlations)
    summary_value = analytic.summary
    summary = summary_value if summary_value is not None else None

    return JSONResponse(
        content={
            "status": 200,
            "message": "Contact correlation analysis completed",
            "data": {
                "devices": list(device_info.values()),
                "correlations": correlations,
                "summary": summary,
                "total_correlations": total_correlations
            }
        },
        status_code=200
    )

@router.get("/analytic/contact-correlation")
def get_contact_correlation(
    analytic_id: int = Query(..., description="Analytic ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return _get_contact_correlation_data(analytic_id, db, current_user)
