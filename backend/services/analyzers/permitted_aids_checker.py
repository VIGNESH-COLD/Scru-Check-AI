"""
Permitted Aids Checker
Validates references to calculators, tables, etc.
"""

from typing import Dict, Any
import re


class PermittedAidsChecker:
    """
    Checks permitted aids references.
    ENFORCED.
    """
    
    COMMON_AIDS = [
        "calculator",
        "scientific calculator",
        "data book",
        "data handbook",
        "formula sheet",
        "log tables",
        "statistical tables",
        "open book",
        "reference material"
    ]
    
    async def analyze(self, question_paper: Dict[str, Any]) -> Dict[str, Any]:
        """Check permitted aids references."""
        raw_text = question_paper.get("raw_text", "").lower()
        
        found_aids = []
        issues = []
        
        # Check for permitted aids mentions
        for aid in self.COMMON_AIDS:
            if aid in raw_text:
                found_aids.append(aid)
        
        # Check for "permitted" or "allowed" statements
        has_permission_statement = bool(re.search(
            r'(permitted|allowed|may use|can use|not allowed|not permitted)',
            raw_text, re.IGNORECASE
        ))
        
        # Check for conflicting statements
        if "not allowed" in raw_text and "allowed" in raw_text:
            issues.append("Conflicting aid permission statements detected")
        
        # Standard check - if calculator is needed
        if re.search(r'\b(calculate|compute|solve numerically)\b', raw_text, re.IGNORECASE):
            if "calculator" not in found_aids and not has_permission_statement:
                issues.append(" Numerical questions but no calculator permission statement")
        
        status = "PASS" if not issues else "FAIL"
        remarks = "; ".join(issues) if issues else "Permitted aids are correctly specified."

        return {
            "criterion": "permitted_aids",
            "section": "mandatory",
            "status": status,
            "remarks": remarks,
            "confidence": 0.9,
            "rule_triggered": "AIDS_REFERENCE_CHECK",
            "evidence": {
                "aids_mentioned": found_aids,
                "has_permission_statement": has_permission_statement,
                "issues": issues
            },
            "baseline": "Institution permitted aids policy",
            "suggestion": remarks
        }
