"""Pydantic schemas for Criterion 9: Repetition Risk Scrutiny.

Enforces strict zero-score compliance: returns purely categorical statuses
(PASS, FLAG, REVIEW_REQUIRED) and categorical similarity classes (DUPLICATE,
SUBSTANTIALLY_SIMILAR, MODERATE_SIMILARITY, UNIQUE).
No numerical compliance scores, similarity floats, or percentages are returned.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.question_mapping import QuestionItem


class RepetitionStatus(StrEnum):
    """Categorical compliance status for repetition risk."""

    PASS = "PASS"
    FLAG = "FLAG"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class RepetitionType(StrEnum):
    """Scope of repetition risk."""

    NONE = "NONE"
    INTERNAL = "INTERNAL"          # Within the current question paper
    HISTORICAL = "HISTORICAL"      # Compared against previous-year paper


class SimilarityCategory(StrEnum):
    """Categorical classification of question overlap."""

    UNIQUE = "UNIQUE"
    DUPLICATE = "DUPLICATE"
    SUBSTANTIALLY_SIMILAR = "SUBSTANTIALLY_SIMILAR"
    MODERATE_SIMILARITY = "MODERATE_SIMILARITY"


class RepetitionMatch(BaseModel):
    """Detailed record of a detected duplicate or similar question pair."""

    source_question_id: str = Field(..., description="ID of question in current paper, e.g. 'Q3' or 'Q6(a)'")
    target_question_id: str = Field(..., description="ID of matched question, e.g. 'Q11' or 'PYQ-Q5'")
    repetition_type: RepetitionType = Field(..., description="INTERNAL or HISTORICAL")
    similarity_category: SimilarityCategory = Field(..., description="DUPLICATE, SUBSTANTIALLY_SIMILAR, or MODERATE_SIMILARITY")
    target_paper_label: str = Field(default="Current Paper", description="'Current Paper' or previous year paper filename")
    source_text_snippet: str = Field(..., description="Snippet of current question text")
    target_text_snippet: str = Field(..., description="Snippet of matched question text")
    explanation: str = Field(..., description="Human-readable explanation of why this pair is flagged")


class QuestionRepetitionEvaluation(BaseModel):
    """Per-question repetition risk scrutiny outcome."""

    question_id: str = Field(..., description="Question identifier, e.g. 'Q1', 'Q6(a)'")
    section: str | None = Field(default=None, description="Examination section, e.g. 'Part A'")
    assigned_marks: float | None = Field(default=None, description="Assigned marks metadata")
    status: RepetitionStatus = Field(..., description="PASS, FLAG, or REVIEW_REQUIRED")
    similarity_category: SimilarityCategory = Field(default=SimilarityCategory.UNIQUE)
    repetition_type: RepetitionType = Field(default=RepetitionType.NONE)
    matched_question_id: str | None = Field(default=None, description="Highest similarity matched question ID if any")
    matched_paper_label: str | None = Field(default=None, description="Paper where matched question was found")
    matched_text_snippet: str | None = Field(default=None, description="Snippet of the matched question")
    matches: list[RepetitionMatch] = Field(default_factory=list, description="All detected matching questions")
    reason: str = Field(..., description="Safe human-readable justification grounded in question content")
    requires_human_review: bool = Field(default=False)


class RepetitionRiskReport(BaseModel):
    """Aggregate Criterion 9 Repetition Risk Scrutiny Report."""

    overall_status: RepetitionStatus = Field(..., description="PASS, FLAG, or REVIEW_REQUIRED")
    total_questions_evaluated: int = Field(..., description="Total questions analyzed in current paper")
    pass_count: int = Field(..., description="Number of unique non-repeated questions")
    flag_count: int = Field(..., description="Number of flagged questions (duplicates or substantially similar)")
    review_required_count: int = Field(..., description="Number of questions requiring human review")
    internal_duplicates_count: int = Field(default=0, description="Number of internal question repetitions")
    historical_duplicates_count: int = Field(default=0, description="Number of repetitions from previous year paper")
    has_previous_year_paper: bool = Field(default=False, description="Whether a previous-year paper was provided")
    previous_year_filename: str | None = Field(default=None, description="Filename of uploaded previous-year paper")
    previous_year_questions_count: int = Field(default=0, description="Number of questions extracted from previous-year paper")
    summary: str = Field(..., description="Executive summary of repetition risk findings")
    evaluations: list[QuestionRepetitionEvaluation] = Field(default_factory=list, description="Per-question evaluation matrix")


class RepetitionRiskCheckRequest(BaseModel):
    """Request payload for standalone Criterion 9 Repetition Risk endpoint."""

    questions: list[QuestionItem] = Field(..., description="List of questions from current paper")
    previous_year_questions: list[QuestionItem] | None = Field(default=None, description="Optional questions from previous-year paper")
    previous_year_filename: str | None = Field(default=None, description="Optional filename or label for previous-year paper")

