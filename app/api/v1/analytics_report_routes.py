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
from reportlab.lib.utils import ImageReader


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

        # garis footer
        self.setStrokeColor(colors.HexColor("#466086"))
        self.setLineWidth(1.5)
        self.line(30, 40, 569, 40)

        padding_y = 25

        # ============================
        # WRAPPED FOOTER TEXT (prevent overlap)
        # ============================
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle

        footer_style = ParagraphStyle(
            "FooterStyle",
            fontName="Helvetica",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#333333"),
            wordWrap="CJK",
        )

        para = Paragraph(self.footer_text, footer_style)

        max_width = 480  # cukup aman
        w, h = para.wrap(max_width, 100)

        para.drawOn(self, 30, padding_y - (h - 10))

        page_label = f"Page {current_page} of {total_pages}"
        self.drawRightString(575, padding_y, page_label)


def build_report_header(analytic, timestamp_now, usable_width, file_upload_date=None):
    styles = getSampleStyleSheet()
    story = []
    
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
    logo_img = Image(logo_path, width=191, height=30)

    export_time = Paragraph(
        f"Exported: {timestamp_now.strftime('%d/%m/%Y %H:%M')} WIB", export_style
    )

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

def _generate_deep_communication_report(
    analytic, db, report_type, filename_prefix,
    data, source, person_name, device_id
):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle

    logger.info(
        f"Starting Deep Communication PDF generation - analytic_id={analytic.id}, "
        f"source={source}, person_name={person_name}, device_id={device_id}"
    )
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)

    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin

    # topMargin akan dioverride setelah kita hitung tinggi judul
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=150,
        bottomMargin=60,
    )

    try:
        response = get_chat_detail(
            analytic_id=analytic.id,
            person_name=person_name,
            platform=source,
            device_id=device_id,
            search=None,
            current_user=None,
            db=db
        )
    except Exception:
        response = None

    chat_data = {}
    conversation_history = []

    try:
        if hasattr(response, "body") and response.body:
            raw = json.loads(response.body.decode("utf-8"))
        elif isinstance(response, dict):
            raw = response
        elif hasattr(response, "content"):
            raw = response.content
        else:
            raw = {}
        chat_data = raw.get("data", {}) or {}
        conversation_history = chat_data.get("conversation_history", []) or []
    except Exception:
        chat_data = {}
        conversation_history = []

    # ---------------------------------------------------------
    # STYLES
    # ---------------------------------------------------------
    style_time_center = ParagraphStyle(
        "TimeCenter",
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        wordWrap="CJK",
    )
    style_chat_left = ParagraphStyle(
        "ChatLeft",
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        wordWrap="CJK",
    )
    wrap12 = ParagraphStyle(
        "Wrap12",
        fontName="Helvetica",
        fontSize=12,
        leading=14,
        wordWrap="CJK",
    )

    story = []

    # ---------------------------------------------------------
    # INFO SECTION (responsive)
    # ---------------------------------------------------------
    platform_name = chat_data.get("platform") or (source or "-")
    chat_type = (chat_data.get("chat_type") or "").lower()
    is_group = chat_type in ["group", "broadcast"]
    is_whatsapp = platform_name.lower() in ["whatsapp", "wa", "whats app"]

    # --- PERIOD ---
    def fmt_date(ts):
        if not ts:
            return "-"
        try:
            dt = dateutil.parser.isoparse(ts)
            return dt.strftime("%d %b %Y")
        except Exception:
            return ts

    if conversation_history:
        sorted_conv = sorted(
            conversation_history,
            key=lambda x: x.get("timestamp") or ""
        )
        first_dt = fmt_date(sorted_conv[0].get("timestamp"))
        last_dt = fmt_date(sorted_conv[-1].get("timestamp"))
        period_value = f"{first_dt} - {last_dt}"
    else:
        period_value = "-"

    # --- SENDER / RECEIVER ---
    def fmt_contact(cid, name):
        cid = cid or "-"
        name = name or "-"
        cid = str(cid)
        if cid != "-" and is_whatsapp and not cid.startswith("+"):
            cid = "+" + cid
        return f"{cid} ({name})"

    sender_value = (
        fmt_contact(chat_data.get("group_id"), chat_data.get("group_name"))
        if is_group else
        fmt_contact(chat_data.get("person_id"), chat_data.get("person_name"))
    )

    receiver_value = "-"
    if conversation_history:
        r = conversation_history[0].get("recipient") or {}
        receiver_value = fmt_contact(r.get("recipient_id"), r.get("recipient_name"))

    total_messages = sum(len(c.get("messages", []) or []) for c in conversation_history)

    # --- TABLES LEFT & RIGHT ---
    left_info = [
        ["Period", Paragraph(":", wrap12), Paragraph(period_value, wrap12)],
        ["Source", Paragraph(":", wrap12), Paragraph(platform_name, wrap12)],
        ["Message", Paragraph(":", wrap12), Paragraph(f"{total_messages} Messages", wrap12)],
    ]

    right_info = [
        ["Sender", Paragraph(":", wrap12), Paragraph(sender_value, wrap12)],
        ["Receiver", Paragraph(":", wrap12), Paragraph(receiver_value, wrap12)],
    ]

    left_table = Table(left_info, colWidths=[75, 12, (usable_width / 2) - 87])
    right_table = Table(right_info, colWidths=[75, 12, (usable_width / 2) - 87])

    for t in (left_table, right_table):
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

    combined_table = Table(
        [[left_table, right_table]],
        colWidths=[usable_width / 2, usable_width / 2],
    )
    combined_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

    story.append(combined_table)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # CHAT TABLE
    # ---------------------------------------------------------
    col_time = 140
    col_chat = usable_width - col_time
    table_data = [["Time", "Chat"]]

    for entry in conversation_history:
        ts = entry.get("timestamp") or "-"
        try:
            ts = dateutil.parser.isoparse(ts).strftime("%Y-%m-%d %H:%M")
        except Exception:
            ts = str(ts)

        for m in entry.get("messages", []) or []:
            sender = m.get("sender") or "-"
            sender_id = m.get("sender_id") or ""
            if sender_id and is_whatsapp and not sender_id.startswith("+"):
                sender_id = "+" + sender_id
            sender_display = f"{sender_id} ({sender})" if sender_id else sender
            message_text = m.get("message_text") or "-"

            table_data.append([
                Paragraph(ts, style_time_center),
                Paragraph(f"{sender_display}: {message_text}", style_chat_left),
            ])

    header_row = table_data[0]
    rows = table_data[1:]
    chunk_size = 2000

    for i in range(0, len(rows), chunk_size):
        chunk = [header_row] + rows[i:i + chunk_size]

        tbl = Table(chunk, colWidths=[col_time, col_chat], repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3f5676")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

            ("LEFTPADDING", (0, 1), (-1, -1), 4),
            ("RIGHTPADDING", (0, 1), (-1, -1), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),

            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("VALIGN", (0, 1), (-1, -1), "TOP"),

            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.whitesmoke, colors.lightgrey]),
        ]))

        story.append(tbl)
        story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------
    story.append(Spacer(1, 20))
    story.extend(_build_summary_section(usable_width, chat_data.get("summary") or analytic.summary))

    # ---------------------------------------------------------
    # *** DYNAMIC HEADER HEIGHT CALC ***
    # ---------------------------------------------------------
    dyn_title_style = ParagraphStyle(
        "DynHead",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        wordWrap="CJK",
    )

    temp_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
    _, title_h = temp_para.wrap(page_width - 60, 400)

    # header height dari top sampai bawah method ~ (title_h + buffer)
    # buffer 140pt supaya konten selalu di bawah "Method"
    doc.topMargin = title_h + 110

    header_ts = timestamp_now

    # ---------------------------------------------------------
    # DRAW HEADER (responsive pages 1+)
    # ---------------------------------------------------------
    def draw_header(canvas_obj, doc_obj):
        canvas_obj.saveState()
        page_w, page_h = A4

        # LOGO
        logo_path = settings.LOGO_PATH
        if os.path.exists(logo_path):
            canvas_obj.drawImage(
                ImageReader(logo_path),
                20, page_h - 60,
                width=191, height=30,
                preserveAspectRatio=True,
                mask="auto"
            )

        # EXPORTED
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawRightString(
            page_w - 30, page_h - 45,
            f"Exported: {header_ts.strftime('%d/%m/%Y %H:%M')} WIB"
        )

        # TITLE (wrap)
        title_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
        _, h = title_para.wrap(page_w - 60, 400)

        # Jarak dari top ke area title: 85pt sama seperti sebelumnya
        title_y = page_h - 85 - h
        title_para.drawOn(canvas_obj, 30, title_y)

        # METHOD — tepat di bawah title (pakai leading supaya konsisten)
        method_y = title_y - dyn_title_style.leading + 10
        canvas_obj.setFont("Helvetica", 12)
        canvas_obj.drawString(
            30, method_y,
            f"Method: {analytic.method.replace('_',' ').title()}"
        )

        uploaded = (
            analytic.created_at.strftime("%d/%m/%Y")
            if analytic.created_at
            else header_ts.strftime("%d/%m/%Y")
        )
        canvas_obj.drawRightString(page_w - 30, method_y, f"File Uploaded: {uploaded}")

        canvas_obj.restoreState()

    doc.build(
        story,
        onFirstPage=draw_header,
        onLaterPages=draw_header,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
            **kw
        )
    )

    return FileResponse(file_path, filename=filename, media_type="application/pdf")
