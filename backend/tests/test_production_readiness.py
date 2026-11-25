"""Production readiness regression tests covering config, concurrency, caching, and error resilience."""

from __future__ import annotations

import asyncio
import io
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
from starlette.testclient import TestClient

from app.core.config import BACKEND_DIR, Settings
from app.main import app
from app.services.llm_service import LLMService
from app.services.report_store import _REPORT_CACHE, MAX_REPORT_CACHE_SIZE, _cache_put
from format_compliance import (
    FormatComplianceReport,
    PatternComplianceStatus,
)


def _create_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    raw = doc.tobytes()
    doc.close()
    return raw


def test_settings_cors_comma_and_json_parsing(monkeypatch) -> None:
    s_csv = Settings(BACKEND_CORS_ORIGINS="https://a.vercel.app, https://b.example.com/")
    assert s_csv.BACKEND_CORS_ORIGINS == ["https://a.vercel.app", "https://b.example.com"]

    s_json = Settings(BACKEND_CORS_ORIGINS='["https://c.vercel.app/"]')
    assert s_json.BACKEND_CORS_ORIGINS == ["https://c.vercel.app"]

    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "http://localhost:5173,https://scrucheck.vercel.app")
    s_env = Settings()
    assert s_env.BACKEND_CORS_ORIGINS == ["http://localhost:5173", "https://scrucheck.vercel.app"]


def test_settings_anchors_relative_paths_and_docs_toggle() -> None:
    dev = Settings(ENVIRONMENT="development")
    assert dev.DOCS_ENABLED is True
    assert Path(dev.REPORT_DIR).is_absolute()
    assert Path(dev.REPORT_DIR) == (BACKEND_DIR / "generated_reports").resolve()

    prod = Settings(ENVIRONMENT="production")
    assert prod.DOCS_ENABLED is False

    prod_override = Settings(ENVIRONMENT="production", ENABLE_API_DOCS=True)
    assert prod_override.DOCS_ENABLED is True


def test_report_cache_is_bounded_lru() -> None:
    _REPORT_CACHE.clear()
    base_pattern = PatternComplianceStatus(selected_category="CAT-1")
    for idx in range(MAX_REPORT_CACHE_SIZE + 15):
        rid = f"00000000-0000-0000-0000-{idx:012d}"
        rep = FormatComplianceReport(
            report_id=rid,
            is_approved=True,
            approval_status="APPROVED",
            compliance_score=100.0,
            selected_pattern_name="CAT-1",
            selected_category="CAT-1",
            header_checks={},
            pattern_compliance=base_pattern,
            missing_fields=[],
            blocking_reasons=[],
            extracted_metadata={},
        )
        _cache_put(rid, rep)

    assert len(_REPORT_CACHE) == MAX_REPORT_CACHE_SIZE
    assert f"00000000-0000-0000-0000-{0:012d}" not in _REPORT_CACHE
    assert f"00000000-0000-0000-0000-{MAX_REPORT_CACHE_SIZE + 14:012d}" in _REPORT_CACHE
    _REPORT_CACHE.clear()


def test_llm_service_run_log_isolated_across_async_tasks() -> None:
    svc = LLMService(provider="mock", fallback_provider="")

    async def worker(tag: str, delay: float) -> list[str]:
        svc.reset_run_log()
        await asyncio.sleep(delay)
        svc.record_delivery(task=tag, tier="MOCK", provider="mock", model=tag)
        await asyncio.sleep(delay)
        summary = svc.get_run_summary()
        return [ev["task"] for ev in summary["events"]]

    async def run_both() -> tuple[list[str], list[str]]:
        return await asyncio.gather(worker("task-a", 0.02), worker("task-b", 0.01))

    res_a, res_b = asyncio.run(run_both())
    assert res_a == ["task-a"]
    assert res_b == ["task-b"]


def test_scrutiny_endpoint_survives_question_parser_failure() -> None:
    client = TestClient(app)
    pdf_bytes = _create_pdf("Anna University Regulations 2021\nCS3351\nPart A\n1. Define gate.")
    files = {"file": ("qp.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"exam_type": "CAT-1", "pattern_name": "CAT-1 (Unit I & II) - Standard"}

    with patch("app.main.question_parser.parse_from_text", side_effect=RuntimeError("parser boom")):
        resp = client.post("/api/v1/scrutiny/check-format", files=files, data=data)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["qp_filename"] == "qp.pdf"
    assert payload["repetition_risk"] is None
    assert payload["blooms_taxonomy"] is None
    assert payload["grammar_check"] is None
