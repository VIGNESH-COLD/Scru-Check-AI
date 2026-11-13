"""Pydantic schemas and categorical types for Criterion 5: Bloom's Taxonomy Scrutiny.

Enforces institutional scrutiny rules:
1. Declared BT level (A1/A2/B1/B2/C1/C2) must be mentioned against each question and verified.
2. The same knowledge level shall be maintained in both 'either' and 'or' options.
3. Open-ended Wh-type questions (What, When, Where, Who, Why, Which) must be avoided as far as possible.
4. UG question papers shall span all levels of BT with distribution:
   - Category A (A1/A2) — Remember / Understand (Base Level): 50%
   - Category B (B1/B2) — Apply / Analyze (Medium Level): 30 – 35%
   - Category C (C1/C2) — Evaluate / Create (Highest Level): Remaining percentage (15 – 20%)
Strict Zero-Score policy: categorical results only (PASS, FLAG, REVIEW_REQUIRED).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.question_mapping import QuestionItem


class BTLevel(StrEnum):
    """Bloom's Taxonomy levels according to institutional definition."""

    A1 = "A1"  # Remembering
    A2 = "A2"  # Understanding
    B1 = "B1"  # Applying
    B2 = "B2"  # Analyzing
    C1 = "C1"  # Evaluating
    C2 = "C2"  # Creating


class BTCategory(StrEnum):
    """Broad cognitive categories grouping Bloom's Taxonomy levels."""

    CATEGORY_A = "Category A"  # Remember / Understand (Base Level)
    CATEGORY_B = "Category B"  # Apply / Analyze (Medium Level)
    CATEGORY_C = "Category C"  # Evaluate / Create (Highest Level)


class ScrutinyStatus(StrEnum):
    """Strict categorical scrutiny verdicts (Zero-Score policy)."""

    PASS = "PASS"
    FLAG = "FLAG"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class BTRuleId(StrEnum):
    """Identifiers for Criterion 5 scrutiny rules."""

    RULE_BT_LEVEL_MENTIONED = "RULE_BT_LEVEL_MENTIONED"
    RULE_BT_LEVEL_MATCH = "RULE_BT_LEVEL_MATCH"
    RULE_BT_LEVEL_MISMATCH = "RULE_BT_LEVEL_MISMATCH"
    RULE_OR_CHOICE_BT_PARITY = "RULE_OR_CHOICE_BT_PARITY"
    RULE_AVOID_WH_QUESTIONS = "RULE_AVOID_WH_QUESTIONS"
    RULE_BT_SPAN_ALL_LEVELS = "RULE_BT_SPAN_ALL_LEVELS"
    RULE_BT_DISTRIBUTION_TARGETS = "RULE_BT_DISTRIBUTION_TARGETS"


class QuestionBTScrutinyItem(BaseModel):
    """Detailed Bloom's Taxonomy scrutiny outcome for an individual question."""

    question_id: str = Field(..., description="Question identifier e.g. 'Q1' or 'Q11(a)'")
    question_number: str | None = Field(default=None, description="Top-level number e.g. '1', '11'")
    subquestion_id: str | None = Field(default=None, description="Subdivision label e.g. 'a', 'b'")
    section: str = Field(default="Part A", description="Section header e.g. 'Part A', 'Part B'")
    marks: float = Field(default=2.0, description="Allocated marks")
    text: str = Field(..., description="Question statement text")

    # Declared vs Evaluated BT
    declared_bt: str | None = Field(
        default=None,
        description="BT level explicitly declared in question paper text (e.g. 'A1', 'B2')",
    )
    evaluated_bt: str = Field(
        ...,
        description="BT level evaluated by system based on action verbs and definitions ('A1'-'C2')",
    )
    evaluated_category: str = Field(
        ...,
        description="Broad category: 'Category A', 'Category B', or 'Category C'",
    )
    bt_level_name: str = Field(
        ...,
        description="Descriptive level name: 'Remembering', 'Understanding', 'Applying', etc.",
    )
    matched_action_verb: str | None = Field(
        default=None,
        description="Operative action verb matched from college taxonomy table",
    )

    # Scrutiny Rule Statuses
    bt_mentioned_status: ScrutinyStatus = Field(
        default=ScrutinyStatus.FLAG,
        description="PASS if declared BT is present, FLAG if missing",
    )
    bt_match_status: ScrutinyStatus = Field(
        default=ScrutinyStatus.REVIEW_REQUIRED,
        description="PASS if declared matches evaluated, FLAG if mismatch, REVIEW_REQUIRED if undeclared",
    )
    has_wh_question: bool = Field(
        default=False,
        description="True if question uses open-ended Wh-words (What, When, Where, Who, Why, Which)",
    )
    wh_question_status: ScrutinyStatus = Field(
        default=ScrutinyStatus.PASS,
        description="PASS if no Wh-word, FLAG if open-ended Wh-word found",
    )
    wh_word_found: str | None = Field(
        default=None,
        description="Specific Wh-word found e.g. 'What', 'Why'",
    )

    overall_status: ScrutinyStatus = Field(
        default=ScrutinyStatus.PASS,
        description="Overall question-level scrutiny status",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Itemized explanations and flags for this question",
    )


