import json
import logging
import re
from pathlib import Path

from app.core.config import settings
from format_compliance import FormatComplianceReport

logger = logging.getLogger(__name__)

UUID_REGEX = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", re.IGNORECASE)

# In-memory fast cache
_REPORT_CACHE: dict[str, FormatComplianceReport] = {}


def _get_reports_dir() -> Path:
    directory = Path(settings.REPORT_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_report(report: FormatComplianceReport) -> str:
    """Persist a completed scrutiny report in memory and on disk.

    Returns the report_id.
    """
    report_id = report.report_id
    if not UUID_REGEX.match(report_id):
        raise ValueError(f"Invalid report_id format: {report_id}")

    _REPORT_CACHE[report_id] = report

    try:
        reports_dir = _get_reports_dir()
        file_path = reports_dir / f"{report_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
    except Exception as e:
        logger.warning("Failed to persist report %s to disk: %s", report_id, e)

    return report_id


def get_report(report_id: str) -> FormatComplianceReport | None:
    """Retrieve a completed scrutiny report by its unique UUID.

    Returns None if the report is not found or if the ID is invalid.
    """
    if not report_id or not UUID_REGEX.match(report_id):
        return None

    # Check in-memory cache first
    if report_id in _REPORT_CACHE:
        return _REPORT_CACHE[report_id]

    # Check filesystem
    try:
        reports_dir = _get_reports_dir()
        file_path = reports_dir / f"{report_id}.json"
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            report = FormatComplianceReport.model_validate(data)
            _REPORT_CACHE[report_id] = report
            return report
    except Exception as e:
        logger.error("Error reading report %s from disk: %s", report_id, e)

    return None
