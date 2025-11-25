import os
import logging
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, CondPageBreak, Flowable
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage, ImageDraw
from app.core.config import settings

WIB = timezone(timedelta(hours=7), 'WIB')

class CaseStatus:
    OPEN = "Open"
    REOPENED = "Re-open"
    CLOSED = "Closed"

logger = logging.getLogger(__name__)

COLOR_PRIMARY_BLUE = colors.HexColor("#1a2b63")
COLOR_HEADER_GREY = colors.HexColor("#f5f5f5")
COLOR_TITLE = colors.HexColor("#0d0d0d")
COLOR_TEXT_GREY = colors.HexColor("#4b4b4b")
COLOR_BORDER_GREY = colors.HexColor("#466087")
COLOR_SECTION_BACKGROUND = colors.HexColor("#cccccc")
COLOR_ROW_BACKGROUND_ODD = colors.HexColor("#f2f2f2")
COLOR_NOTES_BORDER = colors.HexColor("#5c5c5c")
COLOR_TABLE_HEADER_BG = colors.HexColor("#466086")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 24
MARGIN_RIGHT = 30
MARGIN_BOTTOM = 50
NEW_TOP_MARGIN = 170
USABLE_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

def get_wib_now() -> datetime:
    return datetime.now(WIB)

class TimelineFlowable(Flowable):
    def __init__(self, custody_data, width, height=120):
        Flowable.__init__(self)
        self.custody_data = custody_data
        self.width = width
        self.height = height
        self._register_noto_sans()
    
    def _register_noto_sans(self):
        try:
            pdfmetrics.getFont("NotoSans")
        except:
            noto_sans_paths = [
                "/System/Library/Fonts/Supplemental/NotoSans-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                "C:/Windows/Fonts/NotoSans-Regular.ttf",
                os.path.join(os.path.dirname(__file__), "fonts", "NotoSans-Regular.ttf"),
            ]
            for path in noto_sans_paths:
                if os.path.exists(path):
                    try:
                        pdfmetrics.registerFont(TTFont("NotoSans", path))
                        break
                    except:
                        continue

    def wrap(self, availWidth, availHeight):
        return self.width, self.height
    
    def draw(self):
        canvas = self.canv
        canvas.saveState()
        
        dot_color = colors.HexColor("#CCCCCC")
        line_color = colors.HexColor("#CCCCCC")
        text_color = colors.HexColor("#0C0C0C")
        text_color_light = colors.HexColor("#666666")
        
        num_stages = len(self.custody_data)
        if num_stages == 0:
            canvas.restoreState()
            return
        

        dot_radius = 6
        timeline_y = self.height - 20
        text_y = timeline_y - 35
        date_y = text_y - 15
        name_y = date_y - 15
        
        margin_left = 70
        margin_right = 10
        available_width = self.width - margin_left - margin_right
        spacing = available_width / (num_stages - 1) if num_stages > 1 else 0
        start_x = margin_left
        
        if num_stages > 1:
            canvas.setStrokeColor(line_color)
            canvas.setLineWidth(1)
            canvas.setDash([5, 3])
            canvas.line(start_x, timeline_y, start_x + available_width, timeline_y)
            canvas.setDash()
        
        for i, data in enumerate(self.custody_data):
            x = start_x + (i * spacing)
            
            canvas.setFillColor(dot_color)
            canvas.setStrokeColor(dot_color)
            canvas.circle(x, timeline_y, dot_radius, fill=1, stroke=1)
   
            canvas.setFont("Helvetica", 9.47)
            canvas.setFillColor(colors.HexColor("#000000"))
            stage_name = data.get("type", "")
            text_width = canvas.stringWidth(stage_name, "Helvetica", 9.47)
            canvas.drawString(x - text_width / 2, text_y, stage_name)
            
            canvas.setFont("Helvetica", 6.31)
            canvas.setFillColor(colors.HexColor("#545454"))
            date_str = data.get("date", "N/A")
            date_width = canvas.stringWidth(date_str, "Helvetica", 6.31)
            canvas.drawString(x - date_width / 2, date_y, date_str)

            name_str = data.get("name", "N/A")

            try:
                font_name = "NotoSans" if pdfmetrics.getFont("NotoSans") else "Helvetica"
            except:
                font_name = "Helvetica"
            canvas.setFont(font_name, 6.31)  # Medium weight (500), size 6.31px
            canvas.setFillColor(colors.HexColor("#000000"))
            name_width = canvas.stringWidth(name_str, font_name, 6.31)
            canvas.drawString(x - name_width / 2, name_y, name_str)
        
        
        canvas.restoreState()
