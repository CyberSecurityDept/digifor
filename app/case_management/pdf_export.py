import os
import logging
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, CondPageBreak
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
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

        logo_w, logo_h = 130, 45
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
        self.setFont("Helvetica-Bold", 10)
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
            self.case_id and 
            (not is_last_page or (self.has_notes or self.has_person_of_interest))
        )
        
        if should_show_header:
            col1_width = usable_width * 0.80
            col2_width = usable_width * 0.20
            info_y_start = page_height - 60
            title_y = info_y_start - 11
            line_height = 20

            self.setFont("Helvetica-Bold", 17)
            self.setFillColor(COLOR_TITLE)
            textobject = self.beginText(left_margin, title_y)
            textobject.setFont("Helvetica-Bold", 17)
            textobject.setFillColor(COLOR_TITLE)
            textobject.setTextOrigin(left_margin, title_y)

            words = self.case_title.split()
            line = ""
            title_lines_count = 0
            for word in words:
                test_line = line + word + " " if line else word + " "
                test_width = self.stringWidth(test_line, "Helvetica-Bold", 17)
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
            self.setFont("Helvetica-Bold", 14)
            self.setFillColor(COLOR_TITLE)
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
            self.setFont("Helvetica", 14)
            self.setFillColor(colors.black)

            if self.case_officer:
                self.drawString(left_margin, investigator_y, f"Investigator: {self.case_officer}")

            if self.created_date:
                date_text = f"Date Created: {self.created_date}"
                date_x = page_width - right_margin - self.stringWidth(date_text, "Helvetica", 14)
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
            "CaseTitle", parent=styles["Heading1"], fontSize=17, textColor=COLOR_TITLE,
            spaceAfter=4, alignment=TA_LEFT, fontName="Helvetica-Bold", leftIndent=0
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", fontSize=14, textColor=colors.black, spaceAfter=7, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        status_style = ParagraphStyle(
            "StatusStyle", fontSize=16, textColor=colors.black, spaceAfter=7, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )
        investigator_style = ParagraphStyle(
            "Investigator", fontSize=14, textColor=colors.black, spaceAfter=6, alignment=TA_LEFT, fontName="Helvetica", leftIndent=-5
        )
        date_created_style = ParagraphStyle(
            "DateCreated", fontSize=14, textColor=colors.black, spaceAfter=6, alignment=TA_RIGHT, fontName="Helvetica"
        )
        description_title_style = ParagraphStyle(
            "DescriptionTitle", fontSize=14, textColor=COLOR_TITLE, spaceAfter=0, alignment=TA_LEFT, fontName="Helvetica"
        )
        description_text_style = ParagraphStyle(
            "DescriptionText", fontSize=11, leading=16, alignment=TA_JUSTIFY, textColor=COLOR_TITLE, fontName="Helvetica"
        )
        poi_title_style = ParagraphStyle(
            "PersonOfInterestTitle", fontSize=14, textColor=COLOR_TITLE, spaceAfter=0, alignment=TA_LEFT, fontName="Helvetica"
        )
        poi_info_text_style = ParagraphStyle(
            "PersonInfoText", fontSize=11, leading=16, alignment=TA_LEFT, textColor=COLOR_TITLE, fontName="Helvetica"
        )
        notes_title_style = ParagraphStyle(
            "NotesTitle", fontSize=14, textColor=COLOR_TITLE, spaceAfter=8, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        notes_text_style = ParagraphStyle(
            "NotesText", fontSize=11, leading=16, alignment=TA_LEFT, textColor=COLOR_TITLE, fontName="Helvetica"
        )
        table_header_style = ParagraphStyle(
            "TableHeader", parent=styles["Normal"], fontSize=11, alignment=TA_LEFT,
            fontName="Helvetica-Bold", leading=13, textColor=colors.white
        )
        evidence_summary_style = ParagraphStyle(
            "EvidenceSummary", fontSize=10, leading=14, alignment=TA_LEFT, textColor=colors.black, fontName="Helvetica"
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
            [Paragraph(case_title, title_style), status_button_table],
            [Paragraph(f"<b>Case ID:</b> {case_id}", subtitle_style), ""]
        ]
        case_info_table = Table(case_info_data, colWidths=[col1_width, col2_width])
        case_info_table.setStyle(TableStyle([
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
        story.append(case_info_table)
        story.append(Spacer(1, 4))

        title_row_height = max(
            (title_style.fontSize * 1.2 + title_style.spaceAfter + 20),
            button_height + 2
        )
        case_id_row_height = subtitle_style.fontSize * 1.2 + subtitle_style.spaceAfter
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
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_SECTION_BACKGROUND),
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
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_SECTION_BACKGROUND),
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
                [Paragraph("Name", poi_info_text_style), Paragraph(f": {person_name}", poi_info_text_style)],
                [Paragraph("Status", poi_info_text_style), Paragraph(f": {person_type}", poi_info_text_style)],
                [Paragraph("Total Evidence", poi_info_text_style), Paragraph(f": {total_evidence} Evidence", poi_info_text_style)],
            ]
            person_info_table = Table(
                person_info_table_data, colWidths=[USABLE_WIDTH * 0.15, USABLE_WIDTH * 0.85]
            )
            person_info_table.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
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
                    [Paragraph("Name", poi_info_text_style), Paragraph(f": {person_name}", poi_info_text_style)],
                    [Paragraph("Status", poi_info_text_style), Paragraph(f": {person_type}", poi_info_text_style)],
                    [Paragraph("Total Evidence", poi_info_text_style), Paragraph(f": {total_evidence} Evidence", poi_info_text_style)],
                ]
                person_info_table = Table(
                    person_info_table_data, colWidths=[USABLE_WIDTH * 0.15, USABLE_WIDTH * 0.85]
                )
                person_info_table.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))

                if index > 0:
                    subtitle_with_info = [
                        Spacer(1, 25),
                        poi_title_table,
                        Spacer(1, 5),
                        Spacer(1, 10),
                        person_info_table,
                        Spacer(1, 10)
                    ]
                    story.append(KeepTogether(subtitle_with_info))
                else:
                    story.append(Spacer(1, 10))
                    story.append(person_info_table)
                    story.append(Spacer(1, 10))

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

                        if file_path and os.path.exists(file_path):
                            try:
                                img = PILImage.open(file_path)
                                original_width, original_height = img.size
                                aspect_ratio = original_height / original_width
                                
                                image_width = picture_col_width - 10
                                image_height = image_width * aspect_ratio
                                
                                img = img.resize((int(image_width), int(image_height)), PILImage.Resampling.LANCZOS)
                                buf = BytesIO()
                                img.save(buf, format="PNG")
                                buf.seek(0)
                                pic_cell = Image(buf, width=image_width, height=image_height)
                            except Exception as img_e:
                                logger.warning(f"Failed to process image {file_path}: {img_e}")
                                
                                placeholder_width = picture_col_width - 10
                                placeholder_height = placeholder_width
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
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
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
                    story.append(Paragraph("<i>No evidence available</i>", poi_info_text_style))
                    story.append(Spacer(1, 20))

        notes_value = case_notes.strip() if case_notes and case_notes.strip() else "<i>No notes available</i>"
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

        logo_w, logo_h = 130, 45
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
        self.setFont("Helvetica-Bold", 10)
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

            self.setFont("Helvetica-Bold", 17)
            self.setFillColor(COLOR_TITLE)
            textobject = self.beginText(left_margin, title_y)
            textobject.setFont("Helvetica-Bold", 17)
            textobject.setFillColor(COLOR_TITLE)
            textobject.setTextOrigin(left_margin, title_y)

            words = self.suspect_name.split()
            line = ""
            title_lines_count = 0
            for word in words:
                test_line = line + word + " " if line else word + " "
                test_width = self.stringWidth(test_line, "Helvetica-Bold", 17)
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
            self.setFont("Helvetica-Bold", 14)
            self.setFillColor(COLOR_TITLE)
            self.drawString(left_margin, case_name_y, f"Case: {self.case_name}")

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
            self.setFont("Helvetica", 14)
            self.setFillColor(colors.black)

            if self.investigator:
                self.drawString(left_margin, investigator_y, f"Investigator: {self.investigator}")

            if self.created_date:
                date_text = f"Date Created: {self.created_date}"
                date_x = page_width - right_margin - self.stringWidth(date_text, "Helvetica", 14)
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
            "SuspectTitle", parent=styles["Heading1"], fontSize=17, textColor=COLOR_TITLE,
            spaceAfter=4, alignment=TA_LEFT, fontName="Helvetica-Bold", leftIndent=0
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", fontSize=14, textColor=colors.black, spaceAfter=7, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        status_style = ParagraphStyle(
            "StatusStyle", fontSize=16, textColor=colors.black, spaceAfter=7, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )
        investigator_style = ParagraphStyle(
            "Investigator", fontSize=14, textColor=colors.black, spaceAfter=6, alignment=TA_LEFT, fontName="Helvetica", leftIndent=-5
        )
        date_created_style = ParagraphStyle(
            "DateCreated", fontSize=14, textColor=colors.black, spaceAfter=6, alignment=TA_RIGHT, fontName="Helvetica"
        )
        notes_title_style = ParagraphStyle(
            "NotesTitle", fontSize=14, textColor=COLOR_TITLE, spaceAfter=8, alignment=TA_LEFT, fontName="Helvetica-Bold"
        )
        notes_text_style = ParagraphStyle(
            "NotesText", fontSize=11, leading=16, alignment=TA_LEFT, textColor=COLOR_TITLE, fontName="Helvetica"
        )
        table_header_style = ParagraphStyle(
            "TableHeader", parent=styles["Normal"], fontSize=11, alignment=TA_LEFT,
            fontName="Helvetica-Bold", leading=13, textColor=colors.white
        )
        evidence_summary_style = ParagraphStyle(
            "EvidenceSummary", fontSize=10, leading=14, alignment=TA_LEFT, textColor=colors.black, fontName="Helvetica"
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
            [Paragraph(f"<b>Case Related:</b> {case_name}", subtitle_style), ""]
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
                        original_width, original_height = img.size
                        aspect_ratio = original_height / original_width
                        
                        image_width = picture_col_width - 10
                        image_height = image_width * aspect_ratio
                        
                        img = img.resize((int(image_width), int(image_height)), PILImage.Resampling.LANCZOS)
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        pic_cell = Image(buf, width=image_width, height=image_height)
                    except Exception as img_e:
                        logger.warning(f"Failed to process image {file_path}: {img_e}")
                        
                        placeholder_width = picture_col_width - 10
                        placeholder_height = placeholder_width
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
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
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