"""
Marks Analyzer
Validates mark distribution and time balance
"""

from typing import Dict, Any, Optional
import re


class MarksAnalyzer:
    """
    Checks mark distribution and time allocation.
    STRICT enforcement.
    """
    
    # Time estimates per mark (in minutes)
    TIME_PER_MARK = {
        "objective": 0.5,
        "short_answer": 1.5,
        "long_answer": 2.0,
        "problem_solving": 2.5
    }
    
    async def analyze(self, question_paper: Dict[str, Any], pattern: Optional[str]) -> Dict[str, Any]:
        """Analyze mark distribution and time balance."""
        raw_text = question_paper.get("raw_text", "")
        questions = question_paper.get("questions", [])
        
        issues = []
        
        # Extract mark patterns
        mark_patterns = re.findall(r'(\d+)\s*[x×]\s*(\d+)\s*=\s*(\d+)', raw_text)
        
        total_marks = 0
        sections = []
        
        for match in mark_patterns:
            questions_count, marks_each, section_total = int(match[0]), int(match[1]), int(match[2])
            
            # Validate arithmetic
            expected = questions_count * marks_each
            if expected != section_total:
                issues.append(f"❌ Arithmetic error: {questions_count}×{marks_each} = {expected}, not {section_total}")
            
            total_marks += section_total
            sections.append({
                "questions": questions_count,
                "marks_each": marks_each,
                "total": section_total
            })
        
        # Check total marks
        expected_total = 100  # Default
        if total_marks != expected_total and total_marks > 0:
            issues.append(f"⚠️ Total marks = {total_marks}, expected {expected_total}")
        
        # Time estimation
        estimated_time = self._estimate_time(sections)
        if estimated_time > 180:  # 3 hours
            issues.append(f"⚠️ Estimated time {estimated_time:.0f} mins exceeds 180 mins")
        
        # Time-only warnings don't cause FAIL
        has_mark_issues = any("❌" in i or "Total marks" in i for i in issues)
        status = "FAIL" if has_mark_issues else "PASS"
        remarks = "; ".join(issues) if issues else "Mark distribution and time estimation are within expected limits."
        
        return {
            "criterion": "mark_distribution",
            "section": "mandatory",
            "status": status,
            "remarks": remarks,
            "confidence": 1.0,
            "rule_triggered": "MARKS_VALIDATION",
            "evidence": {
                "sections": sections,
                "total_marks": total_marks,
                "estimated_time_mins": estimated_time,
                "issues": issues
            },
            "baseline": f"Expected: {expected_total} marks, 180 minutes",
            "suggestion": remarks,
        }
    
    def _estimate_time(self, sections: list) -> float:
        """Estimate total time needed."""
        total_time = 0
        for section in sections:
            marks = section.get("marks_each", 2)
            count = section.get("questions", 0)
            
            # Estimate based on marks per question
            if marks <= 2:
                time_each = marks * self.TIME_PER_MARK["short_answer"]
            elif marks <= 8:
                time_each = marks * self.TIME_PER_MARK["long_answer"]
            else:
                time_each = marks * self.TIME_PER_MARK["problem_solving"]
            
            total_time += time_each * count
        
        return total_time