class CaseDetailPageCanvas(canvas.Canvas):
    def __init__(self, *args, case_title: str = "", case_id: str = "", export_time: str = "",
                 case_status: str = "", case_officer: str = "", created_date: str = "",
                 case_info_table_height: float = 63, logo_path: str = "", 
                 has_notes: bool = False, has_person_of_interest: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_title = case_title
        self.case_id = case_id
        self.export_time = export_time
        self.case_status = case_status
        self.case_officer = case_officer
        self.created_date = created_date
        self.case_info_table_height = case_info_table_height
        self.logo_path = logo_path
        self.has_notes = has_notes
        self.has_person_of_interest = has_person_of_interest
        self._page_number = 1
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()  # type: ignore[reportAttributeAccessIssue]
        self._page_number += 1

    def save(self):
        total_pages = len(self.pages)
        
        for page_number, page_dict in enumerate(self.pages, start=1):
            self.__dict__.update(page_dict)
            self._draw_header_footer(page_number, str(total_pages))
            super().showPage()
        
        super().save()

    def _draw_header_footer(self, current_page: int, total_pages_placeholder: str):
        page_width, page_height = A4
        left_margin = MARGIN_LEFT
        right_margin = MARGIN_RIGHT
        usable_width = page_width - left_margin - right_margin

        logo_w, logo_h = 175, 30
        logo_x = left_margin - 7
        logo_y = page_height - 30

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                img = PILImage.open(self.logo_path)
                ratio = min(logo_w / img.width, logo_h / img.height)
                final_w = img.width * ratio
                final_h = img.height * ratio
                buf = BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                reportlab_img = Image(buf, width=final_w, height=final_h)
                
                logo_y_aligned = logo_y - final_h + 12
                self.saveState()
                self.setStrokeColor(colors.white)
                self.setLineWidth(0)
                reportlab_img.drawOn(self, logo_x, logo_y_aligned)
                self.restoreState()
            except Exception:
                self.setFont("Helvetica-Bold", 14)
                self.setFillColor(COLOR_PRIMARY_BLUE)
                self.drawString(logo_x, logo_y + 10, "CYBER SENTINEL")
        else:
            self.setFont("Helvetica-Bold", 14)
            self.setFillColor(COLOR_PRIMARY_BLUE)
            self.drawString(logo_x, logo_y + 10, "CYBER SENTINEL")

        export_y = page_height - 35
        self.setFont("Helvetica", 10)
        self.setFillColor(colors.HexColor("#333333"))
        export_text = f"Exported: {self.export_time}"
        self.drawRightString(page_width - right_margin, export_y, export_text)

        self.setStrokeColor(COLOR_HEADER_GREY)
        self.setLineWidth(1)
        self.line(left_margin, export_y - 8, page_width - right_margin, export_y - 8)

        is_last_page = False
        try:
            if total_pages_placeholder != "?":
                total_pages_int = int(total_pages_placeholder)
                is_last_page = (current_page == total_pages_int)
        except (ValueError, TypeError):
            is_last_page = False
        
        should_show_header = (
            current_page > 1 and 
            self.case_id and 
            (not is_last_page or (self.has_notes or self.has_person_of_interest))
        )
        
        if should_show_header:
            col1_width = usable_width * 0.80
            col2_width = usable_width * 0.20
            info_y_start = page_height - 60
            title_y = info_y_start - 11
            line_height = 20

            self.setFont("Helvetica-Bold", 20)
            self.setFillColor(COLOR_TITLE)
            textobject = self.beginText(left_margin, title_y)
            textobject.setFont("Helvetica-Bold", 20)
            textobject.setFillColor(COLOR_TITLE)
            textobject.setTextOrigin(left_margin, title_y)

            words = self.case_title.split()
            line = ""
            title_lines_count = 0
            for word in words:
                test_line = line + word + " " if line else word + " "
                test_width = self.stringWidth(test_line, "Helvetica-Bold", 20)
                if test_width > col1_width and line:
                    textobject.textLine(line.strip())
                    line = word + " "
                    title_lines_count += 1
                else:
                    line = test_line
            if line:
                textobject.textLine(line.strip())
                title_lines_count += 1
            self.drawText(textobject)

            case_id_y = title_y - (title_lines_count * line_height) - 5
            self.setFont("Helvetica-Bold", 12)
            self.setFillColor(colors.HexColor("#333333"))
            self.drawString(left_margin, case_id_y, f"Case ID: {self.case_id}")

            if self.case_status:
                status_width = col2_width * 1.1
                status_height = 37
                status_x = left_margin + col1_width - 10
                
                status_y = title_y - (status_height / 2) - 18

                self.setStrokeColor(COLOR_BORDER_GREY)
                self.setLineWidth(1)
                self.setFillColor(colors.white)
                self.rect(status_x, status_y, status_width, status_height, stroke=1, fill=1)
                self.setFont("Helvetica-Bold", 16)
                self.setFillColor(colors.black)
                text_width = self.stringWidth(self.case_status, "Helvetica-Bold", 16)
                status_text_x = status_x + (status_width / 2) - (text_width / 2)
                status_text_y = status_y + (status_height / 2) - 3
                self.drawString(status_text_x, status_text_y, self.case_status)

           
            grid_case_y = page_height - NEW_TOP_MARGIN + 10
            investigator_y = grid_case_y - 5
            self.setFont("Helvetica", 12)
            self.setFillColor(colors.HexColor("#0C0C0C"))

            if self.case_officer:
                self.drawString(left_margin, investigator_y, f"Investigator: {self.case_officer}")

            if self.created_date:
                date_text = f"Date Created: {self.created_date}"
                date_x = page_width - right_margin - self.stringWidth(date_text, "Helvetica", 12)
                self.drawString(date_x, investigator_y, date_text)
        
        footer_y = 30
        line_y = footer_y + 25
        left_margin_footer = MARGIN_LEFT
        right_margin_footer = MARGIN_RIGHT
        usable_width_footer = page_width - left_margin_footer - right_margin_footer

        self.setFillColor(COLOR_HEADER_GREY)
        self.rect(left_margin_footer, line_y - 1, usable_width_footer, 2, fill=1, stroke=0)
        self.setStrokeColor(COLOR_BORDER_GREY)
        self.setLineWidth(2)
        self.line(left_margin_footer, line_y, left_margin_footer + usable_width_footer, line_y)

        footer_text = f"{self.case_title} - {self.case_id}"
        
        if total_pages_placeholder != "?" and total_pages_placeholder != "0":
            page_text = f"Page {current_page} of {total_pages_placeholder}"
        else:
            page_text = f"Page {current_page}"

        self.setFont("Helvetica", 10)
        self.setFillColor(colors.HexColor("#333333"))
        self.drawString(left_margin_footer, footer_y, footer_text)
        
        # Set different style for page number
        self.setFont("Helvetica", 12)
        self.setFillColor(colors.HexColor("#0C0C0C"))
        self.drawRightString(page_width - right_margin_footer, footer_y, page_text)

def generate_case_detail_pdf(case_data: dict, output_path: str) -> str:
    try:
        case_info = case_data.get("case", {})
        case_title = case_info.get("title") or "Unknown Case"
        case_id = str(case_info.get("case_number") or case_info.get("id") or "N/A")
        case_description = case_info.get("description") or "No description available"
        case_officer = case_info.get("case_officer") or "N/A"
        case_status_raw = case_info.get("status") or CaseStatus.OPEN
        created_date = case_info.get("created_date") or "N/A"
        case_notes = (case_data.get("case_notes") or "").strip()
        export_time = get_wib_now().strftime("%d/%m/%Y %H:%M WIB")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=NEW_TOP_MARGIN,
            bottomMargin=MARGIN_BOTTOM,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CaseTitle", parent=styles["Heading1"], fontSize=20, textColor=COLOR_TITLE,
            spaceAfter=4, alignment=TA_LEFT, fontName="Helvetica-Bold", leftIndent=0
        )
        case_id_style = ParagraphStyle(
            "CaseID", fontSize=12, textColor=colors.HexColor("#333333"), spaceAfter=7, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", fontSize=14, textColor=colors.black, spaceAfter=7, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        status_style = ParagraphStyle(
            "StatusStyle", fontSize=16, textColor=colors.black, spaceAfter=7, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )
        investigator_style = ParagraphStyle(
            "Investigator", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=6, alignment=TA_LEFT, fontName="Helvetica", leftIndent=-5
        )
        date_created_style = ParagraphStyle(
            "DateCreated", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=6, alignment=TA_RIGHT, fontName="Helvetica"
        )
        description_title_style = ParagraphStyle(
            "DescriptionTitle", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=0, alignment=TA_LEFT, fontName="Helvetica"
        )
        description_text_style = ParagraphStyle(
            "DescriptionText", fontSize=12, leading=16, alignment=TA_JUSTIFY, textColor=colors.HexColor("#0C0C0C"), fontName="Helvetica"
        )
        poi_title_style = ParagraphStyle(
            "PersonOfInterestTitle", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=0, alignment=TA_LEFT, fontName="Helvetica"
        )
        poi_info_text_style = ParagraphStyle(
            "PersonInfoText", fontSize=12, leading=16, alignment=TA_LEFT, textColor=colors.HexColor("#0C0C0C"), fontName="Helvetica"
        )
        notes_title_style = ParagraphStyle(
            "NotesTitle", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=8, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        notes_text_style = ParagraphStyle(
            "NotesText", fontSize=12, leading=16, alignment=TA_LEFT, textColor=colors.HexColor("#000000"), fontName="Helvetica"
        )
        table_header_style = ParagraphStyle(
            "TableHeader", parent=styles["Normal"], fontSize=12, alignment=TA_LEFT,
            fontName="Helvetica", leading=13, textColor=colors.HexColor("#F4F6F8")
        )
        evidence_summary_style = ParagraphStyle(
            "EvidenceSummary", fontSize=12, leading=14, alignment=TA_LEFT, textColor=colors.HexColor("#0C0C0C"), fontName="Helvetica"
        )

        story = []
        col1_width = USABLE_WIDTH * 0.80
        col2_width = USABLE_WIDTH * 0.20
        status_bg_color = colors.white
        status_text_color = colors.black

        story.append(Spacer(1, -140))

        button_height = 37
        status_button_data = [[Paragraph(f"<b>{case_status_raw}</b>", status_style)]]
        status_button_table = Table(
            status_button_data, colWidths=[col2_width * 1.1], rowHeights=[button_height]
        )
        status_button_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), status_bg_color),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), -5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        case_info_data = [
            [Paragraph(case_title, title_style), status_button_table]
        ]
        case_info_table = Table(case_info_data, colWidths=[col1_width, col2_width])
        case_info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (0, 0), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (0, 0), 20),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("RIGHTPADDING", (1, 0), (1, 0), 15),
            ("TOPPADDING", (1, 0), (1, 0), 25),
        ]))
        story.append(case_info_table)
        story.append(Spacer(1, 8))
        
        case_id_data = [
            [Paragraph(f"<b>Case ID:</b> {case_id}", case_id_style)]
        ]
        case_id_table = Table(case_id_data, colWidths=[USABLE_WIDTH])
        case_id_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(case_id_table)
        story.append(Spacer(1, 4))

        title_row_height = max(
            (title_style.fontSize * 1.2 + title_style.spaceAfter + 20),
            button_height + 2
        )
        case_id_row_height = case_id_style.fontSize * 1.2 + case_id_style.spaceAfter
        case_info_table_height = title_row_height + case_id_row_height + 2

        story.append(Spacer(1, 20))
        investigator_table = Table([[Paragraph(f"Investigator: {case_officer}", investigator_style)]],
                                   colWidths=[USABLE_WIDTH * 0.5])
        date_created_table = Table([[Paragraph(f"Date Created: {created_date}", date_created_style)]],
                                   colWidths=[USABLE_WIDTH * 0.5])
        case_meta_data = [[investigator_table, date_created_table]]
        case_meta_table = Table(case_meta_data, colWidths=[USABLE_WIDTH * 0.5, USABLE_WIDTH * 0.5])
        case_meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
            ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ]))
        story.append(case_meta_table)
        story.append(Spacer(1, 16))

        desc_title_table = Table(
            [[Paragraph("Case Description", description_title_style)]],
            colWidths=[USABLE_WIDTH]
        )
        desc_title_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(Spacer(1, 10))
        story.append(desc_title_table)
        story.append(Spacer(1, 5))

        desc_value_table = Table(
            [[Paragraph(case_description, description_text_style)]],
            colWidths=[USABLE_WIDTH]
        )
        desc_value_table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(desc_value_table)
        story.append(Spacer(1, 20))

        poi_title_table = Table(
            [[Paragraph("Person of Interest", poi_title_style)]],
            colWidths=[USABLE_WIDTH]
        )
        poi_title_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(poi_title_table)
        story.append(Spacer(1, 5))

        persons_of_interest = case_data.get("persons_of_interest", [])

        if not persons_of_interest or len(persons_of_interest) == 0:
            person_name = "<i>No data available</i>"
            person_type = "<i>No data available</i>"
            total_evidence = 0

            person_info_table_data = [
                [Paragraph("Name", poi_info_text_style), Paragraph(f":&nbsp;&nbsp;{person_name}", poi_info_text_style)],
                [Paragraph("Status", poi_info_text_style), Paragraph(f":&nbsp;&nbsp;{person_type}", poi_info_text_style)],
                [Paragraph("Total Evidence", poi_info_text_style), Paragraph(f":&nbsp;&nbsp;{total_evidence} Evidence", poi_info_text_style)],
            ]
            person_info_table = Table(
                person_info_table_data, colWidths=[USABLE_WIDTH * 0.20, USABLE_WIDTH * 0.80]
            )
            person_info_table.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (1, 0), (1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))

            story.append(Spacer(1, 10))
            story.append(person_info_table)
            story.append(Spacer(1, 10))
            story.append(Paragraph("<i>No evidence available</i>", poi_info_text_style))
            story.append(Spacer(1, 20))
        else:
            for index, person in enumerate(persons_of_interest):
                person_name = str(person.get("name") or "<i>No data available</i>")
                person_type = str(person.get("person_type") or "<i>No data available</i>")
                evidence_list = person.get("evidence") or []
                total_evidence = len(evidence_list)

                person_info_table_data = [
                    [Paragraph("Name", poi_info_text_style), Paragraph(f":&nbsp;&nbsp;{person_name}", poi_info_text_style)],
                    [Paragraph("Status", poi_info_text_style), Paragraph(f":&nbsp;&nbsp;{person_type}", poi_info_text_style)],
                    [Paragraph("Total Evidence", poi_info_text_style), Paragraph(f":&nbsp;&nbsp;{total_evidence} Evidence", poi_info_text_style)],
                ]
                person_info_table = Table(
                    person_info_table_data, colWidths=[USABLE_WIDTH * 0.20, USABLE_WIDTH * 0.80]
                )
                person_info_table.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (1, 0), (1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))

                evidence_table = None
                if evidence_list:
                    table_data = [[
                        Paragraph('Picture', table_header_style),
                        Paragraph('Evidence ID', table_header_style),
                        Paragraph('Summary', table_header_style),
                    ]]

                    picture_col_width = USABLE_WIDTH * 0.25
                    
                    for ev in evidence_list:
                        evidence_id = str(ev.get("evidence_number") or ev.get("evidence_id") or "N/A")
                        summary_text = str(ev.get("evidence_summary") or "No summary available")
                        file_path = ev.get("file_path")
                        pic_cell = Paragraph("<i>No image</i>", evidence_summary_style)

                        if file_path:
                            resolved_path = None
                            if os.path.isabs(file_path):
                                resolved_path = file_path if os.path.exists(file_path) else None
                            else:
                                file_path_clean = file_path.lstrip("./")
                                base_name = os.path.basename(file_path_clean)
                                
                                possible_paths = [
                                    os.path.join(os.getcwd(), file_path_clean),
                                ]
                                
                                if not file_path_clean.startswith("data/"):
                                    possible_paths.extend([
                                        os.path.join(os.getcwd(), settings.UPLOAD_DIR.lstrip("./"), file_path_clean),
                                        os.path.join(os.getcwd(), settings.UPLOAD_DIR.lstrip("./"), base_name),
                                        os.path.join(os.getcwd(), "data", "uploads", file_path_clean),
                                        os.path.join(os.getcwd(), "data", "uploads", base_name),
                                    ])
                                
                                possible_paths.extend([
                                    os.path.join(os.getcwd(), "data", "evidence", base_name),
                                    file_path if os.path.exists(file_path) else None,
                                ])
                                
                                for path in possible_paths:
                                    if path and os.path.exists(path):
                                        resolved_path = path
                                        logger.info(f"Found image at: {resolved_path} (original: {file_path})")
                                        break
                            
                            if resolved_path and os.path.exists(resolved_path):
                                file_path = resolved_path
                            try:
                                img = PILImage.open(file_path)
                                
                                image_width = 130
                                image_height = 78
                                
                                img = img.resize((int(image_width), int(image_height)), PILImage.Resampling.LANCZOS)
                                buf = BytesIO()
                                img.save(buf, format="PNG")
                                buf.seek(0)
                                pic_cell = Image(buf, width=image_width, height=image_height)
                                logger.info(f"Successfully loaded image: {file_path}")
                            except Exception as img_e:
                                logger.warning(f"Failed to process image {file_path}: {img_e}")
                                
                                placeholder_width = 130
                                placeholder_height = 78
                                placeholder = PILImage.new('RGB', (int(placeholder_width), int(placeholder_height)), color='gray')
                                draw = ImageDraw.Draw(placeholder)
                                draw.text((10, int(placeholder_height/2) - 10), "Error", fill='white')
                                buf = BytesIO()
                                placeholder.save(buf, format="PNG")
                                buf.seek(0)
                                pic_cell = Image(buf, width=placeholder_width, height=placeholder_height)
                            else:
                                logger.warning(f"Image file not found: {file_path}")
                        else:
                            logger.debug(f"No file_path for evidence {evidence_id}")

                        table_data.append([
                            pic_cell,
                            Paragraph(evidence_id, evidence_summary_style),
                            Paragraph(summary_text, evidence_summary_style),
                        ])

                    evidence_table = Table(
                        table_data,
                        colWidths=[USABLE_WIDTH * 0.25, USABLE_WIDTH * 0.25, USABLE_WIDTH * 0.5],
                        repeatRows=1
                    )
                    evidence_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER_BG),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F4F6F8")),
                        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
                        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (0, -1), "MIDDLE"),
                        ("VALIGN", (1, 1), (1, -1), "TOP"),
                        ("VALIGN", (2, 1), (2, -1), "TOP"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_ROW_BACKGROUND_ODD, colors.white]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
                        ("LINEBELOW", (0, -1), (-1, -1), 1, colors.black),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
                    ]))

                if index > 0:
                    estimated_height = 250 if evidence_table else 150
                    story.append(CondPageBreak(estimated_height))
                    person_section_elements = []

                    person_section_elements.append(poi_title_table)
                    person_section_elements.append(Spacer(1, 5))

                    person_section_elements.append(Spacer(1, 7))
                    person_section_elements.append(person_info_table)
                    person_section_elements.append(Spacer(1, 10))

                    if evidence_table:
                        person_section_elements.append(Spacer(1, 7))
                        person_section_elements.append(evidence_table)
                        person_section_elements.append(Spacer(1, 20))
                    else:
                        person_section_elements.append(Paragraph("<i>No evidence available</i>", poi_info_text_style))
                        person_section_elements.append(Spacer(1, 20))
                    
                    story.append(KeepTogether(person_section_elements))
                else:
                    story.append(Spacer(1, 10))
                    story.append(person_info_table)
                    story.append(Spacer(1, 10))
                    
                    if evidence_table:
                    story.append(Spacer(1, 7))
                    story.append(evidence_table)
                    story.append(Spacer(1, 20))
                else:
                    story.append(Paragraph("<i>No evidence available</i>", poi_info_text_style))
                    story.append(Spacer(1, 20))

        notes_value = case_notes.strip() if case_notes and case_notes.strip() else "<i>No notes available</i>"
        notes_data = [
            [Paragraph("Notes", notes_title_style)],
            [Paragraph(notes_value, notes_text_style)]
        ]
        notes_table = Table(notes_data, colWidths=[USABLE_WIDTH])
        notes_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F2F2")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_NOTES_BORDER),
        ]))
        notes_elements = [
            Spacer(1, 20),
            notes_table
        ]
        story.append(KeepTogether(notes_elements))
        has_notes = bool(case_notes and case_notes.strip())
        has_person_of_interest = bool(persons_of_interest and len(persons_of_interest) > 0)
        canvas_instance = [None]

        def canvas_maker(*args, **kwargs):
            logo_path = settings.LOGO_PATH
            if not os.path.isabs(logo_path):
                logo_path = os.path.join(os.getcwd(), logo_path.lstrip("./"))
            
            canvas_obj = CaseDetailPageCanvas(
                *args, case_title=case_title,
                case_id=case_id,
                export_time=export_time,
                case_status=case_status_raw,
                case_officer=case_officer,
                created_date=created_date,
                case_info_table_height=case_info_table_height,
                logo_path=logo_path,
                has_notes=has_notes,
                has_person_of_interest=has_person_of_interest,
                **kwargs
            )
            canvas_instance[0] = canvas_obj
            return canvas_obj

        doc.build(
            story,
            canvasmaker=canvas_maker
        )

        logger.info(f"Case detail PDF generated successfully: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error generating case detail PDF: {str(e)}", exc_info=True)
        raise

