import hashlib
import re
from pathlib import Path
from typing import Any

import docx
import pymupdf as fitz

from app.schemas.syllabus import ParsedSyllabus, SyllabusTopicRecord

ROMAN_TO_INT = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "FOUR": 4,
    "FIVE": 5,
}

# Regex to match UNIT / MODULE / CHAPTER / PART headings
UNIT_PATTERN = re.compile(
    r"^\s*(?:UNIT|MODULE|CHAPTER|PART)\s*[-:–—.]?\s*"
    r"(I{1,3}|IV|V|VI{0,3}|IX|X|[1-9]\d?|ONE|TWO|THREE|FOUR|FIVE)\b"
    r"[:\s–—.]*(.*?)$",
    re.IGNORECASE,
)

# Regex to extract explicitly declared Course Outcomes (CO)
CO_EXPLICIT_PATTERN = re.compile(
    r"\b(?:CO|Course\s+Outcome)\s*[:\-_]?\s*([1-6])\b",
    re.IGNORECASE,
)


class SyllabusParser:
    """Syllabus parser extracting structured units, topics, subtopics,

    explicit Course Outcomes (COs), and page metadata from PDF and DOCX files.
    """

    @classmethod
    def parse_file(
        cls,
        file_path: str | Path,
        syllabus_id: str | None = None,
        course_code: str | None = None,
        course_title: str | None = None,
    ) -> ParsedSyllabus:
        """Parse a PDF or DOCX syllabus document into a structured ParsedSyllabus object."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Syllabus file not found: {path}")

        ext = path.suffix.lower()
        if ext == ".pdf":
            pages_data = cls._read_pdf(path)
        elif ext in [".docx", ".doc"]:
            pages_data = cls._read_docx(path)
        elif ext == ".txt":
            pages_data = cls._read_txt(path)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Must be PDF or DOCX.")

        # Compute or assign deterministic syllabus ID if not provided
        if not syllabus_id:
            hasher = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()[:12]
            code_prefix = course_code.replace(" ", "_") if course_code else path.stem
            syllabus_id = f"syl_{code_prefix}_{file_hash}"

        return cls._structure_content(
            pages_data=pages_data,
            syllabus_id=syllabus_id,
            file_name=path.name,
            file_type=ext.lstrip("."),
            default_course_code=course_code,
            default_course_title=course_title,
        )

    @classmethod
    def _read_pdf(cls, path: Path) -> list[dict[str, Any]]:
        """Extract text page by page from PDF using PyMuPDF."""
        doc = fitz.open(str(path))
        pages_data = []
        try:
            for page_idx in range(len(doc)):
                page = doc.load_page(page_idx)
                text = page.get_text("text")
                pages_data.append(
                    {
                        "page_number": page_idx + 1,
                        "text": text,
                    }
                )
        finally:
            doc.close()
        return pages_data

    @classmethod
    def _read_docx(cls, path: Path) -> list[dict[str, Any]]:
        """Extract text from Word document using python-docx."""
        doc = docx.Document(str(path))
        lines: list[str] = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                lines.append(text)

        for table in doc.tables:
            for row in table.rows:
                row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_texts:
                    lines.append(" | ".join(row_texts))

        full_doc_text = "\n".join(lines)
        return [{"page_number": 1, "text": full_doc_text}]

    @classmethod
    def _read_txt(cls, path: Path) -> list[dict[str, Any]]:
        """Extract text from plain text file."""
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        return [{"page_number": 1, "text": text}]

    @classmethod
    def _extract_co_identifiers(cls, text: str) -> list[str]:
        """Extract explicitly declared Course Outcome tags (e.g., 'CO1', 'CO2').

        Strict rule: Do NOT infer or hallucinate CO mappings when absent.
        """
        matches = CO_EXPLICIT_PATTERN.findall(text)
        if not matches:
            return []
        # Return unique normalized CO identifiers in sorted order, e.g. ['CO1', 'CO2']
        unique_cos = sorted({f"CO{m.strip()}" for m in matches if m.strip()})
        return unique_cos

    @classmethod
    def _parse_unit_number(cls, raw_num: str) -> int | None:
        """Convert Roman numeral or numeric string to integer."""
        raw_upper = raw_num.strip().upper()
        if raw_upper in ROMAN_TO_INT:
            return ROMAN_TO_INT[raw_upper]
        if raw_upper.isdigit():
            return int(raw_upper)
        return None

    @classmethod
    def _clean_unit_title(cls, raw_title: str) -> str:
        """Clean unit title by removing trailing hours, periods, or CO indicators."""
        title = raw_title.strip()
        # Remove trailing hours/periods e.g. '9 Hours', '9 Periods', '9'
        title = re.sub(
            r"\s+\d+\s*(?:Hours|Periods|hrs|periods)?\s*$", "", title, flags=re.IGNORECASE
        )
        # Remove trailing/bracketed CO identifiers like (CO1) or [CO2] from the title
        title = re.sub(r"[\(\[\{]\s*CO\s*[1-6]\s*[\)\]\}]", "", title, flags=re.IGNORECASE)
        # Remove leading punctuation
        title = title.strip(" :–—.-")
        return title.strip() or "UNTITLED UNIT"

    @classmethod
    def _split_into_topics(cls, text_block: str) -> list[tuple[str, list[str]]]:
        """Split unit content into discrete topics and their subtopics.

        Does NOT treat an entire syllabus or unit as one single chunk.
        Handles:
        1. Semicolons ';'
        2. En-dash '–', em-dash '—', or spaced hyphens ' - '
        3. Commas ',' outside parentheses '()' and brackets '[]' when no semicolons/dashes exist
        4. Parenthesized subtopics, e.g. 'notation (pseudo code, flow chart, programming language)'
        5. Colon-separated subtopics, e.g. 'Illustrative problems: find minimum, insert a card...'
        """
        raw_lines = [line.strip() for line in text_block.split("\n") if line.strip()]
        combined_text = " ".join(raw_lines)

        has_semicolon = ";" in combined_text
        has_dash = bool(re.search(r"\s+[-–—]\s+|[–—]", combined_text))

        # If semicolons or dashes are present, they are the primary delimiters.
        # Otherwise, commas outside parentheses/brackets are the primary delimiters.
        use_comma_as_topic_delimiter = not (has_semicolon or has_dash)

        chunks: list[str] = []
        current: list[str] = []
        paren_depth = 0
        bracket_depth = 0
        n = len(combined_text)
        idx = 0

        while idx < n:
            char = combined_text[idx]

            if char == "(":
                paren_depth += 1
                current.append(char)
            elif char == ")":
                if paren_depth > 0:
                    paren_depth -= 1
                current.append(char)
            elif char == "[":
                bracket_depth += 1
                current.append(char)
            elif char == "]":
                if bracket_depth > 0:
                    bracket_depth -= 1
                current.append(char)
            elif paren_depth == 0 and bracket_depth == 0:
                is_semicolon = (char == ";")
                is_dash = (
                    char in ["–", "—"]
                    or (
                        char == "-"
                        and idx > 0
                        and combined_text[idx - 1] == " "
                        and idx + 1 < n
                        and combined_text[idx + 1] == " "
                    )
                )
                is_period = (
                    char == "."
                    and (idx + 1 >= n or combined_text[idx + 1].isupper() or combined_text[idx + 1] == " ")
                    and len(current) > 10
                )
                is_comma = (char == "," and use_comma_as_topic_delimiter)

                if is_semicolon or is_dash or is_period or is_comma:
                    c_str = "".join(current).strip(" .–—,;\t\n")
                    if c_str and len(c_str) >= 2:
                        chunks.append(c_str)
                    current = []
                    if is_dash and char == "-" and idx + 1 < n and combined_text[idx + 1] == " ":
                        idx += 1
                else:
                    current.append(char)
            else:
                current.append(char)
            idx += 1

        if current:
            c_str = "".join(current).strip(" .–—,;\t\n")
            if c_str and len(c_str) >= 2:
                chunks.append(c_str)

        # Fallback if no delimiter matched at all
        if not chunks and combined_text.strip():
            chunks = [combined_text.strip()]

        results: list[tuple[str, list[str]]] = []
        for chunk in chunks:
            # Case 1: 'Topic Title (subtopic 1, subtopic 2...)'
            m_paren = re.search(r"^(.*?)\s*\((.*?)\)$", chunk)
            if m_paren and len(m_paren.group(1).strip()) >= 2:
                sub_raw = m_paren.group(2).split(",")
                subs = [s.strip(" .;") for s in sub_raw if len(s.strip(" .;")) >= 2]
                results.append((chunk, subs))
            # Case 2: 'Topic Title: subtopic 1, subtopic 2...'
            elif ":" in chunk and not chunk.lower().startswith("unit"):
                parts = chunk.split(":", 1)
                main_t = parts[0].strip()
                subs = [s.strip(" .;") for s in parts[1].split(",") if len(s.strip(" .;")) >= 2]
                results.append((main_t, subs))
            else:
                results.append((chunk, []))

        return results

    @classmethod
    def _structure_content(
        cls,
        pages_data: list[dict[str, Any]],
        syllabus_id: str,
        file_name: str,
        file_type: str,
        default_course_code: str | None = None,
        default_course_title: str | None = None,
    ) -> ParsedSyllabus:
        """Process page-by-page text streams into structured SyllabusTopicRecord entries."""
        detected_course_code = default_course_code
        detected_course_title = default_course_title

        # First pass: look for Course Code (e.g. CS3351) if not provided
        first_page_text = pages_data[0]["text"] if pages_data else ""
        if not detected_course_code:
            code_match = re.search(r"\b([A-Z]{2,4}\s*\d{4,5})\b", first_page_text)
            if code_match:
                detected_course_code = code_match.group(1).replace(" ", "")

        # Current parsing state
        current_unit_number: int | None = None
        current_unit_title: str = "UNASSIGNED / PREAMBLE"
        current_raw_heading: str | None = None
        current_unit_cos: list[str] = []
        is_unrecognized_unit: bool = True
        unit_counter = 0
        topic_counter = 0

        topics: list[SyllabusTopicRecord] = []
        has_unrecognized_units = False

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]
            lines = [ln.strip() for ln in page_text.split("\n") if ln.strip()]

            # Group lines into unit blocks
            i = 0
            while i < len(lines):
                line = lines[i]

                # Check if this line is a Unit header
                unit_match = UNIT_PATTERN.match(line)
                if unit_match:
                    raw_num = unit_match.group(1)
                    raw_title = unit_match.group(2)

                    parsed_num = cls._parse_unit_number(raw_num)
                    clean_title = cls._clean_unit_title(raw_title)

                    # Extract explicitly declared CO in heading
                    heading_cos = cls._extract_co_identifiers(line)

                    # If the title is on the next line (e.g. line was just "UNIT I" or "UNIT 1")
                    if not clean_title and (i + 1) < len(lines):
                        next_line = lines[i + 1]
                        if not UNIT_PATTERN.match(next_line):
                            clean_title = cls._clean_unit_title(next_line)
                            heading_cos.extend(cls._extract_co_identifiers(next_line))
                            i += 1

                    current_unit_number = parsed_num
                    current_unit_title = clean_title or f"UNIT {parsed_num}"
                    current_raw_heading = line
                    current_unit_cos = sorted(set(heading_cos))
                    is_unrecognized_unit = False
                    unit_counter += 1
                    i += 1
                    continue

                # Content line: accumulate lines until next unit or end of page
                content_lines = []
                while i < len(lines) and not UNIT_PATTERN.match(lines[i]):
                    content_lines.append(lines[i])
                    i += 1

                content_block = " ".join(content_lines).strip()
                if not content_block:
                    continue

                if is_unrecognized_unit:
                    has_unrecognized_units = True
                    low_block = content_block.lower()
                    if low_block.startswith("syllabus") and len(content_block.splitlines()) <= 1 and not detected_course_title:
                        clean_t = re.sub(
                            r"^\s*syllabus\s*[-:–—.]?\s*",
                            "",
                            content_block,
                            flags=re.IGNORECASE,
                        ).strip()
                        if clean_t and len(clean_t) < 80:
                            detected_course_title = clean_t
                            continue

                # Extract discrete topics from this block
                extracted_topics = cls._split_into_topics(content_block)
                for topic_title, subtopics in extracted_topics:
                    topic_counter += 1

                    # Look for explicit CO in the topic text
                    explicit_topic_cos = cls._extract_co_identifiers(topic_title)
                    for st in subtopics:
                        explicit_topic_cos.extend(cls._extract_co_identifiers(st))

                    combined_cos = sorted(set(current_unit_cos + explicit_topic_cos))

                    # Format rich searchable content chunk
                    prefix_parts = []
                    if current_unit_number is not None:
                        prefix_parts.append(f"Unit {current_unit_number}: {current_unit_title}")
                    else:
                        prefix_parts.append(f"Section: {current_unit_title}")

                    if combined_cos:
                        prefix_parts.append(f"[{', '.join(combined_cos)}]")

                    content_str = f"{' | '.join(prefix_parts)} | Topic: {topic_title}"
                    if subtopics:
                        content_str += f" | Subtopics: {', '.join(subtopics)}"

                    topic_id = (
                        f"{syllabus_id}_u{current_unit_number or 'unrec'}_t{topic_counter:03d}"
                    )

                    topic_record = SyllabusTopicRecord(
                        topic_id=topic_id,
                        syllabus_id=syllabus_id,
                        course_code=detected_course_code,
                        course_title=detected_course_title,
                        unit_number=current_unit_number,
                        unit_title=current_unit_title,
                        raw_unit_heading=current_raw_heading,
                        topic_title=topic_title,
                        subtopics=subtopics,
                        content=content_str,
                        co_identifiers=combined_cos,
                        source_page=page_num,
                        source_file=file_name,
                        is_unrecognized_unit=is_unrecognized_unit,
                        metadata={
                            "unit_counter": unit_counter,
                            "topic_index": topic_counter,
                        },
                    )
                    topics.append(topic_record)

        # Count distinct recognized units
        distinct_units = {t.unit_number for t in topics if t.unit_number is not None}

        return ParsedSyllabus(
            syllabus_id=syllabus_id,
            file_name=file_name,
            file_type=file_type,
            course_code=detected_course_code,
            course_title=detected_course_title,
            total_units_found=len(distinct_units),
            total_topics_found=len(topics),
            has_unrecognized_units=has_unrecognized_units,
            topics=topics,
            raw_metadata={
                "distinct_units": sorted(list(distinct_units)),
                "pages_count": len(pages_data),
            },
        )


syllabus_parser = SyllabusParser()
