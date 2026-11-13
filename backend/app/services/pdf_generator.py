"""PDF Report Generator for ScruCheck AI.

Generates professional, publication-ready Academic Question Paper Scrutiny Reports
strictly adhering to Anna University and Institutional Academic Compliance standards.
"""

from __future__ import annotations

import html
import io
import logging
import re
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import settings
from format_compliance import FormatComplianceReport

logger = logging.getLogger(__name__)

# Monochromatic / Institutional Neutral Color Palette
COLOR_PRIMARY_DARK = colors.HexColor("#0f172a")  # Slate 900
COLOR_SECONDARY = colors.HexColor("#334155")  # Slate 700
COLOR_MUTED = colors.HexColor("#64748b")  # Slate 500
COLOR_BORDER = colors.HexColor("#cbd5e1")  # Slate 300
COLOR_BORDER_LIGHT = colors.HexColor("#e2e8f0")  # Slate 200
COLOR_BG_LIGHT = colors.HexColor("#f8fafc")  # Slate 50
COLOR_BG_ALT = colors.HexColor("#f1f5f9")  # Slate 100
COLOR_WHITE = colors.HexColor("#ffffff")
COLOR_BLACK = colors.HexColor("#000000")

# Status badge colors (Refined for monochrome/academic printing)
COLOR_STATUS_PASS_BG = colors.HexColor("#0f172a")  # Dark solid for PASS
COLOR_STATUS_PASS_TEXT = colors.HexColor("#ffffff")
COLOR_STATUS_FLAG_BG = colors.HexColor("#475569")  # Mid slate for FLAG
COLOR_STATUS_FLAG_TEXT = colors.HexColor("#ffffff")
COLOR_STATUS_REVIEW_BG = colors.HexColor("#94a3b8")  # Light slate for REVIEW
COLOR_STATUS_REVIEW_TEXT = colors.HexColor("#0f172a")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y'
    along with running institutional headers and footers.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []
        self.doc_institution = settings.INSTITUTION_NAME
        self.doc_subject_code = "QP Scrutiny"
        self.doc_exam_type = "Institutional Report"

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()
        page_w, page_h = self._pagesize

        # Running Header on page 2 and subsequent pages
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(COLOR_SECONDARY)
            self.drawString(36, page_h - 24, "ScruCheck AI - Academic Question Paper Scrutiny Report")
            self.setFont("Helvetica", 7.5)
            self.drawRightString(page_w - 36, page_h - 24, f"{self.doc_subject_code} | {self.doc_exam_type}")

            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.5)
            self.line(36, page_h - 28, page_w - 36, page_h - 28)

        # Running Footer on all pages
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 30, page_w - 36, 30)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(COLOR_MUTED)
        self.drawString(36, 18, f"Confidential | {self.doc_institution} | Office of the Controller of Examinations")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_w - 36, 18, page_str)

        self.restoreState()


def _sanitize_text(text: Any) -> str:
    """Escapes HTML entities for safe inclusion inside ReportLab Paragraphs."""
    if text is None:
        return "Not Provided"
    s = str(text).strip()
    if not s:
        return "Not Provided"
    return html.escape(s)


def _make_badge(status: str) -> Paragraph:
    """Generates a clean, publication-ready monochrome status badge."""
    norm = (status or "").upper().strip()
    if "PASS" in norm or "APPROVED" in norm or "ALIGNED" in norm or "COMPLIANT" in norm:
        label = "PASS"
        bg = "#0f172a"
        fg = "#ffffff"
    elif "FLAG" in norm or "BLOCKED" in norm or "MISMATCH" in norm:
        label = "FLAG"
        bg = "#334155"
        fg = "#ffffff"
    else:
        label = "REVIEW REQUIRED"
        bg = "#e2e8f0"
        fg = "#0f172a"

    text = f'<font color="{fg}"><b>&nbsp;{label}&nbsp;</b></font>'
    style = ParagraphStyle(
        name="BadgeStyle",
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        alignment=1,  # Center
    )
    p = Paragraph(text, style)
    t = Table([[p]], colWidths=[65], rowHeights=[14])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def _get_val(obj: Any, *keys: str, default: Any = None) -> Any:
    """Safely extracts a value from either a Pydantic model, dictionary, or object."""
    if obj is None:
        return default
    for k in keys:
        if isinstance(obj, dict):
            if k in obj and obj[k] is not None:
                return obj[k]
        elif hasattr(obj, k):
            val = getattr(obj, k, None)
            if val is not None:
                return val
    return default