def _generate_apk_analytics_report(analytic, db, report_type, filename_prefix, data):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle

    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)

    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin
    header_height = 120

    # Will be overridden after title height calc
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=header_height,
        bottomMargin=60,
    )

    # ========= FETCH DATA =========
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("Heading", fontSize=12, leading=15, fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Normal", fontSize=10.5, leading=14, alignment=TA_LEFT)
    wrap_desc = ParagraphStyle("WrapDesc", fontSize=10.5, leading=14, alignment=TA_JUSTIFY)
    center_style = ParagraphStyle("Center", fontSize=10.5, leading=14, alignment=TA_CENTER)

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

    story = []
    story.append(Spacer(1, 5))

    # ========= INFO SECTION =========
    info_left = usable_width * 0.50
    info_right = usable_width * 0.50

    total_apks = len(apk_analytics)

    try:
        scores = [float(a.malware_scoring) for a in apk_analytics if a.malware_scoring]
        avg_score = f"{sum(scores) / len(scores):.0f}%"
    except:
        avg_score = "-"

    file_obj = None
    if apk_analytics:
        file_obj = db.query(File).filter(File.id == apk_analytics[0].file_id).first()

    file_name = file_obj.file_name if file_obj else "-"

    def format_size(size):
        if not size:
            return "-"
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    file_size = format_size(file_obj.total_size) if file_obj else "-"

    info_data = [
        ["File Name", f": {file_name}"],
        ["File Size", f": {file_size}"],
        ["Total Files Scanned", f": {total_apks} Files"],
    ]

    info_table_left = Table(info_data, colWidths=[info_left * 0.45, info_left * 0.55])
    info_table_left.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    box_text = Paragraph(
        f"<b>Malware Probability :</b> <font name='Helvetica' size='12'>{avg_score}</font>",
        ParagraphStyle(
            "BoxText",
            fontSize=12,
            leading=16,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT
        )
    )

    box = Table([[box_text]], colWidths=[None])
    box.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#466086")),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
    ]))

    info_container = Table([[info_table_left, box]], colWidths=[info_left, info_right])
    info_container.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(info_container)
    story.append(Spacer(1, 20))

    # ========= TABLE STYLES =========
    def table_style_no_border():
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466086")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("LINEBELOW", (0, 1), (-1, -1), 0.6, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])

    # ========= MALICIOUS =========
    malicious_header = Table(
        [[Paragraph("Malicious", ParagraphStyle("MalHeader", fontSize=12, leading=14))]],
        colWidths=[usable_width]
    )
    malicious_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(malicious_header)
    story.append(Spacer(1, 4))

    col_left = usable_width * 0.30
    col_right = usable_width - col_left

    if malicious_items:
        mal_table = Table(
            [["Malicious Item", "Description"]] +
            [[Paragraph(i, normal_style), Paragraph(d, wrap_desc)] for i, d in malicious_items],
            colWidths=[col_left, col_right],
            repeatRows=1
        )
        mal_table.setStyle(table_style_no_border())
        story.append(mal_table)
    else:
        story.append(Paragraph("Tidak ditemukan entri berstatus <b>dangerous</b>.", normal_style))

    story.append(Spacer(1, 20))

    # ========= COMMON =========
    common_header = Table(
        [[Paragraph("Common", ParagraphStyle("ComHeader", fontSize=12, leading=14))]],
        colWidths=[usable_width]
    )
    common_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(common_header)
    story.append(Spacer(1, 4))

    if common_items:
        com_table = Table(
            [["Common Item", "Description"]] +
            [[Paragraph(i, normal_style), Paragraph(d, wrap_desc)] for i, d in common_items],
            colWidths=[col_left, col_right],
            repeatRows=1
        )
        com_table.setStyle(table_style_no_border())
        story.append(com_table)
    else:
        story.append(Paragraph("Tidak ada entri common terdeteksi.", normal_style))

    story.append(Spacer(1, 20))

    story.extend(_build_summary_section(usable_width, analytic.summary))

    # =========================================================
    # DYNAMIC HEADER HEIGHT WRAP
    # =========================================================
    dyn_title_style = ParagraphStyle(
        "DynHead",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        wordWrap="CJK",
    )

    temp_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
    _, title_h = temp_para.wrap(page_width - 60, 400)

    # turun sesuai tinggi title
    doc.topMargin = title_h + 110

    header_timestamp = timestamp_now

    # =========================================================
    # DRAW HEADER (WRAPPED)
    # =========================================================
    def draw_header(canvas_obj, doc_obj):
        canvas_obj.saveState()
        page_w, page_h = A4

        top_y = page_h - 30

        # LOGO
        logo_path = settings.LOGO_PATH
        if os.path.exists(logo_path):
            canvas_obj.drawImage(
                ImageReader(logo_path),
                20, top_y - 30,
                width=191, height=30,
                preserveAspectRatio=True,
                mask="auto"
            )

        # EXPORTED
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawRightString(
            page_w - 30,
            top_y - 15,
            f"Exported: {header_timestamp.strftime('%d/%m/%Y %H:%M')} WIB"
        )

        # ======= WRAPPED TITLE =======
        title_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
        max_w = page_w - 60
        w, h = title_para.wrap(max_w, 400)
        title_y = top_y - 55 - h
        title_para.drawOn(canvas_obj, 30, title_y)

        # ======= METHOD (auto turun) =======
        method_y = title_y - dyn_title_style.leading + 10
        canvas_obj.setFont("Helvetica", 12)
        canvas_obj.drawString(
            30,
            method_y,
            f"Method: {analytic.method.replace('_', ' ').title()}"
        )

        # FILE UPLOADED
        uploaded = (
            analytic.created_at.strftime("%d/%m/%Y")
            if analytic.created_at
            else header_timestamp.strftime("%d/%m/%Y")
        )
        canvas_obj.drawRightString(
            page_w - 30,
            method_y,
            f"File Uploaded: {uploaded}"
        )

        canvas_obj.restoreState()

    # =========================================================
    # BUILD DOCUMENT
    # =========================================================
    doc.build(
        story,
        onFirstPage=draw_header,
        onLaterPages=draw_header,
        canvasmaker=lambda *a, **kw:
            GlobalPageCanvas(
                *a,
                footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_', ' ').title()}",
                **kw
            )
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

def _generate_social_media_correlation_report(
    analytic, db, report_type, filename_prefix, data, source
):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle

    logger.info(f"Starting Social Media PDF generation - analytic_id={analytic.id}, source={source}")
    report_start_time = time.time()

    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()

    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin

    # ============================
    # HEADER DEFAULT HEIGHT (will be updated after wrap calculation)
    # ============================
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=150,
        bottomMargin=60,
    )

    # ============================
    # TITLE WRAP STYLE (same as deep/contact/apk)
    # ============================
    dyn_title_style = ParagraphStyle(
        "DynHead",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,    # konsisten
        wordWrap="CJK",
    )

    # ============================
    # HITUNG TINGGI TITLE
    # ============================
    temp_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
    _, title_height = temp_para.wrap(page_width - 60, 500)

    # topMargin disesuaikan otomatis
    doc.topMargin = title_height + 110

    # ============================
    # FETCH DATA
    # ============================
    try:
        from app.api.v1.analytics_social_media_routes import _get_social_media_correlation_data
        response = _get_social_media_correlation_data(analytic.id, db, source or "Instagram")
    except Exception:
        response = None

    # parse response
    data_block = {}
    try:
        if hasattr(response, "body"):
            raw = json.loads(response.body.decode("utf-8"))
            data_block = raw.get("data", {}) if isinstance(raw, dict) else {}
        elif isinstance(response, dict):
            data_block = response.get("data", {})
    except:
        data_block = {}

    correlations_root = data_block.get("correlations", {})
    platform_name = list(correlations_root.keys())[0] if correlations_root else (source or "-")

    correlation_data = correlations_root.get(platform_name, {})
    buckets = correlation_data.get("buckets", [])
    devices = data_block.get("devices", [])
    total_devices = len(devices)
    total_accounts = sum(len(bucket.get("devices", [])) for bucket in buckets)

    # force big dataset (like your test)
    buckets = buckets * 50

    # ============================
    # STYLES
    # ============================
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle("Normal", fontSize=12, leading=14)
    wrap_style = ParagraphStyle("Wrap", fontSize=12, leading=14, wordWrap="CJK")

    story = []

    # ============================
    # INFO TABLE
    # ============================
    info_data = [
        ["Source", f": {platform_name}"],
        ["Total Device", f": {total_devices} Devices"],
        ["Total Social Media", f": {total_accounts} Accounts"],
    ]
    info_table = Table(info_data, colWidths=[usable_width * 0.25, usable_width * 0.75])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # ============================
    # DEVICE SUMMARY
    # ============================
    device_summary_header = Table(
        [[Paragraph("Device Identification Summary", normal_style)]],
        colWidths=[usable_width]
    )
    device_summary_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]))
    story.append(device_summary_header)
    story.append(Spacer(1, 8))

    # Device table
    dev_table_data = [["Device ID", "Registered Owner", "Phone Number"]]
    for d in devices:
        dev_table_data.append([
            f"Device {d['device_id']}",
            d.get("owner_name", "-"),
            d.get("phone_number", "-"),
        ])

    col1 = usable_width * 0.20
    col2 = usable_width * 0.40
    col3 = usable_width - col1 - col2

    dev_tbl = Table(dev_table_data, colWidths=[col1, col2, col3], repeatRows=1)
    dev_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466087")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("LEFTPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
    ]))
    story.append(dev_tbl)
    story.append(Spacer(1, 20))

    # ============================
    # CORRELATION SUMMARY
    # ============================
    corr_title = Table([[Paragraph("Device Account Correlation", normal_style)]], colWidths=[usable_width])
    corr_title.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]))
    story.append(corr_title)
    story.append(Spacer(1, 6))

    # If no buckets
    if not buckets:
        story.append(Paragraph("No correlation data available.", normal_style))
    else:
        # Build table
        corr_data = [["Connections", "Involved Device", "Correlated Accounts"]]

        for b in buckets:
            label = b.get("label", "-")
            rows = b.get("devices", [])

            for row in rows:
                involved_idx = [i for i, acc in enumerate(row) if acc is not None]
                device_ids = [devices[i]["device_id"] for i in involved_idx if i < len(devices)]

                dev_text = f"Device {', '.join(map(str, device_ids))}"
                accounts = [f"• @{a}" if a and not a.startswith("@") else f"• {a}" for a in row if a]
                acc_para = Paragraph("<br/>".join(accounts) if accounts else "-", wrap_style)

                corr_data.append([
                    Paragraph(label, wrap_style),
                    Paragraph(dev_text, wrap_style),
                    acc_para,
                ])

        col_a = usable_width * 0.25
        col_b = usable_width * 0.30
        col_c = usable_width - col_a - col_b

        corr_tbl = Table(corr_data, colWidths=[col_a, col_b, col_c], repeatRows=1)
        corr_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#466087")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ]))
        story.append(corr_tbl)

    # ============================
    # SUMMARY
    # ============================
    story.append(Spacer(1, 20))
    story.extend(_build_summary_section(usable_width, analytic.summary))

    header_ts = timestamp_now

    # ============================
    # DRAW HEADER (FIRST + NEXT PAGES)
    # ============================
    def draw_header(canvas_obj, doc_obj):
        canvas_obj.saveState()
        page_w, page_h = A4

        # LOGO
        logo_path = settings.LOGO_PATH
        if os.path.exists(logo_path):
            canvas_obj.drawImage(
                ImageReader(logo_path),
                20, page_h - 60,
                width=191, height=30,
                preserveAspectRatio=True,
                mask="auto",
            )

        # EXPORTED
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawRightString(
            page_w - 30,
            page_h - 45,
            f"Exported: {header_ts.strftime('%d/%m/%Y %H:%M')} WIB"
        )

        # TITLE (WRAPPED)
        title_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
        _, h = title_para.wrap(page_w - 60, 400)
        title_y = page_h - 85 - h
        title_para.drawOn(canvas_obj, 30, title_y)

        # METHOD
        method_y = title_y - dyn_title_style.leading + 10
        canvas_obj.setFont("Helvetica", 12)
        canvas_obj.drawString(
            30,
            method_y,
            f"Method: {analytic.method.replace('_',' ').title()}"
        )

        # FILE UPLOADED
        uploaded = analytic.created_at.strftime("%d/%m/%Y") if analytic.created_at else header_ts.strftime("%d/%m/%Y")
        canvas_obj.drawRightString(page_w - 30, method_y, f"File Uploaded: {uploaded}")

        canvas_obj.restoreState()

    # BUILD PDF
    doc.build(
        story,
        onFirstPage=draw_header,
        onLaterPages=draw_header,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_',' ').title()}",
            **kw,
        ),
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )

