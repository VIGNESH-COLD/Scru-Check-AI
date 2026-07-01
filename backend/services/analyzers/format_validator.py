"""
Format Validator
Checks question paper structure against the SELECTED university pattern.

Validation Flow (post-fix):
  1. detect_pattern()  — Inspect the uploaded paper's actual section structure
                         and return the best-matching known pattern name.
  2. analyze()         — Compare the detected pattern (from the paper) against
                         the expected pattern object (from the frontend selection).
  3. If they differ    — Return FAIL with a clear mismatch message.
  4. If they match     — Return PASS.

IMPORTANT: The frontend-selected pattern is always the source of truth.
           The uploaded paper is NEVER validated against itself.
"""

from typing import Dict, Any, List, Optional
import re


class FormatValidator:
    """
    Validates question paper format against the expected pattern selected by the user.
    STRICT enforcement — blocks approval if format does not match selection.
    """

    async def analyze(
        self,
        question_paper: Dict[str, Any],
        expected_pattern_obj: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate format compliance by comparing:
          - expected_pattern_obj : the pattern chosen by the user in the frontend
          - detected pattern     : the pattern inferred from the uploaded paper

        Returns a STRICT (mandatory) finding.
        """
        raw_text = question_paper.get("raw_text", "")
        sections_found = question_paper.get("sections", [])
        questions = question_paper.get("questions", [])

        # ── Step 1: Detect the actual pattern of the uploaded paper ──────────
        detected_pattern_name, detected_sections = self._detect_pattern(raw_text, sections_found)

        # ── Step 2: Build expected-pattern description ────────────────────────
        if expected_pattern_obj:
            expected_name = expected_pattern_obj.get("name", "Unknown Pattern")
            expected_sections = expected_pattern_obj.get("sections", [])
            expected_total = expected_pattern_obj.get("total_marks", 100)
        else:
            # No pattern selected — fall back to structural checks only
            expected_name = "Default (Anna University)"
            expected_sections = []
            expected_total = 100

        # ── Step 3: Compare expected vs detected ─────────────────────────────
        mismatch_reasons = []

        if expected_pattern_obj:
            # 3a. Section count check
            if len(detected_sections) != len(expected_sections):
                mismatch_reasons.append(
                    f"Section count mismatch: paper has {len(detected_sections)} section(s) "
                    f"({', '.join(s['name'] for s in detected_sections) or 'none detected'}), "
                    f"but {expected_name} requires {len(expected_sections)} section(s) "
                    f"({', '.join(s['name'] for s in expected_sections)})."
                )
            else:
                # 3b. Per-section marks_per_question check
                for i, (exp_sec, det_sec) in enumerate(zip(expected_sections, detected_sections)):
                    exp_marks = exp_sec.get("marks_per_question", 0)
                    det_marks = det_sec.get("marks_per_question", 0)
                    if exp_marks and det_marks and exp_marks != det_marks:
                        mismatch_reasons.append(
                            f"{exp_sec['name']}: expected {exp_marks} marks/question, "
                            f"detected {det_marks} marks/question."
                        )

            # 3c. Total marks check (using regex from raw text)
            detected_total = self._detect_total_marks(raw_text)
            if detected_total and detected_total != expected_total:
                mismatch_reasons.append(
                    f"Total marks mismatch: paper totals {detected_total} marks, "
                    f"but {expected_name} requires {expected_total} marks."
                )

        # ── Step 4: Additional structural checks (always run) ─────────────────
        structural_issues = []
        if not self._has_section_headers(raw_text, sections_found):
            structural_issues.append("❗ No recognisable section headers (Part A / Part B) found.")
        if not questions:
            structural_issues.append("❗ No questions detected in the document.")

        # ── Step 5: Determine status ──────────────────────────────────────────
        all_issues = mismatch_reasons + structural_issues

        if mismatch_reasons:
            # Pattern mismatch is the primary failure
            status = "FAIL"
            remarks = (
                f"Expected {expected_name}, but the uploaded paper follows "
                f"{detected_pattern_name}. "
                + " ".join(mismatch_reasons)
            )
        elif structural_issues:
            status = "FAIL"
            remarks = " ".join(structural_issues)
        else:
            status = "PASS"
            remarks = (
                f"Document structure matches the selected pattern: {expected_name}."
            )

        return {
            "criterion": "format_compliance",
            "section": "mandatory",
            "status": status,
            "remarks": remarks,
            "confidence": 1.0,  # Rule-based, always confident
            "rule_triggered": "FORMAT_PATTERN_MATCH",
            "evidence": {
                "expected_pattern": expected_name,
                "detected_pattern": detected_pattern_name,
                "expected_sections": [s["name"] for s in expected_sections],
                "detected_sections": [s["name"] for s in detected_sections],
                "sections_found": [s["name"] for s in sections_found],
                "questions_count": len(questions),
                "mismatch_reasons": mismatch_reasons,
                "structural_issues": structural_issues,
            },
            "baseline": f"Expected pattern (user-selected): {expected_name}",
            "suggestion": remarks,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _detect_pattern(
        self,
        raw_text: str,
        sections: List[Dict]
    ) -> tuple:
        """
        Infer the pattern of the uploaded paper from its content.

        Returns:
            (pattern_name: str, detected_sections: list[dict])
            where each detected_section has 'name' and optionally 'marks_per_question'.
        """
        detected_sections = []

        # Detect which named sections exist
        section_names = ["Part A", "Part B", "Part C", "Part D",
                         "Section A", "Section B", "Section C"]
        present = []
        for sname in section_names:
            if re.search(re.escape(sname), raw_text, re.IGNORECASE):
                present.append(sname)

        # For each present section, try to detect the marks-per-question
        for sname in present:
            mpq = self._detect_marks_per_question_for_section(raw_text, sname)
            detected_sections.append({"name": sname, "marks_per_question": mpq})

        # Derive a human-readable pattern description
        if not detected_sections:
            pattern_name = "Unknown Pattern (no sections detected)"
        else:
            parts = []
            for s in detected_sections:
                mpq = s.get("marks_per_question")
                if mpq:
                    parts.append(f"{s['name']} ({mpq} marks/Q)")
                else:
                    parts.append(s["name"])
            pattern_name = "Detected: " + " + ".join(parts)

        return pattern_name, detected_sections

    def _detect_marks_per_question_for_section(
        self,
        raw_text: str,
        section_name: str
    ) -> Optional[int]:
        """
        Attempt to extract the marks-per-question for a given section by looking
        at patterns like '10 x 2 = 20' or '(16 Marks)' near the section header.
        Returns None if not determinable.
        """
        # Find the section's region of text (between this section and the next)
        pattern_pos = re.search(re.escape(section_name), raw_text, re.IGNORECASE)
        if not pattern_pos:
            return None

        # Take up to 500 chars after the section header
        snippet = raw_text[pattern_pos.start(): pattern_pos.start() + 500]

        # Pattern: N × M = Total  →  marks per question = M
        mul_match = re.search(r'(\d+)\s*[x×]\s*(\d+)\s*=\s*(\d+)', snippet)
        if mul_match:
            return int(mul_match.group(2))

        # Pattern: (M Marks) → marks per question = M
        marks_match = re.search(r'\((\d+)\s*[Mm]arks?\)', snippet)
        if marks_match:
            return int(marks_match.group(1))

        return None

    def _detect_total_marks(self, raw_text: str) -> Optional[int]:
        """
        Try to extract the declared total marks from the paper.
        Looks for patterns like 'Total: 100', 'Max. Marks: 100', etc.
        """
        patterns = [
            r'(?:total|max(?:imum)?)[.\s]*marks?\s*[:\-=]\s*(\d+)',
            r'marks?\s*[:\-=]\s*(\d+)',
        ]
        for pat in patterns:
            m = re.search(pat, raw_text, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                # Sanity: only accept sensible exam totals
                if 10 <= val <= 200:
                    return val
        return None

    def _has_section_headers(self, raw_text: str, sections: List[Dict]) -> bool:
        """Return True if at least one section header is found."""
        if sections:
            return True
        return bool(
            re.search(r'part\s*[a-d]', raw_text, re.IGNORECASE) or
            re.search(r'section\s*[a-d]', raw_text, re.IGNORECASE)
        )
