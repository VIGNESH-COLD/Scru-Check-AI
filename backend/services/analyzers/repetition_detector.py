"""
Enhanced Repetition Detector
Uses semantic embeddings for conceptual similarity detection
"""

from typing import Dict, Any, Optional, List
import re
from difflib import SequenceMatcher
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.embeddings import embeddings_manager
from rag.training_data import training_data


class RepetitionDetector:
    """
    Detects repeated questions from previous papers.
    Uses semantic embeddings for conceptual similarity.
    ADVISORY - warning only.
    """
    
    EXACT_THRESHOLD = 0.90     # String similarity for exact match
    SEMANTIC_THRESHOLD = 0.75  # Embedding similarity for conceptual match
    
    async def analyze(self, question_paper: Dict[str, Any], previous_paper: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect repeated questions using hybrid similarity."""
        current_questions = question_paper.get("questions", [])
        
        inter_paper_repeats = []
        intra_paper_repeats = []
        
        # Check intra-paper (within same paper)
        intra_paper_repeats = await self._check_intra_paper(current_questions)
        
        # Check inter-paper (with previous paper)
        if previous_paper:
            prev_questions = previous_paper.get("questions", [])
            inter_paper_repeats = await self._check_inter_paper(current_questions, prev_questions)
        
        # Filter suppressed findings
        inter_paper_repeats = [r for r in inter_paper_repeats 
                               if not training_data.should_suppress_finding("repetition_check", r.get("current_text", ""))]
        
        total_repeats = len(inter_paper_repeats) + len(intra_paper_repeats)
        
        # Calculate quality score (0-100) with capped deductions
        # Exact repeats: -15 each, conceptual: -8 each, total deduction capped at 60
        exact_count = sum(1 for r in inter_paper_repeats + intra_paper_repeats if r.get("type") == "exact")
        conceptual_count = total_repeats - exact_count
        raw_deduction = (exact_count * 15) + (conceptual_count * 8)
        deduction = min(60, raw_deduction)   # cap: worst case score is 40
        score = max(0, 100 - deduction)
        
        # Build remarks
        if score >= 90:
            score_remark = "No significant repetition detected."
        elif score >= 70:
            score_remark = "Minor repetition found."
        elif score >= 50:
            score_remark = "Moderate repetition — consider revising similar questions."
        else:
            score_remark = "Excessive repetition — significant overlap with previous papers."
        
        remarks = f"Score: {score}/100. {score_remark}"

        return {
            "criterion": "repetition_check",
            "section": "quality",
            "status": "PASS" if total_repeats == 0 else "WARNING",
            "score": score,
            "remarks": remarks,
            "confidence": 0.85 if embeddings_manager.model else 0.75,
            "rule_triggered": "SEMANTIC_SIMILARITY_HYBRID",
            "evidence": {
                "inter_paper_repeats": inter_paper_repeats,
                "intra_paper_repeats": intra_paper_repeats,
                "exact_threshold": self.EXACT_THRESHOLD,
                "semantic_threshold": self.SEMANTIC_THRESHOLD,
                "embedding_model": embeddings_manager.MODEL_NAME if embeddings_manager.model else "fallback"
            },
            "baseline": "Previous year question paper" if previous_paper else "No previous paper provided",
            "suggestion": f"Found {len(inter_paper_repeats)} similar questions to previous year" if inter_paper_repeats else "No significant question repetition detected from previous paper."
        }
    
    async def _check_intra_paper(self, questions: List[Dict]) -> List[Dict]:
        """Check for repetition within the same paper using embeddings."""
        repeats = []
        
        for i, q1 in enumerate(questions):
            for j, q2 in enumerate(questions[i+1:], start=i+1):
                text1 = q1.get("text", "")
                text2 = q2.get("text", "")
                
                # Check string similarity
                string_sim = self._calculate_string_similarity(text1, text2)
                
                # Check semantic similarity
                semantic_sim = embeddings_manager.calculate_similarity(text1, text2)
                
                # Use higher of the two
                max_sim = max(string_sim, semantic_sim)
                
                if max_sim >= self.SEMANTIC_THRESHOLD:
                    repeats.append({
                        "question_1": q1.get("number"),
                        "question_2": q2.get("number"),
                        "string_similarity": round(string_sim, 2),
                        "semantic_similarity": round(semantic_sim, 2),
                        "type": "exact" if string_sim > 0.90 else "conceptual",
                        "q1_text": text1[:50],
                        "q2_text": text2[:50]
                    })
        
        return repeats
    
    async def _check_inter_paper(self, current: List[Dict], previous: List[Dict]) -> List[Dict]:
        """Check for repetition with previous paper."""
        repeats = []
        
        for curr_q in current:
            curr_text = curr_q.get("text", "")
            
            for prev_q in previous:
                prev_text = prev_q.get("text", "")
                
                # Check string similarity
                string_sim = self._calculate_string_similarity(curr_text, prev_text)
                
                # Check semantic similarity
                semantic_sim = embeddings_manager.calculate_similarity(curr_text, prev_text)
                
                # Use higher of the two
                max_sim = max(string_sim, semantic_sim)
                
                if max_sim >= self.SEMANTIC_THRESHOLD:
                    repeat_type = "exact" if string_sim > 0.90 else (
                        "paraphrased" if string_sim > 0.70 else "conceptual"
                    )
                    
                    repeats.append({
                        "current_question": curr_q.get("number"),
                        "previous_question": prev_q.get("number"),
                        "string_similarity": round(string_sim, 2),
                        "semantic_similarity": round(semantic_sim, 2),
                        "type": repeat_type,
                        "current_text": curr_text[:100],
                        "previous_text": prev_text[:100]
                    })
        
        return repeats
    
    def _calculate_string_similarity(self, text1: str, text2: str) -> float:
        """Calculate string similarity using SequenceMatcher."""
        text1 = self._normalize(text1)
        text2 = self._normalize(text2)
        
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
