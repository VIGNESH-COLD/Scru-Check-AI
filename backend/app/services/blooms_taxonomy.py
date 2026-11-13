"""Institutional Question Paper Scrutiny Service for Criterion 5: Bloom's Taxonomy.

Enforces:
1. Declared BT level (A1/A2/B1/B2/C1/C2) must be mentioned against each question and verified
   against evaluated cognitive level.
2. The same knowledge level shall be maintained in both 'either' and 'or' options, even when
   sub-divisions are present.
3. Open-ended Wh-type questions (What, When, Where, Who, Why, Which) must be avoided as far as possible.
4. The UG level question paper shall include questions spanning all levels of BT, distributed as follows:
   - Category A (A1/A2) — Remember / Understand (Base Level): 50%
   - Category B (B1/B2) — Apply / Analyze (Medium Level): 30 – 35%
   - Category C (C1/C2) — Evaluate / Create (Highest Level): Remaining percentage (15 – 20%)
Generates data slices and pie chart records for visualization.
Strict Zero-Score policy: purely categorical statuses (PASS, FLAG, REVIEW_REQUIRED).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.schemas.blooms_taxonomy import (
    BloomsTaxonomyReport,
    BTCategory,
    BTDistributionSlice,
    BTLevel,
    ChoicePairBTParityItem,
    QuestionBTScrutinyItem,
    ScrutinyStatus,
)
from app.schemas.question_mapping import QuestionItem

logger = logging.getLogger("scrucheck.blooms_taxonomy")


class BloomsTaxonomyValidator:
    """Validator implementing institutional Bloom's Taxonomy scrutiny rules."""

    # College Bloom's Taxonomy definitions and action verbs table
    TAXONOMY_DEFINITIONS: dict[str, dict[str, Any]] = {
        BTLevel.A1: {
            "name": "Remembering",
            "category": BTCategory.CATEGORY_A,
            "category_tier": "Base Level",
            "definition": (
                "Exhibit Memory of previously learned material by recalling facts, "
                "terms, basic concepts and answers."
            ),
            "verbs": [
                "choose", "define", "find", "flow", "label", "list", "match",
                "name", "omit", "recall", "relate", "select", "show", "spell",
                "tell", "what", "when", "where", "which", "who", "why",
                # Common institutional question paper synonyms
                "state", "mention", "give", "write",
            ],
        },
        BTLevel.A2: {
            "name": "Understanding",
            "category": BTCategory.CATEGORY_A,
            "category_tier": "Base Level",
            "definition": (
                "Demonstrate understanding of facts and ideas by organizing, comparing, "
                "translating, interpreting, giving descriptions and stating main ideas."
            ),
            "verbs": [
                "classify", "compare", "contrast", "demonstrate", "explain",
                "extend", "illustrate", "infer", "interpret", "outline", "relate",
                "rephrase", "show", "summarize", "translate",
                # Common institutional question paper synonyms
                "describe", "discuss", "clarify", "express",
            ],
        },
        BTLevel.B1: {
            "name": "Applying",
            "category": BTCategory.CATEGORY_B,
            "category_tier": "Medium Level",
            "definition": (
                "Solve problems to new situations by applying acquired knowledge "
                "facts, techniques and rules in a different way."
            ),
            "verbs": [
                "apply", "build", "choose", "construct", "develop", "experiment",
                "identify", "interview", "make use of", "model", "organize",
                "plan", "select", "solve", "utilize",
                # Common institutional question paper synonyms
                "calculate", "compute", "implement", "determine", "trace",
            ],
        },
        BTLevel.B2: {
            "name": "Analyzing",
            "category": BTCategory.CATEGORY_B,
            "category_tier": "Medium Level",
            "definition": (
                "Examine and break information into parts by identifying motives or causes. "
                "Make inference and find evidence to support generalizations."
            ),
            "verbs": [
                "analyze", "assume", "categorize", "classify", "compare", "conclusion",
                "contrast", "discover", "dissect", "distinguish", "divide", "examine",
                "function", "inference", "inspect", "list", "motive", "relationships",
                "simplify", "survey", "take part in", "test for", "theme",
                # Common institutional question paper synonyms
                "differentiate", "discriminate", "break down",
            ],
        },
        BTLevel.C1: {
            "name": "Evaluating",
            "category": BTCategory.CATEGORY_C,
            "category_tier": "Highest Level",
            "definition": (
                "Present and defend opinions by making judgments about information, "
                "validity of ideas or quality of work based on a set of criteria."
            ),
            "verbs": [
                "agree", "appraise", "assess", "award", "choose", "compare",
                "conclude", "criteria", "criticize", "decide", "deduct", "defend",
                "determine", "disprove", "estimate", "evaluate", "explain",
                "importance", "influence", "interpret", "judge", "justify",
                "mark", "measure", "opinion", "perceive", "prioritize", "prove",
                "rate", "recommend", "rule on", "select", "support", "value",
                # Common institutional question paper synonyms
                "critique", "validate",
            ],
        },
        BTLevel.C2: {
            "name": "Creating",
            "category": BTCategory.CATEGORY_C,
            "category_tier": "Highest Level",
            "definition": (
                "Compile information together in a different way by combining elements in a "
                "new pattern or proposing alternative solutions."
            ),
            "verbs": [
                "adapt", "build", "change", "choose", "combine", "compile",
                "compose", "construct", "create", "delete", "design", "develop",
                "discuss", "elaborate", "estimate", "formulate", "happen",
                "imagine", "improve", "invent", "make up", "maximize",
                "minimize", "modify", "original", "originate", "plan",
                "predict", "propose", "solution", "solve", "suppose", "test",
                "theory",
                # Common institutional question paper synonyms
                "synthesize", "devise", "generate",
            ],
        },
    }

    # Open-ended Wh-words to avoid
    WH_WORDS_PATTERN = re.compile(
        r"\b(what|when|where|who|why|which)\b",
        re.IGNORECASE,
    )

    # Multi-word action verbs that should take precedence in matching
    MULTI_WORD_VERBS: list[tuple[str, str]] = [
        ("make use of", BTLevel.B1),
        ("take part in", BTLevel.B2),
        ("test for", BTLevel.B2),
        ("break down", BTLevel.B2),
        ("make up", BTLevel.C2),
        ("rule on", BTLevel.C1),
    ]

    def __init__(self) -> None:
        # Pre-index single-word action verbs to their primary BT levels
        self._verb_to_levels: dict[str, list[str]] = {}
        for level, data in self.TAXONOMY_DEFINITIONS.items():
            for v in data["verbs"]:
                v_lower = v.lower()
                if v_lower not in self._verb_to_levels:
                    self._verb_to_levels[v_lower] = []
                self._verb_to_levels[v_lower].append(level)

    def detect_wh_question(self, text: str) -> tuple[bool, str | None]:
        """Check if question contains open-ended Wh-type phrasing (What, When, Where, Who, Why, Which)."""
        m = self.WH_WORDS_PATTERN.search(text)
        if m:
            return True, m.group(1).capitalize()
        return False, None

    def evaluate_cognitive_level(self, text: str) -> tuple[str, str, str | None]:
        """Evaluate the Bloom's Taxonomy cognitive level (A1-C2) from question statement text.

        Returns (bt_level, category, matched_action_verb).
        """
        clean_text = text.strip()
        lower_text = clean_text.lower()

        # 1. Check multi-word action verbs first
        for phrase, level in self.MULTI_WORD_VERBS:
            if re.search(r"\b" + re.escape(phrase) + r"\b", lower_text):
                cat = self.TAXONOMY_DEFINITIONS[level]["category"]
                return level, cat, phrase

        # 2. Extract leading operative word(s) (first 1 to 3 words)
        words = re.findall(r"\b[a-zA-Z-]+\b", lower_text)
        first_word = words[0] if words else ""

        # Special contextual disambiguations for overlapping verbs:
        # - 'explain': usually A2 (understanding), but C1 if assessing criteria/judgment
        if first_word == "explain":
            if any(term in lower_text for term in ["justify", "evaluate", "assess", "criteria", "trade-off", "trade off", "opinion"]):
                return BTLevel.C1, BTCategory.CATEGORY_C, "explain"
            return BTLevel.A2, BTCategory.CATEGORY_A, "explain"

        # - 'solve': usually B1 (applying), but C2 if designing/proposing new solution
        if first_word == "solve":
            if any(term in lower_text for term in ["propose", "devise", "formulate", "new architecture", "design"]):
                return BTLevel.C2, BTCategory.CATEGORY_C, "solve"
            return BTLevel.B1, BTCategory.CATEGORY_B, "solve"

        # - 'compare' or 'contrast': usually B2 (analyzing parts/trade-offs), A2 for basic similarities
        if first_word in ("compare", "contrast"):
            if any(term in lower_text for term in ["trade-off", "trade off", "complexity", "advantages and disadvantages", "difference", "distinguish"]):
                return BTLevel.B2, BTCategory.CATEGORY_B, first_word
            return BTLevel.A2, BTCategory.CATEGORY_A, first_word

        # - 'list': A1 if recall/facts; B2 if breaking into subparts
        if first_word == "list":
            if any(term in lower_text for term in ["breakdown", "motives", "relationships"]):
                return BTLevel.B2, BTCategory.CATEGORY_B, "list"
            return BTLevel.A1, BTCategory.CATEGORY_A, "list"

        # - 'develop', 'build', 'construct': B1 (standard algorithmic implementation) vs C2 (creative synthesis)
        if first_word in ("develop", "build", "construct"):
            if any(term in lower_text for term in ["new", "novel", "original", "design", "invent"]):
                return BTLevel.C2, BTCategory.CATEGORY_C, first_word
            return BTLevel.B1, BTCategory.CATEGORY_B, first_word

        # 3. Check if first word is in verb dictionary
        if first_word in self._verb_to_levels:
            matched_level = self._verb_to_levels[first_word][0]
            cat = self.TAXONOMY_DEFINITIONS[matched_level]["category"]
            return matched_level, cat, first_word

        # 4. Search for any college action verb present in the question text
        # Give higher priority to higher-order verbs if present (C2 -> C1 -> B2 -> B1 -> A2 -> A1)
        priority_levels = [
            BTLevel.C2, BTLevel.C1, BTLevel.B2, BTLevel.B1, BTLevel.A2, BTLevel.A1,
        ]
        for level in priority_levels:
            verbs = self.TAXONOMY_DEFINITIONS[level]["verbs"]
            for v in verbs:
                if re.search(r"\b" + re.escape(v) + r"\b", lower_text):
                    # Avoid false match on generic conjunctions/prepositions
                    if v in ("flow", "show", "tell", "what", "when", "where", "which", "who", "why") and level == BTLevel.A1:
                        continue
                    cat = self.TAXONOMY_DEFINITIONS[level]["category"]
                    return level, cat, v

        # 5. Check if Wh-words triggered A1
        has_wh, wh_word = self.detect_wh_question(clean_text)
        if has_wh and wh_word:
            return BTLevel.A1, BTCategory.CATEGORY_A, wh_word.lower()

        # 6. Default to A1 for short definitions/recalls or A2 for general descriptions
        if len(words) < 10:
            return BTLevel.A1, BTCategory.CATEGORY_A, "recall"
        return BTLevel.A2, BTCategory.CATEGORY_A, "describe"

    def check_question_scrutiny(self, question: QuestionItem) -> QuestionBTScrutinyItem:
        """Perform comprehensive Bloom's Taxonomy scrutiny on a single question."""
        eval_level, eval_cat, matched_verb = self.evaluate_cognitive_level(question.text)
        level_info = self.TAXONOMY_DEFINITIONS[eval_level]
        level_name = level_info["name"]

        has_wh, wh_word = self.detect_wh_question(question.text)
        wh_status = ScrutinyStatus.FLAG if has_wh else ScrutinyStatus.PASS

        reasons: list[str] = []

        # Rule 1: Declared BT Level Mentioned & Verified
        declared_bt = question.declared_bt.upper() if question.declared_bt else None
        if not declared_bt:
            bt_mentioned_status = ScrutinyStatus.FLAG
            bt_match_status = ScrutinyStatus.REVIEW_REQUIRED
            reasons.append(
                f"Question {question.question_id} does not have a declared Bloom's Taxonomy level "
                f"(A1/A2/B1/B2/C1/C2). The BT level should be mentioned against each question."
            )
        else:
            bt_mentioned_status = ScrutinyStatus.PASS
            if declared_bt == eval_level:
                bt_match_status = ScrutinyStatus.PASS
            else:
                bt_match_status = ScrutinyStatus.FLAG
                decl_info = self.TAXONOMY_DEFINITIONS.get(declared_bt, {})
                decl_name = decl_info.get("name", "Unknown")
                verb_clause = f" based on action verb '{matched_verb}'" if matched_verb else ""
                reasons.append(
                    f"Declared BT level ({declared_bt} — {decl_name}) does not match evaluated cognitive "
                    f"level ({eval_level} — {level_name}){verb_clause}."
                )

        # Rule 3: Avoid Open-Ended Wh-Questions
        if has_wh and wh_word:
            reasons.append(
                f"Question {question.question_id} contains open-ended Wh-type phrasing ('{wh_word}...'). "
                f"Kindly avoid open-ended Wh-type questions (What, When, Where, Who, Why, Which) as far as "
                f"possible; use specific Bloom's action verbs."
            )

        # Overall Status for this question
        if bt_mentioned_status == ScrutinyStatus.FLAG or bt_match_status == ScrutinyStatus.FLAG or wh_status == ScrutinyStatus.FLAG:
            overall_status = ScrutinyStatus.FLAG
        else:
            overall_status = ScrutinyStatus.PASS

        return QuestionBTScrutinyItem(
            question_id=question.question_id,
            question_number=question.question_number,
            subquestion_id=question.subquestion_id,
            section=question.section or "Part A",
            marks=question.marks or 2.0,
            text=question.text,
            declared_bt=declared_bt,
            evaluated_bt=eval_level,
            evaluated_category=eval_cat,
            bt_level_name=level_name,
            matched_action_verb=matched_verb,
            bt_mentioned_status=bt_mentioned_status,
            bt_match_status=bt_match_status,
            has_wh_question=has_wh,
            wh_question_status=wh_status,
            wh_word_found=wh_word,
            overall_status=overall_status,
            reasons=reasons,
        )

    def check_or_choice_knowledge_parity(
        self,
        questions: list[QuestionItem],
        question_evaluations: dict[str, QuestionBTScrutinyItem],
    ) -> list[ChoicePairBTParityItem]:
        """Verify that the same knowledge level is maintained across 'either' and 'or' choices."""
        # Group questions by choice group (e.g. Q11, Q12, etc.)
        groups: dict[str, list[QuestionItem]] = {}
        for q in questions:
            if not q.choice_group:
                continue
            grp = q.choice_group
            if grp not in groups:
                groups[grp] = []
            groups[grp].append(q)

        parity_items: list[ChoicePairBTParityItem] = []

        for grp_id, q_list in sorted(groups.items()):
            # Divide into Option A branch vs Option B branch
            option_a_items: list[QuestionItem] = []
            option_b_items: list[QuestionItem] = []

            for q in q_list:
                sub = (q.subquestion_id or "").lower()
                if q.is_alternative or "b" in sub or "c" in sub:
                    option_b_items.append(q)
                else:
                    option_a_items.append(q)

            if not option_a_items or not option_b_items:
                continue

            # Determine dominant BT level & category for Option A
            eval_a_items = [question_evaluations[q.question_id] for q in option_a_items if q.question_id in question_evaluations]
            eval_b_items = [question_evaluations[q.question_id] for q in option_b_items if q.question_id in question_evaluations]

            if not eval_a_items or not eval_b_items:
                continue

            # In sub-divided questions, take max cognitive level
            opt_a_bt = max((item.evaluated_bt for item in eval_a_items), key=lambda x: str(x))
            opt_b_bt = max((item.evaluated_bt for item in eval_b_items), key=lambda x: str(x))

            opt_a_cat = self.TAXONOMY_DEFINITIONS[opt_a_bt]["category"]
            opt_b_cat = self.TAXONOMY_DEFINITIONS[opt_b_bt]["category"]

            opt_a_name = self.TAXONOMY_DEFINITIONS[opt_a_bt]["name"]
            opt_b_name = self.TAXONOMY_DEFINITIONS[opt_b_bt]["name"]

            opt_a_id = option_a_items[0].question_id
            opt_b_id = option_b_items[0].question_id

            section = option_a_items[0].section or "Part B"
            is_exact = (opt_a_bt == opt_b_bt)
            is_category = (opt_a_cat == opt_b_cat)

            if is_exact:
                status = ScrutinyStatus.PASS
                reason = (
                    f"Same knowledge level maintained across 'either' and 'or' choices: "
                    f"{opt_a_id} ({opt_a_bt} — {opt_a_name}) and {opt_b_id} ({opt_b_bt} — {opt_b_name})."
                )
            elif is_category:
                status = ScrutinyStatus.FLAG
                reason = (
                    f"Knowledge level disparity within {opt_a_cat}: {opt_a_id} is {opt_a_bt} ({opt_a_name}) "
                    f"while {opt_b_id} is {opt_b_bt} ({opt_b_name}). The same knowledge level shall be maintained in both options."
                )
            else:
                status = ScrutinyStatus.FLAG
                reason = (
                    f"Cognitive category mismatch across 'either' and 'or' choices: {opt_a_id} is {opt_a_bt} ({opt_a_cat}) "
                    f"while {opt_b_id} is {opt_b_bt} ({opt_b_cat}). The same knowledge level shall be maintained in both options."
                )

            parity_items.append(
                ChoicePairBTParityItem(
                    choice_group=grp_id,
                    section=section,
                    option_a_id=opt_a_id,
                    option_a_bt=opt_a_bt,
                    option_a_category=opt_a_cat,
                    option_b_id=opt_b_id,
                    option_b_bt=opt_b_bt,
                    option_b_category=opt_b_cat,
                    is_exact_match=is_exact,
                    is_category_match=is_category,
                    status=status,
                    reason=reason,
                )
            )

        return parity_items

    def check_distribution_and_spanning(
        self,
        questions: list[QuestionItem],
        question_evaluations: dict[str, QuestionBTScrutinyItem],
    ) -> tuple[list[BTDistributionSlice], list[dict[str, Any]], bool, ScrutinyStatus, list[str]]:
        """Calculate Category A, B, and C mark distribution and verify institutional targets."""
        # Aggregate marks per category using effective paper weightage
        # For choice groups (e.g. Q11(a) OR Q11(b)), avoid double-counting in the 100-mark paper
        # by taking the group average weightage, or allocating per option branch.
        marks_by_cat: dict[str, float] = {
            BTCategory.CATEGORY_A: 0.0,
            BTCategory.CATEGORY_B: 0.0,
            BTCategory.CATEGORY_C: 0.0,
        }
        count_by_cat: dict[str, int] = {
            BTCategory.CATEGORY_A: 0,
            BTCategory.CATEGORY_B: 0,
            BTCategory.CATEGORY_C: 0,
        }
        levels_by_cat: dict[str, set[str]] = {
            BTCategory.CATEGORY_A: set(),
            BTCategory.CATEGORY_B: set(),
            BTCategory.CATEGORY_C: set(),
        }

        for q in questions:
            item = question_evaluations.get(q.question_id)
            if not item:
                continue
            cat = item.evaluated_category
            count_by_cat[cat] += 1
            levels_by_cat[cat].add(item.evaluated_bt)

            if q.choice_group and q.choice_group != q.question_id:
                # Choice group: e.g. Q11 with Q11(a) and Q11(b)
                # Count weightage divided by number of alternative branches (standard 0.5 per OR branch)
                marks_by_cat[cat] += (item.marks / 2.0)
            else:
                marks_by_cat[cat] += item.marks

        total_effective_marks = sum(marks_by_cat.values())
        if total_effective_marks <= 0:
            total_effective_marks = 1.0

        # Percentage calculations
        cat_a_pct = (marks_by_cat[BTCategory.CATEGORY_A] / total_effective_marks) * 100.0
        cat_b_pct = (marks_by_cat[BTCategory.CATEGORY_B] / total_effective_marks) * 100.0
        cat_c_pct = (marks_by_cat[BTCategory.CATEGORY_C] / total_effective_marks) * 100.0

        # Spanning verification: all 3 categories must be present
        spans_all = (
            count_by_cat[BTCategory.CATEGORY_A] > 0
            and count_by_cat[BTCategory.CATEGORY_B] > 0
            and count_by_cat[BTCategory.CATEGORY_C] > 0
        )

        review_triggers: list[str] = []
        if not spans_all:
            missing_cats = [
                c for c in [BTCategory.CATEGORY_A, BTCategory.CATEGORY_B, BTCategory.CATEGORY_C]
                if count_by_cat[c] == 0
            ]
            review_triggers.append(
                f"Question paper fails to span all levels of Bloom's Taxonomy. Missing: {', '.join(missing_cats)}."
            )

        # Institutional targets:
        # Category A: 50% (allow tolerance 42% - 58%)
        # Category B: 30 – 35% (allow tolerance 25% - 40%)
        # Category C: Remaining % (15 – 20%, allow tolerance 10% - 25%)
        def assess_cat(pct: float, target_min: float, target_max: float, name: str) -> tuple[ScrutinyStatus, str]:
            if target_min <= pct <= target_max:
                return ScrutinyStatus.PASS, f"Aligned with institutional target ({pct:.1f}%)."
            if pct < target_min:
                return (
                    ScrutinyStatus.FLAG,
                    f"Below target threshold: {pct:.1f}% (Expected ~{target_min:.0f}–{target_max:.0f}%).",
                )
            return (
                ScrutinyStatus.FLAG,
                f"Exceeds target threshold: {pct:.1f}% (Expected ~{target_min:.0f}–{target_max:.0f}%).",
            )

        status_a, comment_a = assess_cat(cat_a_pct, 42.0, 58.0, "Category A")
        status_b, comment_b = assess_cat(cat_b_pct, 25.0, 40.0, "Category B")
        status_c, comment_c = assess_cat(cat_c_pct, 10.0, 25.0, "Category C")

        if status_a != ScrutinyStatus.PASS or status_b != ScrutinyStatus.PASS or status_c != ScrutinyStatus.PASS:
            dist_status = ScrutinyStatus.FLAG
            if not spans_all:
                dist_status = ScrutinyStatus.FLAG
        else:
            dist_status = ScrutinyStatus.PASS

        slices = [
            BTDistributionSlice(
                category=BTCategory.CATEGORY_A,
                display_name="Category A (A1/A2) — Remember / Understand",
                description="Base Level",
                target_percentage_str="50%",
                target_min=45.0,
                target_max=55.0,
                total_marks=round(marks_by_cat[BTCategory.CATEGORY_A], 1),
                marks_percentage=round(cat_a_pct, 1),
                question_count=count_by_cat[BTCategory.CATEGORY_A],
                levels_present=sorted(list(levels_by_cat[BTCategory.CATEGORY_A])),
                status=status_a,
                comment=comment_a,
            ),
            BTDistributionSlice(
                category=BTCategory.CATEGORY_B,
                display_name="Category B (B1/B2) — Apply / Analyze",
                description="Medium Level",
                target_percentage_str="30 – 35%",
                target_min=30.0,
                target_max=35.0,
                total_marks=round(marks_by_cat[BTCategory.CATEGORY_B], 1),
                marks_percentage=round(cat_b_pct, 1),
                question_count=count_by_cat[BTCategory.CATEGORY_B],
                levels_present=sorted(list(levels_by_cat[BTCategory.CATEGORY_B])),
                status=status_b,
                comment=comment_b,
            ),
            BTDistributionSlice(
                category=BTCategory.CATEGORY_C,
                display_name="Category C (C1/C2) — Evaluate / Create",
                description="Highest Level",
                target_percentage_str="Remaining (15 – 20%)",
                target_min=15.0,
                target_max=20.0,
                total_marks=round(marks_by_cat[BTCategory.CATEGORY_C], 1),
                marks_percentage=round(cat_c_pct, 1),
                question_count=count_by_cat[BTCategory.CATEGORY_C],
                levels_present=sorted(list(levels_by_cat[BTCategory.CATEGORY_C])),
                status=status_c,
                comment=comment_c,
            ),
        ]

        pie_data = [
            {
                "name": "Category A",
                "display_name": "Category A (A1/A2)",
                "tier": "Remember / Understand (Base Level)",
                "target": "50%",
                "marks": round(marks_by_cat[BTCategory.CATEGORY_A], 1),
                "marks_percentage": round(cat_a_pct, 1),
                "question_count": count_by_cat[BTCategory.CATEGORY_A],
                "color": "#ffffff",
            },
            {
                "name": "Category B",
                "display_name": "Category B (B1/B2)",
                "tier": "Apply / Analyze (Medium Level)",
                "target": "30 – 35%",
                "marks": round(marks_by_cat[BTCategory.CATEGORY_B], 1),
                "marks_percentage": round(cat_b_pct, 1),
                "question_count": count_by_cat[BTCategory.CATEGORY_B],
                "color": "#a3a3a3",
            },
            {
                "name": "Category C",
                "display_name": "Category C (C1/C2)",
                "tier": "Evaluate / Create (Highest Level)",
                "target": "Remaining (15 – 20%)",
                "marks": round(marks_by_cat[BTCategory.CATEGORY_C], 1),
                "marks_percentage": round(cat_c_pct, 1),
                "question_count": count_by_cat[BTCategory.CATEGORY_C],
                "color": "#525252",
            },
        ]

        return slices, pie_data, spans_all, dist_status, review_triggers

    async def evaluate_paper(self, questions: list[QuestionItem]) -> BloomsTaxonomyReport:
        """Execute end-to-end institutional scrutiny for Criterion 5: Bloom's Taxonomy."""
        if not questions:
            return BloomsTaxonomyReport(
                is_compliant=False,
                overall_status=ScrutinyStatus.FLAG,
                total_questions=0,
                total_marks=0.0,
                human_review_triggers=["No examination questions provided for Bloom's Taxonomy scrutiny."],
            )

        # 1. Scrutinize individual questions
        question_evaluations: dict[str, QuestionBTScrutinyItem] = {}
        items: list[QuestionBTScrutinyItem] = []

        declared_count = 0
        missing_count = 0
        match_count = 0
        mismatch_count = 0
        wh_count = 0

        for q in questions:
            res = self.check_question_scrutiny(q)
            question_evaluations[q.question_id] = res
            items.append(res)

            if res.declared_bt:
                declared_count += 1
                if res.bt_match_status == ScrutinyStatus.PASS:
                    match_count += 1
                elif res.bt_match_status == ScrutinyStatus.FLAG:
                    mismatch_count += 1
            else:
                missing_count += 1

            if res.has_wh_question:
                wh_count += 1

        # 2. Check Choice Parity across 'either' and 'or' options
        parity_items = self.check_or_choice_knowledge_parity(questions, question_evaluations)
        or_disparity_count = sum(1 for p in parity_items if p.status == ScrutinyStatus.FLAG)

        # 3. Check Distribution and Spanning
        slices, pie_data, spans_all, dist_status, dist_triggers = self.check_distribution_and_spanning(
            questions, question_evaluations
        )

        # 4. Consolidate triggers and overall status
        review_triggers: list[str] = []
        review_triggers.extend(dist_triggers)

        if missing_count > 0:
            review_triggers.append(
                f"{missing_count} question(s) missing declared Bloom's Taxonomy level (A1/A2/B1/B2/C1/C2)."
            )
        if mismatch_count > 0:
            review_triggers.append(
                f"{mismatch_count} question(s) have declared BT level conflicting with evaluated cognitive level."
            )
        if or_disparity_count > 0:
            review_triggers.append(
                f"{or_disparity_count} 'either'/'or' option choice pair(s) have knowledge level disparity."
            )
        if wh_count > 0:
            review_triggers.append(
                f"{wh_count} question(s) contain open-ended Wh-type questions (What, When, Where, Who, Why, Which)."
            )

        # Overall compliance determination:
        # Pass if no blocking mismatch and parity compliant
        if mismatch_count > 0 or or_disparity_count > 0 or not spans_all:
            overall_status = ScrutinyStatus.FLAG
            is_compliant = False
        elif missing_count > 0 or wh_count > 0 or dist_status != ScrutinyStatus.PASS:
            overall_status = ScrutinyStatus.REVIEW_REQUIRED
            is_compliant = True
        else:
            overall_status = ScrutinyStatus.PASS
            is_compliant = True

        total_marks = sum(q.marks or 2.0 for q in questions)

        return BloomsTaxonomyReport(
            is_compliant=is_compliant,
            overall_status=overall_status,
            total_questions=len(questions),
            total_marks=total_marks,
            rule_bt_mentioned_count=declared_count,
            rule_bt_missing_count=missing_count,
            rule_bt_match_count=match_count,
            rule_bt_mismatch_count=mismatch_count,
            rule_wh_avoidance_flag_count=wh_count,
            rule_or_parity_flag_count=or_disparity_count,
            rule_distribution_status=dist_status,
            distribution_slices=slices,
            distribution_pie_data=pie_data,
            spans_all_levels=spans_all,
            questions=items,
            choice_pairs_parity=parity_items,
            human_review_triggers=review_triggers,
        )


blooms_taxonomy_validator = BloomsTaxonomyValidator()
