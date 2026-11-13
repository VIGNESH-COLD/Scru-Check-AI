"""Schemas for Criterion 4: Mark and Time Distribution validation.

Strictly categorical compliance results (PASS, FLAG, REVIEW_REQUIRED).
Zero numerical scores, percentages, or LLM confidence values.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.question_mapping import QuestionItem


class MarkDistributionStatus(StrEnum):
    """Categorical evaluation status for mark and time distribution scrutiny."""

    PASS = "PASS"
    FLAG = "FLAG"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class SemanticComplexity(StrEnum):
    """Categorical semantic complexity assessment generated via LLM API."""

    SHORT_ANSWER = "SHORT_ANSWER"
    LONG_ANSWER = "LONG_ANSWER"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ValidationRuleId(StrEnum):
    """Identifier for the specific distribution rule triggering an evaluation."""

    RULE_PART_A_NO_SUBDIVISIONS = "RULE_PART_A_NO_SUBDIVISIONS"
    RULE_3_SUBDIVISION_COUNT = "RULE_3_SUBDIVISION_COUNT"
    RULE_SUBDIVISION_MARKS_ALLOCATION = "RULE_SUBDIVISION_MARKS_ALLOCATION"
    RULE_SECTION_METADATA_UNCERTAIN = "RULE_SECTION_METADATA_UNCERTAIN"
    # Legacy backward-compatibility aliases
    RULE_1_PART_A_COMPLEXITY = "RULE_PART_A_NO_SUBDIVISIONS"
    RULE_2_SECTION_MARK_MISPLACEMENT = "RULE_SECTION_METADATA_UNCERTAIN"


class LLMComplexityResult(BaseModel):
    """Structured LLM API response schema for question complexity analysis."""

    complexity_classification: SemanticComplexity = Field(
        ...,
        description="Categorical answer depth assessment (SHORT_ANSWER, LONG_ANSWER, REVIEW_REQUIRED)",
    )
    reason: str = Field(
        ...,
        description="Grounded explanation interpreting question demand, scope, and expected depth",
    )
    provider_used: str | None = Field(
        default=None,
        description="Name of the LLM provider that delivered this complexity assessment",
    )
    model_used: str | None = Field(
        default=None,
        description="Model name that generated this classification",
    )


class QuestionMarkEvaluation(BaseModel):
    """Question-level evaluation record for Criterion 4 (Mark and Time Distribution)."""

    question_id: str = Field(..., description="Unique question identifier, e.g. 'Q1' or 'Q11'")
    section: str | None = Field(default=None, description="Examination section, e.g. 'Part A'")
    assigned_marks: float | None = Field(default=None, description="Assigned mark allocation")
    complexity_classification: SemanticComplexity | None = Field(
        default=None,
        description="LLM semantic complexity classification (Part A 2-mark questions)",
    )
    subdivision_count: int | None = Field(
        default=None,
        description="Count of actual subdivisions for Part B/C long-answer questions",
    )
    subdivision_labels: list[str] = Field(
        default_factory=list,
        description="Parsed labels for identified subdivisions (e.g. ['(a)', '(b)'])",
    )
    status: MarkDistributionStatus = Field(
        ...,
        description="Categorical compliance status (PASS, FLAG, REVIEW_REQUIRED)",
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation of the validation finding",
    )
    rule_triggered: ValidationRuleId | None = Field(
        default=None,
        description="Specific distribution rule that governed this evaluation",
    )
    requires_human_review: bool = Field(
        default=False,
        description="True if uncertain structure, unextracted marks, or API failure requires manual review",
    )

    @property
    def marks(self) -> float | None:
        """Alias for assigned_marks to ensure backward compatibility."""
        return self.assigned_marks


class MarkDistributionReport(BaseModel):
    """Aggregated scrutiny report for Criterion 4: Mark and Time Distribution."""

    overall_status: MarkDistributionStatus = Field(
        ...,
        description="Overall categorical status (PASS, FLAG, REVIEW_REQUIRED)",
    )
    total_questions_evaluated: int = Field(
        default=0,
        description="Total distinct questions evaluated across all sections",
    )
    pass_count: int = Field(default=0, description="Count of compliant questions")
    flag_count: int = Field(default=0, description="Count of non-compliant questions")
    review_required_count: int = Field(
        default=0,
        description="Count of questions requiring manual faculty review",
    )
    rule_part_a_subdivision_flags: int = Field(
        default=0,
        description="Rule 1: Count of Part A questions flagged for containing sub-divisions",
    )
    rule_3_subdivision_flags: int = Field(
        default=0,
        description="Rule 2: Count of Part B/C questions flagged for exceeding 2 subdivisions",
    )
    rule_subdivision_mark_flags: int = Field(
        default=0,
        description="Rule 3: Count of Part B/C questions flagged for missing explicit marks on sub-divisions",
    )
    # Backward-compatibility alias fields
    part_a_subdivision_flags: int = Field(default=0)
    subdivision_mark_flags: int = Field(default=0)
    rule_1_part_a_flags: int = Field(default=0)
    rule_2_section_mark_flags: int = Field(default=0)
    requires_human_review: bool = Field(
        default=False,
        description="True if any question or LLM assessment requires human review",
    )
    review_reasons: list[str] = Field(
        default_factory=list,
        description="List of specific conditions necessitating manual review",
    )
    summary: str = Field(
        default="",
        description="Executive summary of mark and time distribution compliance",
    )
    evaluations: list[QuestionMarkEvaluation] = Field(
        default_factory=list,
        description="Question-level evaluation findings",
    )
    llm_provider_used: str | None = Field(
        default=None,
        description="Name of the LLM provider and model that evaluated question complexity",
    )


class MarkDistributionCheckRequest(BaseModel):
    """Request payload for standalone mark distribution scrutiny endpoint."""

    questions: list[QuestionItem] = Field(
        ...,
        description="List of parsed QuestionItem models to evaluate",
    )
    course_context: str | None = Field(
        default=None,
        description="Optional subject name, course code, or syllabus context",
    )
    exam_type: str | None = Field(
        default=None,
        description="Examination category (e.g. CAT-1, CAT-2, University)",
    )
    pattern_name: str | None = Field(
        default=None,
        description="Configured examination pattern name",
    )

