from fastapi import APIRouter, Depends, Query 
from fastapi.responses import JSONResponse, FileResponse  
from sqlalchemy.orm import Session  
from sqlalchemy import func
from app.db.session import get_db
from app.analytics.shared.models import Device, Analytic, AnalyticDevice, File, Contact
from app.analytics.analytics_management.models import ApkAnalytic
from typing import List, Optional, Iterator, Generator
from pydantic import BaseModel
from collections import defaultdict
from app.utils.timezone import get_indonesia_time
from app.core.config import settings
from reportlab.lib.pagesizes import A4  
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether 
from reportlab.lib import colors  
from reportlab.lib.enums import TA_CENTER, TA_LEFT,TA_RIGHT,TA_JUSTIFY 
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from app.api.v1.analytics_contact_routes import _get_contact_correlation_data
from app.api.v1.analytics_management_routes import _get_hashfile_analytics_data, check_analytic_access
from app.api.v1.analytics_social_media_routes import social_media_correlation
from app.api.v1.analytics_communication_enhanced_routes import get_chat_detail
from app.auth.models import User
from app.api.deps import get_current_user
from datetime import datetime
import dateutil.parser
import os, json, gc, logging, time
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

class SummaryRequest(BaseModel):
    summary: str

router = APIRouter()

PDF_EXPORT_BATCH_SIZE = 10000

def stream_query_in_batches(query, batch_size: int = PDF_EXPORT_BATCH_SIZE) -> Generator:
    offset = 0
    batch_number = 0
    total_processed = 0
    start_time = time.time()
    
    logger.info(f"Starting streaming query with batch_size={batch_size}")
    
    while True:
        batch_start_time = time.time()
        batch = query.offset(offset).limit(batch_size).all()
        if not batch:
            elapsed = time.time() - start_time
            logger.info(f"Streaming query completed. Total batches: {batch_number}, Total records: {total_processed}, Time: {elapsed:.2f}s")
            break
        
        batch_number += 1
        batch_size_actual = len(batch)
        total_processed += batch_size_actual
        batch_time = time.time() - batch_start_time
        
        logger.debug(f"Batch {batch_number}: {batch_size_actual} records (offset {offset}), processed in {batch_time:.2f}s, total: {total_processed}")
        
        if batch_number % 10 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Progress: {batch_number} batches, {total_processed} records processed in {elapsed:.2f}s")
        
        yield batch
        offset += batch_size
        
        if offset % (batch_size * 10) == 0:
            gc.collect()
            logger.debug(f"Garbage collection triggered at offset {offset}")

def get_total_count(query) -> int:
    return query.count()

@router.get("/analytic/export-pdf", 
            summary="Export analytics report to PDF",
            description="Export analytics report to PDF. This endpoint is optimized for large datasets (millions of records) and uses streaming/chunking to avoid timeout and memory issues.")
