"""
Enhanced Syllabus Mapper
Uses semantic embeddings + LLM for accurate syllabus alignment
"""

from typing import Dict, Any, List, Optional
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.llm_client import llm_client
from rag.embeddings import embeddings_manager
from rag.training_data import training_data


class SyllabusMapper:
    """
    Maps each question to syllabus units.
    Uses semantic embeddings + LLM for accurate mapping.
    ENFORCED - requires justification to override.
    """
    
    ROMAN_TO_ARABIC = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
    
    def _normalize_unit_name(self, unit_name: str) -> str:
        """
        Normalize unit names to consistent format: 'Unit 1', 'Unit 2', etc.
        Handles variations like 'UNIT III', 'Module 2', 'Unit IV', etc.
        """
        if not unit_name:
            return None
        
        # Extract number from unit name
        import re
        
        # Try to find Roman numerals
        roman_match = re.search(r'\b([IVX]+)\b', unit_name.upper())
        if roman_match:
            roman = roman_match.group(1)
            if roman in self.ROMAN_TO_ARABIC:
                return f"Unit {self.ROMAN_TO_ARABIC[roman]}"
        
        # Try to find Arabic numerals
        arabic_match = re.search(r'\b(\d+)\b', unit_name)
        if arabic_match:
            return f"Unit {arabic_match.group(1)}"
        
        # Return the original if no number found
        return unit_name
    
    async def analyze(self, question_paper: Dict[str, Any], syllabus: Dict[str, Any], pattern_obj: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map questions to syllabus units using semantic similarity.
        Flags out-of-syllabus content.

        pattern_obj: the resolved pattern dict from the frontend selection.
                     Used to determine exam_type and allowed units.
                     For University exams: allowed_units = None (all 5 units in scope).
                     For CAT exams: allowed_units is restricted to specific units.
        """
        questions = question_paper.get("questions", [])
        syllabus_text = syllabus.get("raw_text", "")

        # Determine exam type and allowed units from the resolved pattern object.
        # pattern_obj is already a dict — no JSON parsing needed here.
        exam_type = "University"
        if pattern_obj and isinstance(pattern_obj, dict):
            exam_type = pattern_obj.get("exam_type", "University") or "University"
            # Fallback: infer exam_type from the pattern name if exam_type is missing
            if exam_type == "University":
                name = pattern_obj.get("name", "").upper()
                if "CAT-1" in name or "CAT1" in name:
                    exam_type = "CAT1"
                elif "CAT-2" in name or "CAT2" in name:
                    exam_type = "CAT2"
                elif "CAT-3" in name or "CAT3" in name:
                    exam_type = "CAT3"

        # Map exam type to allowed units for scope enforcement.
        # University exams cover ALL 5 units, so allowed_units = None (no restriction).
        # CAT exams are scoped to specific units.
        allowed_units = None  # None = all units allowed (University exam)
        if "CAT1" in exam_type.upper():
            allowed_units = {"Unit 1", "Unit 2"}
        elif "CAT2" in exam_type.upper():
            allowed_units = {"Unit 3"}
        elif "CAT3" in exam_type.upper():
            allowed_units = {"Unit 4", "Unit 5"}
        # University: allowed_units remains None — all 5 units are valid

        # Extract Part A question count from pattern sections
        part_a_qs = 10  # sensible default
        if pattern_obj and isinstance(pattern_obj, dict):
            sections = pattern_obj.get("sections", [])
            if sections:
                part_a_qs = int(sections[0].get("questions", 10))

        if pattern_obj:
            scope_info = f"allowed_units = {allowed_units if allowed_units else 'ALL (University — all 5 units in scope)'}"
        else:
            scope_info = "allowed_units = None (no pattern selected, defaulting to University)"
        print(f"SyllabusMapper: exam_type='{exam_type}', {scope_info}, part_a_qs={part_a_qs}")

        # Extract and embed units from syllabus
        units = self._extract_units(syllabus_text)
        unit_texts = [f"{u['name']}: {u['content']}" for u in units]

        # Pre-compute unit embeddings (mapping from unit name -> text for lookup)
        unit_embeddings = {}
        for i, unit in enumerate(units):
            unit_embeddings[unit["name"]] = unit_texts[i]

        mappings = []
        out_of_syllabus = []
        # Coverage always reflects ACTUAL unit distribution from the paper
        coverage = {}

        # Get training context for adaptive learning
        training_context = training_data.get_training_prompt_context("syllabus_alignment")

        for question in questions:
            # Try semantic matching first
            mapping = await self._map_with_embeddings(question, units, unit_texts)

            # If low confidence, try LLM
            if mapping["confidence"] < 0.7 and llm_client.client:
                llm_mapping = await self._map_with_llm(question, syllabus_text)
                if llm_mapping["confidence"] > mapping["confidence"]:
                    mapping = llm_mapping

            # Save the originally detected unit BEFORE any scope nullification
            # This is used for CO assignment so CO always reflects real content
            raw_unit = mapping.get("unit")
            if raw_unit:
                raw_unit = self._normalize_unit_name(raw_unit)
            mapping["detected_unit"] = raw_unit  # e.g. "Unit 3" even if out-of-scope

            # Determine if this is a big question (Part B/C) which can be from any unit
            is_big_question = False
            import re
            try:
                actual_num = int(re.search(r'\d+', question.get("label", "")).group())
                if actual_num > part_a_qs:
                    is_big_question = True
            except Exception:
                pass

            # Check if mapped unit is allowed for this exam type (scope enforcement)
            if mapping["unit"]:
                normalized_unit = self._normalize_unit_name(mapping["unit"])
                if allowed_units and normalized_unit not in allowed_units:
                    if is_big_question:
                        # Big questions can be from any unit, don't penalize
                        pass
                    else:
                        mapping["unit"] = None  # null unit = out-of-scope flag
                        mapping["reason"] = (
                            f"Question content belongs to {normalized_unit}, "
                            f"which is outside the scope of {exam_type} "
                            f"(expected: {', '.join(sorted(allowed_units))})"
                        )
                        mapping["confidence"] = 1.0

            # Check for suppression from training
            if training_data.should_suppress_finding("syllabus_alignment", question.get("text", "")):
                mapping["suppressed"] = True

            mappings.append(mapping)

            # Build coverage from the RAW detected unit (not the scope-nullified one)
            # This way coverage shows WHERE questions actually come from
            effective_unit = mapping["detected_unit"]
            if effective_unit:
                coverage[effective_unit] = coverage.get(effective_unit, 0) + 1
            
            if mapping["unit"] is None:
                # Either out-of-scope (scope enforcement) or truly not in syllabus
                out_of_syllabus.append({
                    "question": question["number"],
                    "text": question["text"][:100],
                    "reason": mapping.get("reason", "No matching unit found in syllabus"),
                    "confidence": mapping["confidence"],
                    "detected_unit": mapping.get("detected_unit")  # include for transparency
                })
        
        avg_confidence = sum(m["confidence"] for m in mappings) / len(mappings) if mappings else 0
        
        # Calculate quality score (0-100)
        total_questions = len(questions)
        out_count = len(out_of_syllabus)
        if total_questions > 0:
            coverage_ratio = max(0, (total_questions - out_count)) / total_questions
            score = round(coverage_ratio * 100)
        else:
            score = 0
        score = max(0, min(100, score))

        # Build remarks based on score
        if score >= 90:
            score_remark = "Excellent syllabus coverage."
        elif score >= 70:
            score_remark = "Good syllabus coverage with minor gaps."
        elif score >= 50:
            score_remark = "Partial syllabus coverage — several questions outside scope."
        else:
            score_remark = "Poor syllabus coverage — majority of questions outside prescribed syllabus."

        remarks = (f"Score: {score}/100. {score_remark} "
                   f"{f'Review {out_count} out-of-scope question(s).' if out_count else ''}")

        # Debug logging
        print(f"📚 SyllabusMapper: coverage = {coverage}")
        print(f"📚 SyllabusMapper: out_of_syllabus count = {len(out_of_syllabus)}")
        print(f"📚 SyllabusMapper: score = {score}/100")
        
        return {
            "criterion": "syllabus_alignment",
            "section": "quality",
            "status": "PASS" if not out_of_syllabus else "WARNING",
            "score": score,
            "remarks": remarks,
            "confidence": avg_confidence,
            "rule_triggered": "SEMANTIC_EMBEDDING_MATCH",
            "evidence": {
                "mappings": mappings,  # all mappings needed for CO consistency
                "out_of_syllabus": out_of_syllabus,
                "units_found": len(units),
                "embedding_model": embeddings_manager.MODEL_NAME if embeddings_manager.model else "fallback"
            },
            "baseline": f"Syllabus: {syllabus.get('filename', 'uploaded')}",
            "suggestion": (f"Review {len(out_of_syllabus)} questions: " + ", ".join([f"Q{q['question']} ({q['reason']})" for q in out_of_syllabus[:2]]) + ("..." if len(out_of_syllabus) > 2 else "") + " Use 'Suggest Fix' below.") if out_of_syllabus else "All questions appear to be within the specified syllabus scope.",
            "coverage": coverage
        }
    
    async def _map_with_embeddings(self, question: Dict[str, Any], units: List[Dict], unit_texts: List[str]) -> Dict[str, Any]:
        """Map question to unit using semantic embeddings."""
        question_text = question.get("text", "")
        
        # Find most similar unit
        similarities = embeddings_manager.find_most_similar(question_text, unit_texts, top_k=3)
        
        if similarities and similarities[0]["similarity"] >= 0.5:
            best_match = similarities[0]
            
            # Find which unit this matched text belongs to
            unit_name = "Unit 1"  # Default
            matched_text = best_match["text"]
            
            try:
                # Find the index of the matched text in unit_texts
                matched_index = unit_texts.index(matched_text)
                if matched_index < len(units):
                    unit_name = units[matched_index]["name"]
            except ValueError:
                # Fallback: try partial matching
                for i, ut in enumerate(unit_texts):
                    if ut == matched_text or matched_text in ut or ut in matched_text:
                        if i < len(units):
                            unit_name = units[i]["name"]
                        break
            
            return {
                "question_number": question.get("number"),
                "unit": unit_name,
                "confidence": min(0.95, best_match["similarity"]),
                "matched_keywords": [],
                "reason": f"Semantic similarity: {best_match['similarity']:.2f}",
                "similar_units": [s["text"][:50] for s in similarities[:2]]
            }
        
        return {
            "question_number": question.get("number"),
            "unit": None,
            "confidence": 0.3,
            "matched_keywords": [],
            "reason": "Low semantic similarity to all units"
        }
    
    async def _map_with_llm(self, question: Dict[str, Any], syllabus_text: str) -> Dict[str, Any]:
        """Map question to unit using LLM."""
        question_text = question.get("text", "")
        
        try:
            result = await llm_client.check_syllabus_alignment(question_text, syllabus_text)
            
            if result.get("is_aligned"):
                return {
                    "question_number": question.get("number"),
                    "unit": result.get("matched_unit", "Unit 1"),
                    "confidence": result.get("confidence", 0.8),
                    "matched_keywords": [result.get("matched_topic", "")],
                    "reason": f"LLM: {result.get('reasoning', 'AI analysis')}"
                }
            else:
                return {
                    "question_number": question.get("number"),
                    "unit": None,
                    "confidence": result.get("confidence", 0.7),
                    "matched_keywords": [],
                    "reason": result.get("out_of_scope_reason", "LLM: Out of syllabus")
                }
        except Exception as e:
            pass
        
        return {
            "question_number": question.get("number"),
            "unit": None,
            "confidence": 0.3,
            "matched_keywords": [],
            "reason": "LLM analysis failed"
        }
    
    def _extract_units(self, syllabus_text: str) -> List[Dict[str, Any]]:
        """Extract unit information from syllabus text."""
        units = []
        
        patterns = [
            r'UNIT\s*[-:]?\s*([IVX]+|[1-5])\s*[-:]?\s*(.+?)(?=UNIT|$)',
            r'Unit\s*[-:]?\s*([IVX]+|[1-5])\s*[-:]?\s*(.+?)(?=Unit|$)',
            r'MODULE\s*[-:]?\s*(\d+)\s*[-:]?\s*(.+?)(?=MODULE|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, syllabus_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                unit_num = match[0]
                content = match[1].strip()[:500]
                
                roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
                if unit_num.upper() in roman_map:
                    unit_num = str(roman_map[unit_num.upper()])
                
                units.append({
                    "number": unit_num,
                    "name": f"Unit {unit_num}",
                    "content": content,
                    "keywords": self._extract_keywords(content)
                })
        
        if not units:
            # Create generic units from document
            chunk_size = len(syllabus_text) // 5
            for i in range(1, 6):
                start = (i - 1) * chunk_size
                end = i * chunk_size
                units.append({
                    "number": str(i),
                    "name": f"Unit {i}",
                    "content": syllabus_text[start:end],
                    "keywords": []
                })
        
        return units
    
    def _extract_keywords(self, text: str) -> List[str]:
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", 
                      "being", "have", "has", "had", "do", "does", "did", "will",
                      "and", "or", "but", "if", "of", "to", "in", "for", "on", "with"}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        return list(set(keywords))[:50]
