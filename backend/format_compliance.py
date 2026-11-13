import json
import re
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.blooms_taxonomy import BloomsTaxonomyReport
from app.schemas.grammar_check import GrammarCheckReport
from app.schemas.mark_distribution import MarkDistributionReport
from app.schemas.question_mapping import SyllabusCoverageReport
from app.schemas.repetition_risk import RepetitionRiskReport
from regulation import RegulationCheckResult, check_regulation

DEFAULT_PATTERNS_DIR = Path(__file__).parent / "patterns"

WORD_SEMESTERS = {
    "first": "1",
    "second": "2",
    "third": "3",
    "fourth": "4",
    "fifth": "5",
    "sixth": "6",
    "seventh": "7",
    "eighth": "8",
}


class HeaderItemStatus(BaseModel):
    field_name: str
    label: str
    found: bool
    extracted_value: str | None = None
    severity: str = "Strict — Blocks approval"
    is_blocking: bool = True
    message: str


class ExtractedSectionHeader(BaseModel):
    section: str
    raw_heading: str
    questions: int | None = None
    marks_per_question: int | None = None
    total_marks: int | None = None
    formula_str: str | None = None
    has_formula: bool = False


class PatternComplianceStatus(BaseModel):
    selected_category: str
    matched_pattern_name: str | None = None
    pattern_name_in_paper: str | None = None
    has_pattern_name: bool = False
    pattern_name_match: bool = False
    expected_total_marks: int | None = None
    found_total_marks: int | None = None
    marks_match: bool = False
    expected_duration_minutes: int | None = None
    found_duration_minutes: int | None = None
    duration_match: bool = False
    expected_sections: list[str] = Field(default_factory=list)
    found_sections: list[str] = Field(default_factory=list)
    sections_match: bool = False
    expected_section_structures: list[dict[str, Any]] = Field(default_factory=list)
    found_section_structures: list[dict[str, Any]] = Field(default_factory=list)
    discrepancies: list[str] = Field(default_factory=list)


class ExamDetailItem(BaseModel):
    field_name: str
    label: str
    found: bool
    extracted_value: str | None = None
    note: str


class ExamDetailsReport(BaseModel):
    is_approved: bool = Field(
        description="Strict: True only if all mandatory examination details are clearly given"
    )
    status: str = Field(description="'APPROVED' if complete, 'BLOCKED' if details missing")
    description: str = Field(
        default="The details of examination such as the regulations, programme, branch, semester, subject code and name, duration and maximum marks must be clearly given in the question paper."
    )
    items: dict[str, ExamDetailItem]
    missing_details: list[str] = Field(default_factory=list)


class FormatComplianceReport(BaseModel):
    report_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the generated scrutiny report",
    )
    qp_filename: str | None = Field(
        default=None, description="Filename of uploaded question paper"
    )
    is_approved: bool = Field(
        description="Strict: True only if all mandatory format & pattern requirements comply"
    )
    approval_status: str = Field(description="'APPROVED' or 'BLOCKED'")
    compliance_score: float = Field(
        description="Percentage score based on compliant mandatory items"
    )
    selected_pattern_name: str
    selected_category: str
    header_checks: dict[str, HeaderItemStatus]
    pattern_compliance: PatternComplianceStatus
    exam_details: ExamDetailsReport | None = Field(
        default=None,
        description="Scrutiny of the 8 mandatory exam details: regulations, programme, branch, semester, subject code, subject name, duration, and maximum marks",
    )
    missing_fields: list[str]
    blocking_reasons: list[str]
    extracted_metadata: dict[str, Any]
    extracted_text: str = Field(
        default="", description="Full raw extracted text from the question paper"
    )
    syllabus_filename: str | None = Field(
        default=None, description="Filename of uploaded syllabus document"
    )
    syllabus_extracted_text: str | None = Field(
        default=None, description="Extracted raw text of the syllabus"
    )
    regulation: RegulationCheckResult | None = Field(
        default=None, description="Regulation code check result (ACCEPTED or REJECTED)"
    )
    syllabus_alignment: SyllabusCoverageReport | None = Field(
        default=None, description="Criterion 3 Syllabus Alignment report (Strict Zero-Score)"
    )
    mark_distribution: MarkDistributionReport | None = Field(
        default=None, description="Criterion 4 Mark and Time Distribution report (Strict Zero-Score)"
    )
    repetition_risk: RepetitionRiskReport | None = Field(
        default=None, description="Criterion 9 Repetition Risk report (Strict Zero-Score)"
    )
    blooms_taxonomy: BloomsTaxonomyReport | None = Field(
        default=None, description="Criterion 5 Bloom's Taxonomy Scrutiny report (Strict Zero-Score)"
    )
    grammar_check: GrammarCheckReport | None = Field(
        default=None, description="Criterion 6 Grammar, Spelling and Sentence Formation report (Strict Zero-Score)"
    )
    llm_provider_used: str | None = Field(
        default=None,
        description="Identifies which LLM provider(s) and model delivered the scrutiny results",
    )


