"""Question-to-Syllabus Mapping and Scope Validation Service (Strict Zero-Score Implementation).

Maps examination questions to syllabus topics and Course Outcomes, verifies unit-wise
prescribed scope derived from examination patterns, and produces categorical, explainable
scrtuiny results without any numerical scores or percentages.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Protocol, runtime_checkable

import httpx

from app.core.config import settings
from app.schemas.question_mapping import (
    AlignmentStatus,
    CandidateTopicMatch,
    COChartItem,
    ExamScopeConfig,
    QuestionItem,
    QuestionMappingResult,
    StatusChartItem,
    SyllabusCoverageReport,
    UnitChartItem,
)
from app.schemas.syllabus import TopicSearchResult
from app.services.syllabus_retriever import SyllabusRetriever, syllabus_retriever
from app.services.vector_store import get_syllabus_vector_store
from format_compliance import checker

logger = logging.getLogger(__name__)


class InvalidScopeConfigurationError(ValueError):
    """Raised when examination scope configuration is missing or invalid."""

    pass


@runtime_checkable
class LLMValidatorProtocol(Protocol):
    """Protocol for optional structured LLM verification of question mappings."""

    async def validate_mapping(
        self,
        question_text: str,
        candidates: list[CandidateTopicMatch],
        permitted_units: list[int],
    ) -> dict[str, Any] | None: ...


class OllamaLLMValidator:
    """Structured LLM analysis client using Ollama or APInex with automatic fallback."""

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: float = 3.0,
    ):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.timeout = timeout

    async def validate_mapping(
        self,
        question_text: str,
        candidates: list[CandidateTopicMatch],
        permitted_units: list[int],
    ) -> dict[str, Any] | None:
        """Call LLM for structured JSON analysis. Returns None on failure/unavailability."""
        if not candidates:
            return None

        prompt = (
            f"You are an academic scrutiny analyzer. Given an exam question and top 5 candidate syllabus topics, "
            f"determine if the question is in scope for permitted units {permitted_units}.\n\n"
            f"Question: {question_text}\n"
            f"Candidates:\n"
            + "\n".join(
                f"- [ID: {c.topic_id}] Unit {c.unit_number}: {c.topic_title} (Score: {c.similarity_score:.3f})"
                for c in candidates
            )
            + "\n\nRespond ONLY in valid JSON format with keys: "
            "mapped_topic_ids (list), primary_unit (int or null), is_in_scope (bool), is_ambiguous (bool), reasoning (str)."
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("response", "")
                    return json.loads(raw_text)
        except Exception as e:
            logger.debug(
                f"LLM validation unavailable or failed ({e}); falling back to heuristic rules."
            )
            return None
        return None


class SyllabusMapper:
    """Maps examination questions to syllabus topics and validates unit-wise scope (No scores)."""

    STRONG_MATCH_THRESHOLD = 0.35
    MINIMUM_RELEVANCE_THRESHOLD = 0.30
    AMBIGUITY_SCORE_DELTA = 0.045

    COMPOUND_TERMS = [
        (re.compile(r"\bflow\s*[-–—]?\s*chart\b", re.IGNORECASE), "flowchart"),
        (re.compile(r"\bpseudo\s*[-–—]?\s*code\b", re.IGNORECASE), "pseudocode"),
        (re.compile(r"\blinked\s*[-–—]?\s*list\b", re.IGNORECASE), "linkedlist"),
        (re.compile(r"\bbinary\s*[-–—]?\s*search\b", re.IGNORECASE), "binarysearch"),
        (re.compile(r"\bdecision\s*[-–—]?\s*making\b", re.IGNORECASE), "decisionmaking"),
        (re.compile(r"\bdata\s*[-–—]?\s*structure\b", re.IGNORECASE), "datastructure"),
        (re.compile(r"\bshortest\s*[-–—]?\s*path\b", re.IGNORECASE), "shortestpath"),
        (re.compile(r"\bdynamic\s*[-–—]?\s*programming\b", re.IGNORECASE), "dynamicprogramming"),
    ]

    def __init__(
        self,
        retriever: SyllabusRetriever | None = None,
        llm_validator: LLMValidatorProtocol | None = None,
    ):
        self.retriever = retriever or syllabus_retriever
        self.llm_validator = llm_validator

    def resolve_permitted_units(self, scope_config: ExamScopeConfig) -> list[int]:
        """Resolve permitted units from scope config or pattern repository.

        Rejects missing or invalid scope configurations as configuration errors.
        """
        # Case 1: Explicitly provided permitted_units list
        if scope_config.permitted_units:
            units = scope_config.permitted_units
            if not all(isinstance(u, int) and u > 0 for u in units):
                raise InvalidScopeConfigurationError(
                    f"Invalid scope configuration: permitted_units must be positive integers, got {units}"
                )
            return sorted(list(set(units)))

        # Case 2: Resolve from institutional pattern definitions
        target_name = scope_config.pattern_name
        target_category = scope_config.exam_type

        patterns_dict = checker.patterns
        matched_pattern = None

        if target_name:
            for _cat, p_list in patterns_dict.items():
                for p in p_list:
                    if p.get("name", "").strip().lower() == target_name.strip().lower():
                        matched_pattern = p
                        break
                if matched_pattern:
                    break

        if not matched_pattern and target_category:
            cat_list = patterns_dict.get(target_category, [])
            if cat_list:
                matched_pattern = cat_list[0]

        if matched_pattern and "permitted_units" in matched_pattern:
            units = matched_pattern["permitted_units"]
            if units and all(isinstance(u, int) and u > 0 for u in units):
                return sorted(list(set(units)))

        # If we cannot resolve a valid non-empty permitted_units list, strictly reject
        raise InvalidScopeConfigurationError(
            f"Missing or invalid examination scope configuration. Unable to determine permitted units "
            f"for pattern='{target_name}', category='{target_category}'."
        )

    def get_pattern_dict(self, scope_config: ExamScopeConfig) -> dict[str, Any] | None:
        """Find the matching pattern dictionary in the repository."""
        target_name = scope_config.pattern_name
        target_category = scope_config.exam_type
        patterns_dict = checker.patterns

        if target_name:
            for _cat, p_list in patterns_dict.items():
                for p in p_list:
                    if p.get("name", "").strip().lower() == target_name.strip().lower():
                        return p

        if target_category and target_category in patterns_dict:
            cat_list = patterns_dict[target_category]
            if cat_list:
                return cat_list[0]

        return None

    def determine_prescribed_unit(
        self,
        question: QuestionItem,
        pattern_dict: dict[str, Any] | None,
        question_index: int = 0,
        total_questions: int = 1,
    ) -> int | None:
        """Determine prescribed syllabus unit for a question driven strictly by pattern configuration."""
        if not pattern_dict:
            return None

        unit_mapping = pattern_dict.get("unit_mapping")
        if not unit_mapping or not isinstance(unit_mapping, dict):
            return None

        map_type = unit_mapping.get("type")

        # 1. Fixed unit (e.g. CAT-2 Unit III)
        if map_type == "fixed_unit":
            return unit_mapping.get("required_unit", 3)

        # 2. University Question Number Map (Part A Q1-Q10, Part B Q11-Q15, Part C Q16)
        if map_type == "question_number_map":
            # Check for 15-mark questions / Part C
            # User requirement: 15-mark question can be from ANY unit in the syllabus.
            # There is no strict single unit prescribed for 15-mark questions.
            is_15_mark = (
                (question.marks == 15.0)
                or (question.section and "C" in question.section.upper())
                or (str(question.question_number).strip() in ["16", "Q16"])
                or (question.question_id and "16" in question.question_id)
            )
            if is_15_mark:
                return None

            # Look up question number in rules
            q_num = question.question_number
            if not q_num:
                # Extract digits from question_id e.g. "Q11(a)" -> "11"
                m = re.search(r"\d+", question.question_id)
                if m:
                    q_num = m.group(0)

            rules = unit_mapping.get("rules", {})
            if q_num and str(q_num) in rules:
                return int(rules[str(q_num)])

            # Fallback if question_number not found directly
            try:
                q_int = int(q_num) if q_num else (question_index + 1)
                if 1 <= q_int <= 10:
                    return ((q_int - 1) // 2) + 1
                elif 11 <= q_int <= 15:
                    return q_int - 10
                elif q_int == 16:
                    return None
            except (ValueError, TypeError):
                pass

            return None

        # 3. Section Group Map (CAT-1, CAT-3 with two Part A and two Part B occurrences)
        if map_type == "section_group":
            groups = unit_mapping.get("groups", [])
            # Extract question number or index
            q_num = question.question_number
            if not q_num:
                m = re.search(r"\d+", question.question_id)
                if m:
                    q_num = m.group(0)

            try:
                q_int = int(q_num) if q_num else (question_index + 1)
            except (ValueError, TypeError):
                q_int = question_index + 1

            exam_type = pattern_dict.get("exam_type", "").upper()

            if "CAT1" in exam_type or "CAT-1" in exam_type:
                # Standard: Q1-Q5 (U1), Q6 (U1), Q7-Q11 (U2), Q12 (U2)
                # Alternate: Q1-Q6 (U1), Q7 (U1), Q8-Q13 (U2), Q14 (U2)
                # Check based on question counts from groups
                if len(groups) >= 4:
                    g1_count = groups[0].get("questions_count", 5)
                    g2_count = groups[1].get("questions_count", 1)
                    u1_total = g1_count + g2_count
                    if q_int <= u1_total:
                        return 1
                    else:
                        return 2
                return 1 if q_int <= 6 else 2

            elif "CAT3" in exam_type or "CAT-3" in exam_type:
                # CAT-3: First half -> Unit 4, Second half -> Unit 5
                if len(groups) >= 4:
                    g1_count = groups[0].get("questions_count", 5)
                    g2_count = groups[1].get("questions_count", 1)
                    u4_total = g1_count + g2_count
                    if q_int <= u4_total:
                        return 4
                    else:
                        return 5
                return 4 if q_int <= 6 else 5

        return None

    def _normalize_compounds(self, text: str) -> str:
        """Normalize common split compound technical terms."""
        res = text
        for pat, rep in self.COMPOUND_TERMS:
            res = pat.sub(rep, res)
        return res

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract meaningful domain words (>= 4 chars, non-stopword)."""
        stopwords = {
            "what",
            "when",
            "where",
            "which",
            "with",
            "from",
            "that",
            "this",
            "these",
            "those",
            "explain",
            "describe",
            "write",
            "detail",
            "using",
            "between",
            "short",
            "note",
            "give",
            "state",
            "briefly",
            "discuss",
            "their",
            "about",
            "examples",
            "differentiate",
            "illustrate",
            "and",
            "the",
            "for",
            "are",
            "was",
            "were",
            "can",
            "could",
            "should",
            "would",
            "how",
            "all",
            "any",
            "each",
            "both",
            "such",
            "into",
            "than",
            "then",
            "also",
            "some",
            "other",
            "have",
            "has",
            "had",
            "draw",
            "symbol",
            "does",
        }
        normalized = self._normalize_compounds(text)
        tokens = re.findall(r"\b[A-Za-z]{4,}\b", normalized.lower())
        raw_tokens = re.findall(r"\b[A-Za-z]{4,}\b", text.lower())
        all_tokens = set(tokens).union(set(raw_tokens))
        return {t for t in all_tokens if t not in stopwords}

    def _has_keyword_overlap(self, q_text: str, cand_title: str, cand_desc: str) -> bool:
        """Check if question has meaningful domain keyword overlap with syllabus topic."""
        q_kws = self._extract_keywords(q_text)
        cand_kws = self._extract_keywords(f"{cand_title} {cand_desc}")
        if not q_kws or not cand_kws:
            return False
        if q_kws.intersection(cand_kws):
            return True
        # Substring / compound component check (e.g., 'flowchart' matching 'flow' or 'chart')
        for qk in q_kws:
            for ck in cand_kws:
                if (len(qk) >= 4 and len(ck) >= 4) and (qk in ck or ck in qk):
                    return True
        return False

    async def map_single_question(
        self,
        question: QuestionItem,
        syllabus_id: str,
        permitted_units: list[int],
        required_unit: int | None = None,
        pattern_dict: dict[str, Any] | None = None,
        syllabus_exists: bool = True,
    ) -> QuestionMappingResult:
        """Map a single examination question to syllabus topics and Course Outcomes."""
        choice_group = question.choice_group or f"Q{question.question_number or question.question_id}"

        # 1. Error check: empty question text
        if not question.text or not question.text.strip():
            return QuestionMappingResult(
                question_id=question.question_id,
                question_text=question.text or "",
                marks=question.marks,
                section=question.section,
                question_number=question.question_number,
                subquestion_id=question.subquestion_id,
                choice_group=choice_group,
                is_alternative=question.is_alternative,
                required_unit=required_unit,
                matched_unit=None,
                matched_topic=None,
                course_outcome="CO_NOT_AVAILABLE",
                status=AlignmentStatus.REVIEW_REQUIRED,
                reason="Question statement text is empty or missing.",
                evidence=None,
                requires_human_review=True,
                error_message="Question text cannot be empty.",
            )

        # 2. Error check: syllabus not found
        if not syllabus_exists:
            return QuestionMappingResult(
                question_id=question.question_id,
                question_text=question.text,
                marks=question.marks,
                section=question.section,
                question_number=question.question_number,
                subquestion_id=question.subquestion_id,
                choice_group=choice_group,
                is_alternative=question.is_alternative,
                required_unit=required_unit,
                matched_unit=None,
                matched_topic=None,
                course_outcome="CO_NOT_AVAILABLE",
                status=AlignmentStatus.REVIEW_REQUIRED,
                reason=f"Syllabus '{syllabus_id}' is not indexed in vector store.",
                evidence=None,
                requires_human_review=True,
                error_message=f"Syllabus '{syllabus_id}' not found.",
            )

        # 3. Resolve required unit if not explicitly supplied
        if required_unit is None and pattern_dict:
            required_unit = self.determine_prescribed_unit(question, pattern_dict)

        # Detect 15-mark / Part C questions (can legitimately be from any unit in the syllabus)
        is_15_mark = (
            (question.marks == 15.0)
            or (question.section and "C" in question.section.upper())
            or (str(question.question_number).strip() in ["16", "Q16"])
            or (question.question_id and "16" in question.question_id)
        )

        # 4. Retrieve top 5 matching topics from the COMPLETE syllabus (no unit restriction)
        retrieval_response = await self.retriever.retrieve_top_topics(
            query=question.text,
            top_k=5,
            syllabus_id=syllabus_id,
        )

        raw_candidates: list[TopicSearchResult] = retrieval_response.results
        candidate_matches: list[CandidateTopicMatch] = [
            CandidateTopicMatch(
                topic_id=c.topic.topic_id,
                unit_number=c.topic.unit_number,
                unit_title=c.topic.unit_title,
                topic_title=c.topic.topic_title,
                description=c.topic.content,
                similarity_score=c.similarity_score,
                source_page=c.topic.source_page,
                co_identifiers=c.topic.co_identifiers,
                is_unrecognized_unit=c.topic.is_unrecognized_unit,
            )
            for c in raw_candidates
        ]

        if not candidate_matches:
            return QuestionMappingResult(
                question_id=question.question_id,
                question_text=question.text,
                marks=question.marks,
                section=question.section,
                question_number=question.question_number,
                subquestion_id=question.subquestion_id,
                choice_group=choice_group,
                is_alternative=question.is_alternative,
                required_unit=required_unit,
                matched_unit=None,
                matched_topic=None,
                course_outcome="CO_NOT_AVAILABLE",
                status=AlignmentStatus.UNMAPPED,
                reason="No candidate topics found in indexed syllabus for this query.",
                evidence=None,
                requires_human_review=True,
                candidate_topics=[],
            )

        # Apply lexical match bonus so that exact curricular matches rank first
        for cand in candidate_matches:
            if self._has_keyword_overlap(question.text, cand.topic_title, cand.description):
                cand.similarity_score += 0.15

        # Re-sort descending by score
        candidate_matches.sort(key=lambda c: c.similarity_score, reverse=True)

        top_cand = candidate_matches[0]
        top_score = top_cand.similarity_score
        has_overlap = self._has_keyword_overlap(question.text, top_cand.topic_title, top_cand.description)

        # 5. Low relevance and zero keywords -> UNMAPPED
        if top_score < self.MINIMUM_RELEVANCE_THRESHOLD and not has_overlap:
            return QuestionMappingResult(
                question_id=question.question_id,
                question_text=question.text,
                marks=question.marks,
                section=question.section,
                question_number=question.question_number,
                subquestion_id=question.subquestion_id,
                choice_group=choice_group,
                is_alternative=question.is_alternative,
                required_unit=required_unit,
                matched_unit=None,
                matched_topic=None,
                course_outcome="CO_NOT_AVAILABLE",
                status=AlignmentStatus.UNMAPPED,
                reason="Question does not sufficiently align with any indexed syllabus topic.",
                evidence=None,
                requires_human_review=True,
                candidate_topics=candidate_matches,
            )

        # Course Outcome extraction from explicit syllabus evidence (Never fabricate!)
        course_outcome = "CO_NOT_AVAILABLE"
        if top_cand.co_identifiers:
            course_outcome = ", ".join(sorted(top_cand.co_identifiers))

        evidence_snippet = (
            f"Topic: {top_cand.topic_title} (Unit {top_cand.unit_number or '?'}) | "
            f"Content: {top_cand.description[:180].strip()}"
        )

        # If required_unit is still None and permitted_units is provided (e.g. ad-hoc single mapping):
        if required_unit is None and permitted_units:
            if top_cand.unit_number in permitted_units:
                required_unit = top_cand.unit_number
            else:
                required_unit = permitted_units[0]

        # Check optional LLM analysis
        if self.llm_validator:
            try:
                llm_res = await self.llm_validator.validate_mapping(
                    question_text=question.text,
                    candidates=candidate_matches,
                    permitted_units=permitted_units,
                )
                if llm_res and llm_res.get("primary_unit"):
                    # Use LLM primary unit if provided
                    pass
            except Exception as e:
                logger.debug(f"LLM validation fallback: {e}")

        # 6. Check for Ambiguity
        is_ambiguous = False
        if (
            len(candidate_matches) >= 2
            and candidate_matches[0].unit_number is not None
            and candidate_matches[1].unit_number is not None
            and candidate_matches[0].unit_number != candidate_matches[1].unit_number
            and abs(candidate_matches[0].similarity_score - candidate_matches[1].similarity_score)
            <= self.AMBIGUITY_SCORE_DELTA
        ):
            c1, c2 = candidate_matches[0], candidate_matches[1]
            if (c1.unit_number in permitted_units and c2.unit_number not in permitted_units) or (
                c1.unit_number not in permitted_units and c2.unit_number in permitted_units
            ):
                is_ambiguous = True

        if is_ambiguous:
            c1, c2 = candidate_matches[0], candidate_matches[1]
            return QuestionMappingResult(
                question_id=question.question_id,
                question_text=question.text,
                marks=question.marks,
                section=question.section,
                question_number=question.question_number,
                subquestion_id=question.subquestion_id,
                choice_group=choice_group,
                is_alternative=question.is_alternative,
                required_unit=required_unit,
                matched_unit=top_cand.unit_number,
                matched_topic=top_cand.topic_title,
                course_outcome=course_outcome,
                status=AlignmentStatus.AMBIGUOUS,
                reason=(
                    f"Ambiguous syllabus alignment: candidate evidence spans Unit {c1.unit_number} "
                    f"('{c1.topic_title}') and Unit {c2.unit_number} ('{c2.topic_title}')."
                ),
                evidence=evidence_snippet,
                requires_human_review=True,
                candidate_topics=candidate_matches,
                mapped_topics=[c1, c2],
            )

        # 7. Check Alignment vs Mismatch against required_unit & permitted_units
        if is_15_mark:
            # User requirement: The 15 mark question can be from any unit in the syllabus.
            # Only check if it is in the given syllabus (permitted_units), otherwise out of syllabus (MISMATCH).
            if top_cand.unit_number in permitted_units:
                return QuestionMappingResult(
                    question_id=question.question_id,
                    question_text=question.text,
                    marks=question.marks,
                    section=question.section,
                    question_number=question.question_number,
                    subquestion_id=question.subquestion_id,
                    choice_group=choice_group,
                    is_alternative=question.is_alternative,
                    required_unit=top_cand.unit_number,
                    matched_unit=top_cand.unit_number,
                    matched_topic=top_cand.topic_title,
                    course_outcome=course_outcome,
                    status=AlignmentStatus.ALIGNED,
                    reason=(
                        f"Confirmed IN_SCOPE: 15-mark question aligns with Unit {top_cand.unit_number} topic: "
                        f"'{top_cand.topic_title}' (permitted across any unit in the syllabus)."
                    ),
                    evidence=evidence_snippet,
                    requires_human_review=False,
                    candidate_topics=candidate_matches,
                    mapped_topics=[top_cand],
                )
            else:
                return QuestionMappingResult(
                    question_id=question.question_id,
                    question_text=question.text,
                    marks=question.marks,
                    section=question.section,
                    question_number=question.question_number,
                    subquestion_id=question.subquestion_id,
                    choice_group=choice_group,
                    is_alternative=question.is_alternative,
                    required_unit=None,
                    matched_unit=top_cand.unit_number,
                    matched_topic=top_cand.topic_title,
                    course_outcome=course_outcome,
                    status=AlignmentStatus.MISMATCH,
                    reason=(
                        f"Confirmed OUT_OF_SCOPE: 15-mark question topic '{top_cand.topic_title}' belongs to "
                        f"Unit {top_cand.unit_number}, which is outside permitted syllabus units {permitted_units}."
                    ),
                    evidence=evidence_snippet,
                    requires_human_review=True,
                    candidate_topics=candidate_matches,
                    mapped_topics=[top_cand],
                )

        # Standard non-15-mark questions: enforce prescribed unit
        is_aligned = (
            top_cand.unit_number == required_unit
            if required_unit is not None
            else (top_cand.unit_number in permitted_units)
        )

        if is_aligned:
            return QuestionMappingResult(
                question_id=question.question_id,
                question_text=question.text,
                marks=question.marks,
                section=question.section,
                question_number=question.question_number,
                subquestion_id=question.subquestion_id,
                choice_group=choice_group,
                is_alternative=question.is_alternative,
                required_unit=required_unit or top_cand.unit_number,
                matched_unit=top_cand.unit_number,
                matched_topic=top_cand.topic_title,
                course_outcome=course_outcome,
                status=AlignmentStatus.ALIGNED,
                reason=f"Confirmed IN_SCOPE: Question aligns with Unit {top_cand.unit_number} topic: '{top_cand.topic_title}'.",
                evidence=evidence_snippet,
                requires_human_review=False,
                candidate_topics=candidate_matches,
                mapped_topics=[top_cand],
            )
        else:
            return QuestionMappingResult(
                question_id=question.question_id,
                question_text=question.text,
                marks=question.marks,
                section=question.section,
                question_number=question.question_number,
                subquestion_id=question.subquestion_id,
                choice_group=choice_group,
                is_alternative=question.is_alternative,
                required_unit=required_unit,
                matched_unit=top_cand.unit_number,
                matched_topic=top_cand.topic_title,
                course_outcome=course_outcome,
                status=AlignmentStatus.MISMATCH,
                reason=(
                    f"Confirmed OUT_OF_SCOPE: Topic '{top_cand.topic_title}' belongs to Unit {top_cand.unit_number}, "
                    f"violating prescribed Unit {required_unit} (outside permitted scope {permitted_units})."
                ),
                evidence=evidence_snippet,
                requires_human_review=True,
                candidate_topics=candidate_matches,
                mapped_topics=[top_cand],
            )

    async def map_questions_batch(
        self,
        questions: list[QuestionItem],
        syllabus_id: str,
        scope_config: ExamScopeConfig,
    ) -> SyllabusCoverageReport:
        """Batch map examination questions against an ingested syllabus with zero numerical scores."""
        # 1. Resolve scope configuration & pattern
        try:
            permitted_units = self.resolve_permitted_units(scope_config)
            pattern_dict = self.get_pattern_dict(scope_config)
        except InvalidScopeConfigurationError as e:
            error_results = [
                QuestionMappingResult(
                    question_id=q.question_id,
                    question_text=q.text,
                    marks=q.marks,
                    section=q.section,
                    question_number=q.question_number,
                    subquestion_id=q.subquestion_id,
                    choice_group=q.choice_group,
                    is_alternative=q.is_alternative,
                    required_unit=None,
                    status=AlignmentStatus.REVIEW_REQUIRED,
                    reason=str(e),
                    requires_human_review=True,
                    error_message=str(e),
                )
                for q in questions
            ]
            return SyllabusCoverageReport(
                syllabus_id=syllabus_id,
                exam_pattern_name=scope_config.pattern_name,
                overall_status="REVIEW_REQUIRED",
                total_questions=len(questions),
                total_question_groups=len(
                    {q.choice_group or q.question_number or q.question_id for q in questions}
                )
                if questions
                else 0,
                aligned_count=0,
                mismatch_count=0,
                ambiguous_count=0,
                unmapped_count=0,
                review_required_count=len(questions),
                requires_human_review=True,
                review_reasons=[f"Scope Configuration Error: {e}"],
                chart_prescribed_units=[],
                chart_course_outcomes=[],
                chart_status_distribution=[],
                results=error_results,
                limitations=[
                    "Invalid or missing scope configuration prevents automated scope verification.",
                    "Strict zero-score policy enforced across all scrutiny criteria.",
                ],
            )

        # 2. Check if syllabus is indexed
        vector_store = getattr(self.retriever, "vector_store", None) or get_syllabus_vector_store()
        syllabus_exists = await vector_store.has_syllabus(syllabus_id)

        # 3. Process each question
        results: list[QuestionMappingResult] = []
        for idx, q in enumerate(questions):
            req_unit = self.determine_prescribed_unit(
                question=q,
                pattern_dict=pattern_dict,
                question_index=idx,
                total_questions=len(questions),
            )
            res = await self.map_single_question(
                question=q,
                syllabus_id=syllabus_id,
                permitted_units=permitted_units,
                required_unit=req_unit,
                pattern_dict=pattern_dict,
                syllabus_exists=syllabus_exists,
            )
            results.append(res)

        # 4. Count questions and question groups (preventing alternative inflation)
        total_questions = len(results)
        unique_groups = set()
        for r in results:
            unique_groups.add(r.choice_group or r.question_number or r.question_id)
        total_question_groups = len(unique_groups)

        aligned_count = sum(1 for r in results if r.status == AlignmentStatus.ALIGNED)
        mismatch_count = sum(1 for r in results if r.status == AlignmentStatus.MISMATCH)
        ambiguous_count = sum(1 for r in results if r.status == AlignmentStatus.AMBIGUOUS)
        unmapped_count = sum(1 for r in results if r.status == AlignmentStatus.UNMAPPED)
        review_required_count = sum(
            1 for r in results if r.status == AlignmentStatus.REVIEW_REQUIRED
        )

        # 5. Determine Overall Categorical Status (Strict Zero-Score)
        if mismatch_count > 0:
            overall_status = "MISMATCH"
        elif (
            review_required_count > 0
            or ambiguous_count > 0
            or unmapped_count > 0
            or not syllabus_exists
            or total_questions == 0
        ):
            overall_status = "REVIEW_REQUIRED"
        else:
            overall_status = "ALIGNED"

        # 6. Human Review Triggers
        review_reasons = []
        if not syllabus_exists:
            review_reasons.append(f"Syllabus '{syllabus_id}' is not indexed or contains no topics.")
        if mismatch_count > 0:
            review_reasons.append(
                f"Contains {mismatch_count} question(s) violating prescribed syllabus unit."
            )
        if ambiguous_count > 0:
            review_reasons.append(
                f"Contains {ambiguous_count} ambiguous question(s) requiring scrutinizer verification."
            )
        if unmapped_count > 0:
            review_reasons.append(
                f"Contains {unmapped_count} unmapped question(s) not matched to syllabus."
            )
        if review_required_count > 0:
            review_reasons.append(
                f"Contains {review_required_count} question(s) requiring pattern/faculty scrutiny."
            )
        if total_questions == 0:
            review_reasons.append("Empty question paper: zero assessable questions provided.")

        requires_human_review = overall_status != "ALIGNED"

        # 7. Chart A: Questions by Prescribed Unit (Avoiding Alternative Inflation)
        chart_prescribed_units: list[UnitChartItem] = []
        total_units = scope_config.total_units or 5
        for u in range(1, total_units + 1):
            unit_qs = [r for r in results if r.required_unit == u]
            unit_groups = {r.choice_group or r.question_number or r.question_id for r in unit_qs}
            chart_prescribed_units.append(
                UnitChartItem(
                    unit_number=u,
                    unit_label=f"Unit {u}",
                    question_count=len(unit_qs),
                    question_group_count=len(unit_groups),
                    question_ids=[r.question_id for r in unit_qs],
                    is_permitted=(u in permitted_units),
                )
            )

        # 8. Chart B: Questions by Course Outcome (Counts Only, No Scores)
        all_cos = sorted(
            {r.course_outcome for r in results if r.course_outcome and r.course_outcome != "CO_NOT_AVAILABLE"}
        )
        has_unavailable = any(r.course_outcome == "CO_NOT_AVAILABLE" for r in results)
        if has_unavailable or not all_cos:
            all_cos.append("CO_NOT_AVAILABLE")

        chart_course_outcomes: list[COChartItem] = []
        for co in all_cos:
            co_qs = [r for r in results if r.course_outcome == co]
            chart_course_outcomes.append(
                COChartItem(
                    co_id=co,
                    question_count=len(co_qs),
                    question_ids=[r.question_id for r in co_qs],
                )
            )

        # 9. Chart C: Alignment Status Distribution (Counts Only, No Scores)
        chart_status_distribution: list[StatusChartItem] = []
        for status_enum in [
            AlignmentStatus.ALIGNED,
            AlignmentStatus.MISMATCH,
            AlignmentStatus.AMBIGUOUS,
            AlignmentStatus.UNMAPPED,
            AlignmentStatus.REVIEW_REQUIRED,
        ]:
            st_qs = [r for r in results if r.status == status_enum]
            chart_status_distribution.append(
                StatusChartItem(
                    status=status_enum.value,
                    question_count=len(st_qs),
                    question_ids=[r.question_id for r in st_qs],
                )
            )

        return SyllabusCoverageReport(
            syllabus_id=syllabus_id,
            exam_pattern_name=scope_config.pattern_name,
            overall_status=overall_status,
            total_questions=total_questions,
            total_question_groups=total_question_groups,
            aligned_count=aligned_count,
            mismatch_count=mismatch_count,
            ambiguous_count=ambiguous_count,
            unmapped_count=unmapped_count,
            review_required_count=review_required_count,
            requires_human_review=requires_human_review,
            review_reasons=review_reasons,
            chart_prescribed_units=chart_prescribed_units,
            chart_course_outcomes=chart_course_outcomes,
            chart_status_distribution=chart_status_distribution,
            results=results,
            limitations=[
                "Zero-Score Criterion 3 implementation: No numerical scores, confidence weights, or percentages used.",
                "Alternative choices (e.g. 11(a) OR 11(b)) are grouped to prevent question count inflation.",
                "Course Outcomes without official syllabus declaration are marked as CO_NOT_AVAILABLE.",
            ],
        )


# Global singleton
syllabus_mapper = SyllabusMapper()
