"""
Grammar Checker
Checks grammar and clarity of questions
"""

from typing import Dict, Any, List
import re


class GrammarChecker:
    """
    Checks grammar and clarity.
    ADVISORY - never blocks.
    """
    
    # Common grammar issues to detect
    ISSUES_PATTERNS = [
        (r'\b(a)\s+([aeiou])', "Article 'a' before vowel"),
        (r'\s{2,}', "Multiple spaces"),
        (r'[.]{2,}', "Multiple periods"),
        (r'\?\s*\?', "Multiple question marks"),
        (r'\b(is|are|was|were)\s+\1\b', "Repeated verb"),
        (r'[^.!?]\s*$', "Missing end punctuation"),
    ]
    
    # Ambiguous phrases
    AMBIGUOUS_PATTERNS = [
        (r'\b(it|this|that|these|those)\s+(is|are|was|were)\b', "Ambiguous pronoun reference"),
        (r'\b(some|few|many|several)\b', "Vague quantifier"),
        (r'\b(etc\.?|and so on)\b', "Unclear scope with 'etc.'"),
    ]
    
    async def analyze(self, question_paper: Dict[str, Any]) -> Dict[str, Any]:
        """Check grammar and clarity of questions."""
        questions = question_paper.get("questions", [])
        
        all_issues = []
        problematic_question_nums = set()   # track *which* questions have issues

        for question in questions:
            text = question.get("text", "")
            q_num = question.get("number", 0)
            q_issues = self._check_question(text, q_num)
            if q_issues:
                problematic_question_nums.add(q_num)
            all_issues.extend(q_issues)
        
        # Also check raw text for general issues
        raw_issues = self._check_raw_text(question_paper.get("raw_text", ""))
        
        total_questions = max(1, len(questions))
        problematic_count = len(problematic_question_nums)

        # Score = proportion of clean questions (question-level, not raw-issue-count)
        # 2 bad questions out of 20 → score = 90, not 10
        score = round(100 - (problematic_count / total_questions) * 100)
        score = max(0, min(100, score))

        # Calculate confidence (higher if fewer issues)
        confidence = max(0.6, 1.0 - len(all_issues) * 0.03)
        
        # Build remarks
        if score >= 90:
            score_remark = "Excellent grammar and clarity."
        elif score >= 70:
            score_remark = "Minor grammar or clarity issues."
        elif score >= 50:
            score_remark = "Moderate issues — several questions need revision."
        else:
            score_remark = "Significant grammar and clarity problems throughout the paper."
        
        detail = f"{problematic_count}/{total_questions} questions with issues" if problematic_count else "no issues found"
        remarks = f"Score: {score}/100. {score_remark} ({detail})"
        
        return {
            "criterion": "grammar_clarity",
            "section": "quality",
            "status": "PASS" if problematic_count <= 2 else "WARNING",
            "score": score,
            "remarks": remarks,
            "confidence": confidence,
            "rule_triggered": "GRAMMAR_PATTERN_CHECK",
            "evidence": {
                "issues_count": len(all_issues),
                "problematic_questions": problematic_count,
                "total_questions": total_questions,
                "issues": all_issues[:10],
                "questions_checked": len(questions)
            },
            "baseline": "Grammar rules and clarity standards",
            "suggestion": (
                f"{problematic_count} of {total_questions} questions have grammar/clarity issues. "
                f"Review: {', '.join(f'Q{n}' for n in sorted(problematic_question_nums)[:5])}"
                if problematic_count else "No grammar or clarity issues detected."
            )
        }
    
    def _check_question(self, text: str, question_num: int) -> List[Dict]:
        """Check a single question for grammar issues."""
        issues = []
        
        # Check grammar patterns
        for pattern, description in self.ISSUES_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append({
                    "question": question_num,
                    "type": "grammar",
                    "issue": description,
                    "text_sample": text[:50]
                })
        
        # Check ambiguity
        for pattern, description in self.AMBIGUOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append({
                    "question": question_num,
                    "type": "ambiguity",
                    "issue": description,
                    "text_sample": text[:50]
                })
        
        return issues
    
    def _check_raw_text(self, text: str) -> List[Dict]:
        """Check full document for issues."""
        issues = []
        
        # Check for very long sentences (potential clarity issue)
        sentences = re.split(r'[.!?]', text)
        for i, sentence in enumerate(sentences):
            if len(sentence.split()) > 40:
                issues.append({
                    "type": "clarity",
                    "issue": "Very long sentence (>40 words)",
                    "location": f"Sentence {i+1}"
                })
        
        return issues[:5]  # Limit