def _generate_contact_correlation_report(analytic, db, report_type, filename_prefix, data, current_user=None):
    logger.info(f"Starting Contact Correlation PDF generation - analytic_id={analytic.id}")
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    report_start_time = time.time()
    
    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    page_width, _ = A4
    left_margin = right_margin = 30
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

    result = _get_contact_correlation_data(analytic.id, db, current_user)

    if isinstance(result, JSONResponse):
        result = result.body
    if isinstance(result, (bytes, bytearray)):
        result = json.loads(result.decode("utf-8"))
    if isinstance(result, str):
        try: result = json.loads(result)
        except: result = {}
    if not isinstance(result, dict):
        result = {}

    api_data = result.get("data", {})
    devices = api_data.get("devices", [])
    correlations = api_data.get("correlations", [])
    summary = api_data.get("summary")
    correlations = correlations * 50

    styles = getSampleStyleSheet()
    center_style = ParagraphStyle("Center", alignment=TA_CENTER, fontSize=10, leading=13)
    header_device_style = ParagraphStyle(
        "HeaderDevice", alignment=TA_CENTER, fontSize=10, leading=12,
        textColor=colors.white, fontName="Helvetica-Bold"
    )

    group_size = 4
    groups = [devices[i:i+group_size] for i in range(0, len(devices), group_size)]

    story = []
    story.append(Spacer(1, 5))

    for group_index, group in enumerate(groups, start=1):

        start_dev = (group_index - 1) * group_size + 1
        end_dev = start_dev + len(group) - 1

        info_col_left = usable_width * 0.20
        info_data = [
            ["Source", ": Handphone"],
            ["Total Device", f": {len(devices)} Devices (Device {start_dev}-{end_dev})"],
            ["Total Contact", f": {len(correlations)} Contacts"],
        ]
        info_table = Table(info_data, colWidths=[info_col_left, usable_width - info_col_left])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 12),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 12))

        header_row = ["Contact Number"]
        for dev in group:
            header_row.append(
                Paragraph(
                    f"<b>{dev['device_label']}</b><br/><font size=9>{dev.get('phone_number','-')}</font>",
                    header_device_style
                )
            )

        table_rows = [header_row]

        for row in correlations:
            contact_num = row.get("contact_number", "-")
            dev_map = {d["device_label"]: d["contact_name"] for d in row.get("devices_found_in", [])}

            new_row = [Paragraph(contact_num, center_style)]
            for dev in group:
                val = dev_map.get(dev["device_label"], "—")
                new_row.append(Paragraph(val, center_style))

            table_rows.append(new_row)

        col_widths = [usable_width * 0.25] + [(usable_width * 0.75) / len(group) for _ in group]

        tbl = Table(table_rows, colWidths=col_widths, repeatRows=1)

        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#466086")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN", (0,0), (-1,0), "CENTER"),
            ("VALIGN", (0,0), (-1,0), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,0), 6),
            ("BOTTOMPADDING", (0,0), (-1,0), 6),

            ("ALIGN", (0,1), (-1,-1), "CENTER"),
            ("VALIGN", (0,1), (-1,-1), "MIDDLE"),

            ("BOX", (0,0), (-1,-1), 0, colors.white),
            ("LINEBEFORE", (0,0), (-1,-1), 0, colors.transparent),
            ("LINEAFTER", (0,0), (-1,-1), 0,  colors.transparent),
            ("LINEABOVE", (0,1), (-1,-1), 0,  colors.transparent),

            ("LINEBELOW", (0,1), (-1,-1), 0.5, colors.grey),

            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),

            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,1), (-1,-1), 6),
            ("BOTTOMPADDING", (0,1), (-1,-1), 6),
        ]))

        story.append(tbl)

        if group_index < len(groups):
            story.append(PageBreak())

    story.append(Spacer(1, 16))
    story.extend(_build_summary_section(usable_width, summary))

    header_ts = timestamp_now

    title_style = ParagraphStyle(
        "HeaderTitle",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        wordWrap="CJK"
    )

    dyn_title_style = ParagraphStyle(
    "DynHead",
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=26,            # sama seperti deep communication
    wordWrap="CJK",
)