class SuspectDetailPageCanvas(canvas.Canvas):
    def __init__(self, *args, suspect_name: str = "", case_name: str = "", export_time: str = "",
                 suspect_status: str = "", investigator: str = "", created_date: str = "",
                 total_evidence: int = 0, logo_path: str = "", suspect_info_table_height: float = 63,
                 has_notes: bool = False, has_evidence: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.suspect_name = suspect_name
        self.case_name = case_name
        self.export_time = export_time
        self.suspect_status = suspect_status
        self.investigator = investigator
        self.created_date = created_date
        self.total_evidence = total_evidence
        self.logo_path = logo_path
        self.suspect_info_table_height = suspect_info_table_height
        self.has_notes = has_notes
        self.has_evidence = has_evidence
        self._page_number = 1
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()  # type: ignore[reportAttributeAccessIssue]
        self._page_number += 1

    def save(self):
        total_pages = len(self.pages)
        
        for page_number, page_dict in enumerate(self.pages, start=1):
            self.__dict__.update(page_dict)
            self._draw_header_footer(page_number, str(total_pages))
            super().showPage()
        
        super().save()

    def _draw_header_footer(self, current_page: int, total_pages_placeholder: str):
        page_width, page_height = A4
        left_margin = MARGIN_LEFT
        right_margin = MARGIN_RIGHT
        usable_width = page_width - left_margin - right_margin

        logo_w, logo_h = 175, 30
        logo_x = left_margin - 7
        logo_y = page_height - 30

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                img = PILImage.open(self.logo_path)
                ratio = min(logo_w / img.width, logo_h / img.height)
                final_w = img.width * ratio
                final_h = img.height * ratio
                buf = BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                reportlab_img = Image(buf, width=final_w, height=final_h)
                
                logo_y_aligned = logo_y - final_h + 12
                self.saveState()
                self.setStrokeColor(colors.white)
                self.setLineWidth(0)
                reportlab_img.drawOn(self, logo_x, logo_y_aligned)
                self.restoreState()
            except Exception:
                self.setFont("Helvetica-Bold", 14)
                self.setFillColor(COLOR_PRIMARY_BLUE)
                self.drawString(logo_x, logo_y + 10, "CYBER SENTINEL")
        else:
            self.setFont("Helvetica-Bold", 14)
            self.setFillColor(COLOR_PRIMARY_BLUE)
            self.drawString(logo_x, logo_y + 10, "CYBER SENTINEL")

        export_y = page_height - 35
        self.setFont("Helvetica", 10)
        self.setFillColor(COLOR_TEXT_GREY)
        export_text = f"Exported: {self.export_time}"
        self.drawRightString(page_width - right_margin, export_y, export_text)

        self.setStrokeColor(COLOR_HEADER_GREY)
        self.setLineWidth(1)
        self.line(left_margin, export_y - 8, page_width - right_margin, export_y - 8)

        is_last_page = False
        try:
            if total_pages_placeholder != "?":
                total_pages_int = int(total_pages_placeholder)
                is_last_page = (current_page == total_pages_int)
        except (ValueError, TypeError):
            is_last_page = False
        
        should_show_header = (
            current_page > 1 and 
            self.suspect_name and 
            (not is_last_page or (self.has_notes or self.has_evidence))
        )
        
        if should_show_header:
            col1_width = usable_width * 0.80
            col2_width = usable_width * 0.20
            info_y_start = page_height - 60
            title_y = info_y_start - 11
            line_height = 20

            self.setFont("Helvetica-Bold", 20)
            self.setFillColor(COLOR_TITLE)
            textobject = self.beginText(left_margin, title_y)
            textobject.setFont("Helvetica-Bold", 20)
            textobject.setFillColor(COLOR_TITLE)
            textobject.setTextOrigin(left_margin, title_y)

            words = self.suspect_name.split()
            line = ""
            title_lines_count = 0
            for word in words:
                test_line = line + word + " " if line else word + " "
                test_width = self.stringWidth(test_line, "Helvetica-Bold", 20)
                if test_width > col1_width and line:
                    textobject.textLine(line.strip())
                    line = word + " "
                    title_lines_count += 1
                else:
                    line = test_line
            if line:
                textobject.textLine(line.strip())
                title_lines_count += 1
            self.drawText(textobject)

            case_name_y = title_y - (title_lines_count * line_height) - 5
            self.setFont("Helvetica-Bold", 12)
            self.setFillColor(colors.black)
            self.drawString(left_margin, case_name_y, f"Case Related: {self.case_name}")

            if self.suspect_status:
                status_width = col2_width * 1.1
                status_height = 37
                status_x = left_margin + col1_width - 10
                
                status_y = title_y - (status_height / 2) - 18

                self.setStrokeColor(COLOR_BORDER_GREY)
                self.setLineWidth(1)
                self.setFillColor(colors.white)
                self.rect(status_x, status_y, status_width, status_height, stroke=1, fill=1)
                self.setFont("Helvetica-Bold", 16)
                self.setFillColor(colors.black)
                text_width = self.stringWidth(self.suspect_status, "Helvetica-Bold", 16)
                status_text_x = status_x + (status_width / 2) - (text_width / 2)
                status_text_y = status_y + (status_height / 2) - 3
                self.drawString(status_text_x, status_text_y, self.suspect_status)

           
            grid_suspect_y = page_height - NEW_TOP_MARGIN + 10
            investigator_y = grid_suspect_y - 5
            self.setFont("Helvetica", 12)
            self.setFillColor(colors.black)

            if self.investigator:
                self.drawString(left_margin, investigator_y, f"Investigator: {self.investigator}")

            if self.created_date:
                date_text = f"Date Created: {self.created_date}"
                date_x = page_width - right_margin - self.stringWidth(date_text, "Helvetica", 12)
                self.drawString(date_x, investigator_y, date_text)
        
        footer_y = 30
        line_y = footer_y + 25
        left_margin_footer = MARGIN_LEFT
        right_margin_footer = MARGIN_RIGHT
        usable_width_footer = page_width - left_margin_footer - right_margin_footer

        self.setFillColor(COLOR_HEADER_GREY)
        self.rect(left_margin_footer, line_y - 1, usable_width_footer, 2, fill=1, stroke=0)
        self.setStrokeColor(COLOR_BORDER_GREY)
        self.setLineWidth(2)
        self.line(left_margin_footer, line_y, left_margin_footer + usable_width_footer, line_y)

        footer_text = f"{self.case_name} - {self.suspect_name}"
        
        if total_pages_placeholder != "?" and total_pages_placeholder != "0":
            page_text = f"Page {current_page} of {total_pages_placeholder}"
        else:
            page_text = f"Page {current_page}"

        self.setFont("Helvetica", 10)
        self.setFillColor(colors.HexColor("#333333"))
        self.drawString(left_margin_footer, footer_y, footer_text)
        
        self.setFont("Helvetica", 12)
        self.setFillColor(colors.HexColor("#0C0C0C"))
        self.drawRightString(page_width - right_margin_footer, footer_y, page_text)

def generate_suspect_detail_pdf(suspect_data: dict, output_path: str) -> str:
    try:
        suspect_name = suspect_data.get("person_name") or "Unknown Suspect"
        case_name = suspect_data.get("case_name") or "Unknown Case"
        suspect_status_raw = suspect_data.get("suspect_status") or "Unknown"
        investigator = suspect_data.get("investigator") or "N/A"
        created_date = suspect_data.get("created_at_case") or "N/A"
        suspect_notes = (suspect_data.get("suspect_notes") or "").strip()
        export_time = get_wib_now().strftime("%d/%m/%Y %H:%M WIB")

        evidence_data = suspect_data.get("evidence", [])
        evidence_list = []
        if evidence_data and len(evidence_data) > 0:
            evidence_list = evidence_data[0].get("list_evidence", [])
        
        total_evidence = len(evidence_list)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=NEW_TOP_MARGIN,
            bottomMargin=MARGIN_BOTTOM,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "SuspectTitle", parent=styles["Heading1"], fontSize=20, textColor=COLOR_TITLE,
            spaceAfter=4, alignment=TA_LEFT, fontName="Helvetica-Bold", leftIndent=0
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", fontSize=14, textColor=colors.black, spaceAfter=7, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        case_related_style = ParagraphStyle(
            "CaseRelated", fontSize=12, textColor=colors.black, spaceAfter=7, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        status_style = ParagraphStyle(
            "StatusStyle", fontSize=16, textColor=colors.black, spaceAfter=7, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )
        investigator_style = ParagraphStyle(
            "Investigator", fontSize=12, textColor=colors.black, spaceAfter=6, alignment=TA_LEFT, fontName="Helvetica", leftIndent=-5
        )
        date_created_style = ParagraphStyle(
            "DateCreated", fontSize=12, textColor=colors.black, spaceAfter=6, alignment=TA_RIGHT, fontName="Helvetica"
        )
        notes_title_style = ParagraphStyle(
            "NotesTitle", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=8, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        notes_text_style = ParagraphStyle(
            "NotesText", fontSize=12, leading=16, alignment=TA_LEFT, textColor=colors.HexColor("#000000"), fontName="Helvetica"
        )
        table_header_style = ParagraphStyle(
            "TableHeader", parent=styles["Normal"], fontSize=12, alignment=TA_LEFT,
            fontName="Helvetica", leading=13, textColor=colors.HexColor("#F4F6F8")
        )
        evidence_summary_style = ParagraphStyle(
            "EvidenceSummary", fontSize=12, leading=14, alignment=TA_LEFT, textColor=colors.HexColor("#0C0C0C"), fontName="Helvetica"
        )

        story = []
        col1_width = USABLE_WIDTH * 0.80
        col2_width = USABLE_WIDTH * 0.20
        status_bg_color = colors.white
        status_text_color = colors.black

        story.append(Spacer(1, -140))

        button_height = 37
        status_button_data = [[Paragraph(f"<b>{suspect_status_raw}</b>", status_style)]]
        status_button_table = Table(
            status_button_data, colWidths=[col2_width * 1.1], rowHeights=[button_height]
        )
        status_button_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), status_bg_color),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), -5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        suspect_info_data = [
            [Paragraph(suspect_name, title_style), status_button_table],
            [Paragraph(f"<b>Case Related:</b> {case_name}", case_related_style), ""]
        ]
        suspect_info_table = Table(suspect_info_data, colWidths=[col1_width, col2_width])
        suspect_info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (0, 0), "TOP"),
            ("VALIGN", (0, 1), (0, 1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (0, 0), 20),
            ("TOPPADDING", (0, 1), (0, 1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("SPAN", (1, 0), (1, 1)),
            ("VALIGN", (1, 0), (1, 1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 1), "CENTER"),
            ("RIGHTPADDING", (1, 0), (1, 1), 15),
            ("TOPPADDING", (1, 0), (1, 1), 25),
        ]))
        story.append(suspect_info_table)
        story.append(Spacer(1, 4))

        title_row_height = max(
            (title_style.fontSize * 1.2 + title_style.spaceAfter + 20),
            button_height + 2
        )
        case_row_height = subtitle_style.fontSize * 1.2 + subtitle_style.spaceAfter
        suspect_info_table_height = title_row_height + case_row_height + 2

        story.append(Spacer(1, 20))
        investigator_table = Table([[Paragraph(f"Investigator: {investigator}", investigator_style)]],
                                   colWidths=[USABLE_WIDTH * 0.5])
        date_created_table = Table([[Paragraph(f"Date Created: {created_date}", date_created_style)]],
                                   colWidths=[USABLE_WIDTH * 0.5])
        suspect_meta_data = [[investigator_table, date_created_table]]
        suspect_meta_table = Table(suspect_meta_data, colWidths=[USABLE_WIDTH * 0.5, USABLE_WIDTH * 0.5])
        suspect_meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
            ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ]))
        story.append(suspect_meta_table)
        story.append(Spacer(1, 10))
        total_evidence_data = [
            [Paragraph("Total Evidence", investigator_style), Paragraph(f": {total_evidence} Evidence", investigator_style)]
        ]
        total_evidence_table = Table(total_evidence_data, colWidths=[USABLE_WIDTH * 0.20, USABLE_WIDTH * 0.80])
        total_evidence_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(total_evidence_table)
        story.append(Spacer(1, 16))

        if evidence_list:
            table_data = [[
                Paragraph('Picture', table_header_style),
                Paragraph('Evidence ID', table_header_style),
                Paragraph('Summary', table_header_style),
            ]]

            picture_col_width = USABLE_WIDTH * 0.25
            
            for ev in evidence_list:
                evidence_id = str(ev.get("evidence_number") or ev.get("id") or "N/A")
                summary_text = str(ev.get("evidence_summary") or "No summary available")
                file_path = ev.get("file_path")
                pic_cell = Paragraph("<i>No image</i>", evidence_summary_style)

                if file_path and os.path.exists(file_path):
                    try:
                        img = PILImage.open(file_path)
                        
                        image_width = 130
                        image_height = 78
                        
                        img = img.resize((int(image_width), int(image_height)), PILImage.Resampling.LANCZOS)
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        pic_cell = Image(buf, width=image_width, height=image_height)
                    except Exception as img_e:
                        logger.warning(f"Failed to process image {file_path}: {img_e}")
                        
                        placeholder_width = 130
                        placeholder_height = 78
                        placeholder = PILImage.new('RGB', (int(placeholder_width), int(placeholder_height)), color='gray')
                        draw = ImageDraw.Draw(placeholder)
                        draw.text((10, int(placeholder_height/2) - 10), "Error", fill='white')
                        buf = BytesIO()
                        placeholder.save(buf, format="PNG")
                        buf.seek(0)
                        pic_cell = Image(buf, width=placeholder_width, height=placeholder_height)

                table_data.append([
                    pic_cell,
                    Paragraph(evidence_id, evidence_summary_style),
                    Paragraph(summary_text, evidence_summary_style),
                ])

            evidence_table = Table(
                table_data,
                colWidths=[USABLE_WIDTH * 0.25, USABLE_WIDTH * 0.25, USABLE_WIDTH * 0.5],
                repeatRows=1
            )
            evidence_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER_BG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F4F6F8")),
                ("ALIGN", (0, 0), (-1, 0), "LEFT"),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (0, -1), "MIDDLE"),
                ("VALIGN", (1, 1), (1, -1), "TOP"),
                ("VALIGN", (2, 1), (2, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_ROW_BACKGROUND_ODD, colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
                ("LINEBELOW", (0, -1), (-1, -1), 1, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
            ]))

            story.append(Spacer(1, 7))
            story.append(evidence_table)
            story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("<i>No evidence available</i>", evidence_summary_style))
            story.append(Spacer(1, 20))

        notes_value = suspect_notes.strip() if suspect_notes and suspect_notes.strip() else "<i>No notes available</i>"
        notes_data = [
            [Paragraph("Notes", notes_title_style)],
            [Paragraph(notes_value, notes_text_style)]
        ]
        notes_table = Table(notes_data, colWidths=[USABLE_WIDTH])
        notes_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_ROW_BACKGROUND_ODD),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_NOTES_BORDER),
        ]))
        notes_elements = [
            Spacer(1, 20),
            notes_table
        ]
        story.append(KeepTogether(notes_elements))

        has_notes = bool(suspect_notes and suspect_notes.strip())
        has_evidence = bool(evidence_list and len(evidence_list) > 0)
        
        canvas_instance = [None]

        def canvas_maker(*args, **kwargs):
            logo_path = settings.LOGO_PATH
            if not os.path.isabs(logo_path):
                logo_path = os.path.join(os.getcwd(), logo_path.lstrip("./"))
            
            canvas_obj = SuspectDetailPageCanvas(
                *args, suspect_name=suspect_name,
                case_name=case_name,
                export_time=export_time,
                suspect_status=suspect_status_raw,
                investigator=investigator,
                created_date=created_date,
                total_evidence=total_evidence,
                suspect_info_table_height=suspect_info_table_height,
                logo_path=logo_path,
                has_notes=has_notes,
                has_evidence=has_evidence,
                **kwargs
            )
            canvas_instance[0] = canvas_obj
            return canvas_obj

        doc.build(
            story,
            canvasmaker=canvas_maker
        )

        logger.info(f"Suspect detail PDF generated successfully: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error generating suspect detail PDF: {str(e)}", exc_info=True)
        raise


