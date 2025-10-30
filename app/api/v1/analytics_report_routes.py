from fastapi import APIRouter, Depends  # type: ignore
from fastapi.responses import JSONResponse, FileResponse  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from app.db.session import get_db
from app.analytics.shared.models import Device, Analytic, AnalyticDevice, File, Contact
from app.analytics.analytics_management.models import ApkAnalytic
from typing import List, Optional
from pydantic import BaseModel  # type: ignore
from collections import defaultdict
import re
from app.utils.timezone import get_indonesia_time
from app.core.config import settings
from reportlab.lib.pagesizes import A4  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.lib.enums import TA_CENTER  # type: ignore
import os

class SummaryRequest(BaseModel):
    summary: str

router = APIRouter()


@router.get("/analytic/{analytic_id}/export-pdf")
def export_analytics_pdf(
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

        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        device_ids = list(set(device_ids))
        if not device_ids:
            return JSONResponse(
                content={"status": 400, "message": "No devices linked to this analytic", "data": None},
                status_code=400,
            )

        method = analytic.method or "Unknown"
        
        if "Contact" in method or "contact" in method.lower():
            return _export_contact_correlation_pdf(analytic, device_ids, db)
        elif "APK" in method or "apk" in method.lower():
            return _export_apk_analytics_pdf(analytic, device_ids, db)
        elif "Communication" in method or "communication" in method.lower():
            return _export_communication_analytics_pdf(analytic, device_ids, db)
        elif "Social" in method or "social" in method.lower():
            return _export_social_media_analytics_pdf(analytic, device_ids, db)
        else:
            return _export_generic_analytics_pdf(analytic, device_ids, db)

    except Exception as e:
        return JSONResponse(
            content={"status": 500, "message": f"Failed to generate PDF: {str(e)}", "data": None},
            status_code=500,
        )

@router.post("/analytic/{analytic_id}/save-summary")
def save_analytic_summary(
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


@router.put("/analytic/{analytic_id}/edit-summary")
def edit_analytic_summary(
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

        if request.summary is None or not str(request.summary).strip():
            return JSONResponse(
                content={"status": 400, "message": "Summary cannot be empty", "data": None},
                status_code=400,
            )

        analytic.summary = str(request.summary).strip()
        db.commit()
        db.refresh(analytic)

        return JSONResponse(
            content={
                "status": 200,
                "message": "Summary updated successfully",
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
                "message": f"Failed to edit summary: {str(e)}",
                "data": None,
            },
            status_code=500,
        )

def _export_contact_correlation_pdf(analytic, device_ids, db):
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    file_ids = [d.file_id for d in devices]
    
    contacts = (
        db.query(Contact)
        .filter(Contact.file_id.in_(file_ids))
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

            # Find device_id from contact's file_id
            contact_device_id = None
            for d in devices:
                if d.file_id == contact.file_id:
                    contact_device_id = d.id
                    break
            if contact_device_id:
                if contact_device_id not in device_contacts:
                    device_contacts[contact_device_id] = {}
                device_contacts[contact_device_id][phone] = name

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

    return _generate_pdf_report(
        analytic=analytic,
        device_ids=device_ids,
        db=db,
        report_type="Contact Correlation Analysis",
        filename_prefix="contact_correlation_report",
        data={
            "contacts": contacts,
            "correlation": sorted_correlation,
            "total_contacts": len(contacts),
            "cross_device_contacts": len(sorted_correlation)
        }
    )

def _export_apk_analytics_pdf(analytic, device_ids, db):
    """Export APK Analytics PDF"""
    
    apk_analytics = db.query(ApkAnalytic).filter(
        ApkAnalytic.analytic_id == analytic.id
    ).all()
    
    return _generate_pdf_report(
        analytic=analytic,
        device_ids=device_ids,
        db=db,
        report_type="APK Analytics Report",
        filename_prefix="apk_analytics_report",
        data={
            "apk_analytics": apk_analytics,
            "total_apks": len(apk_analytics)
        }
    )

def _export_communication_analytics_pdf(analytic, device_ids, db):
    communications = []
    
    return _generate_pdf_report(
        analytic=analytic,
        device_ids=device_ids,
        db=db,
        report_type="Communication Analytics Report",
        filename_prefix="communication_analytics_report",
        data={
            "communications": communications,
            "total_messages": len(communications)
        }
    )

def _export_social_media_analytics_pdf(analytic, device_ids, db):
    return _generate_pdf_report(
        analytic=analytic,
        device_ids=device_ids,
        db=db,
        report_type="Social Media Analytics Report (Not Available)",
        filename_prefix="social_media_analytics_report",
        data={
            "total_accounts": 0,
            "note": "Social media analytics tables have been removed"
        }
    )

def _export_generic_analytics_pdf(analytic, device_ids, db):
    return _generate_pdf_report(
        analytic=analytic,
        device_ids=device_ids,
        db=db,
        report_type="Analytics Report",
        filename_prefix="analytics_report",
        data={
            "total_devices": len(device_ids)
        }
    )

def _generate_pdf_report(analytic, device_ids, db, report_type, filename_prefix, data):
    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    
    reports_dir = settings.REPORTS_DIR
    analytic_folder = f"analytic_{analytic.id}"
    report_folder = os.path.join(reports_dir, analytic_folder)
    os.makedirs(report_folder, exist_ok=True)
    
    timestamp = get_indonesia_time().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{analytic.id}_{timestamp}.pdf"
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
    story.append(Paragraph(report_type, title_style))
    story.append(Spacer(1, 12))

    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    story.append(Paragraph(f"<b>Analytic ID:</b> {analytic.id}", info_style))
    story.append(Paragraph(f"<b>Analytic Name:</b> {analytic.analytic_name}", info_style))
    story.append(Paragraph(f"<b>Method:</b> {analytic.method or 'Unknown'}", info_style))
    story.append(Paragraph(f"<b>Generated:</b> {get_indonesia_time().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
    story.append(Spacer(1, 20))


    story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
    story.append(Paragraph(f"Total Devices: {len(device_ids)}", info_style))

    for key, value in data.items():
        if isinstance(value, (int, str)):
            story.append(Paragraph(f"{key.replace('_', ' ').title()}: {value}", info_style))
    
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

    if analytic.summary:
        story.append(Paragraph("<b>Analytic Summary</b>", styles['Heading2']))
        story.append(Paragraph(analytic.summary, info_style))
        story.append(Spacer(1, 20))

    doc.build(story)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