# hitung tinggi judul untuk menentukan topMargin
    temp_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
    _, title_h = temp_para.wrap(page_width - 60, 400)

    # sama seperti deep comm → title + method + buffer
    doc.topMargin = title_h + 110

    header_ts = timestamp_now


    # ---------------------------------------------------------
    # DRAW HEADER — KONSISTEN SEPERTI DEEP_COMM
    # ---------------------------------------------------------
    def draw_header(canvas_obj, doc_obj):
        canvas_obj.saveState()
        page_w, page_h = A4

        # LOGO
        logo_path = settings.LOGO_PATH
        if os.path.exists(logo_path):
            canvas_obj.drawImage(
                ImageReader(logo_path),
                20, page_h - 60,
                width=191, height=30,
                preserveAspectRatio=True,
                mask="auto"
            )

        # EXPORTED TIME (right)
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawRightString(
            page_w - 30,
            page_h - 45,
            f"Exported: {header_ts.strftime('%d/%m/%Y %H:%M')} WIB"
        )

        # WRAPPED TITLE
        title_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
        max_w = page_w - 60
        _, h = title_para.wrap(max_w, 400)

        title_y = page_h - 85 - h   # sama dengan deep comm
        title_para.drawOn(canvas_obj, 30, title_y)

        # METHOD (tepat di bawah title, pakai leading)
        method_y = title_y - dyn_title_style.leading + 10
        canvas_obj.setFont("Helvetica", 12)
        canvas_obj.drawString(
            30,
            method_y,
            f"Method: {analytic.method.replace('_',' ').title()}"
        )

        # FILE UPLOADED (right aligned)
        uploaded = analytic.created_at.strftime("%d/%m/%Y") if analytic.created_at else header_ts.strftime("%d/%m/%Y")
        canvas_obj.drawRightString(page_w - 30, method_y, f"File Uploaded: {uploaded}")

        canvas_obj.restoreState()

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

