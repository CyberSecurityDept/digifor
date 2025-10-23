from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.analytics_management.service import store_analytic, get_all_analytics
from app.analytics.shared.models import Device, Analytic, AnalyticDevice, File, Contact
from app.analytics.device_management.models import HashFile, DeepCommunication
from app.analytics.analytics_management.models import ApkAnalytic
from typing import List, Optional
from pydantic import BaseModel
from collections import defaultdict
import re
from app.utils.timezone import get_indonesia_time
from app.core.config import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
import os

class SummaryRequest(BaseModel):
    summary: str

def format_file_size(size_bytes):
    if size_bytes is None:
        return None
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

router = APIRouter()

# Hashfile Analytics Router with separate tags
hashfile_router = APIRouter(tags=["Hashfile Analytics"])

@router.get("/analytics/get-all-analytic")
def get_all_analytic(db: Session = Depends(get_db)):
    try:
        analytics = get_all_analytics(db)
        return {
            "status": 200,
            "message": f"Retrieved {len(analytics)} analytics successfully",
            "data": analytics
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal mengambil data: {str(e)}",
            "data": []
        }




class CreateAnalyticWithDevicesRequest(BaseModel):
    analytic_name: str
    method: str
    device_ids: List[int]
    min_device_threshold: Optional[int] = 2
    include_suspicious_only: Optional[bool] = False
    hash_algorithm: Optional[str] = "MD5"

@router.post("/analytics/create-analytic-with-devices")
def create_analytic_with_devices(
    data: CreateAnalyticWithDevicesRequest, 
    db: Session = Depends(get_db)
):
    try:
        if not data.analytic_name.strip():
            return {
                "status": 400,
                "message": "analytic_name wajib diisi",
                "data": []
            }

        valid_methods = [
            "Deep communication analytics",
            "Social Media Correlation",
            "Contact Correlation",
            "APK Analytics",
            "Hashfile Analytics"
        ]
        
        if data.method not in valid_methods:
            return {
                "status": 400,
                "message": f"Invalid method. Must be one of: {valid_methods}",
                "data": []
            }

        existing_devices = db.query(Device).filter(Device.id.in_(data.device_ids)).all()
        existing_device_ids = [d.id for d in existing_devices]
        missing_device_ids = [did for did in data.device_ids if did not in existing_device_ids]
        
        if missing_device_ids:
            return {
                "status": 400,
                "message": f"Devices not found: {missing_device_ids}",
                "data": []
            }

        # Create general analytic for all methods
        new_analytic = store_analytic(
            db=db,
            analytic_name=data.analytic_name,
            type=data.method,
            method=data.method,
        )

        linked_count = 0
        already_linked = 0
        
        for device_id in data.device_ids:
            existing_link = db.query(AnalyticDevice).filter(
                AnalyticDevice.analytic_id == new_analytic.id,
                AnalyticDevice.device_id == device_id
            ).first()
            
            if existing_link:
                already_linked += 1
                continue
                
            new_link = AnalyticDevice(
                analytic_id=new_analytic.id,
                device_id=device_id
            )
            db.add(new_link)
            linked_count += 1
        
        db.commit()

        devices_info = []
        for device in existing_devices:
            devices_info.append({
                "device_id": device.id,
                "owner_name": device.owner_name,
                "phone_number": device.phone_number,
                "device_name": device.device_name
            })

        result = {
            "analytic": {
                "id": new_analytic.id,
                "analytic_name": new_analytic.analytic_name,
                "type": new_analytic.type,
                "method": new_analytic.method,
                "summary": new_analytic.summary,
                "created_at": str(new_analytic.created_at)
            },
            "linked_devices": {
                "total_devices": len(data.device_ids),
                "linked_count": linked_count,
                "already_linked": already_linked,
                "devices": devices_info
            }
        }

        return {
            "status": 200,
            "message": f"Analytics created and {linked_count} devices linked successfully",
            "data": result
        }

    except Exception as e:
        db.rollback()
        return {
            "status": 500,
            "message": f"Gagal membuat analytic dengan devices: {str(e)}",
            "data": []
        }


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

