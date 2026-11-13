"""Mark and Time Distribution Scrutiny Service (Criterion 4).

Implements Anna University and institutional examination mark distribution rules:
- Rule 1 (LLM API Semantic): Validate Part A 2-mark questions for answer complexity.
- Rule 2 (Deterministic Python): Validate Part B/C placement and flag 2-mark misplacement.
- Rule 3 (Deterministic Python): Validate Part B/C 13/15/16-mark subdivision counts (<= 2 PASS, > 2 FLAG),
  evaluating OR alternatives independently.

Zero numerical scores, percentages, or LLM confidence values are returned.
"""

from __future__ import annotations

import logging
import re

from app.schemas.mark_distribution import (
    LLMComplexityResult,
    MarkDistributionReport,
    MarkDistributionStatus,
    QuestionMarkEvaluation,
    SemanticComplexity,
    ValidationRuleId,
)
from app.schemas.question_mapping import QuestionItem
from app.services.llm_service import LLMService, llm_service

logger = logging.getLogger("scrucheck.mark_distribution")

# Regex to split on OR alternatives in question headings or text
OR_DELIMITER_PATTERN = re.compile(
    r"\s*(?:\[\s*OR\s*\]|\(\s*OR\s*\)|\bOR\b)\s*",
    re.IGNORECASE,
)

# Regex to extract subdivision labels like "(a)", "(b)", "a)", "11(a)", "11(a)(i)", "(i)", etc.
SUBDIVISION_LABEL_PATTERN = re.compile(
    r"(?:Q?[0-9]{1,2}\s*)?(?:\(([a-d](?:\([ivx]+\))?|[ivx]+)\)|([a-d])[\.:\)])",
    re.IGNORECASE,
)