class EvidenceDetailPageCanvas(canvas.Canvas):
    def __init__(self, *args, case_title: str = "", case_id: str = "", export_time: str = "",
                 case_officer: str = "", created_date: str = "", person_related: str = "",
                 evidence_source: str = "", logo_path: str = "", evidence_number: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.case_title = case_title
        self.case_id = case_id
        self.export_time = export_time
        self.case_officer = case_officer
        self.created_date = created_date
        self.person_related = person_related
        self.evidence_source = evidence_source
        self.logo_path = logo_path
        self.evidence_number = evidence_number
        self._page_number = 1
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()  # type: ignore[reportAttributeAccessIssue]
        self._page_number += 1

    def save(self):
        total_pages = len(self.pages)
        
        for page_number, page_dict in enumerate(self.pages, start=1):
            self.__dict__.update(page_dict)
            self._draw_header_footer(page_number, str(total_pages))
            super().showPage()
        
        super().save()

    def _draw_header_footer(self, current_page: int, total_pages_placeholder: str):
        page_width, page_height = A4
        left_margin = MARGIN_LEFT
        right_margin = MARGIN_RIGHT
        usable_width = page_width - left_margin - right_margin

        logo_w, logo_h = 175, 30
        logo_x = left_margin - 7
        header_y = page_height - 30
        logo_y = header_y

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                img = PILImage.open(self.logo_path)
                final_w = logo_w
                final_h = logo_h
                buf = BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                reportlab_img = Image(buf, width=final_w, height=final_h)
                
                logo_y_aligned = logo_y - final_h + 12
                self.saveState()
                self.setStrokeColor(colors.white)
                self.setLineWidth(0)
                reportlab_img.drawOn(self, logo_x, logo_y_aligned)
                self.restoreState()
            except Exception:
                self.setFont("Helvetica-Bold", 14)
                self.setFillColor(COLOR_PRIMARY_BLUE)
                self.drawString(logo_x, logo_y + 10, "CYBER SENTINEL")
        else:
            self.setFont("Helvetica-Bold", 14)
            self.setFillColor(COLOR_PRIMARY_BLUE)
            self.drawString(logo_x, logo_y + 10, "CYBER SENTINEL")

        self.setFont("Helvetica", 10)
        self.setFillColor(colors.HexColor("#333333"))
        self.drawRightString(page_width - right_margin, header_y - 5, f"Exported: {self.export_time}")

        if current_page > 1:
            info_y = header_y - 45
            
            self.setFont("Helvetica-Bold", 20)
            self.setFillColor(colors.HexColor("#0C0C0C"))
            self.drawString(left_margin, info_y, self.evidence_number)
            
            case_related_y = info_y - 20
            self.setFont("Helvetica-Bold", 12)
            self.setFillColor(colors.HexColor("#333333"))
            self.drawString(left_margin, case_related_y, f"Case Related : {self.case_title}")
            
            investigator_date_y = case_related_y - 40
            self.setFont("Helvetica", 12)
            self.setFillColor(colors.HexColor("#0C0C0C"))
            self.drawString(left_margin, investigator_date_y, f"Investigator: {self.case_officer}")
            self.drawRightString(page_width - right_margin, investigator_date_y, f"Date Created: {self.created_date}")

        footer_text = f"{self.case_title} - {self.case_id}"
        self.setFont("Helvetica", 10)
        self.setFillColor(colors.HexColor("#333333"))
        self.drawString(left_margin, 30, footer_text)

        page_label = f"Page {current_page}"
        self.setFont("Helvetica", 12)
        self.setFillColor(colors.HexColor("#0C0C0C"))
        self.drawRightString(page_width - right_margin, 30, page_label)

def generate_evidence_detail_pdf(evidence_data: dict, output_path: str) -> str:
    try:
        evidence_info = evidence_data.get("evidence", {})
        case_info = evidence_data.get("case", {})
        suspect_info = evidence_data.get("suspect", {})
        custody_reports = evidence_data.get("custody_reports", [])
        
        case_title = case_info.get("title") or "Unknown Case"
        case_id = str(case_info.get("case_number") or case_info.get("id") or "N/A")
        evidence_number = str(evidence_info.get("evidence_number") or "N/A")
        case_officer = case_info.get("case_officer") or evidence_info.get("investigator") or "N/A"
        created_date = case_info.get("created_date") or "N/A"
        person_related = suspect_info.get("name") or "N/A"
        evidence_source = evidence_info.get("source") or custody_reports[0].get("evidence_source") if custody_reports else "N/A"
        evidence_description = evidence_info.get("description") or "No description available"
        export_time = get_wib_now().strftime("%d/%m/%Y %H:%M WIB")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=NEW_TOP_MARGIN,
            bottomMargin=MARGIN_BOTTOM,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CaseTitle", parent=styles["Heading1"], fontSize=20, textColor=COLOR_TITLE,
            spaceAfter=4, alignment=TA_LEFT, fontName="Helvetica-Bold", leftIndent=0
        )
        case_id_style = ParagraphStyle(
            "CaseID", fontSize=12, textColor=colors.HexColor("#333333"), spaceAfter=7, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        investigator_style = ParagraphStyle(
            "Investigator", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=6, alignment=TA_LEFT, fontName="Helvetica", leftIndent=-5
        )
        date_created_style = ParagraphStyle(
            "DateCreated", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=6, alignment=TA_RIGHT, fontName="Helvetica"
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=0, alignment=TA_LEFT, fontName="Helvetica"
        )
        acquisition_investigator_name_subtitle_style = ParagraphStyle(
            "Subtitle", fontSize=100, textColor=colors.HexColor("#0C0C0C"), spaceAfter=0, alignment=TA_LEFT, fontName="Helvetica"
        )
        chain_of_custody_subtitle_style = ParagraphStyle(
            "ChainOfCustodySubtitle", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=0, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        
        summary_subtitle_style = ParagraphStyle(
            "SummarySubtitle", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=0, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        summary_text_style = ParagraphStyle(
            "SummaryText", fontSize=12, leading=16, alignment=TA_JUSTIFY, textColor=colors.HexColor("#000000"), fontName="Helvetica"
        )
        table_header_style = ParagraphStyle(
            "TableHeader", parent=styles["Normal"], fontSize=12, alignment=TA_LEFT,
            fontName="Helvetica", leading=13, textColor=colors.HexColor("#F4F6F8")
        )
        table_text_style = ParagraphStyle(
            "TableText", fontSize=12, leading=14, alignment=TA_LEFT, textColor=colors.HexColor("#0C0C0C"), fontName="Helvetica"
        )
    
        person_source_style = ParagraphStyle(
            "PersonSource", fontSize=12, leading=14, alignment=TA_LEFT, textColor=colors.HexColor("#0C0C0C"), fontName="Helvetica"
        )

        story = []
        story.append(Spacer(1, -140))
        story.append(Spacer(1, 20))

        evidence_number_style = ParagraphStyle(
            "EvidenceNumber", fontSize=20, textColor=colors.HexColor("#0C0C0C"), spaceAfter=4, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        evidence_number_data = [
            [Paragraph(evidence_number, evidence_number_style)]
        ]
        evidence_number_table = Table(evidence_number_data, colWidths=[USABLE_WIDTH])
        evidence_number_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(evidence_number_table)
        story.append(Spacer(1, 12))
        story.append(Spacer(1, 5))
        
        case_related_style = ParagraphStyle(
            "CaseRelated", fontSize=12, textColor=colors.HexColor("#333333"), spaceAfter=7, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        
        case_related_data = [
            [Paragraph(f"Case Related : {case_title}", case_related_style)]
        ]
        case_related_table = Table(case_related_data, colWidths=[USABLE_WIDTH])
        case_related_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(case_related_table)
        story.append(Spacer(1, 4))

        story.append(Spacer(1, 20))
        investigator_table = Table([[Paragraph(f"Investigator: {case_officer}", investigator_style)]],
                                   colWidths=[USABLE_WIDTH * 0.5])
        date_created_table = Table([[Paragraph(f"Date Created: {created_date}", date_created_style)]],
                                   colWidths=[USABLE_WIDTH * 0.5])
        case_meta_data = [[investigator_table, date_created_table]]
        case_meta_table = Table(case_meta_data, colWidths=[USABLE_WIDTH * 0.5, USABLE_WIDTH * 0.5])
        case_meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
            ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ]))
        story.append(case_meta_table)
        story.append(Spacer(1, 16))

        person_related_data = [
            [Paragraph("Person Related", person_source_style), Paragraph(f": {person_related}", person_source_style)]
        ]
        person_related_table = Table(person_related_data, colWidths=[USABLE_WIDTH * 0.20, USABLE_WIDTH * 0.80])
        person_related_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (1, 0), (1, -1), -5),
        ]))
        story.append(person_related_table)
        
        source_data = [
            [Paragraph("Source", person_source_style), Paragraph(f": {evidence_source}", person_source_style)]
        ]
        source_table = Table(source_data, colWidths=[USABLE_WIDTH * 0.20, USABLE_WIDTH * 0.80])
        source_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (1, 0), (1, -1), -5),
        ]))
        story.append(source_table)
        story.append(Spacer(1, 10))
        
        evidence_image = None
        file_path = evidence_info.get("file_path")
        if file_path:
            resolved_path = None
            if os.path.isabs(file_path):
                resolved_path = file_path if os.path.exists(file_path) else None
            else:
                file_path_clean = file_path.lstrip("./")
                base_name = os.path.basename(file_path_clean)
                
                possible_paths = [
                    os.path.join(os.getcwd(), file_path_clean),
                    os.path.join(os.getcwd(), settings.UPLOAD_DIR.lstrip("./"), file_path_clean),
                    os.path.join(os.getcwd(), settings.UPLOAD_DIR.lstrip("./"), base_name),
                    os.path.join(os.getcwd(), "data", "uploads", file_path_clean),
                    os.path.join(os.getcwd(), "data", "uploads", base_name),
                    os.path.join(os.getcwd(), "data", "evidence", base_name),
                ]
                
                for path in possible_paths:
                    if path and os.path.exists(path):
                        resolved_path = path
                        break
            
            if resolved_path and os.path.exists(resolved_path):
                try:
                    img = PILImage.open(resolved_path)
                    image_width = 130
                    image_height = 78
                    img = img.resize((int(image_width), int(image_height)), PILImage.Resampling.LANCZOS)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    evidence_image = Image(buf, width=image_width, height=image_height)
                except Exception as e:
                    logger.warning(f"Failed to load evidence image: {e}")

        summary_table_data = []
        
        summary_table_data.append([Paragraph("Summary", summary_subtitle_style), ""])
        
        if evidence_image:
            summary_table_data.append([evidence_image, Paragraph(evidence_description, summary_text_style)])
        else:
            summary_table_data.append(["", Paragraph(evidence_description, summary_text_style)])
        
        col_width_1 = USABLE_WIDTH * 0.5
        col_width_2 = USABLE_WIDTH * 0.5
        summary_table = Table(summary_table_data, colWidths=[col_width_1, col_width_2])
        summary_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#466086")),
            ("SPAN", (0, 0), (1, 0)),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (1, 1), (1, 1), -120),
            ("TOPPADDING", (0, 0), (0, 0), 8),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (0, -2), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("VALIGN", (1, 1), (1, 1), "TOP"),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        custody_types = ["Acquisition", "Preparation", "Extraction", "Analysis"]
        custody_timeline_data = []
        
        for custody_type in custody_types:
            report = next((r for r in custody_reports if r.get("custody_type", "").lower() == custody_type.lower()), None)
            if report:
                date_str = report.get("created_at", "")
                if isinstance(date_str, str):
                    try:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        month_names = {
                            1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                            9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                        }
                        month_name = month_names.get(dt.month, dt.strftime("%B"))
                        date_str = f"{dt.day} {month_name} {dt.year}, {dt.strftime('%H:%M')}"
                    except:
                        date_str = "N/A"
                else:
                    if hasattr(date_str, 'strftime'):
                        month_names = {
                            1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                            9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                        }
                        month_name = month_names.get(date_str.month, date_str.strftime("%B"))
                        date_str = f"{date_str.day} {month_name} {date_str.year}, {date_str.strftime('%H:%M')}"
                    else:
                        date_str = "N/A"
                investigator = report.get("created_by", "N/A")
            else:
                date_str = "N/A"
                investigator = "N/A"
            
            custody_timeline_data.append({
                "type": custody_type,
                "date": date_str,
                "name": investigator
            })
        
        chain_table_data = []
        chain_table_data.append([Paragraph("Chain of Custody", chain_of_custody_subtitle_style)])

        if custody_timeline_data:
            timeline_width = USABLE_WIDTH - 16 - 70
            timeline = TimelineFlowable(custody_timeline_data, timeline_width, height=120)
            chain_table_data.append([timeline])
        
        chain_table = Table(chain_table_data, colWidths=[USABLE_WIDTH])
        chain_table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (0, 0), 8),
            ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#466086")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(chain_table)
        story.append(Spacer(1, 20))

        evidence_source_value = evidence_source or "N/A"
        evidence_type_value = evidence_info.get('evidence_type', 'N/A') or "N/A"
        evidence_detail_value = evidence_info.get('evidence_detail', 'N/A') or "N/A"
        
        evidence_details_table_data = [
            [
                Paragraph(f"Evidence Source: {evidence_source_value}", table_text_style),
                Paragraph(f"Evidence Type: {evidence_type_value}", table_text_style),
                Paragraph(f"Evidence Detail: {evidence_detail_value}", table_text_style),
            ]
        ]
        
        evidence_details_table = Table(evidence_details_table_data, colWidths=[USABLE_WIDTH/3, USABLE_WIDTH/3, USABLE_WIDTH/3])
        evidence_details_table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (2, 0), (2, 0), -55),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(evidence_details_table)
        story.append(Spacer(1, 20))

        for custody_type in custody_types:
            report = next((r for r in custody_reports if r.get("custody_type", "").lower() == custody_type.lower()), None)
            if not report:
                continue

            date_str = report.get("created_at", "")
            if isinstance(date_str, str):
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_str = dt.strftime("%d %B %Y, %H:%M")
                except:
                    date_str = "N/A"
            else:
                date_str = date_str.strftime("%d %B %Y, %H:%M") if hasattr(date_str, 'strftime') else str(date_str)
            investigator = report.get("created_by", "N/A")
            
            if custody_type.lower() == "acquisition":
                date_style = ParagraphStyle(
                    "DateStyle", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=0, alignment=TA_RIGHT, fontName="Helvetica"
                )
                investigator_style = ParagraphStyle(
                    "InvestigatorStyle", fontSize=10, textColor=colors.HexColor("#545454"), spaceAfter=0, alignment=TA_RIGHT, fontName="Helvetica"
                )
                
                date_investigator_table_data = [
                    [Paragraph(date_str, date_style)],
                    [Paragraph(investigator, investigator_style)]
                ]
                date_investigator_table = Table(date_investigator_table_data, colWidths=[USABLE_WIDTH * 0.3])
                date_investigator_table.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 17),
                    ("TOPPADDING", (0, 0), (0, 0), 0),
                    ("TOPPADDING", (0, 1), (0, 1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                section_title_data = [
                    [Paragraph(custody_type, subtitle_style), date_investigator_table]
                ]
            else:
                date_investigator_text = f"{date_str} {investigator}"
                date_investigator_style = ParagraphStyle(
                    "DateInvestigator", fontSize=12, textColor=colors.HexColor("#0C0C0C"), spaceAfter=0, alignment=TA_RIGHT, fontName="Helvetica"
                )
                section_title_data = [
                    [Paragraph(custody_type, subtitle_style), Paragraph(date_investigator_text, date_investigator_style)]
                ]
            section_title_table = Table(
                section_title_data,
                colWidths=[USABLE_WIDTH * 0.7, USABLE_WIDTH * 0.3]
            )
            section_title_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (1, 0), (1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(section_title_table)
            story.append(Spacer(1, 10))

            details = report.get("details", {})
            
            if custody_type.lower() == "acquisition" and details:
                    steps_title_table = Table(
                        [[Paragraph("Steps for Confiscating Evidence", acquisition_investigator_name_subtitle_style)]],
                        colWidths=[USABLE_WIDTH]
                    )
                    steps_title_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), COLOR_TABLE_HEADER_BG),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#F4F6F8")),
                    ]))
                    story.append(steps_title_table)
                    story.append(Spacer(1, 5))
                    
                    steps_table_data = [[
                        Paragraph("Image", table_header_style),
                        Paragraph("Steps for Confiscating Evidence", table_header_style)
                    ]]

                    steps_list = details if isinstance(details, list) else details.get("steps", [])
                    for step_item in steps_list:
                        if isinstance(step_item, dict):
                            step_text = step_item.get("steps", step_item.get("text", ""))
                            step_image_path = step_item.get("photo", step_item.get("image_path"))
                        else:
                            step_text = str(step_item)
                            step_image_path = None
                        
                        pic_cell = Paragraph("<i>Image not available</i>", table_text_style)
                        if step_image_path:
                            resolved_path = None
                            if os.path.isabs(step_image_path):
                                resolved_path = step_image_path if os.path.exists(step_image_path) else None
                            else:
                                file_path_clean = step_image_path.lstrip("./")
                                base_name = os.path.basename(file_path_clean)
                                
                                possible_paths = [
                                    os.path.join(os.getcwd(), file_path_clean),
                                    os.path.join(os.getcwd(), settings.UPLOAD_DIR.lstrip("./"), file_path_clean),
                                    os.path.join(os.getcwd(), settings.UPLOAD_DIR.lstrip("./"), base_name),
                                    os.path.join(os.getcwd(), "data", "uploads", file_path_clean),
                                    os.path.join(os.getcwd(), "data", "uploads", base_name),
                                    os.path.join(os.getcwd(), "data", "evidence", base_name),
                                ]
                                
                                for path in possible_paths:
                                    if path and os.path.exists(path):
                                        resolved_path = path
                                        break
                            
                            if resolved_path and os.path.exists(resolved_path):
                                try:
                                    img = PILImage.open(resolved_path)
                                    image_width = 130
                                    image_height = 78
                                    img = img.resize((int(image_width), int(image_height)), PILImage.Resampling.LANCZOS)
                                    buf = BytesIO()
                                    img.save(buf, format="PNG")
                                    buf.seek(0)
                                    pic_cell = Image(buf, width=image_width, height=image_height)
                                except Exception as e:
                                    logger.warning(f"Failed to load step image: {e}")
                        
                        steps_table_data.append([pic_cell, Paragraph(step_text, table_text_style)])
                    
                    steps_table = Table(steps_table_data, colWidths=[USABLE_WIDTH * 0.3, USABLE_WIDTH * 0.7])
                    steps_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER_BG),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F4F6F8")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ]))
                    story.append(steps_table)
                    story.append(Spacer(1, 20))
            
            if isinstance(details, dict):
                if custody_type.lower() == "preparation" and details:
                    tools_title_table = Table(
                        [[Paragraph("Tools and Investigation Hypothesis", subtitle_style)]],
                        colWidths=[USABLE_WIDTH]
                    )
                    tools_title_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]))
                    story.append(tools_title_table)
                    story.append(Spacer(1, 5))

                    tools_data = [["Tools", "Investigation Hypothesis"]]
                    tools_list = details if isinstance(details, list) else details.get("tools", [])
                    for item in tools_list:
                        if isinstance(item, dict):
                            tool_name = item.get("tools", item.get("name", ""))
                            hypothesis = item.get("hypothesis", "")
                        else:
                            tool_name = str(item) if item else ""
                            hypothesis = ""
                        tools_data.append([
                            Paragraph(tool_name, table_text_style),
                            Paragraph(hypothesis, table_text_style)
                        ])
                    
                    tools_table = Table(tools_data, colWidths=[USABLE_WIDTH * 0.3, USABLE_WIDTH * 0.7])
                    tools_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER_BG),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F4F6F8")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]))
                    story.append(tools_table)
                    story.append(Spacer(1, 20))
                
                elif custody_type.lower() == "extraction" and details:
                    files_title_table = Table(
                        [[Paragraph("File Details", subtitle_style)]],
                        colWidths=[USABLE_WIDTH]
                    )
                    files_title_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]))
                    story.append(files_title_table)
                    story.append(Spacer(1, 5))

                    files_data = [["File Size", "File Name"]]
                    if isinstance(details, dict) and "extraction_file" in details:
                        file_size = details.get("file_size", "N/A")
                        file_name = details.get("file_name", "N/A")
                        files_data.append([
                            Paragraph(str(file_size), table_text_style),
                            Paragraph(file_name, table_text_style)
                        ])
                    elif isinstance(details, dict) and "files" in details:
                        for file_info in details.get("files", []):
                            file_size = file_info.get("size", "N/A")
                            file_name = file_info.get("name", "N/A")
                            files_data.append([
                                Paragraph(str(file_size), table_text_style),
                                Paragraph(file_name, table_text_style)
                            ])
                    else:
                        file_size = evidence_info.get("file_size", 0)
                        if file_size:
                            size_name = ("B", "KB", "MB", "GB", "TB")
                            i = 0
                            p = 1024
                            while file_size >= p and i < len(size_name) - 1:
                                file_size /= p
                                i += 1
                            file_size_str = f"{file_size:.2f} {size_name[i]}"
                        else:
                            file_size_str = "N/A"
                        file_name = evidence_info.get("file_path", "N/A")
                        if file_name and file_name != "N/A":
                            file_name = os.path.basename(file_name)
                        files_data.append([
                            Paragraph(file_size_str, table_text_style),
                            Paragraph(file_name, table_text_style)
                        ])
                    
                    files_table = Table(files_data, colWidths=[USABLE_WIDTH * 0.3, USABLE_WIDTH * 0.7])
                    files_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER_BG),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F4F6F8")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]))
                    story.append(files_table)
                    story.append(Spacer(1, 20))
                
                elif custody_type.lower() == "analysis" and details:
                    results_title_table = Table(
                        [[Paragraph("Investigation Hypothesis and Analysis Result", subtitle_style)]],
                        colWidths=[USABLE_WIDTH]
                    )
                    results_title_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]))
                    story.append(results_title_table)
                    story.append(Spacer(1, 5))

                    results_data = [["Investigation Hypothesis", "Analysis Result"]]
                    results_list = details if isinstance(details, list) else details.get("results", [])
                    for item in results_list:
                        if isinstance(item, dict):
                            hypothesis = item.get("hypothesis", "")
                            analysis_result = item.get("result", "")
                        else:
                            hypothesis = str(item) if item else ""
                            analysis_result = ""
                        results_data.append([
                            Paragraph(hypothesis, table_text_style),
                            Paragraph(analysis_result, table_text_style)
                        ])
                    
                    results_table = Table(results_data, colWidths=[USABLE_WIDTH * 0.5, USABLE_WIDTH * 0.5])
                    results_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER_BG),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F4F6F8")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]))
                    story.append(results_table)
                    story.append(Spacer(1, 20))

            story.append(Spacer(1, 10))
            summary_section_title_table = Table(
                [[Paragraph("Summary", subtitle_style)]],
                colWidths=[USABLE_WIDTH]
            )
            summary_section_title_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CCCCCC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(summary_section_title_table)
            story.append(Spacer(1, 5))
            story.append(Paragraph(evidence_description, summary_text_style))
            story.append(Spacer(1, 20))

        logo_path = settings.LOGO_PATH
        if not os.path.isabs(logo_path):
            logo_path = os.path.join(os.getcwd(), logo_path.lstrip("./"))

        canvas_instance = [None]

        def canvas_maker(*args, **kwargs):
            canvas_obj = EvidenceDetailPageCanvas(
                *args, case_title=case_title,
                case_id=case_id,
                export_time=export_time,
                case_officer=case_officer,
                created_date=created_date,
                person_related=person_related,
                evidence_source=evidence_source,
                logo_path=logo_path,
                evidence_number=evidence_number,
                **kwargs
            )
            canvas_instance[0] = canvas_obj
            return canvas_obj

        doc.build(
            story,
            canvasmaker=canvas_maker
        )

        logger.info(f"Evidence detail PDF generated successfully: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error generating evidence detail PDF: {str(e)}", exc_info=True)
        raise