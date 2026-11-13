"""Question paper text parsing service.

Extracts structured QuestionItem instances from examination question paper text,
handling sections (Part A, Part B, Part C), question numbering, nested subquestions
(e.g., 11(a)(i), 11(a)(ii)), either-or internal choices (11(a) OR 11(b)),
choice groups, and examination marks metadata.
"""

from __future__ import annotations

import re
from typing import Any

from app.schemas.question_mapping import QuestionItem


class QuestionParser:
    """Parser to convert raw question paper text into structured QuestionItem models."""

    SECTION_PATTERN = re.compile(
        r"(?i)(?:^|[\r\n])\s*(?:(?:UNIT\s*[-–—]?[IVX0-9]+\s*[:.-]?\s*))?"
        r"(?:PART|SECTION)\s*[-–—]?\s*([A-D])\b(?:\s*[-–—:]\s*)?([^\r\n]*)",
        re.MULTILINE,
    )

    # Marks regex: (2), [2], (13 marks), [15 Marks], (7 Marks), etc. at the end or embedded
    MARKS_PATTERN = re.compile(
        r"(?:\[|\()\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*(?:Marks?|marks?|MARKS?|M)?\s*(?:\]|\))\s*$"
    )
    EMBEDDED_MARKS_PATTERN = re.compile(
        r"(?:\[|\()\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*(?:Marks?|marks?|MARKS?|M)\s*(?:\]|\))"
    )

    # Question heading matches:
    # 1. or Q1. or 11. or Q11.
    # 11(a). or 11(a) or 11. (a) or 11 a. or 16(a). or 16(b).
    # (a) or (b) when preceded by OR
    Q_HEADER_PATTERN = re.compile(
        r"^(?:Q(?:uestion)?\s*[\.:]?\s*)?([0-9]{1,2})(?:[\s\.:\)]*\(?([a-d])\)?[\.:\-]?)?(?:[\.:\)]|\s+)\s*(.*)",
        re.IGNORECASE,
    )
    OR_PATTERN = re.compile(
        r"^\s*(?:\[\s*OR\s*\]|\(\s*OR\s*\)|\bOR\b|[-–—*#\s]*\bOR\b[-–—*#\s]*)\s*$",
        re.IGNORECASE,
    )

    # Bloom's Taxonomy pattern: [A1], (B2), [BT: C1], (BT: A2), [BTL: B1], BT Level: A1, or A1/B2 at the end
    BT_BRACKET_PATTERN = re.compile(
        r"(?:\[|\()\s*(?:(?:BT|BTL|Bloom(?:'s)?(?:\s*(?:Taxonomy|Level))?)\s*[:=-]?\s*)?\b([ABC][12])\b(?:\s*[-–—:]\s*[^\]\)]*)?\s*(?:\]|\))",
        re.IGNORECASE,
    )
    BT_PREFIX_PATTERN = re.compile(
        r"\b(?:BT|BTL|Bloom(?:'s)?(?:\s*(?:Taxonomy|Level))?)\s*[:=-]\s*\b([ABC][12])\b",
        re.IGNORECASE,
    )
    BT_END_PATTERN = re.compile(
        r"(?:\b|\[|\()(?:BT|BTL)?[\s:-]*\b([ABC][12])\b\s*$",
        re.IGNORECASE,
    )

    def extract_bt(self, text: str) -> tuple[str, str | None]:
        """Extract declared Bloom's Taxonomy level from question text and return cleaned text and BT level."""
        clean_text = text.strip()
        declared_bt: str | None = None

        m_br = self.BT_BRACKET_PATTERN.search(clean_text)
        if m_br:
            declared_bt = m_br.group(1).upper()
            clean_text = (clean_text[: m_br.start()] + " " + clean_text[m_br.end() :]).strip()
            clean_text = re.sub(r"\s+", " ", clean_text)
            return clean_text, declared_bt

        m_pre = self.BT_PREFIX_PATTERN.search(clean_text)
        if m_pre:
            declared_bt = m_pre.group(1).upper()
            clean_text = (clean_text[: m_pre.start()] + " " + clean_text[m_pre.end() :]).strip()
            clean_text = re.sub(r"\s+", " ", clean_text)
            return clean_text, declared_bt

        m_end = self.BT_END_PATTERN.search(clean_text)
        if m_end:
            declared_bt = m_end.group(1).upper()
            clean_text = clean_text[: m_end.start()].strip()
            return clean_text, declared_bt

        return clean_text, None

    def extract_marks(self, text: str) -> tuple[str, float | None]:
        """Extract marks allocated from question text and return cleaned text and marks float."""
        clean_text = text.strip()
        marks: float | None = None

        m = self.MARKS_PATTERN.search(clean_text)
        if m:
            try:
                marks = float(m.group(1))
                clean_text = clean_text[: m.start()].strip()
            except ValueError:
                pass

        if marks is None:
            m_emb = self.EMBEDDED_MARKS_PATTERN.search(clean_text)
            if m_emb:
                try:
                    marks = float(m_emb.group(1))
                    clean_text = (clean_text[: m_emb.start()] + clean_text[m_emb.end() :]).strip()
                except ValueError:
                    pass

        return clean_text, marks

    def extract_marks_and_bt(self, text: str) -> tuple[str, float | None, str | None]:
        """Extract both marks and declared BT level from question text, returning cleaned text."""
        clean_text = text.strip()
        marks: float | None = None
        declared_bt: str | None = None

        for _ in range(2):
            if declared_bt is None:
                clean_text, declared_bt = self.extract_bt(clean_text)
            if marks is None:
                clean_text, marks = self.extract_marks(clean_text)

        return clean_text, marks, declared_bt

    def parse_from_text(self, text: str) -> list[QuestionItem]:
        """Parse raw text from question paper document into structured QuestionItem models."""
        lines = [line.strip() for line in text.splitlines()]
        questions: list[QuestionItem] = []

        current_section = "Part A"
        current_q_num: str | None = None
        current_sub_id: str | None = None
        current_text_lines: list[str] = []
        is_alternative = False
        saw_or_delimiter = False
        current_marks: float | None = None

        def flush_question():
            nonlocal current_text_lines, current_q_num, current_sub_id, is_alternative, current_marks
            if not current_q_num or not current_text_lines:
                return

            full_text = " ".join(current_text_lines).strip()
            if not full_text:
                return

            cleaned_text, marks, declared_bt = self.extract_marks_and_bt(full_text)
            has_explicit = (marks is not None)
            if marks is None and current_marks is not None:
                marks = current_marks
                has_explicit = True

            # Default marks by section if missing
            if marks is None:
                if current_section == "Part A":
                    marks = 2.0
                elif current_section == "Part B":
                    marks = 13.0
                elif current_section == "Part C":
                    marks = 15.0

            q_id = f"Q{current_q_num}"
            if current_sub_id:
                q_id = f"Q{current_q_num}({current_sub_id})"

            choice_group = f"Q{current_q_num}"

            # Check for sub-sub questions e.g. (i) and (ii) inside full_text
            subparts = self._split_subsubquestions(
                parent_q_num=current_q_num,
                parent_sub_id=current_sub_id,
                text=full_text,
                parent_marks=marks,
                section=current_section,
                choice_group=choice_group,
                is_alternative=is_alternative,
                parent_declared_bt=declared_bt,
            )

            if subparts:
                questions.extend(subparts)
            else:
                questions.append(
                    QuestionItem(
                        question_id=q_id,
                        text=cleaned_text,
                        marks=marks,
                        section=current_section,
                        question_number=current_q_num,
                        subquestion_id=current_sub_id,
                        is_alternative=is_alternative,
                        choice_group=choice_group,
                        has_explicit_marks=has_explicit,
                        declared_bt=declared_bt,
                    )
                )

            current_text_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            if not line:
                i += 1
                continue

            # Check for section header
            sec_match = self.SECTION_PATTERN.search(line)
            if sec_match and (
                line.upper().startswith("PART")
                or line.upper().startswith("SECTION")
                or "PART" in line.upper()
            ):
                letter = sec_match.group(1).upper()
                flush_question()
                current_section = f"Part {letter}"
                current_q_num = None
                current_sub_id = None
                is_alternative = False
                saw_or_delimiter = False
                current_marks = None
                i += 1
                continue

            # Check for OR line between questions
            if self.OR_PATTERN.match(line):
                flush_question()
                saw_or_delimiter = True
                i += 1
                # Next line might start with (b) or 11(b) or just the question text
                continue

            # Check if this line is an alternative choice directly: e.g. "(b) Describe..." or "b) ..."
            alt_match = re.match(
                r"^\s*(?:\(([a-d])\)|([a-d])[\.:\)])\s*(.*)", line, re.IGNORECASE
            )
            if alt_match and current_q_num is not None:
                sub_label = (alt_match.group(1) or alt_match.group(2)).lower()
                flush_question()
                current_sub_id = sub_label
                is_alternative = saw_or_delimiter or (sub_label in ("b", "c", "d"))
                saw_or_delimiter = False
                line_text = alt_match.group(3).strip()
                if line_text:
                    current_text_lines.append(line_text)
                i += 1
                continue

            # Check for top-level question: "1. ", "Q1. ", "11(a).", "11. (a)", "11(a)", "11. ", "16(a)."
            q_match = self.Q_HEADER_PATTERN.match(line)
            if q_match:
                q_num_str = q_match.group(1)
                sub_label = (q_match.group(2) or "").lower() or None
                rest_text = (q_match.group(3) or "").strip()

                # Basic validation: question number should make sense (1 to 40)
                try:
                    q_int = int(q_num_str)
                    if 1 <= q_int <= 40:
                        flush_question()
                        # If previously flagged as alternative (e.g. from OR line) OR if same q_num with sub_label b/c/d
                        new_is_alt = saw_or_delimiter or (
                            sub_label in ("b", "c", "d") and current_q_num == q_num_str
                        )
                        current_q_num = q_num_str
                        current_sub_id = sub_label
                        is_alternative = new_is_alt
                        saw_or_delimiter = False
                        current_marks = None
                        if rest_text:
                            current_text_lines.append(rest_text)
                        i += 1
                        continue
                except ValueError:
                    pass

            # Handle case where OR appeared and next line is question text without explicit numbering
            if saw_or_delimiter and current_q_num is not None:
                current_sub_id = "b"
                is_alternative = True
                saw_or_delimiter = False
                current_text_lines.append(line)
                i += 1
                continue

            # Otherwise, line is part of current question's text
            if current_q_num is not None:
                # Filter out pure noise lines like "Answer all questions" or header fragments
                upper = line.upper()
                if not any(
                    noise in upper
                    for noise in [
                        "TIME :",
                        "TIME:",
                        "MAX. MARKS",
                        "MAX MARKS",
                        "ANSWER ALL QUESTIONS",
                        "REG. NO.",
                        "REGISTRATION NUMBER",
                    ]
                ):
                    current_text_lines.append(line)

            i += 1

        flush_question()

        # If regex failed to parse any questions (e.g. non-standard format), fallback
        if not questions:
            questions = self._fallback_line_parser(text)

        return questions

    def _split_subsubquestions(
        self,
        parent_q_num: str,
        parent_sub_id: str | None,
        text: str,
        parent_marks: float | None,
        section: str,
        choice_group: str,
        is_alternative: bool,
        parent_declared_bt: str | None = None,
    ) -> list[QuestionItem] | None:
        """Split nested subquestions like (i) and (ii) if explicitly delineated."""
        # Pattern for (i) ... (ii) ... or i. ... ii. ... (roman numerals only to avoid capturing mark annotations like (7) or (6))
        sub_regex = re.compile(
            r"(?:\(([ivx]+)\)|([ivx]+)[\.:\)])\s*(.*?)(?=(?:\(([ivx]+)\)|[ivx]+[\.:\)])|$)",
            re.IGNORECASE | re.DOTALL,
        )
        matches = list(sub_regex.finditer(text))
        if len(matches) >= 2:
            items: list[QuestionItem] = []
            base_sub = parent_sub_id or ""
            for m in matches:
                roman = (m.group(1) or m.group(2)).lower()
                sub_content = m.group(3).strip()
                cleaned, m_val, sub_bt = self.extract_marks_and_bt(sub_content)
                if not cleaned:
                    continue
                sub_id = f"({base_sub})({roman})" if base_sub else f"({roman})"
                qid = f"Q{parent_q_num}{sub_id}"
                has_explicit = (m_val is not None)
                assigned_m = m_val or (parent_marks / len(matches) if parent_marks else None)
                items.append(
                    QuestionItem(
                        question_id=qid,
                        text=cleaned,
                        marks=assigned_m,
                        section=section,
                        question_number=parent_q_num,
                        subquestion_id=sub_id,
                        is_alternative=is_alternative,
                        choice_group=choice_group,
                        has_explicit_marks=has_explicit,
                        declared_bt=sub_bt or parent_declared_bt,
                    )
                )
            if items:
                return items
        return None

    def _fallback_line_parser(self, text: str) -> list[QuestionItem]:
        """Fallback to line-by-line question extraction if structured pattern extraction yields 0 questions."""
        items: list[QuestionItem] = []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        q_idx = 1
        for line in lines:
            if len(line) < 15:
                continue
            cleaned, marks, declared_bt = self.extract_marks_and_bt(line)
            items.append(
                QuestionItem(
                    question_id=f"Q{q_idx}",
                    text=cleaned,
                    marks=marks or 2.0,
                    section="Part A",
                    question_number=str(q_idx),
                    subquestion_id=None,
                    is_alternative=False,
                    choice_group=f"Q{q_idx}",
                    declared_bt=declared_bt,
                )
            )
            q_idx += 1
            if q_idx > 25:
                break
        return items

    def parse_from_list(self, raw_questions: list[dict[str, Any]]) -> list[QuestionItem]:
        """Convert a list of raw dicts or objects into validated QuestionItem list."""
        validated: list[QuestionItem] = []
        for q in raw_questions:
            if isinstance(q, QuestionItem):
                validated.append(q)
            elif isinstance(q, dict):
                validated.append(QuestionItem(**q))
        return validated


question_parser = QuestionParser()

