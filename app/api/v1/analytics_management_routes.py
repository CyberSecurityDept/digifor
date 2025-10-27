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
        
        existing_link = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == new_analytic.id
        ).first()
        
        if existing_link:

            for device_id in data.device_ids:
                if device_id not in existing_link.device_ids:
                    existing_link.device_ids.append(device_id)
                    linked_count += 1
                else:
                    already_linked += 1
        else:
            new_link = AnalyticDevice(
                analytic_id=new_analytic.id,
                device_ids=data.device_ids
            )
            db.add(new_link)
            linked_count = len(data.device_ids)
        
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
def get_hashfile_analytics(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    try:
        min_devices = 2
        
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            return JSONResponse(
                content={"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )
        
        if analytic.type != "Hashfile Analytics":
            return JSONResponse(
                content={
                    "status": 400, 
                    "message": f"This endpoint is only for Hashfile Analytics. Current analytic type is '{analytic.type}'", 
                    "data": None
                },
                status_code=400,
            )

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).all()
        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        device_ids = list(set(device_ids))
        
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
        
        # Create device labels (Device A, Device B, etc.)
        device_labels = []
        for i, device in enumerate(devices):
            if i < 26:
                device_label = f"Device {chr(65 + i)}"
            else:
                first_char = chr(65 + (i - 26) // 26)
                second_char = chr(65 + (i - 26) % 26)
                device_label = f"Device {first_char}{second_char}"
            device_labels.append(device_label)

        hashfiles = db.query(HashFile).filter(
            HashFile.device_id.in_(device_ids)
        ).all()

        hashfile_groups = {}
        for hashfile in hashfiles:
            hash_value = hashfile.file_hash
            if hash_value:
                if hash_value not in hashfile_groups:
                    hashfile_groups[hash_value] = {
                        "hash_value": hash_value,
                        "file_path": hashfile.path_original,
                        "file_kind": hashfile.kind or "Unknown",
                        "file_size_bytes": hashfile.size_bytes or 0,
                        "file_type": hashfile.file_type,
                        "file_extension": hashfile.file_extension,
                        "is_suspicious": hashfile.is_suspicious == "True" if hashfile.is_suspicious else False,
                        "risk_level": hashfile.risk_level or "Low",
                        "source_type": hashfile.source_type,
                        "source_tool": hashfile.source_tool,
                        "devices": set(),
                        "hashfile_records": []  # Store all hashfile records for this hash
                    }
                hashfile_groups[hash_value]["devices"].add(hashfile.device_id)
                hashfile_groups[hash_value]["hashfile_records"].append(hashfile)

        common_hashfiles = {
            hash_value: info for hash_value, info in hashfile_groups.items() 
            if len(info["devices"]) >= min_devices
        }

        hashfile_list = []
        for hash_value, info in common_hashfiles.items():
            found_in_devices = []
            
            # Get hashfile records for each device
            hashfile_records = info["hashfile_records"]
            device_hashfiles = {}
            
            # Group hashfile records by device
            for record in hashfile_records:
                device_hashfiles[record.device_id] = record
            
            # Create device-specific file info
            for i, device in enumerate(devices):
                if device.id in info["devices"]:
                    device_label = device_labels[i]
                    hashfile_record = device_hashfiles.get(device.id)
                    
                    if hashfile_record:
                        # Format file size for this specific device
                        file_size_bytes = hashfile_record.size_bytes or 0
                        if file_size_bytes > 0:
                            formatted_size = f"{file_size_bytes:,}".replace(",", ".")
                            if file_size_bytes >= 1024 * 1024 * 1024:  # GB
                                size_display = f"{file_size_bytes / (1024 * 1024 * 1024):.1f} GB"
                            elif file_size_bytes >= 1024 * 1024:  # MB
                                size_mb = file_size_bytes / (1000 * 1000)  # Use 1000 instead of 1024 for decimal MB
                                size_display = f"{size_mb:.1f} MB"
                            elif file_size_bytes >= 1024:  # KB
                                size_display = f"{file_size_bytes / 1024:.1f} KB"
                            else:
                                size_display = f"{file_size_bytes} bytes"
                            file_size_display = f"{formatted_size} ({size_display} on disk)"
                        else:
                            file_size_display = "Unknown size"
                        
                        # Format timestamps
                        if hashfile_record.created_at:
                            created_at = hashfile_record.created_at.strftime("%d %B %Y at %H.%M")
                            month_map = {
                                'January': 'Januari', 'February': 'Februari', 'March': 'Maret',
                                'April': 'April', 'May': 'Mei', 'June': 'Juni',
                                'July': 'Juli', 'August': 'Agustus', 'September': 'September',
                                'October': 'Oktober', 'November': 'November', 'December': 'Desember'
                            }
                            for eng, ind in month_map.items():
                                created_at = created_at.replace(eng, ind)
                        else:
                            created_at = "Unknown"
                            
                        if hashfile_record.updated_at:
                            modified_at = hashfile_record.updated_at.strftime("%d %B %Y at %H.%M")
                            for eng, ind in month_map.items():
                                modified_at = modified_at.replace(eng, ind)
                        else:
                            modified_at = "Unknown"
                        
                        device_file_info = {
                            "device_label": device_label,
                            "file_info": {
                                "file_kind": hashfile_record.kind or "Unknown",
                                "file_size_bytes": file_size_display,
                                "file_location": hashfile_record.path_original or "Unknown location",
                                "created_at": created_at,
                                "modified_at": modified_at,
                                "attributes": {
                                    "stationery_pad": False,
                                    "locked": False
                                }
                            }
                        }
                        found_in_devices.append(device_file_info)
            
            hashfile_data = {
                "hash_value": info["hash_value"],
                "found_in_devices": found_in_devices
            }
            
            hashfile_list.append(hashfile_data)

        # Sort by device count (most common first) - sesuai dengan "daftar teratas merupakan hashfile yang paling banyak ditemui di banyak device"
        hashfile_list.sort(key=lambda x: len(x["found_in_devices"]), reverse=True)

        # Create devices list with labels
        devices_list = []
        for i, device in enumerate(devices):
            devices_list.append({
                "device_label": device_labels[i],
                "owner_name": device.owner_name,
                "phone_number": device.phone_number
            })

        # Get summary from analytics_history table based on id and type
        summary = analytic.summary if analytic.summary else None

        return JSONResponse(
            content={
                "status": 200,
                "message": "Hashfile correlation analysis completed successfully",
                "data": {
                    "devices": devices_list,
                    "hashfiles": hashfile_list,
                    "summary": summary
                }
            },
            status_code=200,
        )

    except Exception as e:
        return JSONResponse(
            content={"status": 500, "message": f"Failed to get hashfile analytics: {str(e)}", "data": None},
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