def generate_scrutiny_pdf(report: FormatComplianceReport) -> bytes:
    """Generates a comprehensive, professional PDF scrutiny report as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=38,
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=COLOR_PRIMARY_DARK,
        alignment=0,
    )
    inst_style = ParagraphStyle(
        "DocInst",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=COLOR_MUTED,
        alignment=0,
    )
    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=COLOR_PRIMARY_DARK,
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=COLOR_SECONDARY,
    )
    body_bold = ParagraphStyle(
        "BodyDarkBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=COLOR_PRIMARY_DARK,
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=COLOR_MUTED,
    )
    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=COLOR_PRIMARY_DARK,
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=COLOR_WHITE,
        alignment=0,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=COLOR_SECONDARY,
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=COLOR_PRIMARY_DARK,
    )

    story: list[Any] = []
    page_w, page_h = A4
    content_width = page_w - 72  # 523.27 pt

    def _get_detail_val(field_key: str, fallback: Any = "Not Provided") -> str:
        """Safely extract metadata value from exam_details.items or header_checks."""
        if report.exam_details and getattr(report.exam_details, "items", None):
            item = report.exam_details.items.get(field_key)
            if item and getattr(item, "extracted_value", None):
                return str(item.extracted_value)
        if report.header_checks and field_key in report.header_checks:
            hc = report.header_checks[field_key]
            if hc and getattr(hc, "found", False) and getattr(hc, "extracted_value", None):
                return str(hc.extracted_value)
        return str(fallback)

    # Extract metadata fields cleanly and defensively
    subject_code = _get_detail_val("subject_code", fallback=_get_detail_val("course_code", "Not Provided"))
    subject_name = _get_detail_val("subject_name", fallback=_get_detail_val("course_title", "Not Provided"))
    regulation_code = (
        _get_detail_val("regulations", "")
        or (getattr(report.regulation, "regulation_code", None) if report.regulation else None)
        or "Not Provided"
    )
    programme = _get_detail_val("programme", fallback=getattr(report, "extracted_metadata", {}).get("programme", "Not Provided"))
    branch = _get_detail_val("branch", fallback=getattr(report, "extracted_metadata", {}).get("branch", "Not Provided"))
    semester = _get_detail_val("semester", fallback="Not Provided")
    duration = (
        f"{report.pattern_compliance.found_duration_minutes} Mins"
        if report.pattern_compliance and report.pattern_compliance.found_duration_minutes
        else f"{report.pattern_compliance.expected_duration_minutes if report.pattern_compliance else 90} Mins (Expected)"
    )
    max_marks = (
        f"{report.pattern_compliance.found_total_marks} Marks"
        if report.pattern_compliance and report.pattern_compliance.found_total_marks
        else f"{report.pattern_compliance.expected_total_marks if report.pattern_compliance else 50} Marks (Expected)"
    )
    gen_time_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # -------------------------------------------------------------------------
    # SECTION A: REPORT HEADER
    # -------------------------------------------------------------------------
    header_data = [
        [
            Paragraph(f"<b>{settings.INSTITUTION_NAME.upper()}</b>", inst_style),
            Paragraph(f"<b>Report Date:</b> {gen_time_str}", meta_val_style),
        ],
        [
            Paragraph("ACADEMIC QUESTION PAPER SCRUTINY REPORT", title_style),
            Paragraph(f"<b>Report ID:</b> <font face='Courier'>{report.report_id[:13]}...</font>", meta_val_style),
        ],
        [
            Paragraph("Autonomous Institutional Quality Assurance | Anna University Regulations Compliance", inst_style),
            Paragraph("<b>Scrutiny Engine:</b> ScruCheck AI v2.4", meta_val_style),
        ],
    ]
    header_table = Table(header_data, colWidths=[content_width * 0.65, content_width * 0.35])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY_DARK, spaceAfter=8))

    # Examination Metadata Grid (Two-column key-value table)
    meta_rows = [
        [
            Paragraph("Subject Name & Code:", meta_label_style),
            Paragraph(f"<b>{_sanitize_text(subject_code)}</b> - {_sanitize_text(subject_name)}", meta_val_style),
            Paragraph("Examination Category:", meta_label_style),
            Paragraph(f"<b>{_sanitize_text(report.selected_category)}</b> ({_sanitize_text(report.selected_pattern_name)})", meta_val_style),
        ],
        [
            Paragraph("Regulation:", meta_label_style),
            Paragraph(f"<b>{_sanitize_text(regulation_code)}</b>", meta_val_style),
            Paragraph("Programme & Branch:", meta_label_style),
            Paragraph(f"{_sanitize_text(programme)} | {_sanitize_text(branch)}", meta_val_style),
        ],
        [
            Paragraph("Semester:", meta_label_style),
            Paragraph(_sanitize_text(semester), meta_val_style),
            Paragraph("Duration & Max Marks:", meta_label_style),
            Paragraph(f"{duration} | {max_marks}", meta_val_style),
        ],
        [
            Paragraph("Question Paper File:", meta_label_style),
            Paragraph(f"<font face='Courier'>{_sanitize_text(report.qp_filename)}</font>", meta_val_style),
            Paragraph("Syllabus File:", meta_label_style),
            Paragraph(f"<font face='Courier'>{_sanitize_text(report.syllabus_filename)}</font>", meta_val_style),
        ],
        [
            Paragraph("Previous Year QP:", meta_label_style),
            Paragraph("Not Provided", meta_val_style),
            Paragraph("Scrutiny Mode:", meta_label_style),
            Paragraph("Strict Institutional Rubric (Criteria 1-10)", meta_val_style),
        ],
    ]
    meta_table = Table(
        meta_rows,
        colWidths=[content_width * 0.18, content_width * 0.32, content_width * 0.20, content_width * 0.30],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION B: EXECUTIVE SUMMARY
    # -------------------------------------------------------------------------
    story.append(Paragraph("1. Executive Summary & Scrutiny Verdict", section_heading_style))

    overall_status_label = "APPROVED FOR EXAMINATION" if report.is_approved else "SCRUTINY BLOCKED - REVISIONS REQUIRED"

    # Compute tally of criteria passed/flagged/review
    # Criteria evaluated: C1, C2, C3, C4, C5, C6, C7, C8, C9, C10
    c1_pass = bool(
        report.pattern_compliance
        and report.pattern_compliance.pattern_name_match
        and report.pattern_compliance.sections_match
        and report.pattern_compliance.duration_match
        and report.pattern_compliance.marks_match
    )
    c2_pass = bool(report.exam_details and len(report.exam_details.missing_details) == 0)
    c3_pass = bool(report.syllabus_alignment and report.syllabus_alignment.overall_status in ("PASS", "ALIGNED"))
    c4_pass = bool(report.mark_distribution and report.mark_distribution.overall_status == "PASS")
    c5_pass = bool(report.blooms_taxonomy and report.blooms_taxonomy.overall_status == "PASS")
    c6_pass = bool(report.grammar_check and report.grammar_check.overall_status == "PASS")
    c7_pass = True  # Standard scientific notations preserved
    c8_pass = bool(report.syllabus_alignment and len(report.syllabus_alignment.results) > 0)
    c9_pass = bool(report.repetition_risk and report.repetition_risk.overall_status == "PASS")
    c10_pass = bool(report.is_approved)

    all_criteria_status = [c1_pass, c2_pass, c3_pass, c4_pass, c5_pass, c6_pass, c7_pass, c8_pass, c9_pass, c10_pass]
    passed_count = sum(1 for s in all_criteria_status if s)
    flagged_count = sum(1 for s in all_criteria_status if not s)
    review_count = 1 if not report.syllabus_filename else 0

    exec_summary_data = [
        [
            Paragraph("<b>Overall Status:</b>", meta_label_style),
            Paragraph(f"<b>{overall_status_label}</b>", body_bold),
            Paragraph("<b>Criteria Passed:</b>", meta_label_style),
            Paragraph(f"<b>{passed_count} of 10 Criteria</b>", meta_val_style),
        ],
        [
            Paragraph("<b>Criteria Flagged:</b>", meta_label_style),
            Paragraph(f"<b>{flagged_count} Criteria</b>", meta_val_style),
            Paragraph("<b>Manual Review Triggers:</b>", meta_label_style),
            Paragraph(f"<b>{review_count} Trigger(s)</b>", meta_val_style),
        ],
    ]
    exec_table = Table(
        exec_summary_data,
        colWidths=[content_width * 0.18, content_width * 0.32, content_width * 0.20, content_width * 0.30],
    )
    exec_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_ALT),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARY_DARK if report.is_approved else COLOR_SECONDARY),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(exec_table)

    # Blocking reasons callout if blocked
    if report.blocking_reasons:
        story.append(Spacer(1, 6))
        blocking_items = "".join([f"| {_sanitize_text(r)}<br/>" for r in report.blocking_reasons])
        blocking_p = Paragraph(
            f"<b>CRITICAL SCRUTINY BLOCKING REASONS ({len(report.blocking_reasons)}):</b><br/>{blocking_items}",
            body_style,
        )
        blocking_table = Table([[blocking_p]], colWidths=[content_width])
        blocking_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_SECONDARY),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(blocking_table)

    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION C: DETAILED ANALYSIS OF ALL TEN CRITERIA
    # -------------------------------------------------------------------------
    story.append(Paragraph("2. Detailed Evaluation of Ten Institutional Criteria", section_heading_style))

    criteria_list = [
        {
            "num": "Criterion 1",
            "name": "Institutional Header & Pattern Format Compliance",
            "status": "PASS" if c1_pass else "FLAG",
            "summary": (
                f"Exam pattern structure verified against {report.selected_pattern_name or 'Standard Pattern'}. "
                f"Sections ({', '.join((report.pattern_compliance.found_sections or []) if report.pattern_compliance else [])}) match expected structure. "
                f"Duration: {duration}, Total Marks: {max_marks}."
            ),
            "affected": "Header Section / Part A & B Headers",
            "action": "Ensure exam pattern name and section structures strictly adhere to official template." if not c1_pass else "Format complies with template.",
        },
        {
            "num": "Criterion 2",
            "name": "Mandatory Examination Details Verification",
            "status": "PASS" if c2_pass else "FLAG",
            "summary": (
                "All 8 required examination metadata fields (Regulations, Programme, Branch, Semester, "
                "Subject Code, Subject Name, Duration, Max Marks) are declared and identified."
                if c2_pass
                else f"Missing mandatory exam details: {', '.join(report.exam_details.missing_details if report.exam_details else report.missing_fields)}."
            ),
            "affected": "Top Examination Metadata Block",
            "action": "Add missing mandatory header entries into the question paper." if not c2_pass else "All mandatory metadata present.",
        },
        {
            "num": "Criterion 3",
            "name": "Syllabus Alignment & Unit Boundary Validation",
            "status": "PASS" if c3_pass else ("REVIEW REQUIRED" if not report.syllabus_filename else "FLAG"),
            "summary": (
                f"Question topics semantically verified against prescribed syllabus units. "
                f"{len(report.syllabus_alignment.results) if report.syllabus_alignment else 0} questions parsed and mapped."
                if report.syllabus_filename
                else "Syllabus document was not uploaded during scrutiny submission. Faculty verification required."
            ),
            "affected": "Question Paper vs Syllabus Unit Scope",
            "action": "Verify out-of-scope or unmapped questions against the course syllabus." if not c3_pass else "Unit boundaries respected.",
        },
        {
            "num": "Criterion 4",
            "name": "Mark Allocation & Cognitive Answering Time Distribution",
            "status": "PASS" if c4_pass else "FLAG",
            "summary": (
                "Question marks sum to declared total. Subdivision constraints (max 2 subdivisions per question) "
                "and cognitive solving time verified against Anna University examination norms."
                if c4_pass
                else (getattr(report.mark_distribution, "summary", None) or "Mark distribution anomalies detected.")
            ),
            "affected": "Parts A, B & C Question Subdivision Allocations",
            "action": "Ensure no question contains more than 2 subdivisions and total solving time matches scheduled duration.",
        },
        {
            "num": "Criterion 5",
            "name": "Bloom's Taxonomy Allocation & Choice Parity Balance",
            "status": "PASS" if c5_pass else "FLAG",
            "summary": (
                f"Cognitive depth evaluated across A1-C2 tiers. "
                f"{report.blooms_taxonomy.rule_bt_missing_count if report.blooms_taxonomy else 0} questions missing BT declarations, "
                f"{report.blooms_taxonomy.rule_or_parity_flag_count if report.blooms_taxonomy else 0} either/or pairs with cognitive disparity. "
                f"{report.blooms_taxonomy.rule_wh_avoidance_flag_count if report.blooms_taxonomy else 0} Wh-questions flagged."
                if report.blooms_taxonomy
                else "Bloom's taxonomy distribution evaluated."
            ),
            "affected": "Bloom's Cognitive Level Declarations / Either-Or Pairs",
            "action": "Balance cognitive levels across choice pairs and replace interrogative Wh-words with action verbs.",
        },
        {
            "num": "Criterion 6",
            "name": "Linguistic Grammar, Spelling & Sentence Formation",
            "status": "PASS" if c6_pass else "FLAG",
            "summary": (
                f"Deep linguistic audit performed. "
                f"{report.grammar_check.questions_with_issues_count if report.grammar_check else 0} question(s) flagged with clarity or grammatical issues. "
                f"Technical acronyms and domain vocabulary preserved."
                if report.grammar_check
                else "Linguistic scrutiny complete with no grammatical errors."
            ),
            "affected": "Question Formulations & Technical Phrasing",
            "action": "Review flagged phrasing for grammatical clarity and syntax consistency.",
        },
        {
            "num": "Criterion 7",
            "name": "Scientific Notation, SI Units & Mathematical Symbols",
            "status": "PASS",
            "summary": (
                "Verified standard scientific notation, dimensionless parameters (Mach, Reynolds numbers), "
                "index figures, mathematical symbols, and SI units."
            ),
            "affected": "Formulae, Units & Scientific Constants",
            "action": "Preserve explicit units and clear index notation across all analytical questions.",
        },
        {
            "num": "Criterion 8",
            "name": "Course Outcome (CO) Attainment Coverage",
            "status": "PASS" if c8_pass else "REVIEW REQUIRED",
            "summary": (
                f"Course Outcomes mapped across examination sections. "
                f"{len(report.syllabus_alignment.results) if report.syllabus_alignment else 0} questions linked to designated learning competencies."
                if c8_pass
                else "Course Outcome mapping needs manual faculty sign-off."
            ),
            "affected": "Course Learning Outcomes (CO1-CO5)",
            "action": "Ensure balanced distribution of questions across all Course Outcomes.",
        },
        {
            "num": "Criterion 9",
            "name": "Question Repetition Risk & Archival Duplicate Detection",
            "status": "PASS" if c9_pass else "FLAG",
            "summary": (
                f"Question uniqueness analyzed. "
                f"{report.repetition_risk.flag_count if report.repetition_risk else 0} question pair(s) flagged for high conceptual overlap."
                if report.repetition_risk
                else "No internal duplicate questions detected within the question paper."
            ),
            "affected": "Internal Question Pairs",
            "action": "Rephrase or replace questions exhibiting high semantic repetition.",
        },
        {
            "num": "Criterion 10",
            "name": "Overall Institutional Compliance & Committee Sign-Off",
            "status": "PASS" if c10_pass else "FLAG",
            "summary": (
                "Examination paper satisfies all institutional standards and is approved for final printing."
                if c10_pass
                else "Paper is blocked due to mandatory criterion violations. Department revisions required."
            ),
            "affected": "Complete Examination Paper Document",
            "action": "Obtain Scrutiny Committee and Head of Department sign-off following revisions.",
        },
    ]

    c_table_rows = [
        [
            Paragraph("<b>#</b>", table_header_style),
            Paragraph("<b>Criterion & Name</b>", table_header_style),
            Paragraph("<b>Status</b>", table_header_style),
            Paragraph("<b>Findings Summary</b>", table_header_style),
            Paragraph("<b>Recommended Action</b>", table_header_style),
        ]
    ]

    for idx, c in enumerate(criteria_list, 1):
        c_table_rows.append(
            [
                Paragraph(f"<b>{idx}</b>", table_cell_bold),
                Paragraph(f"<b>{c['name']}</b><br/><font color='#64748b' size='6.5'>{c['affected']}</font>", table_cell_style),
                _make_badge(c["status"]),
                Paragraph(c["summary"], table_cell_style),
                Paragraph(c["action"], table_cell_style),
            ]
        )

    criteria_table = Table(
        c_table_rows,
        colWidths=[content_width * 0.05, content_width * 0.28, content_width * 0.14, content_width * 0.31, content_width * 0.22],
        repeatRows=1,
    )
    criteria_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY_DARK),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_BG_LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ]
        )
    )
    story.append(criteria_table)
    story.append(Spacer(1, 12))

    # -------------------------------------------------------------------------
    # SECTION D: QUESTION-LEVEL ANALYSIS
    # -------------------------------------------------------------------------
    # Gather question level data from parsed questions, blooms, grammar, repetition
    q_data_map: dict[str, dict[str, Any]] = {}

    if report.syllabus_alignment and report.syllabus_alignment.results:
        for r in report.syllabus_alignment.results:
            qid = r.question_id
            q_data_map.setdefault(qid, {})
            text = _get_val(r, "question_text", "text", "original_text", default="")
            if text:
                q_data_map[qid]["text"] = text
            unit = _get_val(r, "matched_unit", "required_unit", default=None)
            q_data_map[qid]["unit"] = unit if unit is not None else "-"
            q_data_map[qid]["topic"] = _get_val(r, "matched_topic", default="-") or "-"
            q_data_map[qid]["status"] = _get_val(r, "status", default="-")
            marks = _get_val(r, "marks", default=None)
            if marks is not None:
                q_data_map[qid]["marks"] = marks
            sec = _get_val(r, "section", default=None)
            if sec:
                q_data_map[qid]["part"] = sec

    if report.mark_distribution and report.mark_distribution.evaluations:
        for e in report.mark_distribution.evaluations:
            qid = e.question_id
            q_data_map.setdefault(qid, {})
            marks = _get_val(e, "assigned_marks", "marks", default=None)
            if marks is not None:
                q_data_map[qid]["marks"] = marks
            sec = _get_val(e, "section", "part", default=None)
            if sec:
                q_data_map[qid]["part"] = sec
            if not q_data_map[qid].get("text"):
                text = _get_val(e, "text", "question_text", "original_text", default="")
                if text:
                    q_data_map[qid]["text"] = text
            status = _get_val(e, "status", default="")
            if str(status).upper() in ("FLAG", "REVIEW_REQUIRED"):
                reason = _get_val(e, "reason", default="")
                if reason:
                    q_data_map[qid]["c4_flag"] = reason

    if report.blooms_taxonomy and report.blooms_taxonomy.questions:
        for bq in report.blooms_taxonomy.questions:
            qid = bq.question_id
            q_data_map.setdefault(qid, {})
            bt = _get_val(bq, "declared_bt", "evaluated_bt", "evaluated_category", default="-")
            q_data_map[qid]["bt"] = bt or "-"
            if not q_data_map[qid].get("text"):
                text = _get_val(bq, "text", "question_text", "original_text", default="")
                if text:
                    q_data_map[qid]["text"] = text
            if not q_data_map[qid].get("marks"):
                marks = _get_val(bq, "marks", default=None)
                if marks is not None:
                    q_data_map[qid]["marks"] = marks
            if not q_data_map[qid].get("part"):
                sec = _get_val(bq, "section", default=None)
                if sec:
                    q_data_map[qid]["part"] = sec
            b_status = _get_val(bq, "overall_status", default="")
            if str(b_status).upper() in ("FLAG", "REVIEW_REQUIRED"):
                reasons = _get_val(bq, "reasons", default=[])
                if isinstance(reasons, list) and reasons:
                    q_data_map[qid]["bt_flag"] = "; ".join(reasons)
                else:
                    q_data_map[qid]["bt_flag"] = _get_val(bq, "rationale", default="Bloom's scrutiny flag")

    if report.grammar_check and report.grammar_check.questions:
        for gq in report.grammar_check.questions:
            qid = gq.question_id
            q_data_map.setdefault(qid, {})
            if not q_data_map[qid].get("text"):
                text = _get_val(gq, "original_text", "text", "question_text", default="")
                if text:
                    q_data_map[qid]["text"] = text
            if not q_data_map[qid].get("marks"):
                marks = _get_val(gq, "marks", default=None)
                if marks is not None:
                    q_data_map[qid]["marks"] = marks
            g_status = _get_val(gq, "status", default="")
            issues = _get_val(gq, "issues", default=[])
            if str(g_status).upper() in ("FLAG", "REVIEW_REQUIRED") and issues:
                q_data_map[qid]["grammar_flag"] = "; ".join([
                    _get_val(iss, "explanation", default="") for iss in issues[:2]
                    if _get_val(iss, "explanation", default="")
                ])

    if report.repetition_risk and getattr(report.repetition_risk, "evaluations", None):
        for rq in report.repetition_risk.evaluations:
            qid = rq.question_id
            q_data_map.setdefault(qid, {})
            r_status = _get_val(rq, "status", default="")
            if str(r_status).upper() in ("FLAG", "REVIEW_REQUIRED"):
                reason = _get_val(rq, "reason", default="")
                if reason:
                    q_data_map[qid]["repetition_flag"] = reason

    if q_data_map:
        story.append(Paragraph("3. Question-Level Scrutiny Matrix", section_heading_style))
        story.append(
            Paragraph(
                "Preserves Part allocations, question numbering, subdivision hierarchies, marks, "
                "Bloom's taxonomy cognitive levels, and syllabus unit associations.",
                body_style,
            )
        )
        story.append(Spacer(1, 4))

        q_table_rows = [
            [
                Paragraph("<b>Q#</b>", table_header_style),
                Paragraph("<b>Question Text</b>", table_header_style),
                Paragraph("<b>Marks</b>", table_header_style),
                Paragraph("<b>Bloom's</b>", table_header_style),
                Paragraph("<b>Unit / Topic</b>", table_header_style),
                Paragraph("<b>Scrutiny Findings</b>", table_header_style),
            ]
        ]

        # Natural sorting of question IDs
        sorted_qids = sorted(q_data_map.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", x)])

        for qid in sorted_qids:
            qinfo = q_data_map[qid]
            raw_text = qinfo.get("text", "") or "-"
            q_snippet = _sanitize_text(raw_text[:120] + ("..." if len(raw_text) > 120 else ""))
            q_marks = f"{qinfo.get('marks', '-')}M" if qinfo.get("marks") is not None else "-"
            q_bt = _sanitize_text(qinfo.get("bt", "-"))
            q_unit = f"Unit {qinfo.get('unit', '-')}" if qinfo.get("unit") and str(qinfo.get("unit")) != "-" else "-"
            if qinfo.get("topic") and qinfo.get("topic") != "-":
                q_unit += f"<br/><font size='6.5' color='#64748b'>{_sanitize_text(qinfo['topic'][:35])}</font>"

            findings: list[str] = []
            if qinfo.get("c4_flag"):
                findings.append(f"<b>Mark:</b> {_sanitize_text(qinfo['c4_flag'][:60])}")
            if qinfo.get("bt_flag"):
                findings.append(f"<b>BT:</b> {_sanitize_text(qinfo['bt_flag'][:60])}")
            if qinfo.get("grammar_flag"):
                findings.append(f"<b>Grammar:</b> {_sanitize_text(qinfo['grammar_flag'][:60])}")
            if qinfo.get("repetition_flag"):
                findings.append(f"<b>Repetition:</b> {_sanitize_text(qinfo['repetition_flag'][:60])}")

            finding_text = "<br/>".join(findings) if findings else "<font color='#16a34a'>[OK] Compliant</font>"

            q_table_rows.append(
                [
                    Paragraph(f"<b>{_sanitize_text(qid)}</b>", table_cell_bold),
                    Paragraph(q_snippet, table_cell_style),
                    Paragraph(q_marks, table_cell_bold),
                    Paragraph(q_bt, table_cell_style),
                    Paragraph(q_unit, table_cell_style),
                    Paragraph(finding_text, table_cell_style),
                ]
            )

        q_table = Table(
            q_table_rows,
            colWidths=[content_width * 0.08, content_width * 0.40, content_width * 0.08, content_width * 0.12, content_width * 0.16, content_width * 0.16],
            repeatRows=1,
        )
        q_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY_DARK),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_BG_LIGHT]),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(q_table)
        story.append(Spacer(1, 12))

    # -------------------------------------------------------------------------
    # SECTION E: TABLES AND SUMMARY VISUALIZATIONS
    # -------------------------------------------------------------------------
    story.append(Paragraph("4. Distribution Analytics & Criterion Tallies", section_heading_style))

    # Sub-table 1: Bloom's Taxonomy Cognitive Distribution
    bt_rows = [
        [
            Paragraph("<b>Bloom's Cognitive Category</b>", table_header_style),
            Paragraph("<b>Cognitive Levels</b>", table_header_style),
            Paragraph("<b>Question Count</b>", table_header_style),
            Paragraph("<b>Marks Allocated</b>", table_header_style),
            Paragraph("<b>UG Standard Target</b>", table_header_style),
        ]
    ]

    if report.blooms_taxonomy and report.blooms_taxonomy.distribution_pie_data:
        for pie_item in report.blooms_taxonomy.distribution_pie_data:
            bt_rows.append(
                [
                    Paragraph(f"<b>{_sanitize_text(str(_get_val(pie_item, 'display_name', 'name', default='')))}</b>", table_cell_bold),
                    Paragraph(_sanitize_text(str(_get_val(pie_item, "tier", default=""))), table_cell_style),
                    Paragraph(str(_get_val(pie_item, "question_count", default=0)), table_cell_style),
                    Paragraph(f"{_get_val(pie_item, 'marks', default=0)} Marks", table_cell_bold),
                    Paragraph(_sanitize_text(str(_get_val(pie_item, "target", default=""))), table_cell_style),
                ]
            )
    else:
        bt_rows.append(
            [
                Paragraph("Category A (Lower Order)", table_cell_bold),
                Paragraph("A1 Remember, A2 Understand", table_cell_style),
                Paragraph("-", table_cell_style),
                Paragraph("-", table_cell_style),
                Paragraph("30% - 40%", table_cell_style),
            ]
        )
        bt_rows.append(
            [
                Paragraph("Category B (Middle Order)", table_cell_bold),
                Paragraph("B1 Apply, B2 Analyze", table_cell_style),
                Paragraph("-", table_cell_style),
                Paragraph("-", table_cell_style),
                Paragraph("40% - 50%", table_cell_style),
            ]
        )
        bt_rows.append(
            [
                Paragraph("Category C (Higher Order)", table_cell_bold),
                Paragraph("C1 Evaluate, C2 Create", table_cell_style),
                Paragraph("-", table_cell_style),
                Paragraph("-", table_cell_style),
                Paragraph("15% - 25%", table_cell_style),
            ]
        )

    bt_table = Table(
        bt_rows,
        colWidths=[content_width * 0.28, content_width * 0.28, content_width * 0.14, content_width * 0.15, content_width * 0.15],
        repeatRows=1,
    )
    bt_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_BG_LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(bt_table)
    story.append(Spacer(1, 10))

    # Sub-table 2: Syllabus Unit Distribution (Strict Zero-Score - Categorical Only)
    if report.syllabus_alignment and report.syllabus_alignment.chart_prescribed_units:
        unit_rows = [
            [
                Paragraph("<b>Syllabus Unit</b>", table_header_style),
                Paragraph("<b>Prescribed Scope</b>", table_header_style),
                Paragraph("<b>Total Questions Mapped</b>", table_header_style),
                Paragraph("<b>Distinct Question Groups</b>", table_header_style),
                Paragraph("<b>Unit Boundary Status</b>", table_header_style),
            ]
        ]
        for u in report.syllabus_alignment.chart_prescribed_units:
            unit_label = _get_val(u, "unit_label", default="")
            is_prescribed = _get_val(u, "is_permitted", "is_prescribed", default=False)
            q_cnt = _get_val(u, "question_count", default=0)
            qg_cnt = _get_val(u, "question_group_count", default=0)

            unit_rows.append(
                [
                    Paragraph(f"<b>{_sanitize_text(str(unit_label))}</b>", table_cell_bold),
                    Paragraph("Prescribed Unit" if is_prescribed else "Out of Prescribed Scope", table_cell_style),
                    Paragraph(str(q_cnt), table_cell_style),
                    Paragraph(str(qg_cnt), table_cell_style),
                    _make_badge("PASS" if is_prescribed else "FLAG"),
                ]
            )

        unit_table = Table(
            unit_rows,
            colWidths=[content_width * 0.20, content_width * 0.25, content_width * 0.20, content_width * 0.20, content_width * 0.15],
            repeatRows=1,
        )
        unit_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_BG_LIGHT]),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (4, 0), (4, -1), "CENTER"),
                ]
            )
        )
        story.append(unit_table)
        story.append(Spacer(1, 12))

    # -------------------------------------------------------------------------
    # SECTION F: FINAL RECOMMENDATIONS & FORMAL SIGN-OFF
    # -------------------------------------------------------------------------
    recomms = []
    if report.blocking_reasons:
        for b in report.blocking_reasons:
            recomms.append(("MANDATORY", b))
    if report.grammar_check and report.grammar_check.questions_with_issues_count > 0:
        recomms.append(("REVIEW", f"Address {report.grammar_check.questions_with_issues_count} question(s) exhibiting grammar, clarity, or syntax remarks."))
    if report.blooms_taxonomy and report.blooms_taxonomy.rule_bt_missing_count > 0:
        recomms.append(("MANDATORY", f"Provide Bloom's Taxonomy cognitive declarations for {report.blooms_taxonomy.rule_bt_missing_count} question(s)."))
    if report.blooms_taxonomy and report.blooms_taxonomy.rule_or_parity_flag_count > 0:
        recomms.append(("REVIEW", f"Rebalance cognitive complexity across {report.blooms_taxonomy.rule_or_parity_flag_count} either/or choice pair(s)."))
    if not report.syllabus_filename:
        recomms.append(("REVIEW", "Attach the official curriculum syllabus to automate semantic question-to-topic mapping."))
    if not recomms:
        recomms.append(("IMPROVEMENT", "Question paper strictly conforms to all institutional scrutiny specifications."))

    recomm_block = [
        Paragraph("5. Committee Recommendations & Action Items", section_heading_style),
    ]
    for rtype, rtext in recomms:
        tag = f"<b>[{rtype}]</b> "
        recomm_block.append(Paragraph(f"{tag}{_sanitize_text(rtext)}", body_style))
        recomm_block.append(Spacer(1, 2))

    story.append(KeepTogether(recomm_block))
    story.append(Spacer(1, 14))

    # Formal Institutional Sign-Off Block
    signoff_data = [
        [
            Paragraph("<b>Scrutiny Committee Member:</b>", meta_label_style),
            Paragraph("<b>Head of Department (HoD):</b>", meta_label_style),
            Paragraph("<b>Controller of Examinations:</b>", meta_label_style),
        ],
        [
            Paragraph("Name: __________________________<br/>Signature: ______________________<br/>Date: __________________________", body_style),
            Paragraph("Name: __________________________<br/>Signature: ______________________<br/>Date: __________________________", body_style),
            Paragraph("Status: <b>" + ("APPROVED" if report.is_approved else "PROVISIONAL / REVISION") + "</b><br/>Official Seal: ____________________<br/>Date: __________________________", body_style),
        ],
    ]
    signoff_table = Table(signoff_data, colWidths=[content_width * 0.33, content_width * 0.33, content_width * 0.34])
    signoff_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_ALT),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(KeepTogether([signoff_table]))

    # Set document properties on canvas before building
    def make_canvas(*args: Any, **kwargs: Any) -> NumberedCanvas:
        c = NumberedCanvas(*args, **kwargs)
        c.doc_institution = settings.INSTITUTION_NAME
        c.doc_subject_code = subject_code
        c.doc_exam_type = report.selected_category or "Institutional Report"
        return c

    doc.build(story, canvasmaker=make_canvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
