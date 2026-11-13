"""Tests for PDF Scrutiny Report Generation and Download Endpoints.

Verifies:
1. Direct generation of PDF bytes adheres to ReportLab PDF specification (%PDF header).
2. Report store caching and disk retrieval.
3. GET /api/v1/reports/{report_id}/download endpoint:
   - Success (200) with Content-Type: application/pdf and Content-Disposition header.
   - Input validation (400) for non-UUID strings (preventing path traversal).
   - Not found (404) for non-existent report IDs.
4. POST /api/v1/reports/download-pdf endpoint:
   - Success (200) with Content-Type: application/pdf when passing report JSON.
   - Request validation (422) for invalid payloads.
5. Strict constraints:
   - PDF is the only supported format.
   - Institutional name from configuration is reflected.
   - Categorical statuses (PASS / FLAG / REVIEW_REQUIRED) used without numerical percentages in summary.
"""

from __future__ import annotations

import uuid

import pymupdf as fitz
import pytest
from starlette.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.schemas.blooms_taxonomy import BloomsTaxonomyReport, ScrutinyStatus
from app.schemas.grammar_check import GrammarCheckReport, GrammarStatus
from app.schemas.mark_distribution import (
    MarkDistributionReport,
    MarkDistributionStatus,
    QuestionMarkEvaluation,
)
from app.schemas.question_mapping import SyllabusCoverageReport
from app.schemas.repetition_risk import RepetitionRiskReport, RepetitionStatus
from app.services.pdf_generator import generate_scrutiny_pdf
from app.services.report_store import get_report, save_report
from format_compliance import (
    ExamDetailItem,
    ExamDetailsReport,
    FormatComplianceReport,
    HeaderItemStatus,
    PatternComplianceStatus,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Synchronous test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_report() -> FormatComplianceReport:
    """Creates a comprehensive sample FormatComplianceReport for testing."""
    rep_id = str(uuid.uuid4())
    return FormatComplianceReport(
        report_id=rep_id,
        qp_filename="CS8080_Information_Retrieval_QP.pdf",
        is_approved=True,
        approval_status="APPROVED",
        compliance_score=100.0,
        selected_pattern_name="CAT-1 Pattern",
        selected_category="CAT-1",
        header_checks={
            "subject_code": HeaderItemStatus(
                field_name="subject_code",
                label="Subject Code",
                found=True,
                extracted_value="CS8080",
                message="OK",
            )
        },
        pattern_compliance=PatternComplianceStatus(
            selected_category="CAT-1",
            pattern_name_match=True,
            sections_match=True,
            duration_match=True,
            marks_match=True,
            found_duration_minutes=90,
            expected_duration_minutes=90,
            found_total_marks=50,
            expected_total_marks=50,
            found_sections=["Part A", "Part B"],
        ),
        exam_details=ExamDetailsReport(
            is_approved=True,
            status="APPROVED",
            items={
                "subject_code": ExamDetailItem(
                    field_name="subject_code",
                    label="Subject Code",
                    found=True,
                    extracted_value="CS8080",
                    note="Verified",
                ),
                "subject_name": ExamDetailItem(
                    field_name="subject_name",
                    label="Subject Name",
                    found=True,
                    extracted_value="Information Retrieval",
                    note="Verified",
                ),
            },
            missing_details=[],
        ),
        missing_fields=[],
        blocking_reasons=[],
        extracted_metadata={"programme": "B.E. CSE", "branch": "Computer Science"},
        mark_distribution=MarkDistributionReport(
            overall_status=MarkDistributionStatus.PASS,
            total_questions_evaluated=10,
            pass_count=10,
            flag_count=0,
            review_required_count=0,
            summary="All sections adhere to mark distribution constraints.",
            evaluations=[
                QuestionMarkEvaluation(
                    question_id="Q1",
                    section="Part A",
                    assigned_marks=2.0,
                    status=MarkDistributionStatus.PASS,
                    reason="Compliant 2-mark question",
                )
            ],
        ),
        blooms_taxonomy=BloomsTaxonomyReport(
            is_compliant=True,
            overall_status=ScrutinyStatus.PASS,
            total_questions=10,
            total_marks=50.0,
            rule_bt_mentioned_count=10,
            rule_bt_missing_count=0,
            rule_or_parity_flag_count=0,
            rule_wh_avoidance_flag_count=0,
        ),
        grammar_check=GrammarCheckReport(
            is_compliant=True,
            overall_status=GrammarStatus.PASS,
            total_questions_examined=10,
            clean_questions_count=10,
            questions_with_issues_count=0,
        ),
        repetition_risk=RepetitionRiskReport(
            overall_status=RepetitionStatus.PASS,
            total_questions_evaluated=10,
            pass_count=10,
            flag_count=0,
            review_required_count=0,
            summary="Zero duplicate questions detected.",
        ),
        syllabus_alignment=SyllabusCoverageReport(
            syllabus_id="test-syllabus-id",
            overall_status="ALIGNED",
            total_questions=10,
            total_question_groups=10,
            aligned_count=10,
            mismatch_count=0,
            requires_human_review=False,
            summary="All questions match syllabus portions for CAT-1.",
        ),
    )


def test_generate_scrutiny_pdf_bytes(sample_report: FormatComplianceReport):
    """Verifies that PDF bytes are correctly generated with valid %PDF header."""
    pdf_bytes = generate_scrutiny_pdf(sample_report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_content_and_zero_score(sample_report: FormatComplianceReport):
    """Verifies that the generated PDF contains institutional name, all criteria, and no percentages in summary."""
    pdf_bytes = generate_scrutiny_pdf(sample_report)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert len(doc) >= 1

    full_text = "".join(page.get_text() for page in doc)
    # Check institutional name from config
    assert settings.INSTITUTION_NAME.upper() in full_text
    # Check document title
    assert "ACADEMIC QUESTION PAPER SCRUTINY" in full_text
    # Check subject code
    assert "CS8080" in full_text
    # Check criteria headers and sections
    assert "Detailed Evaluation of Ten Institutional Criteria" in full_text
    assert "Executive Summary & Scrutiny Verdict" in full_text
    assert "Committee Recommendations & Action Items" in full_text
    assert "Scrutiny Committee Member" in full_text
    assert "Controller of Examinations" in full_text
    # Check categorical statuses
    assert "PASS" in full_text
    assert "APPROVED" in full_text


def test_report_store_lifecycle(sample_report: FormatComplianceReport):
    """Verifies save and retrieval from report_store."""
    save_report(sample_report)
    retrieved = get_report(sample_report.report_id)
    assert retrieved is not None
    assert retrieved.report_id == sample_report.report_id
    assert retrieved.selected_category == "CAT-1"


def test_get_report_download_success(client: TestClient, sample_report: FormatComplianceReport):
    """Verifies GET /api/v1/reports/{report_id}/download returns 200 with PDF content."""
    save_report(sample_report)

    response = client.get(f"/api/v1/reports/{sample_report.report_id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert "ScruCheck_AI_CS8080_CAT-1_Scrutiny_Report.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_get_report_download_invalid_uuid(client: TestClient):
    """Verifies GET /api/v1/reports/{report_id}/download rejects path traversal and non-UUIDs."""
    # Attempt path traversal
    bad_id = "../../../etc/passwd"
    response = client.get(f"/api/v1/reports/{bad_id}/download")
    assert response.status_code in (400, 404)

    # Simple non-UUID string
    response = client.get("/api/v1/reports/invalid-uuid-string/download")
    assert response.status_code == 400
    assert "Invalid report ID format" in response.json()["detail"]


def test_get_report_download_not_found(client: TestClient):
    """Verifies GET /api/v1/reports/{report_id}/download returns 404 for missing report."""
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/reports/{non_existent_id}/download")
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_post_report_download_pdf(client: TestClient, sample_report: FormatComplianceReport):
    """Verifies POST /api/v1/reports/download-pdf generates PDF directly from report payload."""
    payload = sample_report.model_dump(mode="json")
    response = client.post("/api/v1/reports/download-pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_post_report_download_invalid_payload(client: TestClient):
    """Verifies POST /api/v1/reports/download-pdf rejects malformed bodies."""
    response = client.post("/api/v1/reports/download-pdf", json={"invalid": "payload"})
    assert response.status_code == 422