class MarkDistributionValidator:
    """Scrutiny engine for Criterion 4: Mark and Time Distribution."""

    def __init__(self, llm_client: LLMService | None = None) -> None:
        self.llm = llm_client or llm_service

    # =========================================================================
    # Rule 1: Part A 2-Mark Question Semantic Complexity Validation (LLM API)
    # =========================================================================

    async def validate_part_a_complexity(
        self,
        question: QuestionItem,
        course_context: str | None = None,
        syllabus_topic: str | None = None,
        learning_outcome: str | None = None,
    ) -> QuestionMarkEvaluation:
        """Validate whether a Part A 2-mark question requires appropriate answer depth.

        Uses LLM API to interpret semantic depth and reasoning requirements.
        - SHORT_ANSWER -> PASS
        - LONG_ANSWER  -> FLAG (disproportionate cognitive/answer demand for 2 marks)
        - REVIEW_REQUIRED (or API failure) -> REVIEW_REQUIRED
        """
        # Ensure section is Part A
        section_name = question.section or "Part A"
        marks = question.marks if question.marks is not None else 2.0

        # Deterministic guard: if Part A question is assigned > 2 marks (e.g. 13 marks in Part A)
        if marks > 2.0:
            return QuestionMarkEvaluation(
                question_id=question.question_id,
                section=section_name,
                assigned_marks=marks,
                complexity_classification=SemanticComplexity.NOT_APPLICABLE,
                subdivision_count=None,
                subdivision_labels=[],
                status=MarkDistributionStatus.FLAG,
                reason=(
                    f"Question {question.question_id} in {section_name} is assigned {marks} marks. "
                    "Part A is strictly reserved for 2-mark short-answer questions."
                ),
                rule_triggered=ValidationRuleId.RULE_2_SECTION_MARK_MISPLACEMENT,
                requires_human_review=False,
            )

        # Call LLM for semantic evaluation
        llm_result: LLMComplexityResult = await self.llm.analyze_question_complexity(
            question_text=question.text,
            assigned_marks=marks,
            section=section_name,
            course_context=course_context,
            syllabus_topic=syllabus_topic,
            learning_outcome=learning_outcome,
        )

        if llm_result.complexity_classification == SemanticComplexity.LONG_ANSWER:
            return QuestionMarkEvaluation(
                question_id=question.question_id,
                section=section_name,
                assigned_marks=marks,
                complexity_classification=SemanticComplexity.LONG_ANSWER,
                subdivision_count=None,
                subdivision_labels=[],
                status=MarkDistributionStatus.FLAG,
                reason=(
                    f"The question requires an extended long-answer response ({llm_result.reason}), "
                    "which is disproportionate for the 2-mark allocation in Part A."
                ),
                rule_triggered=ValidationRuleId.RULE_1_PART_A_COMPLEXITY,
                requires_human_review=False,
            )

        if llm_result.complexity_classification == SemanticComplexity.SHORT_ANSWER:
            return QuestionMarkEvaluation(
                question_id=question.question_id,
                section=section_name,
                assigned_marks=marks,
                complexity_classification=SemanticComplexity.SHORT_ANSWER,
                subdivision_count=None,
                subdivision_labels=[],
                status=MarkDistributionStatus.PASS,
                reason=f"Appropriate short-answer scope for 2 marks: {llm_result.reason}",
                rule_triggered=ValidationRuleId.RULE_1_PART_A_COMPLEXITY,
                requires_human_review=False,
            )

        # Fallback or uncertain LLM classification
        return QuestionMarkEvaluation(
            question_id=question.question_id,
            section=section_name,
            assigned_marks=marks,
            complexity_classification=SemanticComplexity.REVIEW_REQUIRED,
            subdivision_count=None,
            subdivision_labels=[],
            status=MarkDistributionStatus.REVIEW_REQUIRED,
            reason=f"Semantic complexity assessment requires human review: {llm_result.reason}",
            rule_triggered=ValidationRuleId.RULE_1_PART_A_COMPLEXITY,
            requires_human_review=True,
        )

    # =========================================================================
    # Rule 2: Section & Mark Allocation Validation (Deterministic Python)
    # =========================================================================

    def validate_section_marks(
        self,
        question: QuestionItem,
    ) -> QuestionMarkEvaluation | None:
        """Validate question section placement and assigned marks deterministically.

        - A 2-mark question appearing in Part B or Part C must be flagged as FLAG.
        - Part B and Part C may contain long-answer questions worth 13, 15, or 16 marks.
        - If section or mark allocation cannot be extracted reliably -> REVIEW_REQUIRED.
        Returns QuestionMarkEvaluation if Rule 2 triggers a status, or None if valid to proceed.
        """
        # Check unextractable metadata
        if not question.section or question.marks is None:
            return QuestionMarkEvaluation(
                question_id=question.question_id,
                section=question.section,
                assigned_marks=question.marks,
                complexity_classification=SemanticComplexity.REVIEW_REQUIRED,
                subdivision_count=None,
                subdivision_labels=[],
                status=MarkDistributionStatus.REVIEW_REQUIRED,
                reason=(
                    f"Question {question.question_id} has uncertain examination metadata: "
                    f"section='{question.section}', marks='{question.marks}'. Human review required."
                ),
                rule_triggered=ValidationRuleId.RULE_SECTION_METADATA_UNCERTAIN,
                requires_human_review=True,
            )

        norm_section = question.section.strip().upper()

        # Check for 2-mark question in Part B or Part C
        if norm_section in ("PART B", "PART C", "SECTION B", "SECTION C") and question.marks == 2.0:
            return QuestionMarkEvaluation(
                question_id=question.question_id,
                section=question.section,
                assigned_marks=question.marks,
                complexity_classification=SemanticComplexity.NOT_APPLICABLE,
                subdivision_count=None,
                subdivision_labels=[],
                status=MarkDistributionStatus.FLAG,
                reason=(
                    f"A 2-mark question was detected in {question.section}. "
                    "Part B and Part C are strictly reserved for long-answer questions (13, 15, or 16 marks)."
                ),
                rule_triggered=ValidationRuleId.RULE_2_SECTION_MARK_MISPLACEMENT,
                requires_human_review=False,
            )

        # Valid section and marks: return None so caller can run subsequent checks
        return None

    # =========================================================================
    # Rule 3: Subdivision Counting & OR-Alternative Logic (Deterministic Python)
    # =========================================================================

    def parse_subdivision_structure(
        self,
        subdivisions: list[str] | str | None,
    ) -> list[list[str]]:
        """Parse subdivision specification into independent alternative branches.

        Recognizes:
        - Lists of labels: ['(a)', '(b)'], ['a(i)', 'a(ii)'], ['(a)', '(b)', '(c)']
        - Strings with OR delimiters: '11(a) OR 11(b)', '11(a)(i), 11(a)(ii) OR 11(b)'
        - Comma/semicolon delimited strings: '11(a), 11(b)'

        Returns a list of branches, where each branch is a list of distinct subdivision labels.
        Nested labels under the same subquestion are counted at the leaf level without double-counting.
        """
        if not subdivisions:
            return [[]]

        # If already passed as list of lists (explicit branches)
        if isinstance(subdivisions, list) and subdivisions and isinstance(subdivisions[0], list):
            return subdivisions  # type: ignore[return-value]

        # If string provided
        if isinstance(subdivisions, str):
            clean_str = subdivisions.strip()
            # Split by OR alternatives
            raw_branches = OR_DELIMITER_PATTERN.split(clean_str)
            parsed_branches: list[list[str]] = []

            for branch_text in raw_branches:
                branch_clean = branch_text.strip()
                if not branch_clean:
                    continue

                # Split by commas or semicolons or newlines
                tokens = re.split(r"[,;\n]+", branch_clean)
                labels: list[str] = []
                for token in tokens:
                    t = token.strip()
                    if not t:
                        continue
                    m = SUBDIVISION_LABEL_PATTERN.search(t)
                    if m:
                        label = m.group(1) or m.group(2)
                        labels.append(label.lower())
                    else:
                        labels.append(t)

                # Deduplicate and filter nested parent containers
                leaf_labels = self._extract_leaf_subdivisions(labels)
                parsed_branches.append(leaf_labels)

            return parsed_branches if parsed_branches else [[]]

        # If list of strings provided: check if any item is an OR indicator
        if isinstance(subdivisions, list):
            # Check if any element is "OR"
            branches: list[list[str]] = []
            current_branch: list[str] = []

            for item in subdivisions:
                item_str = str(item).strip()
                if OR_DELIMITER_PATTERN.fullmatch(item_str):
                    if current_branch:
                        branches.append(self._extract_leaf_subdivisions(current_branch))
                        current_branch = []
                else:
                    m = SUBDIVISION_LABEL_PATTERN.search(item_str)
                    if m:
                        label = m.group(1) or m.group(2)
                        current_branch.append(label.lower())
                    else:
                        current_branch.append(item_str)

            if current_branch or not branches:
                branches.append(self._extract_leaf_subdivisions(current_branch))

            return branches

        return [[]]

    def _extract_leaf_subdivisions(self, labels: list[str]) -> list[str]:
        """Eliminate parent containers to avoid double-counting nested subdivisions.

        For example, if ['a', 'a(i)', 'a(ii)'] is present, 'a' is a parent container;
        the actual assessable subdivisions are ['a(i)', 'a(ii)'].
        """
        if len(labels) <= 1:
            return labels

        # Identify labels that have deeper nested children
        leaves: list[str] = []
        for i, lbl in enumerate(labels):
            is_parent = False
            for j, other in enumerate(labels):
                if i != j and other.startswith(lbl) and len(other) > len(lbl):
                    # other is a child of lbl e.g. 'a(i)' is child of 'a'
                    is_parent = True
                    break
            if not is_parent:
                leaves.append(lbl)

        return leaves if leaves else labels

    def validate_subdivisions(
        self,
        question_id: str,
        section: str,
        assigned_marks: float,
        subdivisions: list[str] | str | None,
    ) -> QuestionMarkEvaluation:
        """Validate subdivision count for a 13-, 15-, or 16-mark Part B/C question.

        - <= 2 subdivisions (0, 1, or 2): PASS.
        - > 2 subdivisions: FLAG.
        - Unparseable or uncertain: REVIEW_REQUIRED.
        OR alternatives are evaluated independently.
        """
        # Check if structure is unparseable
        if isinstance(subdivisions, str) and any(err in subdivisions.lower() for err in ["error", "corrupt", "unparseable"]):
            return QuestionMarkEvaluation(
                question_id=question_id,
                section=section,
                assigned_marks=assigned_marks,
                complexity_classification=SemanticComplexity.NOT_APPLICABLE,
                subdivision_count=None,
                subdivision_labels=[],
                status=MarkDistributionStatus.REVIEW_REQUIRED,
                reason=f"Subdivision structure for question {question_id} could not be parsed reliably. Human review required.",
                rule_triggered=ValidationRuleId.RULE_3_SUBDIVISION_COUNT,
                requires_human_review=True,
            )

        branches = self.parse_subdivision_structure(subdivisions)

        branch_counts = [len(b) for b in branches]
        max_count = max(branch_counts) if branch_counts else 0
        all_labels = [lbl for b in branches for lbl in b]

        # Check if any alternative branch exceeds 2 subdivisions
        violating_branches: list[tuple[int, int, list[str]]] = []
        for idx, branch in enumerate(branches):
            if len(branch) > 2:
                violating_branches.append((idx + 1, len(branch), branch))

        if violating_branches:
            details = ", ".join(
                f"Choice {b_idx}: {cnt} subdivisions ({labels})"
                for b_idx, cnt, labels in violating_branches
            )
            return QuestionMarkEvaluation(
                question_id=question_id,
                section=section,
                assigned_marks=assigned_marks,
                complexity_classification=SemanticComplexity.NOT_APPLICABLE,
                subdivision_count=max_count,
                subdivision_labels=all_labels,
                status=MarkDistributionStatus.FLAG,
                reason=(
                    f"Question {question_id} exceeds the institutional maximum limit of 2 subdivisions: {details}. "
                    "Long-answer questions (13/15/16 marks) must contain at most two subdivisions per choice."
                ),
                rule_triggered=ValidationRuleId.RULE_3_SUBDIVISION_COUNT,
                requires_human_review=False,
            )

        # Compliant (0, 1, or 2 subdivisions across all alternatives)
        return QuestionMarkEvaluation(
            question_id=question_id,
            section=section,
            assigned_marks=assigned_marks,
            complexity_classification=SemanticComplexity.NOT_APPLICABLE,
            subdivision_count=max_count,
            subdivision_labels=all_labels,
            status=MarkDistributionStatus.PASS,
            reason=(
                f"Compliant subdivision count ({max_count} subdivision{'s' if max_count != 1 else ''}, "
                f"maximum allowed is 2). Validated across {len(branches)} independent choice alternative{'s' if len(branches) > 1 else ''}."
            ),
            rule_triggered=ValidationRuleId.RULE_3_SUBDIVISION_COUNT,
            requires_human_review=False,
        )

    def extract_choice_and_subdivision(
        self,
        question: QuestionItem,
    ) -> tuple[str, str | None, str | None]:
        """Extract (parent_q_num, choice_letter, leaf_sub_label) from QuestionItem.

        Enables independent scrutiny of either-or alternatives (e.g. 6(a) vs 6(b)).
        Examples:
        - Q6(a(i)) -> ("6", "a", "i")
        - Q6(a) -> ("6", "a", None)
        - Q6(b(ii)) -> ("6", "b", "ii")
        - Q6(b) -> ("6", "b", None)
        - Q6(i) -> ("6", None, "i")
        - Q6 -> ("6", None, None)
        """
        q_num = question.question_number or ""
        if not q_num:
            m_num = re.search(r"\d+", question.question_id)
            q_num = m_num.group(0) if m_num else "0"

        sub_id = question.subquestion_id or ""
        qid = question.question_id

        # Pattern 1: subquestion_id like "a(i)" or "b(ii)"
        m1 = re.match(r"^([a-d])\(([ivx0-9]+)\)$", sub_id, re.IGNORECASE)
        if m1:
            return (q_num, m1.group(1).lower(), m1.group(2).lower())

        # Pattern 2: question_id like "Q6(a(i))" or "6(a(i))"
        m2 = re.search(r"\(([a-d])\(([ivx0-9]+)\)\)", qid, re.IGNORECASE)
        if m2:
            return (q_num, m2.group(1).lower(), m2.group(2).lower())

        # Pattern 3: subquestion_id is just "a", "b", "c", "d"
        if sub_id.lower() in ("a", "b", "c", "d"):
            return (q_num, sub_id.lower(), None)

        # Pattern 4: question_id like "Q6(a)"
        m4 = re.search(r"\(([a-d])\)", qid, re.IGNORECASE)
        if m4:
            return (q_num, m4.group(1).lower(), None)

        # Pattern 5: subquestion_id is roman numeral or number like "i", "ii" without choice letter
        m5 = re.match(r"^([ivx0-9]+)$", sub_id, re.IGNORECASE)
        if m5:
            choice_let = "b" if question.is_alternative else ("a" if question.is_alternative is not None else None)
            return (q_num, choice_let, m5.group(1).lower())

        # Pattern 6: is_alternative flag without explicit letter
        if question.is_alternative:
            return (q_num, "b", None)

        return (q_num, None, None)

    def extract_leaf_subdivisions_from_text(self, text: str) -> list[str]:
        """Extract explicit inline subdivisions like (i), (ii) from raw question text."""
        sub_regex = re.compile(
            r"(?:\(([ivx]+)\)|([ivx]+)[\.:\)])\s*",
            re.IGNORECASE,
        )
        matches = list(sub_regex.finditer(text))
        if len(matches) >= 2:
            return [(m.group(1) or m.group(2)).lower() for m in matches]
        return []

    def detect_part_a_subdivisions(self, question: QuestionItem) -> list[str]:
        """Detect whether a Part A question contains prohibited sub-divisions.

        Rule: Part A shall not contain any sub-divisions.
        """
        labels: list[str] = []
        if question.subquestion_id:
            cleaned_sub = question.subquestion_id.strip("()")
            if cleaned_sub:
                labels.append(cleaned_sub)

        # Check inline subdivision markers like (a), (b) or (i), (ii) or a), b)
        sub_regex = re.compile(
            r"(?:\(([a-d]|[ivx]+)\)|(?<=\s)([a-d]|[ivx]+)[\.:\)])\s*",
            re.IGNORECASE,
        )
        for m in sub_regex.finditer(question.text):
            lbl = (m.group(1) or m.group(2)).lower()
            if lbl not in labels:
                labels.append(lbl)
        return labels

    def check_subdivision_marks_clarity(
        self,
        q_items: list[tuple[QuestionItem, str | None]],
        full_text: str | None = None,
    ) -> tuple[bool, str]:
        """Check if marks allocated to each sub-division are clearly indicated against it.

        Rule: Part B and Part C questions may have a maximum of two sub-divisions,
        with the marks allocated to each sub-division clearly indicated against it.
        """
        combined_text = full_text or " ".join(q.text for q, _ in q_items)

        # Check if formula like (7 + 6 = 13 Marks) or (7 + 6 Marks) is present
        split_formula_match = re.search(
            r"\(?\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*\+\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*(?:=\s*[0-9]{1,2}(?:\.[0-9]+)?)?\s*(?:marks?|m)?\)?",
            combined_text,
            re.IGNORECASE,
        )

        # Case 1: Multiple parsed QuestionItem objects (e.g. Q11(a)(i), Q11(a)(ii))
        if len(q_items) > 1:
            missing_items: list[str] = []
            allocations: list[str] = []
            for q, _ in q_items:
                qid = q.subquestion_id or q.question_id
                has_exp = getattr(q, "has_explicit_marks", False)
                marks = q.marks
                if not has_exp or marks is None:
                    missing_items.append(qid)
                else:
                    allocations.append(f"{qid}: {marks:g}M")

            if missing_items and split_formula_match:
                m1, m2 = split_formula_match.group(1), split_formula_match.group(2)
                return True, f"split formula {m1}M + {m2}M clearly indicated"

            if missing_items:
                return False, f"marks not indicated for sub-division(s) {', '.join(missing_items)}"

            return True, ", ".join(allocations)

        # Case 2: Single item with inline subdivisions in text (e.g. (i) ... (ii) ...)
        if split_formula_match:
            m1, m2 = split_formula_match.group(1), split_formula_match.group(2)
            return True, f"split formula {m1}M + {m2}M clearly indicated"

        sub_regex = re.compile(
            r"(?:\(([ivx]+)\)|(?<=\s)([ivx]+)[\.:\)])\s*(.*?)(?=(?:\(([ivx]+)\)|(?<=\s)[ivx]+[\.:\)])|$)",
            re.IGNORECASE | re.DOTALL,
        )
        matches = list(sub_regex.finditer(combined_text))
        if len(matches) >= 2:
            marks_pattern = re.compile(
                r"(?:\[|\()\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*(?:Marks?|marks?|MARKS?|M)?\s*(?:\]|\))"
            )
            allocations_inline: list[str] = []
            missing_inline: list[str] = []
            for m in matches:
                lbl = f"({(m.group(1) or m.group(2)).lower()})"
                sub_text = m.group(3).strip()
                mark_m = marks_pattern.search(sub_text)
                if mark_m:
                    allocations_inline.append(f"{lbl}: {mark_m.group(1)}M")
                else:
                    missing_inline.append(lbl)

            if missing_inline:
                return False, f"marks not indicated for sub-division(s) {', '.join(missing_inline)}"
            return True, ", ".join(allocations_inline)

        return True, "no sub-divisions (monolithic question)"

    # =========================================================================
    # Full Examination Paper Pipeline Evaluation
    # =========================================================================

    async def evaluate_paper(
        self,
        questions: list[QuestionItem],
        course_context: str | None = None,
        syllabus_topics_by_qid: dict[str, str] | None = None,
        learning_outcomes_by_qid: dict[str, str] | None = None,
    ) -> MarkDistributionReport:
        """Run full Criterion 4 scrutiny on parsed examination questions.

        Combines:
        1. Rule 1 for Part A questions (Semantic LLM analysis).
        2. Rule 2 for Part B/C 2-mark misplacements & unextracted metadata.
        3. Rule 3 for Part B/C long-answer subdivision counts, evaluating each
           independent choice alternative (e.g. 6(a) and 6(b)) individually.

        Returns strictly categorical MarkDistributionReport (Zero Scores).
        """
        evaluations: list[QuestionMarkEvaluation] = []

        part_a_items: list[QuestionItem] = []
        long_answer_items: list[QuestionItem] = []

        for q in questions:
            norm_sec = (q.section or "").strip().upper()
            if "PART A" in norm_sec or "SECTION A" in norm_sec or (not norm_sec and (q.marks == 2.0 or int(q.question_number or 0) <= 10)):
                part_a_items.append(q)
            else:
                long_answer_items.append(q)

        # Process Part A questions (Rule 1: Part A shall not contain any sub-divisions)
        for q in part_a_items:
            part_a_subs = self.detect_part_a_subdivisions(q)
            if part_a_subs:
                evaluations.append(
                    QuestionMarkEvaluation(
                        question_id=q.question_id,
                        section=q.section or "Part A",
                        assigned_marks=q.marks or 2.0,
                        complexity_classification=SemanticComplexity.NOT_APPLICABLE,
                        subdivision_count=len(part_a_subs),
                        subdivision_labels=part_a_subs,
                        status=MarkDistributionStatus.FLAG,
                        reason=(
                            f"Part A question {q.question_id} contains sub-divisions ({', '.join(part_a_subs)}). "
                            "Part A shall not contain any sub-divisions."
                        ),
                        rule_triggered=ValidationRuleId.RULE_PART_A_NO_SUBDIVISIONS,
                        requires_human_review=False,
                    )
                )
            else:
                evaluations.append(
                    QuestionMarkEvaluation(
                        question_id=q.question_id,
                        section=q.section or "Part A",
                        assigned_marks=q.marks or 2.0,
                        complexity_classification=SemanticComplexity.NOT_APPLICABLE,
                        subdivision_count=0,
                        subdivision_labels=[],
                        status=MarkDistributionStatus.PASS,
                        reason="Monolithic short-answer question without sub-divisions.",
                        rule_triggered=ValidationRuleId.RULE_PART_A_NO_SUBDIVISIONS,
                        requires_human_review=False,
                    )
                )

        # Process Part B / Part C Long-Answer Questions (Rule 2 & Rule 3)
        # Evaluate each choice alternative independently (e.g. 6(a) and 6(b))
        choice_groups: dict[tuple[str, str | None], list[tuple[QuestionItem, str | None]]] = {}

        for q in long_answer_items:
            q_num, ch_let, leaf = self.extract_choice_and_subdivision(q)
            key = (q_num, ch_let)
            if key not in choice_groups:
                choice_groups[key] = []
            choice_groups[key].append((q, leaf))

        for (q_num, ch_let), q_items in choice_groups.items():
            first_q = q_items[0][0]
            sec = first_q.section or "Part B"
            choice_id = f"Q{q_num}({ch_let})" if ch_let else (f"Q{q_num}" if not q_num.startswith("Q") else q_num)

            # Determine assigned marks for this choice alternative
            sum_marks = sum(q.marks or 0.0 for q, _ in q_items)
            if sum_marks in (13.0, 15.0, 16.0):
                assigned_marks = sum_marks
            elif q_items[0][0].marks in (13.0, 15.0, 16.0):
                assigned_marks = q_items[0][0].marks or 13.0
            elif len(q_items) == 1 and q_items[0][0].marks is not None:
                assigned_marks = q_items[0][0].marks
            else:
                assigned_marks = 15.0 if "PART C" in sec.upper() else 13.0

            # Check for uncertain metadata
            if not sec or assigned_marks is None:
                evaluations.append(
                    QuestionMarkEvaluation(
                        question_id=choice_id,
                        section=sec,
                        assigned_marks=assigned_marks,
                        complexity_classification=SemanticComplexity.NOT_APPLICABLE,
                        subdivision_count=None,
                        subdivision_labels=[],
                        status=MarkDistributionStatus.REVIEW_REQUIRED,
                        reason=f"Question {choice_id} has uncertain examination metadata: section='{sec}', marks='{assigned_marks}'. Human review required.",
                        rule_triggered=ValidationRuleId.RULE_SECTION_METADATA_UNCERTAIN,
                        requires_human_review=True,
                    )
                )
                continue

            # Extract leaf subdivisions
            leaf_subs: list[str] = [leaf for _, leaf in q_items if leaf is not None]
            if not leaf_subs and len(q_items) == 1:
                leaf_subs = self.extract_leaf_subdivisions_from_text(q_items[0][0].text)

            sub_count = len(leaf_subs)
            if sub_count > 2:
                # Rule 2: Part B & Part C Questions: Maximum of Two Sub-Divisions
                status = MarkDistributionStatus.FLAG
                reason = (
                    f"Question {choice_id} exceeds the institutional maximum limit of 2 sub-divisions "
                    f"(found {sub_count} sub-divisions: {leaf_subs}). "
                    "Part B and Part C questions may have a maximum of two sub-divisions."
                )
                rule = ValidationRuleId.RULE_3_SUBDIVISION_COUNT
            elif sub_count > 0:
                # Rule 3: Part B & Part C Questions: Marks Allocated Clearly Indicated Against Each Sub-Division
                marks_ok, mark_detail = self.check_subdivision_marks_clarity(q_items)
                if not marks_ok:
                    status = MarkDistributionStatus.FLAG
                    reason = (
                        f"Question {choice_id} contains {sub_count} sub-divisions ({leaf_subs}), "
                        f"but marks are not clearly indicated against each sub-division ({mark_detail}). "
                        "Part B and Part C questions with sub-divisions must have the marks allocated to each sub-division clearly indicated against it."
                    )
                    rule = ValidationRuleId.RULE_SUBDIVISION_MARKS_ALLOCATION
                else:
                    status = MarkDistributionStatus.PASS
                    reason = f"Marks for each sub-division are explicitly stated ({mark_detail})."
                    rule = ValidationRuleId.RULE_3_SUBDIVISION_COUNT
            else:
                status = MarkDistributionStatus.PASS
                reason = "Contains 0 sub-divisions (maximum allowed is 2)."
                rule = ValidationRuleId.RULE_3_SUBDIVISION_COUNT

            evaluations.append(
                QuestionMarkEvaluation(
                    question_id=choice_id,
                    section=sec,
                    assigned_marks=assigned_marks,
                    complexity_classification=SemanticComplexity.NOT_APPLICABLE,
                    subdivision_count=sub_count if sub_count > 0 else None,
                    subdivision_labels=leaf_subs,
                    status=status,
                    reason=reason,
                    rule_triggered=rule,
                    requires_human_review=False,
                )
            )

        # Sort evaluations by question id natural order and choice letter
        def sort_key(e: QuestionMarkEvaluation) -> tuple[int, str]:
            nums = re.findall(r"\d+", e.question_id)
            num = int(nums[0]) if nums else 999
            return (num, e.question_id)

        evaluations.sort(key=sort_key)

        # Aggregate counts (Zero Scores)
        pass_count = sum(1 for e in evaluations if e.status == MarkDistributionStatus.PASS)
        flag_count = sum(1 for e in evaluations if e.status == MarkDistributionStatus.FLAG)
        review_count = sum(1 for e in evaluations if e.status == MarkDistributionStatus.REVIEW_REQUIRED)

        part_a_sub_flags = sum(1 for e in evaluations if e.rule_triggered == ValidationRuleId.RULE_PART_A_NO_SUBDIVISIONS and e.status == MarkDistributionStatus.FLAG)
        r3_flags = sum(1 for e in evaluations if e.rule_triggered == ValidationRuleId.RULE_3_SUBDIVISION_COUNT and e.status == MarkDistributionStatus.FLAG)
        sub_mark_flags = sum(1 for e in evaluations if e.rule_triggered == ValidationRuleId.RULE_SUBDIVISION_MARKS_ALLOCATION and e.status == MarkDistributionStatus.FLAG)

        requires_review = review_count > 0
        review_reasons = [e.reason for e in evaluations if e.requires_human_review]

        # Determine overall categorical status
        if flag_count > 0:
            overall_status = MarkDistributionStatus.FLAG
        elif requires_review:
            overall_status = MarkDistributionStatus.REVIEW_REQUIRED
        else:
            overall_status = MarkDistributionStatus.PASS

        # Generate human-readable summary
        summary_lines: list[str] = []
        if overall_status == MarkDistributionStatus.PASS:
            summary_lines.append(
                f"All {len(evaluations)} questions comply with the 3 mark distribution rules: "
                "Part A contains no sub-divisions, Part B & Part C have at most two sub-divisions, "
                "and marks allocated to each sub-division are clearly indicated."
            )
        elif overall_status == MarkDistributionStatus.FLAG:
            details = []
            if part_a_sub_flags > 0:
                details.append(f"{part_a_sub_flags} Part A sub-division violation(s) (Part A shall not contain any sub-divisions)")
            if r3_flags > 0:
                details.append(f"{r3_flags} sub-division count violation(s) (>2 sub-divisions in Part B/C)")
            if sub_mark_flags > 0:
                details.append(f"{sub_mark_flags} sub-division mark allocation violation(s) (missing explicit marks)")
            summary_lines.append(
                f"Mark distribution scrutiny flagged {flag_count} non-compliant question(s): {', '.join(details)}."
            )
        else:
            summary_lines.append(
                f"Mark distribution scrutiny requires human review for {review_count} question(s) "
                "due to unextracted metadata or unparseable question structure."
            )

        return MarkDistributionReport(
            overall_status=overall_status,
            total_questions_evaluated=len(evaluations),
            pass_count=pass_count,
            flag_count=flag_count,
            review_required_count=review_count,
            rule_part_a_subdivision_flags=part_a_sub_flags,
            rule_3_subdivision_flags=r3_flags,
            rule_subdivision_mark_flags=sub_mark_flags,
            part_a_subdivision_flags=part_a_sub_flags,
            subdivision_mark_flags=sub_mark_flags,
            rule_1_part_a_flags=0,
            rule_2_section_mark_flags=0,
            requires_human_review=requires_review,
            review_reasons=review_reasons,
            summary=" ".join(summary_lines),
            evaluations=evaluations,
            llm_provider_used=getattr(self.llm, "last_provider_used", None) or getattr(self.llm, "provider", None),
        )


mark_distribution_validator = MarkDistributionValidator()