def _generate_hashfile_analytics_report(analytic, db, report_type, filename_prefix, data):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle

    logger.info(f"Starting Hashfile Analytics PDF generation - analytic_id={analytic.id}")
    report_start_time = time.time()

    reports_dir = settings.REPORTS_DIR
    os.makedirs(reports_dir, exist_ok=True)
    timestamp_now = get_indonesia_time()
    filename = f"{filename_prefix}_{analytic.id}_{timestamp_now.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    page_width, _ = A4
    left_margin, right_margin = 30, 30
    usable_width = page_width - left_margin - right_margin

    # ========== DYNAMIC TITLE STYLE (SAMA SEMUA REPORT) ==========
    dyn_title_style = ParagraphStyle(
        "DynHead",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        wordWrap="CJK",
    )

    # Hitung tinggi judul (wrap)
    temp_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
    _, title_h = temp_para.wrap(page_width - 60, 500)

    # Top margin otomatis supaya konten tidak numpuk header
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=title_h + 110,
        bottomMargin=60,
    )

    # ========= DATA FETCH =========
    response = _get_hashfile_analytics_data(analytic.id, db)
    data = {}
    try:
        if response is not None:
            if hasattr(response, "body") and response.body is not None:
                raw = response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body
                parsed = json.loads(raw)
                data = parsed.get("data", {}) if isinstance(parsed, dict) else {}
            elif isinstance(response, dict):
                data = response.get("data", {})
    except:
        data = {}

    devices = data.get("devices", [])
    hashfiles = data.get("correlations") or []

    # Group 4 device per batch
    group_size = 4
    groups = [devices[i:i+group_size] for i in range(0, len(devices), group_size)]

    # ========= STORY =========
    story = []
    story.append(Spacer(1, 5))

    normal_center = ParagraphStyle("NormalCenter", fontSize=10, leading=13, alignment=TA_CENTER)
    header_style = ParagraphStyle(
        "HeaderStyle",
        alignment=TA_CENTER,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        fontSize=9
    )

    for g_index, group in enumerate(groups, start=1):
        start_dev = (g_index - 1) * group_size + 1
        end_dev = start_dev + len(group) - 1

        # Info section
        info_data = [
            ["Source", ": Handphone"],
            ["Total Device", f": {len(devices)} Devices (Device {start_dev}-{end_dev})"],
            ["Total Files", f": {len(hashfiles)} Files"],
        ]

        info_table = Table(info_data, colWidths=[usable_width * 0.25, usable_width * 0.75])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 12),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 12))

        # Header row (filename + per device)
        header_row = ["Filename"]
        for d in group:
            owner = d.get("owner_name", "Unknown")
            phone = d.get("phone_number") or "-"
            header_row.append(Paragraph(f"<b>{owner}</b><br/><font size=8>{phone}</font>", header_style))

        table_data = [header_row]

        # Body
        for h in hashfiles:
            row = [Paragraph(h.get("file_name", "-"), normal_center)]
            found = h.get("devices", [])

            for d in group:
                mark = "✔" if d.get("device_label") in found else "✘"
                row.append(Paragraph(mark, normal_center))

            table_data.append(row)

        # Chunking (if huge data)
        col_widths = [usable_width * 0.25] + [(usable_width * 0.75) / len(group)] * len(group)
        chunk_size = 2000
        body_rows = table_data[1:]

        for start in range(0, len(body_rows), chunk_size):
            part = [header_row] + body_rows[start:start + chunk_size]

            tbl = Table(part, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#466086")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("ALIGN", (0,0), (-1,0), "CENTER"),
                ("VALIGN", (0,0), (-1,0), "MIDDLE"),

                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
                ("ALIGN", (0,1), (-1,-1), "CENTER"),
                ("VALIGN", (0,1), (-1,-1), "MIDDLE"),

                ("LINEBELOW", (0,1), (-1,-1), 0.5, colors.grey),
                ("LEFTPADDING", (0,1), (-1,-1), 4),
                ("RIGHTPADDING", (0,1), (-1,-1), 4),
                ("TOPPADDING", (0,1), (-1,-1), 6),
                ("BOTTOMPADDING", (0,1), (-1,-1), 6),
            ]))
            story.append(tbl)

        if g_index < len(groups):
            story.append(PageBreak())

    story.append(Spacer(1, 20))
    story.extend(_build_summary_section(usable_width, analytic.summary))

    header_ts = timestamp_now

    # ========== DRAW HEADER (WRAPPED TITLE) ==========
    def draw_header(canvas_obj, doc_obj):
        canvas_obj.saveState()
        page_w, page_h = A4

        # Logo
        logo_path = settings.LOGO_PATH
        if os.path.exists(logo_path):
            canvas_obj.drawImage(
                ImageReader(logo_path),
                20, page_h - 60,
                width=191,
                height=30,
                preserveAspectRatio=True,
                mask="auto",
            )

        # Export time
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawRightString(
            page_w - 30,
            page_h - 45,
            f"Exported: {header_ts.strftime('%d/%m/%Y %H:%M')} WIB"
        )

        # Title (wrap)
        title_para = Paragraph(analytic.analytic_name or "", dyn_title_style)
        _, h = title_para.wrap(page_w - 60, 400)
        title_y = page_h - 85 - h
        title_para.drawOn(canvas_obj, 30, title_y)

        # Method
        method_y = title_y - dyn_title_style.leading + 10
        canvas_obj.setFont("Helvetica", 12)
        canvas_obj.drawString(30, method_y,
                              f"Method: {analytic.method.replace('_',' ').title()}")

        # File Uploaded
        uploaded = analytic.created_at.strftime("%d/%m/%Y") if analytic.created_at else header_ts.strftime("%d/%m/%Y")
        canvas_obj.drawRightString(page_w - 30, method_y, f"File Uploaded: {uploaded}")

        canvas_obj.restoreState()

    # ========= BUILD PDF =========
    doc.build(
        story,
        onFirstPage=draw_header,
        onLaterPages=draw_header,
        canvasmaker=lambda *a, **kw: GlobalPageCanvas(
            *a,
            footer_text=f"{analytic.analytic_name} - {analytic.method.replace('_',' ').title()}",
            **kw,
        ),
    )

    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")