class FormatComplianceChecker:
    """Scrutiny checker for Institutional Question Papers.

    Verifies pattern naming for CAT exams, pattern structure matching for University exams,
    Maximum Marks, Duration, Section Headers, and checks all mandatory
    examination details (regulations, programme, branch, semester, subject code, name, duration, max marks).
    Institutional header check is excluded from compliance rules.
    """

    def __init__(self, patterns_dir: Path | str | None = None):
        self.patterns_dir = Path(patterns_dir) if patterns_dir else DEFAULT_PATTERNS_DIR
        self.patterns: dict[str, list[dict[str, Any]]] = self._load_patterns()

    def _load_patterns(self) -> dict[str, list[dict[str, Any]]]:
        """Load all examination patterns from JSON files in the patterns directory."""
        patterns: dict[str, list[dict[str, Any]]] = {}
        if not self.patterns_dir.exists():
            return patterns

        pattern_files = {
            "CAT-1": self.patterns_dir / "cat1_patterns.json",
            "CAT-2": self.patterns_dir / "cat2_patterns.json",
            "CAT-3": self.patterns_dir / "cat3_patterns.json",
            "University": self.patterns_dir / "university_patterns.json",
        }

        for key, filepath in pattern_files.items():
            if filepath.exists():
                try:
                    with open(filepath, encoding="utf-8") as f:
                        patterns[key] = json.load(f)
                except Exception as e:
                    print(f"Warning: Failed to load pattern file {filepath}: {e}")

        return patterns

    def get_pattern_categories(self) -> dict[str, list[dict[str, Any]]]:
        """Return categorized pattern definitions formatted for the UI."""
        categories: dict[str, list[dict[str, Any]]] = {}
        for cat_key, p_list in self.patterns.items():
            cat_items = []
            for p in p_list:
                sec_strs = []
                for s in p.get("sections", []):
                    q = s.get("questions", "")
                    m = s.get("marks_per_question", "")
                    sec_strs.append(f"{q}×{m}")

                cat_items.append(
                    {
                        "id": p.get("name"),
                        "name": p.get("name"),
                        "category": cat_key,
                        "exam_type": p.get("exam_type", cat_key),
                        "subtitle": ", ".join(sec_strs),
                        "total_marks": p.get("total_marks"),
                        "time_minutes": p.get("time_minutes"),
                        "sections": [s["name"] for s in p.get("sections", [])],
                    }
                )
            categories[cat_key] = cat_items
        return categories

    def check_document(
        self,
        file_path: Path | str,
        exam_type: str | None = None,
        pattern_name: str | None = None,
        expected_regulation_year: int | str | None = None,
    ) -> FormatComplianceReport:
        """Extract text from PDF, DOCX, or text file and check format compliance against user-selected pattern."""
        from app.services.text_extractor import extractor

        doc_data = extractor.extract(file_path)
        full_text = doc_data.get("full_text", "")
        return self.check_compliance(
            full_text,
            exam_type=exam_type,
            pattern_name=pattern_name,
            expected_regulation_year=expected_regulation_year,
        )

    def _extract_exam_pattern_name(self, text: str) -> tuple[str | None, str | None]:
        """Extract declared exam pattern name (e.g. CAT-1, CAT-2, CAT-3, University Exam)
        and map to canonical category ('CAT-1', 'CAT-2', 'CAT-3', 'University').
        """
        cat_match = re.search(
            r"\b(?:CONTINUOUS\s+ASSESSMENT\s+TEST|CONTINUOUS\s+INTERNAL\s+ASSESSMENT|"
            r"INTERNAL\s+ASSESSMENT\s+TEST|ASSESSMENT\s+TEST|CYCLE\s+TEST|UNIT\s+TEST|"
            r"CAT|IAT|CIA)\s*[-–—:]?\s*(1|2|3|III|II|I)\b",
            text,
            re.IGNORECASE,
        )
        if cat_match:
            raw = cat_match.group(0).strip()
            num = cat_match.group(1).upper()
            norm_num = "1" if num in ("1", "I") else ("2" if num in ("2", "II") else "3")
            return raw, f"CAT-{norm_num}"

        univ_match = re.search(
            r"\b(?:END\s+SEMESTER|SEMESTER|AUTONOMOUS\s+SEMESTER|UNIVERSITY|MODEL)\s+(?:THEORY\s+)?(?:EXAMINATIONS?|EXAM)\b",
            text,
            re.IGNORECASE,
        )
        if univ_match:
            raw = univ_match.group(0).strip()
            return raw, "University"

        return None, None

    def _extract_programme(self, text: str) -> str | None:
        """Extract degree / programme (e.g. B.E., B.Tech, M.E., M.Tech, M.B.A, M.C.A)."""
        explicit_prog = re.search(
            r"\b(?:Programme|Program|Degree)\b\s*[:.-]?\s*([A-Za-z0-9\.\s&/-]+?)(?=\n|Branch|Dept|Sem|Date|Time|Max|Course|$)",
            text,
            re.IGNORECASE,
        )
        if explicit_prog:
            raw_p = explicit_prog.group(1).strip()
            raw_p = re.sub(r"^[/-]\s*", "", raw_p).strip()
            if "/" in raw_p:
                raw_p = raw_p.split("/")[0].strip()
            acro = re.search(
                r"\b(B\.E\.?|B\.Tech\.?|M\.E\.?|M\.Tech\.?|M\.C\.A\.?|M\.B\.A\.?|B\.Sc\.?|M\.Sc\.?)\b",
                raw_p,
                re.IGNORECASE,
            )
            if acro:
                return acro.group(0).upper()
            if len(raw_p) >= 2 and not re.match(r"^(?:Date|Time|Max|Sem|Branch)", raw_p, re.IGNORECASE):
                return raw_p

        acro_match = re.search(
            r"\b(B\.E\.?|B\.Tech\.?|M\.E\.?|M\.Tech\.?|M\.C\.A\.?|M\.B\.A\.?|B\.Sc\.?|M\.Sc\.?|"
            r"Bachelor\s+of\s+Engineering|Bachelor\s+of\s+Technology|"
            r"Master\s+of\s+Engineering|Master\s+of\s+Technology)\b",
            text,
            re.IGNORECASE,
        )
        if acro_match:
            return acro_match.group(0).strip()
        return None

    def _extract_branch(self, text: str, programme: str | None = None) -> str | None:
        """Extract academic branch / department (e.g. Computer Science and Engineering, CSE)."""
        explicit_branch = re.search(
            r"\b(?:Branch|Dept(?:artment)?|Specialization)\b\s*[:.-]?\s*([A-Za-z\s&,-]+?)(?=\n|Sem|Date|Time|Max|Course|Degree|Programme|$)",
            text,
            re.IGNORECASE,
        )
        if explicit_branch:
            raw_b = explicit_branch.group(1).strip()
            raw_b = re.sub(r"^[/-]\s*", "", raw_b).strip()
            if len(raw_b) >= 2 and not re.match(r"^(?:Date|Time|Max|Sem|Programme|Degree)", raw_b, re.IGNORECASE):
                return raw_b

        branch_match = re.search(
            r"\b(Computer\s+Science\s+and\s+Engineering|Information\s+Technology|"
            r"Mechanical\s+Engineering|Civil\s+Engineering|"
            r"Electrical\s+and\s+Electronics\s+Engineering|"
            r"Electronics\s+and\s+Communication\s+Engineering|"
            r"Artificial\s+Intelligence\s+and\s+Data\s+Science|"
            r"Artificial\s+Intelligence\s+and\s+Machine\s+Learning|"
            r"Data\s+Science|Chemical\s+Engineering|Biomedical\s+Engineering|"
            r"Biotechnology|Mechatronics\s+Engineering|Mechatronics|"
            r"Automobile\s+Engineering|CSE|IT|ECE|EEE|MECH|CIVIL|AIDS|AIML)\b",
            text,
            re.IGNORECASE,
        )
        if branch_match:
            return branch_match.group(0).strip()

        combined_match = re.search(
            r"(?:Degree\s*/\s*Branch|Degree\s*&\s*Branch)\s*[:.-]?\s*([A-Za-z0-9\.\s&/-]+?)(?=\n|Sem|Date|Time|Max|Course|$)",
            text,
            re.IGNORECASE,
        )
        if combined_match:
            parts = combined_match.group(1).split("/")
            if len(parts) > 1:
                return parts[1].strip()

        return None

    def _extract_course_title(self, text: str) -> str | None:
        """Extract course title / subject name from question paper.
        Supports:
        1. Explicit specifiers: 'Course Title:', 'Subject Name:', 'Subject:', etc.
        2. Code - Title format: 'CS23431 - DESIGN AND ANALYSIS OF ALGORITHMS'
        3. Standalone lines without specifiers in the header block (e.g. 'DESIGN AND ANALYSIS OF ALGORITHMS').
        """
        # Find header boundary before first section heading
        part_match = re.search(r"\b(?:PART|SECTION)\s*[-–—]?[A-D]\b", text, re.IGNORECASE)
        header = text[: part_match.start()] if part_match else text[:2500]

        # 1. Explicit specifier
        explicit_match = re.search(
            r"(?:Course\s*Title|Sub(?:ject)?\s*(?:Title|Name)|Course\s*Name|Subject)\s*[:.-]\s*([A-Za-z0-9\s&,-]+?)(?=\n|Degree|Branch|Sem|Date|Time|Max|Regulation|Question|$)",
            header,
            re.IGNORECASE,
        )
        if explicit_match:
            val = explicit_match.group(1).strip()
            if len(val) >= 3 and not re.match(r"^(?:Code|Duration|Marks|Semester)", val, re.IGNORECASE):
                return val

        # 2. Code - Title format: e.g. CS23431 - DESIGN AND ANALYSIS OF ALGORITHMS
        code_title_match = re.search(
            r"\b[A-Z]{2,4}\s*\d{3,5}\s*[-–—:]\s*([A-Za-z0-9\s&,-]+?)(?=\n|\(|\r|$)",
            header,
            re.IGNORECASE,
        )
        if code_title_match:
            val = code_title_match.group(1).strip()
            if len(val) >= 3:
                return val

        # 3. Standalone title line without specifier in header
        branch_patterns = (
            r"\b(?:Computer\s+Science(?:\s+and\s+Engineering)?|Information\s+Technology|"
            r"Mechanical\s+Engineering|Civil\s+Engineering|"
            r"Electrical\s+and\s+Electronics(?:\s+Engineering)?|"
            r"Electronics\s+and\s+Communication(?:\s+Engineering)?|"
            r"Artificial\s+Intelligence(?:\s+and\s+Data\s+Science)?|"
            r"Biotechnology|Chemical\s+Engineering|Biomedical\s+Engineering|Mechatronics)\b"
        )
        ignore_patterns = [
            r"^\s*$",
            r"(?:Question\s*Paper|QP|Q\.P\.)\s*Code",
            r"(?:Course|Sub(?:ject)?)\s*Code",
            r"Semester|Sem\b",
            r"Regulation",
            r"(?:Time|Duration)",
            r"(?:Maximum|Max(?:\.|\b|imum)?|Total)\s*Marks?",
            r"PART\s*[-–—]?[A-D]",
            r"SECTION\s*[-–—]?[A-D]",
            r"B\.E|B\.Tech|M\.E|M\.Tech|M\.C\.A|M\.B\.A|DEGREE\s+EXAMINATION",
            r"COLLEGE|INSTITUTE|UNIVERSITY|AUTONOMOUS|CONTROLLER",
            r"DEPARTMENT\s+OF|BRANCH\b|PROGRAMME\b",
            branch_patterns,
            r"REG(?:ISTRATION)?\.?\s*NO|ROLL\s*NO",
            r"APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER",
            r"^[0-9\s\-–—:=/().]+$",
            r"^[A-Z]{2,4}\s*\d{3,5}$",  # Pure course code line
        ]
        combined_ignore = re.compile("|".join(f"(?:{p})" for p in ignore_patterns), re.IGNORECASE)

        candidate_lines = []
        for line in header.splitlines():
            line_clean = line.strip()
            if not line_clean:
                continue
            if combined_ignore.search(line_clean):
                continue
            line_clean = re.sub(r"^[0-9]+[.)\s-]+", "", line_clean).strip(" -–—:=/()[]")
            letter_count = len(re.findall(r"[A-Za-z]", line_clean))
            if letter_count >= 5 and len(line_clean) <= 100:
                candidate_lines.append(line_clean)

        if candidate_lines:
            return candidate_lines[0]

        return None

    def _extract_month_year(self, text: str) -> str | None:
        """Extract Month and Year of Examinations for University question papers
        (e.g. 'April/May 2026', 'Nov / Dec 2023', 'November/December 2024').
        """
        # 1. Explicit keyword: Month and Year of Examinations: ...
        m1 = re.search(
            r"(?:Month\s*(?:and|&)\s*Year(?:\s*of\s*Examinations?)?|Examination\s*Session|Session)\s*[:.-]?\s*([A-Za-z\s/&,.-]+?(?:20\d{2}))",
            text,
            re.IGNORECASE,
        )
        if m1:
            val = m1.group(1).strip(" ,.-")
            if re.search(r"20\d{2}", val):
                return val

        # 2. Paired months with 4-digit year (e.g. April/May 2026, Nov / Dec 2023, November/December 2024)
        m2 = re.search(
            r"\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*(?:/|-|&|\band\b)\s*(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*[-–—,]?\s*20\d{2})\b",
            text,
            re.IGNORECASE,
        )
        if m2:
            return m2.group(1).strip(" ,.-")

        # 3. Single month with 4-digit year (e.g. November 2024, May 2026)
        m3 = re.search(
            r"\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*[-–—,]?\s*20\d{2})\b",
            text,
            re.IGNORECASE,
        )
        if m3:
            return m3.group(1).strip(" ,.-")

        return None

    def _extract_duration_minutes(self, text: str) -> int | None:
        """Extract duration in minutes from duration/time string."""
        duration_match = re.search(
            r"(?:Duration|Time)\s*[:.-]?\s*([0-9\.\/½]+)\s*(Hours?|Hrs?|Minutes?|Mins?)?",
            text,
            re.IGNORECASE,
        )
        if not duration_match:
            duration_match = re.search(
                r"\b([0-9]+(?:\.[0-9]+)?)\s*(Hours?|Hrs?|Minutes?|Mins?)\b",
                text[:1000],
                re.IGNORECASE,
            )

        if duration_match:
            val_str = duration_match.group(1).strip()
            unit = (duration_match.group(2) or "").lower()

            if "½" in val_str or "1/2" in val_str:
                return 90
            try:
                num = float(val_str)
                if "hour" in unit or "hr" in unit or num <= 4:
                    return int(num * 60)
                else:
                    return int(num)
            except ValueError:
                pass
        return None

    def _extract_max_marks(self, text: str) -> int | None:
        """Extract maximum marks (e.g., 'Max. Marks: 50', 'Maximum: 100 Marks', 'Total Marks: 25')."""
        match = re.search(
            r"(?:Max(?:\.|\b|imum)?\s*Marks?|Total\s*Marks?)\s*[:.-]?\s*([0-9]{2,3})\b|"
            r"(?:Max(?:\.|\b|imum)?|Total)\s*[:.-]\s*([0-9]{2,3})\s*(?:Marks)?\b",
            text[:1500],
            re.IGNORECASE,
        )
        if match:
            for g in match.groups():
                if g:
                    try:
                        return int(g)
                    except ValueError:
                        pass
        return None

    def _extract_section_headers_detailed(self, text: str) -> list[ExtractedSectionHeader]:
        """Extract all occurrences of section headers and their mark formulas."""
        results: list[ExtractedSectionHeader] = []
        heading_regex = re.compile(
            r"(?i)(?:^|[\r\n]|\s{2,}|;\s*)(?:(?:UNIT\s*[-–—]?[IVX0-9]+\s*[:.-]?\s*))?"
            r"(?:PART|SECTION)\s*[-–—]?\s*([A-D])\b(?:\s*[-–—:]\s*)?([^\r\n]*)",
            re.MULTILINE,
        )
        formula_regex = re.compile(
            r"(?:\[|\()?\s*([0-9]{1,2})\s*(?:Questions?|Qs?)?\s*[\*xX×]\s*([0-9]{1,2})\s*(?:Marks?|M)?\s*=\s*([0-9]{1,3})\s*(?:Marks?|marks?|MARKS?)?\s*(?:\]|\))?"
        )

        for match in heading_regex.finditer(text):
            letter = match.group(1).upper()
            sec_name = f"Part {letter}"
            rest = match.group(2).strip()
            raw_heading = f"PART {letter} {rest}".strip()

            formula_match = formula_regex.search(rest)
            if not formula_match:
                snippet = text[match.end() : match.end() + 100].split("\n")[0]
                formula_match = formula_regex.search(snippet)
                if formula_match:
                    raw_heading = f"{raw_heading} {formula_match.group(0).strip()}".strip()

            q: int | None = None
            m: int | None = None
            tot: int | None = None
            formula_str: str | None = None
            has_formula = False

            if formula_match:
                try:
                    q = int(formula_match.group(1))
                    m = int(formula_match.group(2))
                    tot = int(formula_match.group(3))
                    formula_str = f"{q} × {m} = {tot} Marks"
                    has_formula = True
                except (ValueError, IndexError):
                    pass

            results.append(
                ExtractedSectionHeader(
                    section=sec_name,
                    raw_heading=raw_heading,
                    questions=q,
                    marks_per_question=m,
                    total_marks=tot,
                    formula_str=formula_str,
                    has_formula=has_formula,
                )
            )

        return results

    def _extract_section_headers(self, text: str) -> list[str]:
        """Extract present section headers like 'Part A', 'Part B', 'Part C'."""
        detailed = self._extract_section_headers_detailed(text)
        if detailed:
            seen = set()
            res = []
            for d in detailed:
                if d.section not in seen:
                    seen.add(d.section)
                    res.append(d.section)
            return res

        sections = []
        for part in ["A", "B", "C", "D"]:
            pattern = rf"\b(?:PART|SECTION)\s*[-–—]?\s*{part}\b"
            if re.search(pattern, text, re.IGNORECASE):
                sections.append(f"Part {part}")
        return sections

    def check_compliance(
        self,
        text: str,
        exam_type: str | None = None,
        pattern_name: str | None = None,
        expected_regulation_year: int | str | None = None,
    ) -> FormatComplianceReport:
        """Execute strict format compliance checking against exam pattern naming (CAT exams),
        pattern structure matching (University exams), and the 8 mandatory exam details.
        Institutional header checking is excluded from compliance rules.
        """
        header_checks: dict[str, HeaderItemStatus] = {}
        missing_fields: list[str] = []
        blocking_reasons: list[str] = []

        part_match = re.search(r"\b(?:PART|SECTION)\s*[-–—]?[A-D]\b", text, re.IGNORECASE)
        header_sample = text[: part_match.start()] if part_match else text[:2500]

        # Institutional Header: Extracted for metadata inspection only (NOT blocking or checked)
        inst_pattern = r"(?:COLLEGE|INSTITUTE|UNIVERSITY|AUTONOMOUS|DEPARTMENT\s+OF|CONTROLLER\s+OF\s+EXAMINATIONS|AFFILIATED\s+TO|ACCREDITED|CENTRAL\s+EVALUATION)"
        inst_match = re.search(inst_pattern, header_sample, re.IGNORECASE)
        inst_val = inst_match.group(0).strip() if inst_match else None

        # 1. Exam Pattern Name Check from question paper header
        raw_pattern_name, canonical_pattern_cat = self._extract_exam_pattern_name(header_sample)

        # 2. Subject / Course Code Check
        course_code_match = re.search(
            r"(?:Course\s*Code|Sub(?:ject)?\s*Code)\s*[:.-]?\s*([A-Z0-9]{5,9})\b|"
            r"\b([A-Z]{2,4}\s*\d{3,5}|\d{2}[A-Z]{2,4}\d{2,4})\b",
            header_sample,
            re.IGNORECASE,
        )
        cc_val = None
        if course_code_match:
            cc_candidate = (course_code_match.group(1) or course_code_match.group(2)).strip()
            if re.search(r"[A-Z]", cc_candidate, re.IGNORECASE) and re.search(r"\d", cc_candidate):
                cc_val = cc_candidate

        header_checks["course_code"] = HeaderItemStatus(
            field_name="course_code",
            label="Course Code",
            found=bool(cc_val),
            extracted_value=cc_val,
            message=f"Course code found: {cc_val}"
            if cc_val
            else "Course code is missing or invalid format",
        )

        # 3. Subject / Course Title Check
        # Supports explicit specifiers ('Course Title:', 'Subject Name:'),
        # code-title formats ('CS23431 - DESIGN AND ANALYSIS OF ALGORITHMS'),
        # and standalone subject title lines without specifiers.
        title_val = self._extract_course_title(text)

        header_checks["course_title"] = HeaderItemStatus(
            field_name="course_title",
            label="Course Title",
            found=bool(title_val),
            extracted_value=title_val,
            message=f"Course title found: {title_val}"
            if title_val
            else "Course title / subject name is missing",
        )

        # 4. Programme & Branch Checks
        prog_val = self._extract_programme(header_sample)
        branch_val = self._extract_branch(header_sample, programme=prog_val)
        deg_val = None
        if prog_val and branch_val:
            deg_val = f"{prog_val} / {branch_val}"
        elif prog_val:
            deg_val = prog_val
        elif branch_val:
            deg_val = branch_val

        header_checks["degree_branch"] = HeaderItemStatus(
            field_name="degree_branch",
            label="Degree / Branch",
            found=bool(prog_val or branch_val),
            extracted_value=deg_val,
            message=f"Programme & Branch identified: {deg_val}"
            if deg_val
            else "Degree and Branch details are missing",
        )

        # 5. Semester Check
        sem_val = None
        sem_match = re.search(
            r"(?:Semester|Sem|Year\s*/\s*Sem)\s*[:.-]?\s*\b([0-9IVXLCDM]{1,4})\b|"
            r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth)\s+Semester\b",
            header_sample,
            re.IGNORECASE,
        )
        if sem_match:
            if sem_match.group(1):
                sem_val = sem_match.group(1).strip()
            elif sem_match.group(2):
                word = sem_match.group(2).lower()
                sem_val = f"{WORD_SEMESTERS.get(word, word)} (from {sem_match.group(2)})"

        header_checks["semester"] = HeaderItemStatus(
            field_name="semester",
            label="Semester",
            found=bool(sem_val),
            extracted_value=sem_val,
            message=f"Semester found: {sem_val}" if sem_val else "Semester number is missing",
        )

        # 6. Exam Date Check
        # For University papers, check Month and Year of Examinations (e.g. April/May 2026) instead of calendar date.
        # For CAT papers, check standard exam calendar date (e.g. 15.02.2024).
        is_univ_check = bool(
            (exam_type and "univ" in exam_type.lower())
            or (pattern_name and "univ" in pattern_name.lower())
        )
        if is_univ_check:
            month_year_val = self._extract_month_year(header_sample)
            date_val = month_year_val
            header_checks["exam_date"] = HeaderItemStatus(
                field_name="exam_date",
                label="Month & Year of Examination",
                found=bool(month_year_val),
                extracted_value=month_year_val,
                message=f"Month and Year of Examinations found: {month_year_val}"
                if month_year_val
                else "Month and Year of Examinations is missing (e.g. April/May 2026, Nov/Dec 2023)",
            )
        else:
            date_match = re.search(
                r"(?:Date|Exam\s*Date)\s*[:.-]?\s*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4}|[0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+[0-9]{2,4})",
                header_sample,
                re.IGNORECASE,
            )
            date_val = date_match.group(1).strip() if date_match else None
            header_checks["exam_date"] = HeaderItemStatus(
                field_name="exam_date",
                label="Exam Date",
                found=bool(date_match),
                extracted_value=date_val,
                message=f"Exam date found: {date_val}" if date_match else "Exam date is missing",
            )

        # 7. Duration Check
        duration_mins = self._extract_duration_minutes(header_sample)
        header_checks["duration"] = HeaderItemStatus(
            field_name="duration",
            label="Duration",
            found=duration_mins is not None,
            extracted_value=f"{duration_mins} Minutes" if duration_mins else None,
            message=f"Duration found: {duration_mins} mins"
            if duration_mins
            else "Duration / Time is missing",
        )

        # 8. Maximum Marks Check
        max_marks = self._extract_max_marks(header_sample)
        header_checks["maximum_marks"] = HeaderItemStatus(
            field_name="maximum_marks",
            label="Maximum Marks",
            found=max_marks is not None,
            extracted_value=str(max_marks) if max_marks else None,
            message=f"Maximum Marks found: {max_marks}"
            if max_marks
            else "Maximum Marks header is missing",
        )

        # 9. Section Headers & Mark Structures Check
        detailed_headers = self._extract_section_headers_detailed(text)

        # Validate against the user-selected pattern
        pattern_status = self._verify_pattern_compliance(
            exam_type=exam_type,
            pattern_name=pattern_name,
            found_marks=max_marks,
            found_duration=duration_mins,
            detailed_headers=detailed_headers,
            found_pattern_name=raw_pattern_name,
            canonical_category=canonical_pattern_cat,
        )

        # Build readable section summary
        section_summary_items = []
        for sec in ["Part A", "Part B", "Part C", "Part D"]:
            sec_matches = [h for h in detailed_headers if h.section.lower() == sec.lower()]
            if sec_matches:
                formula_desc = sec_matches[0].formula_str or "no mark formula"
                section_summary_items.append(f"{len(sec_matches)} × {sec} [{formula_desc}]")

        extracted_sec_summary = ", ".join(section_summary_items) if section_summary_items else None
        pattern_status.found_sections = (
            section_summary_items
            if section_summary_items
            else [h.section for h in detailed_headers]
        )

        section_discrepancies = [
            d
            for d in pattern_status.discrepancies
            if any(term in d.lower() for term in ["section", "mark structure", "heading"])
        ]

        header_checks["section_headers"] = HeaderItemStatus(
            field_name="section_headers",
            label="Section Headers & Mark Structures",
            found=pattern_status.sections_match,
            extracted_value=extracted_sec_summary,
            message=(
                f"Section mark structures verified: {extracted_sec_summary}"
                if pattern_status.sections_match
                else (
                    "; ".join(section_discrepancies)
                    if section_discrepancies
                    else "Section headers or mark structures do not comply with selected pattern"
                )
            ),
        )

        is_univ = (pattern_status.selected_category.upper() == "UNIVERSITY")

        # Re-verify Month & Year of Examination if selected category resolved to University
        if is_univ and header_checks.get("exam_date") and header_checks["exam_date"].label != "Month & Year of Examination":
            month_year_val = self._extract_month_year(header_sample)
            date_val = month_year_val
            header_checks["exam_date"] = HeaderItemStatus(
                field_name="exam_date",
                label="Month & Year of Examination",
                found=bool(month_year_val),
                extracted_value=month_year_val,
                message=f"Month and Year of Examinations found: {month_year_val}"
                if month_year_val
                else "Month and Year of Examinations is missing (e.g. April/May 2026, Nov/Dec 2023)",
            )

        # 10. Exam / Pattern Name Check
        # For University exams, no need to declare pattern name in text — verify whether selected pattern matches QP structure.
        # For CAT exams, check declared name matches selected category.

        if is_univ:
            if pattern_status.pattern_name_match:
                pat_msg = f"Question paper structure matches selected pattern '{pattern_status.matched_pattern_name}'"
                pat_val = f"{pattern_status.matched_pattern_name} (Structure Verified)"
            else:
                pat_msg = f"Question paper structure does not match selected pattern '{pattern_status.matched_pattern_name}': {'; '.join(pattern_status.discrepancies)}"
                pat_val = pattern_status.pattern_name_in_paper or f"{pattern_status.matched_pattern_name} (Mismatched)"

            header_checks["exam_pattern_name"] = HeaderItemStatus(
                field_name="exam_pattern_name",
                label="Exam / Pattern Name",
                found=pattern_status.pattern_name_match,
                extracted_value=pat_val,
                severity="Strict — Blocks approval",
                is_blocking=True,
                message=pat_msg,
            )
        else:
            if not pattern_status.has_pattern_name:
                pat_msg = f"Missing exam pattern name in question paper (expected {pattern_status.selected_category})"
            elif not pattern_status.pattern_name_match:
                pat_msg = f"Pattern name mismatch: Question paper specifies '{pattern_status.pattern_name_in_paper}' ({canonical_pattern_cat}), but user selected '{pattern_status.selected_category}'"
            else:
                pat_msg = f"Exam pattern confirmed: '{pattern_status.pattern_name_in_paper}' matches selected '{pattern_status.selected_category}'"

            header_checks["exam_pattern_name"] = HeaderItemStatus(
                field_name="exam_pattern_name",
                label="Exam / Pattern Name",
                found=bool(pattern_status.has_pattern_name and pattern_status.pattern_name_match),
                extracted_value=pattern_status.pattern_name_in_paper,
                severity="Strict — Blocks approval",
                is_blocking=True,
                message=pat_msg,
            )

        # 11. Regulation Code Check (e.g. [Regulations 2023])
        reg_result = check_regulation(text, expected_year=expected_regulation_year)
        header_checks["regulation_code"] = HeaderItemStatus(
            field_name="regulation_code",
            label="Regulation Code",
            found=reg_result.is_accepted,
            extracted_value=reg_result.regulation_code or reg_result.raw_match,
            severity="Strict — Blocks approval",
            is_blocking=True,
            message=reg_result.message,
        )

        # 12. Assemble the 8 Mandatory Examination Details Report
        exam_items = {
            "regulations": ExamDetailItem(
                field_name="regulations",
                label="Regulations",
                found=reg_result.is_accepted,
                extracted_value=reg_result.regulation_code or reg_result.raw_match,
                note=reg_result.message,
            ),
            "programme": ExamDetailItem(
                field_name="programme",
                label="Programme",
                found=bool(prog_val),
                extracted_value=prog_val,
                note=f"Programme found: {prog_val}"
                if prog_val
                else "Programme is missing from question paper (e.g. B.E., B.Tech, M.E.)",
            ),
            "branch": ExamDetailItem(
                field_name="branch",
                label="Branch",
                found=bool(branch_val),
                extracted_value=branch_val,
                note=f"Branch found: {branch_val}"
                if branch_val
                else "Branch / department is missing from question paper",
            ),
            "semester": ExamDetailItem(
                field_name="semester",
                label="Semester",
                found=bool(sem_val),
                extracted_value=sem_val,
                note=f"Semester found: {sem_val}"
                if sem_val
                else "Semester number is missing from question paper",
            ),
            "subject_code": ExamDetailItem(
                field_name="subject_code",
                label="Subject Code",
                found=bool(cc_val),
                extracted_value=cc_val,
                note=f"Subject code found: {cc_val}"
                if cc_val
                else "Subject code is missing or invalid format",
            ),
            "subject_name": ExamDetailItem(
                field_name="subject_name",
                label="Subject Name",
                found=bool(title_val),
                extracted_value=title_val,
                note=f"Subject name found: {title_val}"
                if title_val
                else "Subject name / title is missing from question paper",
            ),
            "duration": ExamDetailItem(
                field_name="duration",
                label="Duration",
                found=duration_mins is not None,
                extracted_value=f"{duration_mins} Minutes" if duration_mins else None,
                note=f"Duration found: {duration_mins} mins"
                if duration_mins
                else "Duration / time is missing from question paper",
            ),
            "maximum_marks": ExamDetailItem(
                field_name="maximum_marks",
                label="Maximum Marks",
                found=max_marks is not None,
                extracted_value=f"{max_marks} Marks" if max_marks else None,
                note=f"Maximum marks found: {max_marks}"
                if max_marks
                else "Maximum marks header is missing from question paper",
            ),
        }

        missing_exam_details = [it.label for it in exam_items.values() if not it.found]
        exam_details_approved = len(missing_exam_details) == 0
        exam_details_report = ExamDetailsReport(
            is_approved=exam_details_approved,
            status="APPROVED" if exam_details_approved else "BLOCKED",
            description="The details of examination such as the regulations, programme, branch, semester, subject code and name, duration and maximum marks must be clearly given in the question paper.",
            items=exam_items,
            missing_details=missing_exam_details,
        )

        # Evaluate Header completeness
        for _key, item in header_checks.items():
            if not item.found:
                missing_fields.append(item.label)
                blocking_reasons.append(f"Format Failure: {item.label} is invalid. {item.message}")

        # Evaluate Pattern Compliance discrepancies
        if is_univ:
            if not pattern_status.pattern_name_match:
                reason = f"Pattern Mismatch: Question paper structure does not match selected pattern '{pattern_status.matched_pattern_name}'."
                if reason not in blocking_reasons:
                    blocking_reasons.append(reason)
        else:
            if not pattern_status.has_pattern_name:
                reason = f"Pattern Failure: Question paper does not declare an exam pattern name (e.g. {pattern_status.selected_category})."
                if reason not in blocking_reasons:
                    blocking_reasons.append(reason)
            elif not pattern_status.pattern_name_match:
                reason = f"Pattern Mismatch: Question paper declares '{pattern_status.pattern_name_in_paper}' ({canonical_pattern_cat}), which does not match selected pattern '{pattern_status.selected_category}'."
                if reason not in blocking_reasons:
                    blocking_reasons.append(reason)

        if not pattern_status.marks_match:
            blocking_reasons.append(
                f"Pattern Mismatch: Maximum Marks ({max_marks}) does not match expected "
                f"{pattern_status.expected_total_marks} marks for pattern '{pattern_status.matched_pattern_name or exam_type}'"
            )
        if not pattern_status.duration_match:
            blocking_reasons.append(
                f"Pattern Mismatch: Duration ({duration_mins} mins) does not match expected "
                f"{pattern_status.expected_duration_minutes} mins for pattern '{pattern_status.matched_pattern_name or exam_type}'"
            )
        if not pattern_status.sections_match:
            for disc in section_discrepancies:
                reason = f"Pattern Mismatch: {disc}"
                if reason not in blocking_reasons and not any(disc in r for r in blocking_reasons):
                    blocking_reasons.append(reason)

        # Evaluate Exam Details completeness
        for it in exam_items.values():
            if not it.found:
                reason = f"Exam Details Failure: {it.label} is not clearly given in the question paper."
                if reason not in blocking_reasons:
                    blocking_reasons.append(reason)

        # Strict Compliance Rule: Blocks approval if any mandatory header, pattern check, or exam detail fails
        total_checks = len(header_checks) + 3
        passed_checks = sum(1 for item in header_checks.values() if item.found)
        if pattern_status.marks_match:
            passed_checks += 1
        if pattern_status.duration_match:
            passed_checks += 1
        if pattern_status.sections_match:
            passed_checks += 1

        compliance_score = round((passed_checks / total_checks) * 100, 2)
        is_approved = len(blocking_reasons) == 0

        return FormatComplianceReport(
            is_approved=is_approved,
            approval_status="APPROVED" if is_approved else "BLOCKED",
            compliance_score=compliance_score,
            selected_pattern_name=pattern_status.matched_pattern_name or pattern_name or "Custom",
            selected_category=pattern_status.selected_category,
            header_checks=header_checks,
            pattern_compliance=pattern_status,
            exam_details=exam_details_report,
            missing_fields=missing_fields,
            blocking_reasons=blocking_reasons,
            extracted_metadata={
                "institutional_header": inst_val,
                "pattern_name_in_paper": pattern_status.pattern_name_in_paper,
                "programme": prog_val,
                "branch": branch_val,
                "course_code": cc_val,
                "course_title": title_val,
                "degree_branch": deg_val,
                "semester": sem_val,
                "exam_date": date_val,
                "duration_minutes": duration_mins,
                "maximum_marks": max_marks,
                "sections": pattern_status.found_sections,
                "regulation_code": reg_result.regulation_code,
            },
            extracted_text=text,
            regulation=reg_result,
        )

    def _verify_pattern_compliance(
        self,
        exam_type: str | None,
        pattern_name: str | None,
        found_marks: int | None,
        found_duration: int | None,
        detailed_headers: list[ExtractedSectionHeader],
        found_pattern_name: str | None = None,
        canonical_category: str | None = None,
    ) -> PatternComplianceStatus:
        """Find the pattern and verify pattern naming, marks, duration, and section headers with mark structures.
        For University patterns, text pattern name is not required; instead verifies question paper matches
        user-selected pattern structure.
        """
        category = "CAT-1"
        target_pattern = None

        # 1. Search by exact pattern_name if given
        if pattern_name:
            for cat_key, p_list in self.patterns.items():
                for p in p_list:
                    if p.get("name") == pattern_name:
                        target_pattern = p
                        category = cat_key
                        break
                if target_pattern:
                    break

        # 2. Search by exam_type if pattern not yet found
        if not target_pattern and exam_type:
            key_map = {
                "CAT1": "CAT-1",
                "CAT-1": "CAT-1",
                "CAT2": "CAT-2",
                "CAT-2": "CAT-2",
                "CAT3": "CAT-3",
                "CAT-3": "CAT-3",
                "UNIVERSITY": "University",
                "University": "University",
            }
            category = key_map.get(exam_type.strip(), exam_type.strip())
            p_list = self.patterns.get(category, [])
            if p_list:
                target_pattern = p_list[0]

        is_university = (category.upper() == "UNIVERSITY")

        status = PatternComplianceStatus(
            selected_category=category,
            found_total_marks=found_marks,
            found_duration_minutes=found_duration,
            found_sections=[h.section for h in detailed_headers],
            pattern_name_in_paper=found_pattern_name,
            has_pattern_name=bool(found_pattern_name) or is_university,
            found_section_structures=[
                {
                    "section": h.section,
                    "raw_heading": h.raw_heading,
                    "questions": h.questions,
                    "marks_per_question": h.marks_per_question,
                    "total_marks": h.total_marks,
                    "formula": h.formula_str,
                }
                for h in detailed_headers
            ],
        )

        # Check pattern name in paper vs selected pattern category
        if is_university:
            # For University: no need to check pattern name string in question paper text.
            # Only flag if paper explicitly claims to be a CAT exam.
            if found_pattern_name and canonical_category in ("CAT-1", "CAT-2", "CAT-3"):
                status.pattern_name_match = False
                status.discrepancies.append(
                    f"Pattern Name Mismatch: Question paper declares '{found_pattern_name}' ({canonical_category}), but user selected University pattern"
                )
            else:
                # Tentatively true; will be verified against target_pattern structure below
                status.pattern_name_match = True
        else:
            # For CAT exams: strictly require pattern name in question paper and match selected
            if found_pattern_name:
                cat_norm = category.upper().replace(" ", "").replace("-", "")
                paper_norm = (canonical_category or "").upper().replace(" ", "").replace("-", "")
                status.pattern_name_match = (cat_norm == paper_norm)
                if not status.pattern_name_match:
                    status.discrepancies.append(
                        f"Pattern Name Mismatch: Question paper declares '{found_pattern_name}' ({canonical_category}), but selected pattern is '{category}'"
                    )
            else:
                status.pattern_name_match = False
                status.discrepancies.append(
                    f"Missing Pattern Name: Question paper does not declare an exam pattern name (e.g. {category})"
                )

        if not target_pattern:
            status.discrepancies.append(
                f"No pattern definition found for '{pattern_name or exam_type}'"
            )
            return status

        status.matched_pattern_name = target_pattern.get("name")
        status.expected_total_marks = target_pattern.get("total_marks")
        status.expected_duration_minutes = target_pattern.get("time_minutes")
        status.expected_sections = [s["name"] for s in target_pattern.get("sections", [])]
        expected_structs = target_pattern.get("section_structures", [])
        status.expected_section_structures = expected_structs

        # Verify Marks
        status.marks_match = found_marks is not None and found_marks == status.expected_total_marks
        if not status.marks_match:
            status.discrepancies.append(
                f"Marks mismatch: Found {found_marks}, expected {status.expected_total_marks}"
            )

        # Verify Duration
        status.duration_match = (
            found_duration is not None and found_duration == status.expected_duration_minutes
        )
        if not status.duration_match:
            status.discrepancies.append(
                f"Duration mismatch: Found {found_duration} mins, expected {status.expected_duration_minutes} mins"
            )

        # Verify Section Structures
        if expected_structs:
            all_sections_ok = True
            for struct in expected_structs:
                sec_name = struct["section"]
                exp_count = struct["count"]
                exp_formula = struct.get("formula", "")
                exp_q = struct.get("questions")
                exp_m = struct.get("marks_per_question")
                exp_tot = struct.get("total_marks")

                matches = [h for h in detailed_headers if h.section.lower() == sec_name.lower()]

                if len(matches) != exp_count:
                    all_sections_ok = False
                    if len(matches) < exp_count:
                        status.discrepancies.append(
                            f"Missing section headings: Expected {exp_count} headings of '{sec_name}' "
                            f"with mark structure [{exp_formula}], but found {len(matches)}."
                        )
                    else:
                        status.discrepancies.append(
                            f"Unexpected section headings: Expected {exp_count} headings of '{sec_name}', "
                            f"but found {len(matches)}."
                        )
                    continue

                for idx, h in enumerate(matches, 1):
                    if not h.has_formula:
                        all_sections_ok = False
                        status.discrepancies.append(
                            f"Missing mark structure: Heading '{h.raw_heading}' does not specify "
                            f"the required mark structure [{exp_formula}]."
                        )
                    elif (h.questions, h.marks_per_question, h.total_marks) != (
                        exp_q,
                        exp_m,
                        exp_tot,
                    ):
                        all_sections_ok = False
                        hint = ""
                        if (h.questions, h.marks_per_question) in [(6, 2), (1, 13)]:
                            hint = " (which corresponds to Alternate pattern)"
                        elif (h.questions, h.marks_per_question) in [(5, 2), (1, 15)]:
                            hint = " (which corresponds to Standard pattern)"
                        elif (h.questions, h.marks_per_question) in [(5, 16)]:
                            hint = " (which corresponds to University Pattern 2)"
                        elif (h.questions, h.marks_per_question) in [(5, 13)]:
                            hint = " (which corresponds to University Pattern 1)"

                        status.discrepancies.append(
                            f"Mark structure mismatch in {sec_name} (heading {idx}): Found [{h.formula_str}]{hint}, "
                            f"but selected pattern '{target_pattern.get('name')}' strictly requires [{exp_formula}]."
                        )

            status.sections_match = all_sections_ok and not any(
                any(term in d.lower() for term in ["section", "mark structure", "heading"])
                for d in status.discrepancies
            )
        else:
            expected_set = set(status.expected_sections)
            found_set = {h.section for h in detailed_headers}
            status.sections_match = expected_set.issubset(found_set) and len(expected_set) > 0
            if not status.sections_match:
                missing_secs = list(expected_set - found_set)
                status.discrepancies.append(f"Missing required section headers: {missing_secs}")

        # For University: Verify that the user-selected pattern structure matches the question paper
        if is_university:
            struct_match = (
                status.marks_match
                and status.sections_match
                and (status.duration_match or found_duration is None)
            )
            if not struct_match:
                status.pattern_name_match = False
                if not any("Pattern Structure Mismatch" in d for d in status.discrepancies):
                    status.discrepancies.append(
                        f"Pattern Structure Mismatch: Question paper does not match selected pattern '{target_pattern.get('name')}'"
                    )
            else:
                status.pattern_name_match = True

        return status


checker = FormatComplianceChecker()