@hashfile_router.get("/analytic/{analytic_id}/hashfile-analytics")
def get_hashfile_correlation(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Set minimum devices threshold to 2 (fixed value)
        min_devices = 2
        
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                content={"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).all()
        device_ids = [link.device_id for link in device_links]
        
        if not device_ids:
            return JSONResponse(
                content={"status": 400, "message": "No devices linked to this analytic", "data": None},
                status_code=400,
            )

        # Get devices info
        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        device_info = {
            d.id: {
                "id": d.id,
                "owner_name": d.owner_name,
                "phone_number": d.phone_number,
                "device_name": getattr(d, 'device_name', d.owner_name)
            }
            for d in devices
        }

        # Get all hashfiles from these devices
        hashfiles = db.query(HashFile).filter(
            HashFile.device_id.in_(device_ids)
        ).all()

        # Group hashfiles by hash value
        hashfile_groups = {}
        for hashfile in hashfiles:
            hash_value = hashfile.file_hash
            if hash_value:
                if hash_value not in hashfile_groups:
                    hashfile_groups[hash_value] = {
                        "hash_value": hash_value,
                        "file_name": hashfile.name or "Unknown",
                        "file_path": hashfile.file_path,
                        "file_size": hashfile.file_size,
                        "file_type": hashfile.file_type,
                        "file_extension": hashfile.file_extension,
                        "is_suspicious": hashfile.is_suspicious == "True" if hashfile.is_suspicious else False,
                        "risk_level": hashfile.risk_level or "Low",
                        "source_type": hashfile.source_type,
                        "source_tool": hashfile.source_tool,
                        "devices": set()
                    }
                hashfile_groups[hash_value]["devices"].add(hashfile.device_id)

        # Filter hashfiles that appear on at least min_devices devices
        common_hashfiles = {
            hash_value: info for hash_value, info in hashfile_groups.items() 
            if len(info["devices"]) >= min_devices
        }

        # Convert to list and add device presence info
        hashfile_list = []
        for hash_value, info in common_hashfiles.items():
            hashfile_data = {
                "hash_value": info["hash_value"],
                "file_name": info["file_name"],
                "file_path": info["file_path"],
                "file_size": info["file_size"],
                "file_type": info["file_type"],
                "file_extension": info["file_extension"],
                "is_suspicious": info["is_suspicious"],
                "risk_level": info["risk_level"],
                "source_type": info["source_type"],
                "source_tool": info["source_tool"],
                "device_count": len(info["devices"]),
                "devices": {}
            }
            
            # Create device presence matrix for UI
            for device in devices:
                hashfile_data["devices"][device.id] = {
                    "device_id": device.id,
                    "device_name": device_info[device.id]["device_name"],
                    "owner_name": device_info[device.id]["owner_name"],
                    "phone_number": device_info[device.id]["phone_number"],
                    "is_present": device.id in info["devices"],
                    "device_info": device_info[device.id]
                }
            
            hashfile_list.append(hashfile_data)

        # Sort by device count (most common first) - sesuai dengan "daftar teratas merupakan hashfile yang paling banyak ditemui di banyak device"
        hashfile_list.sort(key=lambda x: x["device_count"], reverse=True)

        return JSONResponse(
            content={
                "status": 200,
                "message": "Hashfile correlation retrieved successfully",
                "data": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name,
                    "devices": list(device_info.values()),
                    "hashfiles": hashfile_list,
                    "statistics": {
                        "total_devices": len(devices),
                        "total_hashfiles": len(hashfile_groups),
                        "common_hashfiles": len(hashfile_list),  # Hashfiles yang muncul di minimal min_devices device
                        "unique_hashfiles": len(hashfile_groups) - len(hashfile_list),  # Hashfiles yang hanya muncul di 1 device
                        "min_devices_threshold": min_devices
                    },
                    "description": {
                        "endpoints": {
                            "save_summary": f"/api/v1/analytic/{analytic_id}/save-summary",
                            "export_pdf": f"/api/v1/analytic/{analytic_id}/export-pdf"
                        }
                    }
                }
            },
            status_code=200,
        )

    except Exception as e:
        return JSONResponse(
            content={"status": 500, "message": f"Failed to get hashfile correlation: {str(e)}", "data": None},
            status_code=500,
        )


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

        device_ids = [link.device_id for link in device_links]
        if not device_ids:
            return JSONResponse(
                content={"status": 400, "message": "No devices linked to this analytic", "data": None},
                status_code=400,
            )

        # Determine export type based on analytic method
        method = analytic.method or analytic.type or "Unknown"
        
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

def _export_contact_correlation_pdf(analytic, device_ids, db):
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
    """Export Communication Analytics PDF"""
    
    communications = db.query(DeepCommunication).filter(
        DeepCommunication.device_id.in_(device_ids)
    ).all()
    
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
    """Export Social Media Analytics PDF - DISABLED (tables removed)"""
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
    """Export Generic Analytics PDF"""
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
    """Generate PDF report with common structure"""
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

    # Title
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

    # Info
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    story.append(Paragraph(f"<b>Analytic ID:</b> {analytic.id}", info_style))
    story.append(Paragraph(f"<b>Analytic Name:</b> {analytic.analytic_name}", info_style))
    story.append(Paragraph(f"<b>Method:</b> {analytic.method or analytic.type}", info_style))
    story.append(Paragraph(f"<b>Generated:</b> {get_indonesia_time().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
    story.append(Spacer(1, 20))

    # Summary
    story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
    story.append(Paragraph(f"Total Devices: {len(device_ids)}", info_style))
    
    # Add specific data based on report type
    for key, value in data.items():
        if isinstance(value, (int, str)):
            story.append(Paragraph(f"{key.replace('_', ' ').title()}: {value}", info_style))
    
    story.append(Spacer(1, 20))

    # Device Information
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

    # Add summary if available
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

# Export both routers
__all__ = ["router", "hashfile_router"]