def export_analytics_pdf(
    analytic_id: int = Query(..., description="Analytic ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    person_name: Optional[str] = Query(None, description="if method = Deep Communication Analytics"),
    device_id: Optional[int] = Query(None, description="if method = Deep Communication Analytics"),
    source: Optional[str] = Query(None, description="if method = Social Media Correlation or Deep Communication Analytics")
):
    export_start_time = time.time()
    logger.info(f"PDF Export started - analytic_id={analytic_id}, person_name={person_name}, device_id={device_id}, source={source}")
    
    try:
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            logger.warning(f"Analytic not found - analytic_id={analytic_id}")
            return JSONResponse(
                content={"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )
        
        if current_user is not None and not check_analytic_access(analytic, current_user):
            return JSONResponse(
                content={"status": 403, "message": "You do not have permission to access this analytic", "data": None},
                status_code=403,
            )
        
        logger.info(f"Analytic found - id={analytic.id}, name={analytic.analytic_name}, method={analytic.method}")

        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).order_by(AnalyticDevice.id).all()

        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        device_ids = list(set(device_ids))
        method = analytic.method
        
        logger.info(f"Found {len(device_ids)} device(s) linked to analytic {analytic_id}")
        
        if "APK" not in method or "apk" not in method.lower():
            if not device_ids:
                logger.warning(f"No devices linked to analytic {analytic_id}")
                return JSONResponse(
                    content={"status": 400, "message": "No devices linked to this analytic", "data": None},
                    status_code=400,
                )

        logger.info(f"Routing to PDF export function based on method: {method}")
        
        if "Contact" in method or "contact" in method.lower():
            result = _export_contact_correlation_pdf(analytic, db, current_user)
        elif "APK" in method or "apk" in method.lower():
            result = _export_apk_analytics_pdf(analytic, db)
        elif "Communication" in method or "communication" in method.lower():
            result = _export_communication_analytics_pdf(analytic, db, source=source,person_name=person_name,device_id=device_id)
        elif "Social" in method or "social" in method.lower():
            result = _export_social_media_analytics_pdf(analytic, db, source=source)
        elif "Hashfile" in method or "hashfile" in method.lower():
            result = _export_hashfile_analytic_pdf(analytic, db)
        else:
            result = _export_generic_analytics_pdf(analytic, db)
        
        elapsed_time = time.time() - export_start_time
        logger.info(f"PDF Export completed successfully - analytic_id={analytic_id}, method={method}, elapsed_time={elapsed_time:.2f}s")
        
        return result

    except Exception as e:
        elapsed_time = time.time() - export_start_time
        logger.error(f"PDF Export failed - analytic_id={analytic_id}, error={str(e)}, elapsed_time={elapsed_time:.2f}s", exc_info=True)
        return JSONResponse(
            content={"status": 500, "message": f"Failed to generate PDF: {str(e)}", "data": None},
            status_code=500,
        )

@router.post("/analytic/save-summary")
def save_analytic_summary(
    request: SummaryRequest,
    analytic_id: int = Query(..., description="Analytic ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
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

@router.put("/analytic/edit-summary")
def edit_analytic_summary(
    request: SummaryRequest,
    analytic_id: int = Query(..., description="Analytic ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
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

class GlobalPageCanvas(canvas.Canvas):

    def __init__(self, *args, footer_text="Generated Report", **kwargs):
        self.footer_text = footer_text
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):

        self.pages.append(dict(self.__dict__))
        self._startPage()  # type: ignore[reportAttributeAccessIssue]

    def save(self):
        total_pages = len(self.pages)

        for page_number, page_dict in enumerate(self.pages, start=1):
            self.__dict__.update(page_dict)
            self._draw_footer(page_number, total_pages)
            super().showPage()

        super().save()

    def _draw_footer(self, current_page, total_pages):
        self.setFont("Helvetica", 10)
        self.setFillColor(colors.HexColor("#333333"))

        self.setStrokeColor(colors.HexColor("#466086"))
        self.setLineWidth(1.5)
        self.line(30, 40, 569, 40)

        padding_y = 25
        self.drawString(30, padding_y, self.footer_text)

        page_label = f"Page {current_page} of {total_pages}"
        self.drawRightString(575, padding_y, page_label)

def build_report_header(analytic, timestamp_now, usable_width, file_upload_date=None):
    styles = getSampleStyleSheet()
    story = []
    
    # Initial spacing - adjusted to move logo and exported up on page 1 only
    story.append(Spacer(1, -130))

    subtitle_style = ParagraphStyle("Subtitle", fontSize=12, textColor=colors.black, leftIndent=-7, fontName="Helvetica")
    subtitle_style_right = ParagraphStyle("SubtitleRight", fontSize=12, textColor=colors.black, alignment=TA_RIGHT, rightIndent=7, fontName="Helvetica")
    try:
        try:
            pdfmetrics.registerFont(TTFont('Arial-Bold', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
            title_font = "Arial-Bold"
        except:
            try:
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
                title_font = "Arial-Bold"
            except:
                title_font = "Helvetica-Bold"
    except:
        title_font = "Helvetica-Bold"
    
    title_style = ParagraphStyle(
        "Title", fontSize=20, textColor=colors.HexColor("#0d0d0d"), spaceAfter=8, alignment=TA_LEFT, fontName=title_font, leftIndent=-8
    )
    export_style = ParagraphStyle(
        "ExportStyle", fontSize=10, alignment=TA_RIGHT, textColor=colors.HexColor("#4b4b4b"), fontName="Helvetica", valign="MIDDLE"
    )

    logo_path = settings.LOGO_PATH
    if not os.path.exists(logo_path):
        raise FileNotFoundError(f"Logo tidak ditemukan di {logo_path}")
    logo_img = Image(logo_path, width=130, height=30)

    export_time = Paragraph(
        f"Exported: {timestamp_now.strftime('%d/%m/%Y %H:%M')} WIB", export_style
    )

    # Logo and Exported in 1 grid (1 row, 2 columns) - moved up on page 1
    header_table = Table(
        [[logo_img, export_time]], colWidths=[usable_width * 0.5, usable_width * 0.5]
    )
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), -10),
        ("LEFTPADDING", (1, 0), (1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph(analytic.analytic_name, title_style))
    story.append(Spacer(1, 14))

    if file_upload_date:
        file_date_str = file_upload_date.strftime('%d/%m/%Y')
    elif analytic.created_at:
        file_date_str = analytic.created_at.strftime('%d/%m/%Y')
    else:
        file_date_str = timestamp_now.strftime('%d/%m/%Y')

    subheader_data = [[
        Paragraph(f"Method: {analytic.method.replace('_', ' ').title()}", subtitle_style),
        Paragraph(f"File Uploaded: {file_date_str}", subtitle_style_right),
    ]]
    subheader_table = Table(subheader_data, colWidths=[usable_width * 6 / 12, usable_width * 6 / 12], hAlign="LEFT")
    subheader_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, -1), 2),
        ("RIGHTPADDING", (0, 0), (0, -1), 6),
        ("LEFTPADDING", (1, 0), (1, -1), 0),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
    ]))
    story.append(subheader_table)
    story.append(Spacer(1, 20))

    return story

def _export_contact_correlation_pdf(analytic, db, current_user=None):
    logger.info(f"Starting Contact Correlation PDF export for analytic_id={analytic.id}")
    start_time = time.time()
    
    total_contacts = db.query(Contact).count()
    logger.info(f"Total contacts to process: {total_contacts}")
    
    result = _generate_pdf_report(
        analytic, db,
        report_type="Contact Correlation Analysis",
        filename_prefix="contact_correlation_report",
        data={"total_contacts": total_contacts},
        method="contact_correlation",
        current_user=current_user
    )
    
    elapsed = time.time() - start_time
    logger.info(f"Contact Correlation PDF export completed - analytic_id={analytic.id}, total_contacts={total_contacts}, elapsed_time={elapsed:.2f}s")
    
    return result
def _export_hashfile_analytic_pdf(analytic, db):
    logger.info(f"Starting Hashfile Analytics PDF export for analytic_id={analytic.id}")
    start_time = time.time()
    
    total_contacts = db.query(Contact).count()
    logger.info(f"Total contacts to process: {total_contacts}")
    
    result = _generate_pdf_report(
        analytic, db,
        report_type="Hashfile Analytics",
        filename_prefix="hashfile_analytics_report",
        data={"total_contacts": total_contacts},
        method="hashfile_analytics"
    )
    elapsed = time.time() - start_time
    logger.info(f"Hashfile Analytics PDF export completed - analytic_id={analytic.id}, total_contacts={total_contacts}, elapsed_time={elapsed:.2f}s")
    
    return result

def _export_apk_analytics_pdf(analytic, db):
    logger.info(f"Starting APK Analytics PDF export for analytic_id={analytic.id}")
    start_time = time.time()
    total_apks = db.query(ApkAnalytic).filter(ApkAnalytic.analytic_id == analytic.id).count()
    logger.info(f"Total APK analytics to process: {total_apks}")
    result = _generate_pdf_report(
        analytic, db,
        report_type="APK Analytics Report",
        filename_prefix="apk_analytics_report",
        data={"total_apks": total_apks},
        method="apk_analytics"
    )
    
    elapsed = time.time() - start_time
    logger.info(f"APK Analytics PDF export completed - analytic_id={analytic.id}, total_apks={total_apks}, elapsed_time={elapsed:.2f}s")
    return result

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

def _generate_pdf_report(
        analytic, db, report_type, filename_prefix, data, method,source:Optional[str] = None,
        person_name:Optional[str] = None, device_id:Optional[int] = None, current_user=None,
    ):
    if method == "deep_communication":
        return _generate_deep_communication_report(analytic, db, report_type, filename_prefix, data, source, person_name,device_id)
    elif method == "contact_correlation":
        return _generate_contact_correlation_report(analytic, db, report_type, filename_prefix, data, current_user)
    elif method == "apk_analytics":
        return _generate_apk_analytics_report(analytic, db, report_type, filename_prefix, data)
    elif method == "social_media_correlation":
        return _generate_social_media_correlation_report(analytic, db, report_type, filename_prefix, data,source)
    elif method == "hashfile_analytics":
        return _generate_hashfile_analytics_report(analytic, db, report_type, filename_prefix, data)

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
    summary_title_style = ParagraphStyle(
        "SummaryTitle",
        fontSize=12,
        leading=16,
        textColor=colors.black,
        spaceAfter=8,
        fontName="Helvetica-Bold"
    )

    bullet_style = ParagraphStyle(
        "Bullet",
        fontSize=11,
        alignment=TA_LEFT,
        leading=16,
        spaceAfter=8,
        textColor=colors.black,
        fontName="Helvetica",
        leftIndent=0
    )

    if summary_text is None or not summary_text or not summary_text.strip():
        summary_text = "No summary available."
    else:
        summary_text = summary_text.strip()

    lines = summary_text.split('\n')
    bullet_points = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('- '):
            line = line[2:].strip()
        elif line.startswith('• '):
            line = line[2:].strip()
        elif line.startswith('* '):
            line = line[2:].strip()
        
        bullet_points.append(line)
    
    title_paragraph = Paragraph("Summary", summary_title_style)
    
    if bullet_points:
        bullet_content = []
        for point in bullet_points:
            bullet_para = Paragraph(f"• {point}", bullet_style)
            bullet_content.append(bullet_para)
        
        summary_table = Table(
            [
                [title_paragraph],
            ] + [[bullet] for bullet in bullet_content],
            colWidths=[usable_width]
        )
    else:
        normal_style = ParagraphStyle(
            "Normal",
            fontSize=11,
            alignment=TA_LEFT,
            leading=16,
            spaceAfter=0,
            textColor=colors.black
        )
        summary_content = Paragraph(summary_text, normal_style)
        summary_table = Table(
            [
                [title_paragraph],
                [summary_content]
            ],
            colWidths=[usable_width]
        )

    summary_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
        
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    return [KeepTogether(summary_table)]

def _generate_deep_communication_report(analytic, db, report_type, filename_prefix, data, source, person_name, device_id):
    logger.info(f"Starting Deep Communication PDF generation - analytic_id={analytic.id}, source={source}, person_name={person_name}, device_id={device_id}")
    report_start_time = time.time()
    
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)

    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)
    
    logger.info(f"PDF file path: {file_path}")

    # === PAGE SETUP (HEADER STANDARDIZED) ===
    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    header_height = 120  # SAMAKAN DENGAN REPORT LAIN
    
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=header_height,   
        bottomMargin=50,
    )

    # === FETCH CHAT DETAIL ===
    response = get_chat_detail(
        analytic_id=analytic.id,
        person_name=person_name,
        platform=source,
        device_id=device_id,
        search=None,
        db=db
    )

    logger.info("Fetching chat detail data...")
    chat_data = {}
    chat_messages = []
    try:
        if response is not None and hasattr(response, "body") and response.body is not None:
            response_data = json.loads(response.body.decode("utf-8"))
            chat_data = response_data.get("data", {}) if isinstance(response_data, dict) else {}
            chat_messages = chat_data.get("chat_messages", []) if isinstance(chat_data, dict) else []
            logger.info(f"Retrieved {len(chat_messages)} chat messages")
    except Exception as e:
        logger.error(f"Failed to parse chat_detail: {e}", exc_info=True)
        chat_messages = []
        chat_data = {}

    # === STYLES ===
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("Heading", fontSize=12, leading=15, fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Normal", fontSize=11, leading=14, alignment=TA_LEFT)
    wrap_style = ParagraphStyle("Wrap", fontSize=11, leading=14, wordWrap="CJK", alignment=TA_JUSTIFY)

    # === STORY START ===
    story = []
    story.append(Spacer(1, 5))

    # === INFO SECTION ===
    sender_name = chat_messages[0].get("sender", "Unknown") if chat_messages else "Unknown"
    receiver_name = chat_messages[0].get("recipient", "Unknown") if chat_messages else "Unknown"
    total_messages = len(chat_messages)
    platform_name = chat_data.get("platform", source or "Unknown") if isinstance(chat_data, dict) else (source or "Unknown")

    info_data = [
        ["Source", f": {platform_name}", "Sender", f": {sender_name}"],
        ["Receiver", f": {receiver_name}", "Messages", f": {total_messages} total"],
    ]
    info_table = Table(info_data, colWidths=[60, (usable_width/2 - 60), 60, (usable_width/2 - 60)])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # === CHAT TABLE BUILDING ===
    col_time = 140
    col_chat = usable_width - col_time
    chat_data = [["Time", "Chat"]]

    batch_size = 5000
    total_messages = len(chat_messages)

    for batch_start in range(0, total_messages, batch_size):
        batch_end = min(batch_start + batch_size, total_messages)
        batch_messages = chat_messages[batch_start:batch_end]

        for msg in batch_messages:
            timestamp_raw = msg.get("timestamp")
            time_display = msg.get("times") or ""

            if timestamp_raw:
                try:
                    dt = dateutil.parser.isoparse(timestamp_raw)
                    time_val = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    time_val = time_display or timestamp_raw
            else:
                time_val = time_display

            sender = msg.get("sender", "Unknown")
            text = msg.get("message_text", "")
            chat_data.append([Paragraph(time_val, wrap_style), Paragraph(f"{sender}: {text}", wrap_style)])

    table_chunk_size = 2000
    header_row = chat_data[0]
    data_rows = chat_data[1:]
    total_chunks = (len(data_rows) + table_chunk_size - 1) // table_chunk_size if len(data_rows) > 0 else 0
    
    for chunk_start in range(0, len(data_rows), table_chunk_size):
        chunk_end = min(chunk_start + table_chunk_size, len(data_rows))
        chunk_data = [header_row] + data_rows[chunk_start:chunk_end]
        chunk_num = (chunk_start // table_chunk_size) + 1
        
        chunk_table = Table(chunk_data, colWidths=[col_time, col_chat])
        chunk_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ]))

        story.append(chunk_table)
        if chunk_end < len(data_rows):
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 20))

    summary_points = analytic.summary
    story.extend(_build_summary_section(usable_width, summary_points))

    # =====================================================================
    #               HEADER CANVAS (IDENTIK DENGAN SEMUA REPORT LAIN)
    # =====================================================================
    header_timestamp = timestamp_now

    def draw_header(canvas_obj, doc):
        canvas_obj.saveState()

        page_width, page_height = A4
        top_y = page_height - 30

        # LOGO
        logo_path = settings.LOGO_PATH
        logo_x = 20
        logo_y = top_y - 30

        if os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                canvas_obj.drawImage(
                    ImageReader(logo_path),
                    logo_x,
                    logo_y,
                    width=130,
                    height=30,
                    preserveAspectRatio=True,
                    mask="auto"
                )
            except:
                pass

        # Exported timestamp
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.HexColor("#4b4b4b"))
        canvas_obj.drawRightString(565, logo_y + 15, f"Exported: {header_timestamp.strftime('%d/%m/%Y %H:%M')} WIB")

        # Title
        canvas_obj.setFont("Helvetica-Bold", 20)
        title_y = logo_y - 20
        canvas_obj.drawString(30, title_y, analytic.analytic_name)

        # Method + File Uploaded
        canvas_obj.setFont("Helvetica", 12)
        method_y = title_y - 25

        canvas_obj.drawString(30, method_y, f"Method: {analytic.method.replace('_', ' ').title()}")

        uploaded_str = analytic.created_at.strftime("%d/%m/%Y") if analytic.created_at else header_timestamp.strftime("%d/%m/%Y")
        canvas_obj.drawRightString(565, method_y, f"File Uploaded: {uploaded_str}")

        canvas_obj.restoreState()

    # === BUILD PDF ===
    doc.build(
        story,
        onFirstPage=draw_header,
        onLaterPages=draw_header,
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

def _generate_apk_analytics_report(analytic, db, report_type, filename_prefix, data):

    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)

    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    # === PAGE SETUP ===
    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    header_height = 120

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=header_height,   # important
        bottomMargin=60
    )

    # === STYLES ===
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("Heading", fontSize=12, leading=15, fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Normal", fontSize=10.5, leading=14, alignment=TA_LEFT)
    wrap_desc = ParagraphStyle("WrapDesc", fontSize=10.5, leading=14, alignment=TA_JUSTIFY)

    # === FETCH DATA ===
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

    # === STORY (NO HEADER HERE) ===
    story = []

    # === INFO SECTION ===
    total_apks = len(apk_analytics)
    total_malicious = len(malicious_items)
    total_common = len(common_items)
    avg_score = "-"

    try:
        scores = [float(a.malware_scoring) for a in apk_analytics if a.malware_scoring]
        avg_score = f"{sum(scores) / len(scores):.1f}%" if scores else "-"
    except:
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

    # === MALICIOUS ===
    story.append(Paragraph("<b>Malicious</b>", heading_style))
    story.append(Spacer(1, 4))

    col_left = round(usable_width * 0.3, 2)
    col_right = usable_width - col_left

    if malicious_items:
        mal_data = [["Malicious Item", "Description"]]
        for item, desc in malicious_items:
            mal_data.append([Paragraph(item, normal_style), Paragraph(desc, wrap_desc)])
        mal_table = Table(mal_data, colWidths=[col_left, col_right])
        mal_table.setStyle(_build_table_header_style())
        story.append(mal_table)
    else:
        story.append(Paragraph("Tidak ditemukan entri berstatus <b>dangerous</b>.", normal_style))
    story.append(Spacer(1, 20))

    # === COMMON ===
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

    # === SUMMARY ===
    story.extend(_build_summary_section(usable_width, analytic.summary))

    # === HEADER FOR ALL PAGES ===
    header_timestamp = timestamp_now

    def draw_header(canvas_obj, doc):
        canvas_obj.saveState()

        page_width, page_height = A4
        top_y = page_height - 30

        # LOGO
        logo_path = settings.LOGO_PATH
        logo_x = 20
        logo_y = top_y - 30

        if os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                canvas_obj.drawImage(
                    ImageReader(logo_path),
                    logo_x,
                    logo_y,
                    width=130,
                    height=30,
                    preserveAspectRatio=True,
                    mask="auto"
                )
            except:
                pass

        # Export time
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.HexColor("#4b4b4b"))
        canvas_obj.drawRightString(
            565,
            logo_y + 15,
            f"Exported: {header_timestamp.strftime('%d/%m/%Y %H:%M')} WIB"
        )

        # Title
        canvas_obj.setFont("Helvetica-Bold", 20)
        title_y = logo_y - 20
        canvas_obj.drawString(30, title_y, analytic.analytic_name)

        # Method + File Uploaded
        canvas_obj.setFont("Helvetica", 12)
        method_y = title_y - 25

        canvas_obj.drawString(30, method_y, f"Method: {analytic.method.replace('_', ' ').title()}")

        if analytic.created_at:
            file_uploaded_str = analytic.created_at.strftime("%d/%m/%Y")
        else:
            file_uploaded_str = header_timestamp.strftime("%d/%m/%Y")

        canvas_obj.drawRightString(565, method_y, f"File Uploaded: {file_uploaded_str}")

        canvas_obj.restoreState()

    # === BUILD PDF ===
    doc.build(
        story,
        onFirstPage=draw_header,
        onLaterPages=draw_header,
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


def _generate_social_media_correlation_report(analytic, db, report_type, filename_prefix, data, source):
    logger.info(f"Starting Social Media PDF generation - analytic_id={analytic.id}, source={source}")
    report_start_time = time.time()
    
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)
    
    logger.info(f"PDF file path: {file_path}")

    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    
    # Calculate header height: logo (30) + spacing (6) + title (20) + spacing (14) + method (12) + spacing (20) = ~102 points
    # We need topMargin to accommodate header on pages 2+ to prevent content overlap
    header_height = 140  # Approximate header height in points
    
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=header_height,  # Increased to accommodate header on pages 2+
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle("Normal", fontSize=12, leading=13)
    bold_style = ParagraphStyle("Bold", fontSize=10, leading=13, fontName="Helvetica-Bold")

    file_upload_date = None
    try:
        from app.analytics.shared.models import AnalyticDevice, Device
        analytic_device = db.query(AnalyticDevice).filter(AnalyticDevice.analytic_id == analytic.id).first()
        if analytic_device and analytic_device.device_ids:
            device = db.query(Device).filter(Device.id == analytic_device.device_ids[0]).first()
            if device and device.file_id:
                from app.analytics.device_management.models import File
                file_record = db.query(File).filter(File.id == device.file_id).first()
                if file_record and file_record.created_at:
                    file_upload_date = file_record.created_at
    except Exception as e:
        logger.warning(f"Could not get file upload date: {e}")

    story = []
    story.extend(build_report_header(analytic, timestamp_now, usable_width, file_upload_date))

    logger.info("Fetching social media correlation data...")
    from app.api.v1.analytics_social_media_routes import _get_social_media_correlation_data
    response = _get_social_media_correlation_data(analytic.id, db, source or "Instagram")
    response_data = {}
    if response is not None:
        if hasattr(response, "body") and response.body is not None:
            try:
                body = json.loads(response.body)
                response_data = body.get("data", {}) if isinstance(body, dict) else {}
            except Exception as e:
                logger.error(f"Error parsing social media correlation response: {e}", exc_info=True)
                response_data = {}
        elif isinstance(response, dict):
            response_data = response.get("data", {}) if isinstance(response, dict) else {}

    platform_name = list(response_data.get("correlations", {}).keys())[0] if response_data.get("correlations") else source.capitalize()
    correlation_data = response_data.get("correlations", {}).get(platform_name, {})
    buckets = correlation_data.get("buckets", [])
    buckets = buckets * 50
    devices = response_data.get("devices", [])
    total_devices = response_data.get("total_devices", len(devices))
    total_accounts = sum(len(bucket.get("devices", [])) for bucket in buckets)
    
    logger.info(f"Retrieved {total_devices} devices and {total_accounts} social media accounts for platform {platform_name}")
    story.append(Spacer(1, 4))

    info_data = [
        ["Source", f":  {platform_name}"],
        ["Total Device", f":  {total_devices} Devices"],
        ["Total Social Media", f":  {total_accounts} Account"],
    ]
    info_table = Table(info_data, colWidths=[usable_width * 4 / 12, usable_width * 8 / 12])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (0, -1), 1),
        ("LEFTPADDING", (1, 0), (1, -1), -67),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    device_summary_title = Paragraph("Device Identification Summary", normal_style)
    device_summary_table = Table(
        [[device_summary_title]],
        colWidths=[usable_width]
    )
    device_summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, 0), 8),
        ("RIGHTPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
    ]))
    story.append(device_summary_table)
    story.append(Spacer(1, 6))

    device_table_data = [["Device ID", "Registered Owner", "Phone Number"]]
    for d in devices:
        device_table_data.append([f"Device {d['device_id']}", d["owner_name"], d["phone_number"]])

    col1 = round(usable_width * 0.20, 2)
    col2 = round(usable_width * 0.40, 2)
    col3 = usable_width - (col1 + col2)

    device_table = Table(device_table_data, colWidths=[col1, col2, col3], repeatRows=1)
    device_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#000408")),
        ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#000408")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466087")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, 0), 6),
        ("RIGHTPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("LEFTPADDING", (0, 1), (-1, -1), 6),
        ("RIGHTPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
    ]))
    story.append(device_table)
    story.append(Spacer(1, 20))

    device_correlation_title = Paragraph("Device Account Correlation", normal_style)
    device_correlation_table = Table(
        [[device_correlation_title]],
        colWidths=[usable_width]
    )
    device_correlation_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, 0), 8),
        ("RIGHTPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
    ]))
    story.append(device_correlation_table)
    story.append(Spacer(1, 6))

    if not buckets:
        story.append(Paragraph("No correlation data found for this platform.", normal_style))
    else:
        correlation_table_data = [["Connections", "Involved Device", "Correlated Account"]]

        # Group rows by (label, involved_devices_set) to combine accounts
        grouped_data = {}
        
        for bucket in buckets:
            label = bucket.get("label", "")
            devices_rows = bucket.get("devices", [])

            for accounts_row in devices_rows:
                # Find devices involved in this correlation (non-None accounts)
                involved_device_indices = [i for i, acc in enumerate(accounts_row) if acc is not None]
                involved_device_ids = [devices[i]["device_id"] for i in involved_device_indices if i < len(devices)]
                
                # Create a key for grouping: (label, sorted_device_ids_tuple)
                if involved_device_ids:
                    # Sort device IDs for consistent grouping
                    sorted_device_ids = tuple(sorted(involved_device_ids))
                    group_key = (label, sorted_device_ids)
                    
                    # Get all unique accounts from this row (replace null with "unknown")
                    # Each position in accounts_row corresponds to a device
                    # We collect all account values from this row, replacing null with "unknown"
                    accounts_from_row = set()
                    for acc in accounts_row:
                        if acc is None:
                            accounts_from_row.add("unknown")
                        elif str(acc).strip():
                            accounts_from_row.add(str(acc).strip())
                    
                    # Add accounts to the group
                    if group_key not in grouped_data:
                        grouped_data[group_key] = {
                            "label": label,
                            "device_ids": sorted_device_ids,
                            "accounts": set()
                        }
                    
                    # Add all accounts from this row to the group (set will deduplicate)
                    grouped_data[group_key]["accounts"].update(accounts_from_row)
        
        # Convert grouped data to table rows
        for (label, device_ids_tuple), group_info in grouped_data.items():
            # Format device numbers as "Device 1, 2, 3"
            device_numbers = ", ".join([str(did) for did in device_ids_tuple])
            involved_devices_text = f"Device {device_numbers}"
            
            # Format all accounts for this group
            accounts_list = sorted(list(group_info["accounts"]))  # Sort for consistent display
            if accounts_list:
                formatted_accounts = []
                for acc in accounts_list:
                    if acc == "unknown":
                        formatted_accounts.append(f"• unknown")
                    elif not acc.startswith("@"):
                        formatted_accounts.append(f"• @{acc}")
                    else:
                        formatted_accounts.append(f"• {acc}")
                accounts_text = "<br/>".join(formatted_accounts)
                accounts_para = Paragraph(accounts_text, normal_style)
            else:
                accounts_para = Paragraph("-", normal_style)
            
            row = [
                Paragraph(label, normal_style),
                Paragraph(involved_devices_text, normal_style),
                accounts_para,
            ]
            correlation_table_data.append(row)

        col_a = round(usable_width * 0.25, 2)
        col_b = round(usable_width * 0.30, 2)
        col_c = usable_width - (col_a + col_b)

        corr_table = Table(correlation_table_data, colWidths=[col_a, col_b, col_c], repeatRows=1)
        corr_table.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#000408")),
            ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#000408")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466087")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 12),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ("ALIGN", (2, 1), (2, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("VALIGN", (0, 1), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, 0), 6),
            ("RIGHTPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("LEFTPADDING", (0, 1), (-1, -1), 6),
            ("RIGHTPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
        ]))
        story.append(corr_table)
    story.append(Spacer(1, 20))

    story.extend(_build_summary_section(usable_width, analytic.summary))
    story.append(Spacer(1, 10))

    logger.info(f"Building PDF document with {len(story)} story elements...")
    pdf_build_start = time.time()
    
    # Store header data for use in onLaterPages callback
    header_data = {
        'analytic': analytic,
        'timestamp_now': timestamp_now,
        'file_upload_date': file_upload_date
    }
    
    def draw_header_on_new_page(canvas_obj, doc):
        """Draw header on pages 2+ to maintain consistent structure"""
        page_number = canvas_obj._pageNumber
        if page_number > 1:
            canvas_obj.saveState()
            
            # Get header data from closure
            analytic = header_data['analytic']
            timestamp_now = header_data['timestamp_now']
            file_upload_date = header_data['file_upload_date']
            
            # Get header data
            page_height = 842  # A4 height in points
            top_margin = page_height - 30  # Standard top margin
            
            # Draw logo and exported time in same row (1 grid) - moved down
            logo_path = settings.LOGO_PATH
            logo_y = top_margin - 30  # Logo top position
            logo_height = 30
            logo_width = 130
            # Logo x position should match page 1: left margin (30) + LEFTPADDING (-10) = 20
            logo_x = 20
            
            if os.path.exists(logo_path):
                try:
                    from reportlab.lib.utils import ImageReader
                    img = ImageReader(logo_path)
                    # Logo position - aligned in grid, matching page 1 position and size
                    canvas_obj.drawImage(img, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    logger.warning(f"Failed to draw logo on page {page_number}: {e}")
                    pass
            
            # Draw exported time (top right) - aligned with logo vertically in same grid
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.setFillColor(colors.HexColor("#4b4b4b"))
            export_time_text = f"Exported: {timestamp_now.strftime('%d/%m/%Y %H:%M')} WIB"
            # Align exported time vertically with logo center (logo center is at logo_y + logo_height/2)
            exported_y = logo_y + (logo_height / 2) - 3  # Center align with logo, -3 for text baseline adjustment
            canvas_obj.drawRightString(565, exported_y, export_time_text)
            
            # Draw title
            try:
                try:
                    pdfmetrics.registerFont(TTFont('Arial-Bold', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
                    title_font = "Arial-Bold"
                except:
                    try:
                        pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
                        title_font = "Arial-Bold"
                    except:
                        title_font = "Helvetica-Bold"
            except:
                title_font = "Helvetica-Bold"
            
            # Draw title in its own grid, shifted down slightly
            canvas_obj.setFont(title_font, 20)
            canvas_obj.setFillColor(colors.HexColor("#0d0d0d"))
            # Title in separate grid, positioned below logo/exported with spacing
            # logo_y is at top_margin - 30, logo_height is 30, so logo bottom is at top_margin
            # Add spacing (6 points like page 1) then title, shifted down a bit more
            title_y = top_margin - 6 - 50  # Shift down: logo bottom + spacing - additional downward shift
            canvas_obj.drawString(29, title_y, analytic.analytic_name)
            
            # Draw method and file uploaded in 6:6 grid (same as page 1)
            canvas_obj.setFont("Helvetica", 12)
            canvas_obj.setFillColor(colors.black)
            # Method positioned below title with spacing (14 points like page 1), shifted down a bit more
            method_y = title_y - 14 - 12 - 7  # title_y - spacing - method font size - additional downward shift
            
            # Calculate grid positions: usable_width = 535 (A4 width 595 - left 30 - right 30)
            # Grid 6:6 means each column is 50% of usable_width
            usable_width = 535
            method_col_width = usable_width * 6 / 12  # 267.5
            file_uploaded_col_width = usable_width * 6 / 12  # 267.5
            
            # Method: left-aligned, starting from left margin + LEFTPADDING (2) = 32
            method_text = f"Method: {analytic.method.replace('_', ' ').title()}"
            canvas_obj.drawString(32, method_y, method_text)
            
            if file_upload_date:
                file_date_str = file_upload_date.strftime('%d/%m/%Y')
            elif analytic.created_at:
                file_date_str = analytic.created_at.strftime('%d/%m/%Y')
            else:
                file_date_str = timestamp_now.strftime('%d/%m/%Y')
            
            # File Uploaded: right-aligned in second grid column
            # Right edge of second column = left margin + usable_width = 30 + 535 = 565
            file_uploaded_text = f"File Uploaded: {file_date_str}"
            canvas_obj.drawRightString(565, method_y, file_uploaded_text)
            
            canvas_obj.restoreState()
            
            # Note: Content spacing is handled by ReportLab's flow mechanism
            # The header is drawn on the canvas, and ReportLab will automatically
            # place content below it based on the document's margins and flow
            # The topMargin of 30 points should be sufficient for the header area
            # If content overlaps, we may need to increase topMargin in SimpleDocTemplate
    
    doc.build(
        story,
        onFirstPage=lambda canvas_obj, doc: None,
        onLaterPages=draw_header_on_new_page,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        ),
    )
    
    pdf_build_time = time.time() - pdf_build_start
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    file_size_mb = file_size / (1024 * 1024)
    
    total_time = time.time() - report_start_time
    logger.info(f"Social Media PDF generation completed - file: {filename}, size: {file_size_mb:.2f} MB, "
               f"pdf_build_time: {pdf_build_time:.2f}s, total_time: {total_time:.2f}s")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
def _generate_contact_correlation_report(analytic, db, report_type, filename_prefix, data, current_user=None):
    logger.info(f"Starting Contact Correlation PDF generation - analytic_id={analytic.id}")
    report_start_time = time.time()
    
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)
    
    logger.info(f"PDF file path: {file_path}")

    # === PAGE SETUP WITH STANDARD HEADER MARGIN ===
    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    header_height = 120

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=header_height,    
        bottomMargin=50,
    )

    # === FETCH DATA ===
    logger.info("Fetching contact correlation data...")
    result = _get_contact_correlation_data(analytic.id, db, current_user)

    if isinstance(result, JSONResponse):
        result = result.body
    if isinstance(result, (bytes, bytearray)):
        result = json.loads(result.decode("utf-8"))
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except:
            result = {}
    if not isinstance(result, dict):
        result = {}

    api_data = result.get("data", {})
    devices = api_data.get("devices", [])
    correlations = api_data.get("correlations", [])
    summary = api_data.get("summary")
    logger.info(f"Retrieved {len(devices)} devices and {len(correlations)} correlations")

    # === STYLES ===
    styles = getSampleStyleSheet()

    header_device_style = ParagraphStyle(
        "HeaderDevice", alignment=TA_CENTER, textColor=colors.white,
        fontName="Helvetica-Bold", fontSize=10, leading=12
    )

    normal_center = ParagraphStyle("NormalCenter", fontSize=10, leading=13, alignment=TA_CENTER)
    normal_left = ParagraphStyle("NormalLeft", fontSize=10, leading=13, alignment=TA_LEFT)

    # === DEVICE GROUP SPLITTING ===
    group_size = 4
    grouped_devices = [devices[i:i + group_size] for i in range(0, len(devices), group_size)]
    total_groups = len(grouped_devices)

    story = []

    # === FIX HEADER OVERLAP FOR PAGE 1 ===
    story.append(Spacer(1, 2))

    # === BUILD PER GROUP ===
    for group_index, group in enumerate(grouped_devices, start=1):

        start_device = (group_index - 1) * group_size + 1
        end_device = start_device + len(group) - 1

        # Info Table
        info_data = [
            ["Source", "         : Contact Correlation"],
            ["Total Device", f"         : {len(devices)} Devices (Device {start_device}-{end_device})"],
            ["Total Correlated Contacts", f"         : {len(correlations)} Contacts"],
        ]
        info_table = Table(info_data, colWidths=[100, usable_width - 100])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 16))

        # Header Row
        header_row = ["Contact Number"]
        for dev in group:
            header_row.append(Paragraph(
                f"<b>{dev['device_label']}</b><br/><font size=9>{dev['phone_number'] or '-'}</font>",
                header_device_style
            ))

        table_data = [header_row]

        # === CORRELATION BATCHING ===
        batch_size = 10000
        total_correlations = len(correlations)

        for batch_start in range(0, total_correlations, batch_size):
            batch_end = min(batch_start + batch_size, total_correlations)
            batch_correlations = correlations[batch_start:batch_end]

            for corr in batch_correlations:
                contact_num = corr.get("contact_number", "-")
                row = [Paragraph(contact_num, normal_left)]

                dev_map = {d["device_label"]: d["contact_name"] for d in corr.get("devices_found_in", [])}

                for dev in group:
                    device_label = dev["device_label"]
                    cell_value = dev_map.get(device_label, "—")
                    row.append(Paragraph(cell_value, normal_center))

                table_data.append(row)

        # === CHUNK LARGE TABLE ===
        table_chunk_size = 2000
        col_widths = [usable_width * 0.25] + [
            (usable_width * 0.75) / len(group)
            for _ in group
        ]

        header_row_copy = table_data[0]
        data_rows = table_data[1:]
        total_chunks = (len(data_rows) + table_chunk_size - 1) // table_chunk_size if len(data_rows) > 0 else 0
        
        for chunk_start in range(0, len(data_rows), table_chunk_size):
            chunk_end = min(chunk_start + table_chunk_size, len(data_rows))
            chunk_data = [header_row] + data_rows[chunk_start:chunk_end]
            chunk_num = (chunk_start // table_chunk_size) + 1
            
            chunk_table = Table(
                chunk_data,
                colWidths=col_widths,
                repeatRows=1,
            )

            chunk_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            story.append(chunk_table)

            if chunk_end < len(data_rows):
                story.append(Spacer(1, 6))

        if group_index < total_groups:
            story.append(PageBreak())

    # === SUMMARY ===
    story.append(Spacer(1, 20))
    story.extend(_build_summary_section(usable_width, summary))

    # === HEADER CANVAS (STANDARDIZED) ===
    header_timestamp = timestamp_now

    def draw_header(canvas_obj, doc):
        canvas_obj.saveState()
        page_width, page_height = A4
        top_y = page_height - 30

        # LOGO
        logo_path = settings.LOGO_PATH
        logo_x = 20
        logo_y = top_y - 30

        if os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                canvas_obj.drawImage(
                    ImageReader(logo_path),
                    logo_x,
                    logo_y,
                    width=130,
                    height=30,
                    preserveAspectRatio=True,
                    mask="auto"
                )
            except:
                pass

        # Exported
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.HexColor("#4b4b4b"))
        exported_text = f"Exported: {header_timestamp.strftime('%d/%m/%Y %H:%M')} WIB"
        canvas_obj.drawRightString(565, logo_y + 15, exported_text)

        # Title
        canvas_obj.setFont("Helvetica-Bold", 20)
        title_y = logo_y - 20
        canvas_obj.setFillColor(colors.black)
        canvas_obj.drawString(30, title_y, analytic.analytic_name)

        # Method & File Uploaded
        canvas_obj.setFont("Helvetica", 12)
        method_y = title_y - 25
        canvas_obj.drawString(30, method_y, f"Method: {analytic.method.replace('_', ' ').title()}")

        if analytic.created_at:
            uploaded_str = analytic.created_at.strftime("%d/%m/%Y")
        else:
            uploaded_str = header_timestamp.strftime("%d/%m/%Y")

        canvas_obj.drawRightString(565, method_y, f"File Uploaded: {uploaded_str}")

        canvas_obj.restoreState()

    # === BUILD PDF ===
    logger.info(f"Building PDF with {len(story)} story items...")

    doc.build(
        story,
        onFirstPage=draw_header,
        onLaterPages=draw_header,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        ),
    )

    logger.info(f"Contact Correlation PDF generation completed - file: {filename}")

    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")

