"""
Enhanced Bloom's Taxonomy Classifier
Uses LLM + Rule-based hybrid approach with training data
"""

from typing import Dict, Any, List, Optional
import re
import sys
import os

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.llm_client import llm_client
from rag.training_data import training_data


class BloomsClassifier:
    """
    Classify questions based on Bloom's Taxonomy levels.
    Hybrid approach: LLM + verb-based heuristics + training data.
    """
    
    # Bloom's Taxonomy verb mappings (fallback)
    BLOOM_VERBS = {
        "Remember": [
            "define", "list", "name", "state", "identify", "label", "recall",
            "recognize", "repeat", "describe", "match", "select", "outline", "what is"
        ],
        "Understand": [
            "explain", "summarize", "paraphrase", "classify", "compare",
            "contrast", "interpret", "discuss", "distinguish", "extend",
            "illustrate", "infer", "relate", "rephrase", "translate", "describe"
        ],
        "Apply": [
            "apply", "calculate", "compute", "solve", "use", "demonstrate",
            "determine", "implement", "execute", "modify", "operate",
            "practice", "prepare", "produce", "show", "sketch", "find"
        ],
        "Analyze": [
            "analyze", "differentiate", "examine", "experiment", "question",
            "test", "distinguish", "categorize", "compare", "contrast",
            "investigate", "separate", "deduce", "break down", "derive"
        ],
        "Evaluate": [
            "evaluate", "assess", "argue", "defend", "judge", "justify",
            "critique", "support", "value", "appraise", "decide", "rank",
            "prioritize", "recommend", "rate", "review"
        ],
        "Create": [
            "create", "design", "develop", "formulate", "construct", "build",
            "compose", "generate", "invent", "plan", "produce", "propose",
            "devise", "synthesize", "arrange", "assemble"
        ]
    }
    
    LEVEL_WEIGHTS = {
        "Remember": 1, "Understand": 2, "Apply": 3,
        "Analyze": 4, "Evaluate": 5, "Create": 6
    }
    
    async def analyze(self, question_paper: Dict[str, Any], syllabus: Dict[str, Any], pattern_obj: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze each question and classify Bloom's level.
        Uses LLM when available, falls back to rule-based.

        pattern_obj: resolved pattern dict from the frontend selection (already parsed).
        """
        from typing import Optional
        questions = question_paper.get("questions", [])
        syllabus_text = syllabus.get("raw_text", "")[:2000]

        # Determine exam type directly from the resolved pattern object (no JSON parsing needed)
        exam_type = "University"
        if pattern_obj and isinstance(pattern_obj, dict):
            exam_type = pattern_obj.get("exam_type", "University") or "University"
            if exam_type == "University":
                name = pattern_obj.get("name", "").upper()
                if "CAT-1" in name or "CAT1" in name:
                    exam_type = "CAT1"
                elif "CAT-2" in name or "CAT2" in name:
                    exam_type = "CAT2"
                elif "CAT-3" in name or "CAT3" in name:
                    exam_type = "CAT3"


        classification_results = []
        distribution = {level: 0 for level in self.BLOOM_VERBS.keys()}
        co_mapping = []
        
        # Get training context for LLM
        training_context = training_data.get_training_prompt_context("blooms_taxonomy")
        
        for question in questions:
            # Try LLM first, then fallback
            result = await self._classify_with_llm(question, syllabus_text, training_context)
            
            if result["bloom_level"] == "Unknown" or result["confidence"] < 0.6:
                # Fallback to rule-based
                rule_result = self._classify_rule_based(question)
                if rule_result["confidence"] > result["confidence"]:
                    result = rule_result
            
            # Check for false positive suppression
            if training_data.should_suppress_finding("blooms_taxonomy", question.get("text", "")):
                result["suppressed"] = True
            
            classification_results.append(result)
            
            if result["bloom_level"] != "Unknown":
                distribution[result["bloom_level"]] += 1
            
            co_mapping.append({
                "question_no": f"Q{question['number']}",
                "question_text": question["text"][:50] + "..." if len(question["text"]) > 50 else question["text"],
                "bloom_level": result["bloom_level"],
                "co_mapped": self._estimate_co(question["number"], len(questions), exam_type),
                "confidence": result["confidence"],
                "reasoning": result.get("reasoning", ""),
                "improvement": result.get("suggested_improvement", "")
            })
        
        # Calculate stats
        avg_confidence = sum(r["confidence"] for r in classification_results) / len(classification_results) if classification_results else 0
        total = sum(distribution.values())
        is_balanced = self._check_balance(distribution, total)
        
        # Calculate quality score via deviation from target distribution
        # Target: Remember+Understand=30%, Apply=30%, Analyze+Evaluate+Create=40%
        TARGET = {
            "lower":  0.30,   # Remember + Understand
            "apply":  0.30,   # Apply
            "higher": 0.40,   # Analyze + Evaluate + Create
        }
        if total > 0:
            actual_lower  = (distribution["Remember"] + distribution["Understand"]) / total
            actual_apply  = distribution["Apply"] / total
            actual_higher = (distribution["Analyze"] + distribution["Evaluate"] + distribution["Create"]) / total

            # Sum of absolute deviations across the three groups (range 0 → ~1.4)
            total_deviation = (
                abs(actual_lower  - TARGET["lower"]) +
                abs(actual_apply  - TARGET["apply"]) +
                abs(actual_higher - TARGET["higher"])
            )

            # Normalise: worst case all questions in one group → deviation ≈ 1.4
            # Dividing by 1.4 maps worst→0, perfect→100
            MAX_DEV = 1.4
            score = max(0, round(100 * (1 - total_deviation / MAX_DEV)))

            # Build human-readable deviation breakdown for remarks
            lower_pct  = round(actual_lower  * 100)
            apply_pct  = round(actual_apply  * 100)
            higher_pct = round(actual_higher * 100)
            deviation_detail = (
                f"Lower-order (R+U): {lower_pct}% (target 30%)  |  "
                f"Apply: {apply_pct}% (target 30%)  |  "
                f"Higher-order (A+E+C): {higher_pct}% (target 40%)"
            )
        else:
            score = 0
            deviation_detail = "No questions classified."
        
        # Build remarks
        if score >= 90:
            score_remark = "Distribution closely matches the target cognitive balance."
        elif score >= 70:
            score_remark = "Minor deviation from target distribution."
        elif score >= 50:
            score_remark = "Moderate imbalance — adjust question mix toward targets."
        else:
            score_remark = "Significant imbalance — paper skewed away from target distribution."
        
        remarks = f"Score: {score}/100. {score_remark} {deviation_detail}"

        # Debug logging
        print(f"🧠 BloomsClassifier: distribution = {distribution}")
        print(f"🧠 BloomsClassifier: total questions classified = {total}")
        print(f"🧠 BloomsClassifier: score = {score}/100")
        print(f"🧠 BloomsClassifier: co_mapping count = {len(co_mapping)}")
        
        return {
            "criterion": "blooms_taxonomy",
            "section": "quality",
            "status": "PASS" if is_balanced else "WARNING",
            "score": score,
            "remarks": remarks,
            "confidence": avg_confidence,
            "rule_triggered": "BLOOM_LLM_HYBRID" if llm_client.client else "BLOOM_VERB_CLASSIFIER",
            "evidence": {
                "distribution": distribution,
                "total_questions": total,
                "classifications": classification_results[:5],
                "llm_used": llm_client.client is not None,
                "target_distribution": {
                    "lower_order": "30% (Remember + Understand)",
                    "apply": "30% (Apply)",
                    "higher_order": "40% (Analyze + Evaluate + Create)"
                }
            },
            "baseline": "Target: Lower-order 30% | Apply 30% | Higher-order 40%",
            "suggestion": (
                "Distribution matches the target cognitive balance (Lower 30% | Apply 30% | Higher 40%)."
                if is_balanced else
                "Adjust question mix: target Lower-order=30%, Apply=30%, Higher-order (Analyze/Evaluate/Create)=40%."
            ),
            "distribution": distribution,
            "co_mapping": co_mapping
        }
    
    async def _classify_with_llm(self, question: Dict[str, Any], syllabus_context: str, training_context: str) -> Dict[str, Any]:
        """Classify using LLM with training context."""
        text = question.get("text", "")
        
        try:
            result = await llm_client.classify_bloom_level(text, syllabus_context)
            
            if "bloom_level" in result:
                return {
                    "question_number": question.get("number"),
                    "bloom_level": result.get("bloom_level", "Unknown"),
                    "confidence": result.get("confidence", 0.8),
                    "matched_verbs": [result.get("key_verb", "")],
                    "evidence": f"LLM: {result.get('reasoning', 'AI classification')}",
                    "reasoning": result.get("reasoning", ""),
                    "suggested_improvement": result.get("suggested_improvement", "")
                }
        except Exception as e:
            pass  # Fall through to return unknown
        
        return {
            "question_number": question.get("number"),
            "bloom_level": "Unknown",
            "confidence": 0.0,
            "matched_verbs": [],
            "evidence": "LLM not available"
        }
    
    def _classify_rule_based(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Classify using rule-based verb matching."""
        text = question.get("text", "").lower()
        
        matched_levels = {}
        
        for level, verbs in self.BLOOM_VERBS.items():
            for verb in verbs:
                patterns = [rf'\b{verb}\b', rf'^{verb}']
                for pattern in patterns:
                    if re.search(pattern, text):
                        if level not in matched_levels:
                            matched_levels[level] = []
                        matched_levels[level].append(verb)
        
        if not matched_levels:
            return {
                "question_number": question.get("number"),
                "bloom_level": "Unknown",
                "confidence": 0.5,
                "matched_verbs": [],
                "evidence": "No clear Bloom's verb detected"
            }
        
        # Select highest matched level
        for level in ["Create", "Evaluate", "Analyze", "Apply", "Understand", "Remember"]:
            if level in matched_levels:
                return {
                    "question_number": question.get("number"),
                    "bloom_level": level,
                    "confidence": min(0.85, 0.6 + len(matched_levels[level]) * 0.1),
                    "matched_verbs": matched_levels[level],
                    "evidence": f"Rule-based: matched verbs {', '.join(matched_levels[level])}"
                }
        
        return {
            "question_number": question.get("number"),
            "bloom_level": "Remember",
            "confidence": 0.6,
            "matched_verbs": [],
            "evidence": "Default classification"
        }
    
    def _check_balance(self, distribution: Dict[str, int], total: int) -> bool:
        """PASS when actual distribution is within ~20% of each target group."""
        if total == 0:
            return False
        actual_lower  = (distribution["Remember"] + distribution["Understand"]) / total
        actual_apply  = distribution["Apply"] / total
        actual_higher = (distribution["Analyze"] + distribution["Evaluate"] + distribution["Create"]) / total
        # Within 20 percentage points of each target
        return (
            abs(actual_lower  - 0.30) <= 0.20 and
            abs(actual_apply  - 0.30) <= 0.20 and
            abs(actual_higher - 0.40) <= 0.20
        )
    
    def _estimate_co(self, question_number: int, total_questions: int, exam_type: str) -> str:
        if not total_questions:
            return "CO1"
            
        exam_type = (exam_type or "").upper()
        
        if "CAT1" in exam_type:
            co_number = 1 if (question_number <= (total_questions + 1) // 2) else 2
        elif "CAT2" in exam_type:
            co_number = 3
        elif "CAT3" in exam_type:
            co_number = 4 if (question_number <= (total_questions + 1) // 2) else 5
        else:
            co_number = min(5, int((question_number - 1) * 5 / total_questions) + 1)
            
        return f"CO{co_number}"
