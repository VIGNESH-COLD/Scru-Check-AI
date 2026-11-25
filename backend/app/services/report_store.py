import json
import logging
import re
import threading
from collections import OrderedDict
from pathlib import Path

from app.core.config import settings
from format_compliance import FormatComplianceReport

logger = logging.getLogger(__name__)

UUID_REGEX = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", re.IGNORECASE)

# Bounded LRU in-memory fast cache to prevent unbounded memory growth in long-running deployments
MAX_REPORT_CACHE_SIZE = 100
_REPORT_CACHE: OrderedDict[str, FormatComplianceReport] = OrderedDict()
_CACHE_LOCK = threading.Lock()


def _cache_put(report_id: str, report: FormatComplianceReport) -> None:
    with _CACHE_LOCK:
        _REPORT_CACHE[report_id] = report
        _REPORT_CACHE.move_to_end(report_id)
        while len(_REPORT_CACHE) > MAX_REPORT_CACHE_SIZE:
            _REPORT_CACHE.popitem(last=False)


def _get_reports_dir() -> Path:
    directory = Path(settings.REPORT_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_report(report: FormatComplianceReport) -> str:
    """Persist a completed scrutiny report in bounded memory cache and on disk.

    Returns the report_id.
    """
    report_id = report.report_id
    if not UUID_REGEX.match(report_id):
        raise ValueError(f"Invalid report_id format: {report_id}")

    _cache_put(report_id, report)

    try:
        reports_dir = _get_reports_dir()
        file_path = reports_dir / f"{report_id}.json"
        temp_path = reports_dir / f"{report_id}.json.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        temp_path.replace(file_path)
    except Exception as e:
        logger.warning("Failed to persist report %s to disk: %s", report_id, e)

    return report_id


def get_report(report_id: str) -> FormatComplianceReport | None:
    """Retrieve a completed scrutiny report by its unique UUID.

    Returns None if the report is not found or if the ID is invalid.
    """
    if not report_id or not UUID_REGEX.match(report_id):
        return None

    # Check bounded LRU cache first
    with _CACHE_LOCK:
        cached = _REPORT_CACHE.get(report_id)
        if cached is not None:
            _REPORT_CACHE.move_to_end(report_id)
            return cached

    # Check filesystem
    try:
        reports_dir = _get_reports_dir()
        file_path = reports_dir / f"{report_id}.json"
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            report = FormatComplianceReport.model_validate(data)
            _cache_put(report_id, report)
            return report
    except Exception as e:
        logger.error("Error reading report %s from disk: %s", report_id, e)

    return None