def _generate_hashfile_analytics_report(analytic, db, report_type, filename_prefix, data):
    logger.info(f"Starting Hashfile Analytics PDF generation - analytic_id={analytic.id}")
    report_start_time = time.time()
    
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)
    
    logger.info(f"PDF file path: {file_path}")

    # === PAGE SETUP (WITH STANDARD GLOBAL HEADER SPACE) ===
    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    header_height = 120

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=header_height,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle("Normal", fontSize=10, leading=13, alignment=TA_CENTER)
    header_style = ParagraphStyle(
        "HeaderDevice", alignment=TA_CENTER, textColor=colors.white,
        fontName="Helvetica-Bold", fontSize=9
    )

    # === FETCH DATA ===
    logger.info("Fetching hashfile analytics data...")
    response = _get_hashfile_analytics_data(analytic.id, db)

    data = {}
    try:
        if response is not None:
            if hasattr(response, "body") and response.body is not None:
                body = response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body
                parsed = json.loads(body)
                data = parsed.get("data", {}) if isinstance(parsed, dict) else {}
            elif isinstance(response, dict):
                data = response.get("data", {})
    except Exception as e:
        logger.error(f"Error parsing hashfile analytics response: {e}", exc_info=True)
        data = {}

    devices = data.get("devices", [])
    hashfiles = data.get("correlations") or []

    logger.info(f"Retrieved {len(devices)} devices for hashfile analytics")

    group_size = 4
    grouped_devices = [devices[i:i + group_size] for i in range(0, len(devices), group_size)]
    total_groups = len(grouped_devices)

    story = []

    # === SMALL SPACER TO AVOID PAGE 1 OVERLAP ===
    story.append(Spacer(1, 5))

    # === MAIN CONTENT ===
    for group_index, group in enumerate(grouped_devices, start=1):

        # Info box
        start_device = (group_index - 1) * group_size + 1
        end_device = start_device + len(group) - 1

        info_data = [
            ["Source", f"     : Handphone"],
            ["Total Device", f"     : {len(devices)} Devices (Device {start_device}-{end_device})"],
            ["Total Correlated Hashfiles", f"     : {len(hashfiles)} Files"],
        ]
        info_table = Table(info_data, colWidths=[120, usable_width - 120])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 16))

        # Table header
        header_row = ["Filename"]
        for dev in group:
            owner_name = dev.get("owner_name", "Unknown")
            phone_number = dev.get("phone_number", "-") or "-"
            header_html = f"<b>{owner_name}</b><br/><font size=9>({phone_number})</font>"
            header_row.append(Paragraph(header_html, header_style))

        table_data = [header_row]

        total_hashfiles = len(hashfiles)
        batch_size = 10000

        # Batch processing
        for batch_start in range(0, total_hashfiles, batch_size):
            batch_end = min(batch_start + batch_size, total_hashfiles)
            for h in hashfiles[batch_start:batch_end]:
                file_name = h.get("file_name", "Unknown")
                row = [Paragraph(file_name, normal_style)]
                for dev in group:
                    symbol = "✔" if dev.get("device_label") in h.get("devices", []) else "✘"
                    row.append(Paragraph(symbol, normal_style))
                table_data.append(row)

        # Chunking
        table_chunk_size = 2000
        col_widths = [usable_width * 0.25] + [(usable_width * 0.75) / len(group) for _ in group]

        header_row_copy = table_data[0]
        data_rows = table_data[1:]
        total_chunks = (len(data_rows) + table_chunk_size - 1) // table_chunk_size if len(data_rows) > 0 else 0
        
        for chunk_start in range(0, len(data_rows), table_chunk_size):
            chunk_end = min(chunk_start + table_chunk_size, len(data_rows))
            chunk_data = [header_row] + data_rows[chunk_start:chunk_end]
            chunk_num = (chunk_start // table_chunk_size) + 1
            
            chunk_table = Table(
                chunk_data,
                colWidths=col_widths,
                repeatRows=1,
            )
            chunk_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(chunk_table)

            if chunk_end < len(data_rows):
                story.append(Spacer(1, 6))

        if group_index < total_groups:
            story.append(PageBreak())

    # SUMMARY
    story.append(Spacer(1, 20))
    story.extend(_build_summary_section(usable_width, analytic.summary))

    # === STANDARDIZED GLOBAL HEADER (MATCH OTHER REPORTS) ===
    header_timestamp = timestamp_now

    def draw_header(canvas_obj, doc):
        canvas_obj.saveState()
        page_width, page_height = A4
        top_y = page_height - 30

        # Logo
        logo_path = settings.LOGO_PATH
        logo_x = 20
        logo_y = top_y - 30

        if os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                canvas_obj.drawImage(
                    ImageReader(logo_path),
                    logo_x, logo_y,
                    width=130, height=30,
                    preserveAspectRatio=True, mask="auto"
                )
            except:
                pass

        # Exported timestamp
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.HexColor("#4b4b4b"))
        exported_text = f"Exported: {header_timestamp.strftime('%d/%m/%Y %H:%M')} WIB"
        canvas_obj.drawRightString(565, logo_y + 15, exported_text)

        # Title
        canvas_obj.setFont("Helvetica-Bold", 20)
        title_y = logo_y - 20
        canvas_obj.setFillColor(colors.black)
        canvas_obj.drawString(30, title_y, analytic.analytic_name)

        # Method + Uploaded
        canvas_obj.setFont("Helvetica", 12)
        method_y = title_y - 25
        canvas_obj.drawString(30, method_y, f"Method: {analytic.method.replace('_', ' ').title()}")

        uploaded_str = analytic.created_at.strftime("%d/%m/%Y") if analytic.created_at else header_timestamp.strftime("%d/%m/%Y")
        canvas_obj.drawRightString(565, method_y, f"File Uploaded: {uploaded_str}")

        canvas_obj.restoreState()

    # === BUILD PDF ===
    logger.info(f"Building PDF document with {len(story)} story elements...")

    doc.build(
        story,
        onFirstPage=draw_header,
        onLaterPages=draw_header,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        ),
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )
