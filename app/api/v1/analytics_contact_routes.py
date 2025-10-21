from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, Device, AnalyticDevice, Contact
from collections import defaultdict
import re
from typing import List, Dict, Any
from pydantic import BaseModel
from app.utils.timezone import get_indonesia_time
from app.core.config import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
import os

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

@router.get("/analytic/{analytic_id}/contact-correlation")
def get_contact_correlation(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    min_devices = 2
    
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()

    device_ids = [link.device_id for link in device_links]
    if not device_ids:
        return JSONResponse(
            content={"status": 200, "message": "No devices linked", "data": {"devices": [], "correlations": []}},
            status_code=200
        )

    contacts = (
        db.query(Contact)
        .filter(Contact.device_id.in_(device_ids))
        .order_by(Contact.id)
        .all()
    )

    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
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
        phones_found = []
        names_found = []

        contact_text = contact.display_name or ""
        phones_emails_text = contact.phone_number or ""

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

            correlation_map[normalized_phone][contact.device_id] = contact_name

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

    return JSONResponse(
        content={
            "status": 200,
            "message": "Contact correlation analysis completed",
            "data": {
                "devices": list(device_info.values()),
                "correlations": correlations
            }
        },
        status_code=200
    )


class SummaryRequest(BaseModel):
    summary: str


@router.post("/analytic/{analytic_id}/save-summary")
def save_contact_correlation_summary(
    analytic_id: int,
    request: SummaryRequest,
    db: Session = Depends(get_db)
):
    try:
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                content={"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )

        if not request.summary or not request.summary.strip():
            return JSONResponse(
                content={"status": 400, "message": "Summary cannot be empty", "data": None},
                status_code=400,
            )

        analytic.summary = request.summary.strip()
        db.commit()
        db.refresh(analytic)

        return JSONResponse(
            content={
                "status": 200,
                "message": "Summary saved successfully",
                "data": {
                    "analytic_id": analytic.id,
                    "analytic_name": analytic.analytic_name,
                    "summary": analytic.summary,
                    "updated_at": str(analytic.updated_at),
                },
            },
            status_code=200,
        )

    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={
                "status": 500,
                "message": f"Failed to save summary: {str(e)}",
                "data": None,
            },
            status_code=500,
        )


@router.get("/analytic/{analytic_id}/export-pdf")
def export_contact_correlation_pdf(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    try:
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                content={"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).order_by(AnalyticDevice.id).all()

        device_ids = [link.device_id for link in device_links]
        if not device_ids:
            return JSONResponse(
                content={"status": 400, "message": "No devices linked to this analytic", "data": None},
                status_code=400,
            )

        contacts = (
            db.query(Contact)
            .filter(Contact.device_id.in_(device_ids))
            .order_by(Contact.id)
            .all()
        )

        device_contacts = defaultdict(dict)

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

        for contact in contacts:
            phones_found = []
            names_found = []

            contact_text = contact.display_name or ""
            phones_emails_text = contact.phone_number or ""

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

                phone = re.sub(r"\D", "", phone)
                if len(phone) < 7:
                    continue

                if not phone.startswith("62") and not phone.startswith("+62"):
                    if phone.startswith("0"):
                        phone = "62" + phone[1:]
                    else:
                        phone = "62" + phone

                name = names_found[0] if names_found else phone
                name = re.sub(r"\s+", " ", name).strip()

                device_contacts[contact.device_id][phone] = name

        correlation = defaultdict(dict)
        for device_id, phone_dict in device_contacts.items():
            for phone, name in phone_dict.items():
                correlation[phone][device_id] = name

        correlation = {
            phone: devices for phone, devices in correlation.items()
            if len(devices) >= 2
        }

        sorted_correlation = dict(
            sorted(correlation.items(), key=lambda x: len(x[1]), reverse=True)
        )

        devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
        device_info = {
            d.id: {
                "device_name": d.owner_name,
                "phone_number": d.phone_number,
                "device_id": d.id
            }
            for d in devices
        }

        reports_dir = settings.REPORTS_DIR
        analytic_folder = f"analytic_{analytic_id}"
        report_folder = os.path.join(reports_dir, analytic_folder)
        os.makedirs(report_folder, exist_ok=True)
        
        timestamp = get_indonesia_time().strftime('%Y%m%d_%H%M%S')
        filename = f"contact_correlation_report_{analytic_id}_{timestamp}.pdf"
        file_path = os.path.join(report_folder, filename)

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("Contact Correlation Analysis Report", title_style))
        story.append(Spacer(1, 12))

        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6
        )
        story.append(Paragraph(f"<b>Analytic ID:</b> {analytic_id}", info_style))
        story.append(Paragraph(f"<b>Analytic Name:</b> {analytic.analytic_name}", info_style))
        story.append(Paragraph(f"<b>Generated:</b> {get_indonesia_time().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
        story.append(Paragraph(f"Total Devices: {len(device_ids)}", info_style))
        story.append(Paragraph(f"Total Contacts: {len(contacts)}", info_style))
        story.append(Paragraph(f"Cross-Device Contacts: {len(sorted_correlation)}", info_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("<b>Device Information</b>", styles['Heading2']))
        device_data = [['Device ID', 'Device Name', 'Phone Number']]
        for device in devices:
            device_data.append([
                str(device.id),
                device.owner_name or 'N/A',
                device.phone_number or 'N/A'
            ])
        
        device_table = Table(device_data)
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(device_table)
        story.append(Spacer(1, 20))

        if sorted_correlation:
            story.append(Paragraph("<b>Contact Correlations</b>", styles['Heading2']))
            
            for phone, devices_dict in sorted_correlation.items():
                contact_style = ParagraphStyle(
                    'ContactStyle',
                    parent=styles['Normal'],
                    fontSize=12,
                    spaceAfter=6,
                    textColor=colors.darkblue
                )
                
                names = [name for name in devices_dict.values() if name and name != phone]
                contact_name = names[0] if names else phone
                
                story.append(Paragraph(f"<b>Contact:</b> {contact_name} ({phone})", contact_style))
                story.append(Paragraph(f"<b>Found on {len(devices_dict)} device(s):</b>", info_style))
                
                for device_id, name in devices_dict.items():
                    device_name = device_info.get(device_id, {}).get('device_name', 'Unknown')
                    story.append(Paragraph(f"• {device_name} (ID: {device_id}) - {name}", info_style))
                
                story.append(Spacer(1, 12))
        else:
            story.append(Paragraph("<b>No cross-device contacts found</b>", styles['Heading2']))

        doc.build(story)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        return JSONResponse(
            content={"status": 500, "message": f"Failed to generate PDF: {str(e)}", "data": None},
            status_code=500,
        )
