"""
Format Validator
Checks question paper structure against institutional patterns
"""

from typing import Dict, Any, List, Optional
import re


class FormatValidator:
    """
    Validates question paper format against expected pattern.
    STRICT enforcement - blocks approval if fails.
    """
    
    # Default patterns
    DEFAULT_PATTERNS = {
        "Anna University": {
            "sections": [
                {"name": "Part A", "questions": 10, "marks": 2, "total": 20},
                {"name": "Part B", "questions": 5, "marks": 16, "total": 80}
            ],
            "total_marks": 100
        }
    }
    
    async def analyze(self, question_paper: Dict[str, Any], pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate format compliance.
        Returns STRICT finding - blocks if fails.
        """
        sections = question_paper.get("sections", [])
        questions = question_paper.get("questions", [])
        raw_text = question_paper.get("raw_text", "")
        
        issues = []
        
        # Check section headers exist
        section_check = self._check_sections(sections, raw_text)
        issues.extend(section_check["issues"])
        
        # Check question numbering
        numbering_check = self._check_numbering(questions)
        issues.extend(numbering_check["issues"])
        
        # Check mark distribution pattern
        marks_check = self._check_marks_pattern(raw_text, pattern)
        issues.extend(marks_check["issues"])
        
        status = "PASS" if not issues else "FAIL"
        
        remarks = "; ".join(issues) if issues else "Document structure complies with the standard format pattern."

        return {
            "criterion": "format_compliance",
            "section": "mandatory",
            "status": status,
            "remarks": remarks,
            "confidence": 1.0,  # Rule-based, always confident
            "rule_triggered": "FORMAT_PATTERN_MATCH",
            "evidence": {
                "sections_found": [s["name"] for s in sections],
                "questions_count": len(questions),
                "issues": issues
            },
            "baseline": f"Expected pattern: {pattern or 'Anna University (default)'}",
            "suggestion": remarks
        }
    
    def _check_sections(self, sections: List[Dict], raw_text: str) -> Dict[str, Any]:
        """Check if required section headers exist."""
        issues = []
        
        # Look for Part A, Part B patterns
        has_part_a = any("part a" in s["name"].lower() for s in sections) or \
                     re.search(r'part\s*a', raw_text, re.IGNORECASE)
        has_part_b = any("part b" in s["name"].lower() for s in sections) or \
                     re.search(r'part\s*b', raw_text, re.IGNORECASE)
        
        if not has_part_a:
            issues.append("❗ Part A section header not found")
        if not has_part_b:
            issues.append("❗ Part B section header not found")
        
        return {"issues": issues}
    
    def _check_numbering(self, questions: List[Dict]) -> Dict[str, Any]:
        """Check question numbering sequence."""
        issues = []
        
        if not questions:
            issues.append("❗ No questions detected in document")
            return {"issues": issues}
        
        # Check for gaps in numbering
        numbers = [q.get("number", 0) for q in questions]
        expected = list(range(1, len(questions) + 1))
        
        if numbers != expected:
            issues.append(f"⚠️ Question numbering may have gaps or duplicates")
        
        return {"issues": issues}
    
    def _check_marks_pattern(self, raw_text: str, pattern: Optional[str]) -> Dict[str, Any]:
        """Check if marks pattern is correctly stated."""
        issues = []
        
        # Look for common patterns like "10 x 2 = 20"
        mark_patterns = [
            r'(\d+)\s*[x×]\s*(\d+)\s*=\s*(\d+)',
            r'(\d+)\s*questions?\s*[x×]\s*(\d+)\s*marks?',
        ]
        
        found_patterns = []
        for mp in mark_patterns:
            matches = re.findall(mp, raw_text, re.IGNORECASE)
            found_patterns.extend(matches)
        
        if not found_patterns:
            issues.append("⚠️ Mark allocation pattern not clearly stated (e.g., 10×2=20)")
        else:
            # Validate arithmetic
            for match in found_patterns:
                if len(match) == 3:
                    questions, marks, total = int(match[0]), int(match[1]), int(match[2])
                    if questions * marks != total:
                        issues.append(f"❌ Arithmetic error: {questions}×{marks} ≠ {total}")
        
        return {"issues": issues}