class ChoicePairBTParityItem(BaseModel):
    """Scrutiny of knowledge level parity between 'either' and 'or' options."""

    choice_group: str = Field(..., description="Grouping identifier e.g. 'Q11'")
    section: str = Field(default="Part B", description="Section e.g. 'Part B' or 'Part C'")
    option_a_id: str = Field(..., description="Option A identifier e.g. 'Q11(a)'")
    option_a_bt: str = Field(..., description="Evaluated BT level for Option A")
    option_a_category: str = Field(..., description="Category for Option A e.g. 'Category B'")
    option_b_id: str = Field(..., description="Option B identifier e.g. 'Q11(b)'")
    option_b_bt: str = Field(..., description="Evaluated BT level for Option B")
    option_b_category: str = Field(..., description="Category for Option B e.g. 'Category B'")
    is_exact_match: bool = Field(
        ...,
        description="True if option A and option B have exact same BT level (e.g. B1 == B1)",
    )
    is_category_match: bool = Field(
        ...,
        description="True if option A and option B belong to same broad category (e.g. Category B)",
    )
    status: ScrutinyStatus = Field(
        ...,
        description="PASS if same knowledge level, FLAG if disparity exists",
    )
    reason: str = Field(..., description="Evaluation comment regarding choice parity")


class BTDistributionSlice(BaseModel):
    """Data slice for Category A, Category B, and Category C distribution."""

    category: str = Field(..., description="'Category A', 'Category B', or 'Category C'")
    display_name: str = Field(
        ...,
        description="Formatted label e.g. 'Category A (A1/A2) — Remember / Understand'",
    )
    description: str = Field(
        ...,
        description="Institutional cognitive tier e.g. 'Base Level', 'Medium Level', 'Highest Level'",
    )
    target_percentage_str: str = Field(
        ...,
        description="Target percentage guideline e.g. '50%', '30 – 35%', 'Remaining (15 – 20%)'",
    )
    target_min: float = Field(..., description="Minimum target percentage threshold")
    target_max: float = Field(..., description="Maximum target percentage threshold")
    total_marks: float = Field(..., description="Total marks allocated to this category")
    marks_percentage: float = Field(..., description="Calculated percentage of total marks")
    question_count: int = Field(..., description="Number of questions in this category")
    levels_present: list[str] = Field(
        default_factory=list,
        description="Specific BT levels present e.g. ['A1', 'A2']",
    )
    status: ScrutinyStatus = Field(
        default=ScrutinyStatus.PASS,
        description="PASS if within target, FLAG or REVIEW_REQUIRED if skewed",
    )
    comment: str = Field(..., description="Compliance note vs institutional target")


class BloomsTaxonomyReport(BaseModel):
    """Comprehensive Scrutiny Report for Criterion 5: Bloom's Taxonomy."""

    is_compliant: bool = Field(
        ...,
        description="True if all critical Bloom's Taxonomy checks pass without blocking flags",
    )
    overall_status: ScrutinyStatus = Field(
        ...,
        description="'PASS', 'REVIEW_REQUIRED', or 'FLAG'",
    )
    total_questions: int = Field(..., description="Total questions analyzed")
    total_marks: float = Field(..., description="Total evaluated marks")

    # Scrutiny Rule Metric Counts
    rule_bt_mentioned_count: int = Field(
        default=0,
        description="Number of questions with declared BT level present",
    )
    rule_bt_missing_count: int = Field(
        default=0,
        description="Number of questions missing declared BT level",
    )
    rule_bt_match_count: int = Field(
        default=0,
        description="Number of questions where declared BT matches evaluated BT",
    )
    rule_bt_mismatch_count: int = Field(
        default=0,
        description="Number of questions where declared BT conflicts with evaluated BT",
    )
    rule_wh_avoidance_flag_count: int = Field(
        default=0,
        description="Number of questions flagged for open-ended Wh-words",
    )
    rule_or_parity_flag_count: int = Field(
        default=0,
        description="Number of OR-choice pairs with knowledge level disparity",
    )
    rule_distribution_status: ScrutinyStatus = Field(
        default=ScrutinyStatus.PASS,
        description="Status of UG distribution targets and level spanning",
    )

    # Distribution & Pie Chart Data
    distribution_slices: list[BTDistributionSlice] = Field(
        default_factory=list,
        description="Detailed slices for Category A, B, and C",
    )
    distribution_pie_data: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recharts-ready pie chart data entries",
    )
    spans_all_levels: bool = Field(
        default=True,
        description="True if question paper contains questions across all 3 categories (A, B, C)",
    )

    # Detailed Audit Items
    questions: list[QuestionBTScrutinyItem] = Field(
        default_factory=list,
        description="Question-by-question Bloom's scrutiny results",
    )
    choice_pairs_parity: list[ChoicePairBTParityItem] = Field(
        default_factory=list,
        description="Scrutiny of either/or alternative choices",
    )
    human_review_triggers: list[str] = Field(
        default_factory=list,
        description="Consolidated list of human review triggers or institutional violations",
    )


class BloomsTaxonomyCheckRequest(BaseModel):
    """API request model for standalone Bloom's Taxonomy evaluation."""

    questions: list[QuestionItem] = Field(
        ...,
        description="List of structured question items to evaluate",
    )

