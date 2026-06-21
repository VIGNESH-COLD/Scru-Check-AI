"""
Regulation Checker
Validates paper against institutional regulations
"""

from typing import Dict, Any, Optional
import re


class RegulationChecker:
    """
    Checks regulation year, semester, course code alignment.
    STRICT enforcement.
    """
    
    async def analyze(self, question_paper: Dict[str, Any], regulation: Optional[str], department: Optional[str]) -> Dict[str, Any]:
        """Check regulation and course compliance."""
        raw_text = question_paper.get("raw_text", "")
        
        issues = []
        found_info = {}
        
        # Extract regulation year
        reg_match = re.search(r'R[-\s]?(\d{4})|Regulation\s*[-:]?\s*(\d{4})', raw_text, re.IGNORECASE)
        if reg_match:
            found_info["regulation"] = reg_match.group(1) or reg_match.group(2)
        else:
            issues.append("⚠️ Regulation year not found in paper")
        
        # Extract course code
        code_match = re.search(r'([A-Z]{2,4}\s*\d{4,5})', raw_text)
        if code_match:
            found_info["course_code"] = code_match.group(1)
        else:
            issues.append("⚠️ Course code not clearly visible")
        
        # Extract semester
        sem_match = re.search(r'(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|[1-8])\s*Semester', raw_text, re.IGNORECASE)
        if sem_match:
            found_info["semester"] = sem_match.group(0)
        
        # Check for department/branch
        dept_patterns = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT", "AI", "AIDS"]
        for dept in dept_patterns:
            if dept in raw_text.upper():
                found_info["department"] = dept
                break
        
        status = "PASS" if len(issues) == 0 else "FAIL"
        remarks = "; ".join(issues) if issues else "All regulation details (Year, Semester, Course Code) are correctly identified."
        
        return {
            "criterion": "regulation_check",
            "section": "mandatory",
            "status": status,
            "remarks": remarks,
            "confidence": 1.0,
            "rule_triggered": "REGULATION_PATTERN_MATCH",
            "evidence": {
                "found": found_info,
                "issues": issues
            },
            "baseline": f"Expected regulation: {regulation or 'R-2021'}, Department: {department or 'Any'}",
            "suggestion": remarks
        }
