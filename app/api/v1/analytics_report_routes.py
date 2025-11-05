from fastapi import APIRouter, Depends, Query 
from fastapi.responses import JSONResponse, FileResponse  
from sqlalchemy.orm import Session  
from app.db.session import get_db
from app.analytics.shared.models import Device, Analytic, AnalyticDevice, File, Contact
from app.analytics.analytics_management.models import ApkAnalytic
from typing import List, Optional
from pydantic import BaseModel
from collections import defaultdict
from app.utils.timezone import get_indonesia_time
from app.core.config import settings
from reportlab.lib.pagesizes import A4  
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,Image,PageBreak 
from reportlab.lib import colors  
from reportlab.lib.enums import TA_CENTER, TA_LEFT,TA_RIGHT,TA_JUSTIFY 
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from app.api.v1.analytics_contact_routes import get_contact_correlation
from app.api.v1.analytics_management_routes import get_hashfile_analytics
from app.api.v1.analytics_social_media_routes import social_media_correlation
from app.api.v1.analytics_communication_enhanced_routes import get_chat_detail
from datetime import datetime
import dateutil.parser
import os, json
class SummaryRequest(BaseModel):
    summary: str

router = APIRouter()

@router.get("/analytic/{analytic_id}/export-pdf")
def export_analytics_pdf(
    analytic_id: int,
    db: Session = Depends(get_db),
    person_name: Optional[str] = Query(None, description="if method = Deep Communication Analytics"),
    device_id: Optional[int] = Query(None, description="if method = Deep Communication Analytics"),
    source: Optional[str] = Query(None, description="if method = Social Media Correlation or Deep Communication Analytics")
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

        method = analytic.method
        if "Contact" in method or "contact" in method.lower():
            return _export_contact_correlation_pdf(analytic, db)
        elif "APK" in method or "apk" in method.lower():
            return _export_apk_analytics_pdf(analytic, db)
        elif "Communication" in method or "communication" in method.lower():
            return _export_communication_analytics_pdf(analytic, db, source=source,person_name=person_name,device_id=device_id)
        elif "Social" in method or "social" in method.lower():
            return _export_social_media_analytics_pdf(analytic, db, source=source)
        elif "Hashfile" in method or "hashfile" in method.lower():
            return _export_hashfile_analytic_pdf(analytic, db)
        else:
            return _export_generic_analytics_pdf(analytic, db)

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

        setattr(analytic, 'summary', request.summary.strip())
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

        setattr(analytic, 'summary', str(request.summary).strip())
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

# def _export_contact_correlation_pdf(analytic, device_ids, db):
#     devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
#     file_ids = [d.file_id for d in devices]
    
#     contacts = (
#         db.query(Contact)
#         .filter(Contact.file_id.in_(file_ids))
#         .order_by(Contact.id)
#         .all()
#     )

#     device_contacts = defaultdict(dict)

#     phone_patterns = [
#         re.compile(r"(\+?\d{7,15})"),
#         re.compile(r"Mobile:\s*(\+?\d{7,15})", re.IGNORECASE),
#         re.compile(r"Phone number:\s*(\+?\d{7,15})", re.IGNORECASE),
#     ]

#     name_patterns = [
#         re.compile(r"First name:\s*(.*)", re.IGNORECASE),
#         re.compile(r"Display Name:\s*(.*)", re.IGNORECASE),
#         re.compile(r"Contact:\s*(.*)", re.IGNORECASE),
#     ]

#     for contact in contacts:
#         phones_found = []
#         names_found = []

#         contact_text = contact.display_name or ""
#         phones_emails_text = contact.phone_number or ""

#         for pattern in phone_patterns:
#             phones_found.extend(pattern.findall(contact_text))
#             phones_found.extend(pattern.findall(phones_emails_text))

#         for pattern in name_patterns:
#             match = pattern.search(contact_text)
#             if match:
#                 name = match.group(1).strip()
#                 if name and name not in names_found:
#                     names_found.append(name)

#         if not names_found and contact_text and not re.search(r"\d{7,15}", contact_text):
#             potential_name = contact_text.strip()
#             if potential_name and potential_name != "(Unknown)":
#                 names_found.append(potential_name)

#         for phone in phones_found:
#             if not phone:
#                 continue

#             phone = re.sub(r"\D", "", phone)
#             if len(phone) < 7:
#                 continue

#             if not phone.startswith("62") and not phone.startswith("+62"):
#                 if phone.startswith("0"):
#                     phone = "62" + phone[1:]
#                 else:
#                     phone = "62" + phone

#             name = names_found[0] if names_found else phone
#             name = re.sub(r"\s+", " ", name).strip()

#             # Find device_id from contact's file_id
#             contact_device_id = None
#             for d in devices:
#                 if d.file_id == contact.file_id:
#                     contact_device_id = d.id
#                     break
#             if contact_device_id:
#                 if contact_device_id not in device_contacts:
#                     device_contacts[contact_device_id] = {}
#                 device_contacts[contact_device_id][phone] = name

#     correlation = defaultdict(dict)
#     for device_id, phone_dict in device_contacts.items():
#         for phone, name in phone_dict.items():
#             correlation[phone][device_id] = name

#     correlation = {
#         phone: devices for phone, devices in correlation.items()
#         if len(devices) >= 2
#     }

#     sorted_correlation = dict(
#         sorted(correlation.items(), key=lambda x: len(x[1]), reverse=True)
#     )

#     return _generate_pdf_report(
#         analytic=analytic,
#         device_ids=device_ids,
#         db=db,
#         report_type="Contact Correlation Analysis",
#         filename_prefix="contact_correlation_report",
#         data={
#             "contacts": contacts,
#             "correlation": sorted_correlation,
#             "total_contacts": len(contacts),
#             "cross_device_contacts": len(sorted_correlation)
#         }
#     )

from reportlab.pdfgen import canvas
from reportlab.lib import colors

class GlobalPageCanvas(canvas.Canvas):
    """
    Canvas global dengan footer text + nomor halaman normal (Page X of Y).
    """

    def __init__(self, *args, footer_text="Generated Report", **kwargs):
        """
        Args:
            footer_text (str): teks footer kiri bawah.
        """
        self.footer_text = footer_text
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        """Simpan semua halaman sementara sebelum disave."""
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Render semua halaman dengan footer Page X of Y."""
        total_pages = len(self.pages)

        for page_number, page_dict in enumerate(self.pages, start=1):
            self.__dict__.update(page_dict)
            self._draw_footer(page_number, total_pages)
            super().showPage()

        super().save()

    def _draw_footer(self, current_page, total_pages):
        """Footer global + nomor halaman bawah normal."""
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.gray)

        # Garis atas footer
        self.setStrokeColor(colors.HexColor("#B0B0B0"))
        self.setLineWidth(0.5)
        self.line(40, 40, 575, 40)

        padding_y = 25
        # Kiri = teks footer
        self.drawString(40, padding_y, self.footer_text)

        # Kanan = nomor halaman
        page_label = f"Page {current_page} of {total_pages}"
        self.drawRightString(575, padding_y, page_label)


def build_report_header(analytic, timestamp_now, usable_width):
    """
    Generate header elemen (logo, exported time, title, method info)
    Return: list elemen story (Table + Spacer)
    """
    styles = getSampleStyleSheet()
    story = []

    subtitle_style = ParagraphStyle("Subtitle", fontSize=11, textColor=colors.black)
    title_style = ParagraphStyle(
        "Title", fontSize=18, textColor=colors.HexColor("#1a2b63"), spaceAfter=8, alignment=TA_LEFT
    )
    export_style = ParagraphStyle(
        "ExportStyle", fontSize=10, alignment=TA_RIGHT, textColor=colors.HexColor("#4b4b4b")
    )

    # === Logo dan waktu export ===
    logo_path = os.path.join(os.getcwd(), "assets", "logo.png")
    if not os.path.exists(logo_path):
        raise FileNotFoundError(f"Logo tidak ditemukan di {logo_path}")
    logo_img = Image(logo_path, width=130, height=30)

    export_time = Paragraph(
        f"<b>Exported:</b> {timestamp_now.strftime('%d/%m/%Y %H:%M:%S')}", export_style
    )

    header_table = Table(
        [[logo_img, export_time]], colWidths=[usable_width * 0.5, usable_width * 0.5]
    )
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # === Title ===
    story.append(Paragraph(f"<b>{analytic.analytic_name}</b>", title_style))
    story.append(Spacer(1, 10))

    # === Subheader Method dan File Uploaded ===
    subheader_data = [[
        Paragraph(f"<b>Method:</b> {analytic.method.replace('_', ' ').title()}", subtitle_style),
        Paragraph(f"<b>File Uploaded:</b> {timestamp_now.strftime('%d/%m/%Y %H:%M')}", subtitle_style),
    ]]
    subheader_table = Table(subheader_data, colWidths=[usable_width / 2, usable_width / 2], hAlign="LEFT")
    subheader_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#466086")),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#466086")),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(subheader_table)
    story.append(Spacer(1, 20))

    return story

# ===============================================================
# 🧩 EXPORT IMPLEMENTATIONS (tanpa device_ids)
# ===============================================================
def _export_contact_correlation_pdf(analytic, db):
    contacts = db.query(Contact).order_by(Contact.id).all()
    return _generate_pdf_report(
        analytic, db,
        report_type="Contact Correlation Analysis",
        filename_prefix="contact_correlation_report",
        data={"total_contacts": len(contacts)},
        method="contact_correlation"
    )
def _export_hashfile_analytic_pdf(analytic, db):
    contacts = db.query(Contact).order_by(Contact.id).all()
    return _generate_pdf_report(
        analytic, db,
        report_type="Hashfile Analytics",
        filename_prefix="hashfile_analytics_report",
        data={"total_contacts": len(contacts)},
        method="hashfile_analytics"
    )


def _export_apk_analytics_pdf(analytic, db):
    apk_analytics = db.query(ApkAnalytic).filter(ApkAnalytic.analytic_id == analytic.id).all()
    return _generate_pdf_report(
        analytic, db,
        report_type="APK Analytics Report",
        filename_prefix="apk_analytics_report",
        data={"total_apks": len(apk_analytics)},
        method="apk_analytics"
    )


def _export_communication_analytics_pdf(analytic, db,source,person_name,device_id):
    communications = []
    return _generate_pdf_report(
        analytic, db,
        report_type="Communication Analytics Report",
        filename_prefix="communication_analytics_report",
        data={"total_messages": len(communications)},
        method="deep_communication",
        source=source,
        person_name=person_name,
        device_id=device_id
    )


def _export_social_media_analytics_pdf(analytic, db,source):
    return _generate_pdf_report(
        analytic, db,
        report_type="Social Media Analytics Report",
        filename_prefix="social_media_analytics_report",
        data={"total_accounts": 0, "note": "Social media analytics tables removed"},
        method="social_media_correlation",
        source=source
    )


def _export_generic_analytics_pdf(analytic, db):
    return _generate_pdf_report(
        analytic, db,
        report_type="Generic Analytics Report",
        filename_prefix="analytics_report",
        data={"analytic_name": analytic.analytic_name},
        method="generic"
    )


# ===============================================================
# 🧱 ROUTER GENERATOR
# ===============================================================
def _generate_pdf_report(
        analytic, db, report_type, filename_prefix, data, method,source:Optional[str] = None,
        person_name:Optional[str] = None, device_id:Optional[int] = None,
    ):
    if method == "deep_communication":
        return _generate_deep_communication_report(analytic, db, report_type, filename_prefix, data, source, person_name,device_id)
    elif method == "contact_correlation":
        return _generate_contact_correlation_report(analytic, db, report_type, filename_prefix, data)
    elif method == "apk_analytics":
        return _generate_apk_analytics_report(analytic, db, report_type, filename_prefix, data)
    elif method == "social_media_correlation":
        return _generate_social_media_correlation_report(analytic, db, report_type, filename_prefix, data,source)
    elif method == "hashfile_analytics":
        return _generate_hashfile_analytics_report(analytic, db, report_type, filename_prefix, data)


# ===============================================================
# Utility Functions for Reports
# ===============================================================
def _build_table_header_style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

def _build_summary_section(usable_width, summary_text):
    """
    Build summary box with single text string instead of list.
    """
    # === Styles ===
    summary_title_style = ParagraphStyle(
        "SummaryTitle",
        fontSize=13,
        leading=16,
        textColor=colors.black,
        spaceAfter=6,
        fontName="Helvetica-Bold"
    )

    normal_style = ParagraphStyle(
        "Normal",
        fontSize=11,
        alignment=TA_JUSTIFY,
        leading=15,
        spaceAfter=4
    )

    # Handle None summary
    if summary_text is None:
        summary_text = "No summary."

    # === Build content ===
    summary_elements = [
        Paragraph("<b>Summary</b>", summary_title_style),
        Paragraph(summary_text, normal_style)
    ]

    summary_table = Table(
        [[elem] for elem in summary_elements],
        colWidths=[usable_width - 4]
    )

    summary_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#466086")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return summary_table


# ===============================================================
# 🧩 Deep Communication Report Example
# ===============================================================
def _generate_deep_communication_report(analytic, db, report_type, filename_prefix, data, source, person_name, device_id):
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)

    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    # === Setup halaman ===
    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=30,
        bottomMargin=50,
    )

    # ======================================================
    # 🔹 Ambil data chat real dari get_chat_detail()
    # ======================================================
    response = get_chat_detail(
        analytic_id=analytic.id,
        person_name=person_name,
        platform=source,
        device_id=device_id,
        search=None,
        db=db
    )

    try:
        response_data = json.loads(response.body.decode("utf-8"))
        chat_data = response_data.get("data", {})
        chat_messages = chat_data.get("chat_messages", [])
    except Exception as e:
        print(f"⚠️ Gagal parse chat_detail: {e}")
        chat_messages = []

    # === Styles ===
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("Heading", fontSize=12, leading=15, fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Normal", fontSize=11, leading=14, alignment=TA_LEFT)
    wrap_style = ParagraphStyle("Wrap", fontSize=11, leading=14, wordWrap="CJK", alignment=TA_JUSTIFY)

    # === Build content ===
    story = []
    story.extend(build_report_header(analytic, timestamp_now, usable_width))

    # === Example Metadata Table ===
    sender_name = chat_messages[0]["sender"] if chat_messages else "Unknown"
    receiver_name = chat_messages[0]["recipient"] if chat_messages else "Unknown"
    total_messages = len(chat_messages)
    platform_name = chat_data.get("platform", source or "Unknown")

    info_data = [
        ["Source", f": {platform_name}", "Sender", f": {sender_name}"],
        ["Receiver", f": {receiver_name}", "Messages", f": {total_messages} total"],
    ]
    info_table = Table(info_data, colWidths=[60, (usable_width / 2 - 60), 60, (usable_width / 2 - 60)])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # ======================================================
    # 🔹 Chat data dinamis dari get_chat_detail()
    # ======================================================
    chat_records = []
    for msg in chat_messages:
        # Gunakan timestamp lengkap + format jadi YYYY-MM-DD HH:MM
        timestamp_raw = msg.get("timestamp")
        time_display = msg.get("times") or ""

        if timestamp_raw:
            try:
                dt = dateutil.parser.isoparse(timestamp_raw)
                # Format tanggal + jam lokal
                time_val = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                # fallback jika parsing gagal
                time_val = time_display or timestamp_raw
        else:
            time_val = time_display

        sender = msg.get("sender", "Unknown")
        text = msg.get("message_text", "")
        chat_records.append({
            "time": time_val,
            "chat": f"{sender}: {text}"
        })

    # === Header dan isi tabel chat ===
    col_time = 140  # diperlebar sedikit biar muat tanggal
    col_chat = usable_width - col_time
    chat_data = [["Time", "Chat"]]
    for row in chat_records:
        chat_data.append([
            Paragraph(row["time"], wrap_style),
            Paragraph(row["chat"], wrap_style)
        ])

    # === Buat tabel chat ===
    chat_table = Table(chat_data, colWidths=[col_time, col_chat])
    chat_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 10.5),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        # Body
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(chat_table)
    story.append(Spacer(1, 20))

    # === Summary ===
    summary_points = analytic.summary
    summary_table = _build_summary_section(usable_width, summary_points)
    story.append(summary_table)

    # === Build PDF ===
    doc.build(
        story,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        ),
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ===============================================================
# 3️⃣ APK Analytics Report
# ===============================================================
def _generate_apk_analytics_report(analytic, db, report_type, filename_prefix, data):

    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    # === Setup halaman ===
    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=30,
        bottomMargin=60
    )

    # === Styles ===
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("Heading", fontSize=12, leading=15, fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Normal", fontSize=10.5, leading=14, alignment=TA_LEFT)
    wrap_desc = ParagraphStyle("WrapDesc", fontSize=10.5, leading=14, alignment=TA_JUSTIFY)
    title_box_style = ParagraphStyle("TitleBox", fontSize=11.5, leading=14, fontName="Helvetica-Bold", textColor=colors.black)

    # === Ambil data real dari DB ===
    apk_analytics = db.query(ApkAnalytic).filter(ApkAnalytic.analytic_id == analytic.id).all()

    malicious_items = []
    common_items = []

    for row in apk_analytics:
        item = row.item or "-"
        desc = row.description or "-"
        if (row.status or "").lower() == "dangerous":
            malicious_items.append([item, desc])
        else:
            common_items.append([item, desc])

    # === Build content ===
    story = []
    story.extend(build_report_header(analytic, timestamp_now, usable_width))

    # === Ringkasan umum (jumlah & scoring rata-rata) ===
    total_apks = len(apk_analytics)
    total_malicious = len(malicious_items)
    total_common = len(common_items)
    avg_score = "-"
    try:
        scores = [float(a.malware_scoring) for a in apk_analytics if a.malware_scoring]
        avg_score = f"{sum(scores) / len(scores):.1f}%" if scores else "-"
    except Exception:
        pass

    info_data = [
        ["Total APK Files", f": {total_apks}"],
        ["Malicious Items", f": {total_malicious}"],
        ["Common Items", f": {total_common}"],
        ["Average Malware Scoring", f": {avg_score}"],
    ]
    info_table = Table(info_data, colWidths=[160, usable_width - 160])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # === Section: Malicious ===
    story.append(Paragraph("<b>Malicious</b>", heading_style))
    story.append(Spacer(1, 4))
    if malicious_items:
        col_left = round(usable_width * 0.3, 2)
        col_right = usable_width - col_left
        mal_data = [["Malicious Item", "Description"]]
        for item, desc in malicious_items:
            mal_data.append([Paragraph(item, normal_style), Paragraph(desc, wrap_desc)])
        mal_table = Table(mal_data, colWidths=[col_left, col_right])
        mal_table.setStyle(_build_table_header_style())
        story.append(mal_table)
    else:
        story.append(Paragraph("Tidak ditemukan entri berstatus <b>dangerous</b>.", normal_style))
    story.append(Spacer(1, 20))

    # === Section: Common ===
    story.append(Paragraph("<b>Common</b>", heading_style))
    story.append(Spacer(1, 4))
    if common_items:
        com_data = [["Common Item", "Description"]]
        for item, desc in common_items:
            com_data.append([Paragraph(item, normal_style), Paragraph(desc, wrap_desc)])
        com_table = Table(com_data, colWidths=[col_left, col_right])
        com_table.setStyle(_build_table_header_style())
        story.append(com_table)
    else:
        story.append(Paragraph("Tidak ada entri common terdeteksi.", normal_style))
    story.append(Spacer(1, 20))

    # === Summary ===
    summary_points = analytic.summary
    summary_table = _build_summary_section(usable_width, summary_points)
    story.append(summary_table)

    # === Build PDF ===
    doc.build(
        story,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        ),
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
# ===============================================================
# 4️⃣ Social Media Correlations Report (Fixed spacing & padding)
# ===============================================================
def _generate_social_media_correlation_report(analytic, db, report_type, filename_prefix, data, source):
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    # === Setup layout PDF ===
    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=30,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle("Normal", fontSize=10, leading=13)
    bold_style = ParagraphStyle("Bold", fontSize=10, leading=13, fontName="Helvetica-Bold")

    story = []
    story.extend(build_report_header(analytic, timestamp_now, usable_width))

    # === Ambil data langsung dari endpoint correlation ===
    response = social_media_correlation(analytic.id, source, db)
    if hasattr(response, "body"):
        body = json.loads(response.body)
        response_data = body.get("data", {})
    else:
        response_data = response.get("data", {}) if isinstance(response, dict) else {}

    platform_name = list(response_data.get("correlations", {}).keys())[0] if response_data.get("correlations") else source.capitalize()
    correlation_data = response_data.get("correlations", {}).get(platform_name, {})
    buckets = correlation_data.get("buckets", [])
    devices = response_data.get("devices", [])
    total_devices = response_data.get("total_devices", len(devices))
    total_accounts = sum(len(bucket.get("devices", [])) for bucket in buckets)

    # === Info Summary ===
    info_data = [
        ["Source", f": {platform_name}"],
        ["Total Device", f": {total_devices} Devices"],
        ["Total Social Media Accounts", f": {total_accounts} Accounts"],
    ]
    info_table = Table(info_data, colWidths=[150, usable_width - 150])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # === Device Identification Summary ===
    story.append(Paragraph("<b>Device Identification Summary</b>", bold_style))
    story.append(Spacer(1, 4))

    device_table_data = [["Device ID", "Registered Owner", "Phone Number"]]
    for d in devices:
        device_table_data.append([str(d["device_id"]), d["owner_name"], d["phone_number"]])

    col1 = round(usable_width * 0.25, 2)
    col2 = round(usable_width * 0.35, 2)
    col3 = usable_width - (col1 + col2)

    device_table = Table(device_table_data, colWidths=[col1, col2, col3])
    device_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(device_table)
    story.append(Spacer(1, 20))

    # === Device Account Correlation ===
    story.append(Paragraph("<b>Device Account Correlation</b>", bold_style))
    story.append(Spacer(1, 6))

    if not buckets:
        story.append(Paragraph("No correlation data found for this platform.", normal_style))
    else:
        correlation_table_data = [["Connections", "Involved Devices", "Correlated Accounts"]]

        for bucket in buckets:
            label = bucket.get("label", "")
            devices_rows = bucket.get("devices", [])

            first_row = True
            for accounts in devices_rows:
                # Format daftar akun jadi bullet list
                accounts_clean = [a for a in accounts if a]
                acc_formatted = [
                    Paragraph(f"• {a}", normal_style) for a in accounts_clean
                ]
                acc_table = Table([[a] for a in acc_formatted], colWidths=[usable_width * 0.4])
                acc_table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]))

                involved_devices = ", ".join(
                    [d["owner_name"] for d in devices]
                )
                row = [
                    Paragraph(label if first_row else "", normal_style),
                    Paragraph(involved_devices, normal_style),
                    acc_table,
                ]
                correlation_table_data.append(row)
                first_row = False

        col_a = round(usable_width * 0.25, 2)
        col_b = round(usable_width * 0.25, 2)
        col_c = usable_width - (col_a + col_b)

        corr_table = Table(correlation_table_data, colWidths=[col_a, col_b, col_c])
        corr_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(corr_table)
    story.append(Spacer(1, 20))

    # === Summary ===
    story.append(_build_summary_section(usable_width, analytic.summary))
    story.append(Spacer(1, 10))

    # === Build PDF ===
    doc.build(
        story,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        ),
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _generate_contact_correlation_report(analytic, db, report_type, filename_prefix, data):
    """
    Generate PDF report for Contact Correlation analytic
    """
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    # === PDF Setup ===
    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=30,
        bottomMargin=50,
    )

    result = get_contact_correlation(analytic.id,db)
    if isinstance(result, JSONResponse):
        result = result.body
    if isinstance(result, (bytes, bytearray)):
        result = json.loads(result.decode("utf-8"))
    
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            result = {}
    elif not isinstance(result, dict):
        result = {}

    api_data = result.get("data", {})
    devices = api_data.get("devices", [])
    correlations = api_data.get("correlations", [])
    summary = api_data.get("summary")

    styles = getSampleStyleSheet()
    normal_center = ParagraphStyle("NormalCenter", fontSize=10, leading=13, alignment=TA_CENTER)
    normal_left = ParagraphStyle("NormalLeft", fontSize=10, leading=13, alignment=TA_LEFT)

    group_size = 4
    grouped_devices = [devices[i:i + group_size] for i in range(0, len(devices), group_size)]
    total_groups = len(grouped_devices)

    story = []
    group_page_map = []

    for group_index, group in enumerate(grouped_devices, start=1):
        story.extend(build_report_header(analytic, timestamp_now, usable_width))
        group_page_map.append(group_index)

        start_device = (group_index - 1) * group_size + 1
        end_device = start_device + len(group) - 1

        info_data = [
            ["Source", "        : Contact Correlation"],
            ["Total Device", f"        : {len(devices)} Devices (Device {start_device}-{end_device})"],
            ["Total Correlated Contacts", f"        : {len(correlations)} Contacts"],
        ]
        story.append(Table(info_data, colWidths=[100, usable_width - 100]))
        story.append(Spacer(1, 16))

        header_row = ["Contact Number"]
        for dev in group:
            header_row.append(Paragraph(
                f"<b>{dev['device_label']}</b><br/><font size=9>{dev['phone_number'] or '-'}</font>",
                ParagraphStyle("HeaderDevice", alignment=TA_CENTER, textColor=colors.white, fontName="Helvetica-Bold")
            ))

        table_data = [header_row]

        for corr in correlations:
            contact_num = corr.get("contact_number", "-")
            row = [Paragraph(contact_num, normal_left)]

            dev_map = {d["device_label"]: d["contact_name"] for d in corr.get("devices_found_in", [])}

            for dev in group:
                device_label = dev["device_label"]
                cell_value = dev_map.get(device_label, "—")
                row.append(Paragraph(cell_value, normal_center))

            table_data.append(row)

        col_widths = [usable_width * 0.25] + [((usable_width * 0.75) / len(group)) for _ in group]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(table)

        if group_index < total_groups:
            story.append(PageBreak())

    story.append(Spacer(1, 20))
    story.append(_build_summary_section(usable_width, summary))

    doc.build(
        story,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        ),
    )

    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")

def _generate_hashfile_analytics_report(analytic, db, report_type, filename_prefix, data):
    # === Setup path dan file ===
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=30,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle("Normal", fontSize=10, leading=13, alignment=TA_CENTER)
    header_style = ParagraphStyle("HeaderDevice", alignment=TA_CENTER, textColor=colors.white, fontName="Helvetica-Bold", fontSize=9)

    response = get_hashfile_analytics(analytic.id, db)
    if hasattr(response, "body"):
        body = json.loads(response.body)
        data = body.get("data", {})
    elif isinstance(response, dict):
        data = response.get("data", {})
    else:
        data = {}

    devices = data.get("devices", [])
    hashfiles = data.get("correlations") or []

    group_size = 4
    grouped_devices = [devices[i:i + group_size] for i in range(0, len(devices), group_size)]
    total_groups = len(grouped_devices)

    story = []
    for group_index, group in enumerate(grouped_devices, start=1):
        story.extend(build_report_header(analytic, timestamp_now, usable_width))

        start_device = (group_index - 1) * group_size + 1
        end_device = start_device + len(group) - 1
        info_data = [
            ["Source", ": Handphone"],
            ["Total Device", f": {len(devices)} Devices (Device {start_device}-{end_device})"],
            ["Total Correlated Hashfiles", f": {len(hashfiles)} Files"],
        ]
        story.append(Table(info_data, colWidths=[120, usable_width - 120]))
        story.append(Spacer(1, 16))

        header_row = ["Filename"]
        for dev in group:
            device_label = dev.get("device_label", "Unknown")
            phone_number = dev.get("phone_number", "-") or "-"
            header_html = f"<b>{device_label}</b><br/><font size=9>{phone_number}</font>"
            header_row.append(Paragraph(header_html, header_style))

        table_data = [header_row]

        for h in hashfiles:
            file_name = h.get("file_name", "Unknown")
            row = [Paragraph(file_name, normal_style)]
            for dev in group:
                symbol = "✔" if dev.get("device_label") in h.get("devices", []) else "✘"
                row.append(Paragraph(symbol, normal_style))
            table_data.append(row)

        table = Table(
            table_data,
            colWidths=[usable_width * 0.25] +
                      [((usable_width * 0.75) / len(group)) for _ in group],
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(table)

        if group_index < total_groups:
            story.append(PageBreak())

    story.append(Spacer(1, 20))
    story.append(_build_summary_section(usable_width, analytic.summary))

    doc.build(
        story,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        ),
    )

    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")
