from enum import StrEnum

from pydantic import BaseModel, Field


class AlignmentStatus(StrEnum):
    """Categorical alignment statuses for question-to-syllabus validation."""

    ALIGNED = "ALIGNED"
    MISMATCH = "MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"
    UNMAPPED = "UNMAPPED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


# Alias for backward compatibility
MappingStatus = AlignmentStatus


class QuestionItem(BaseModel):
    """Input representation of an individual examination question item."""

    question_id: str = Field(..., description="Unique question identifier, e.g. 'Q1' or 'Q11(a)'")
    text: str = Field(..., description="Question statement text")
    marks: float | None = Field(
        default=None, description="Marks allocated strictly as examination-structure metadata"
    )
    section: str | None = Field(default=None, description="Section or Part heading e.g. 'Part A'")
    question_number: str | None = Field(
        default=None, description="Top-level question number e.g. '1', '11'"
    )
    subquestion_id: str | None = Field(
        default=None, description="Nested subquestion label e.g. 'a', 'a(i)', 'b'"
    )
    is_alternative: bool = Field(
        default=False,
        description="True if this is an optional internal choice alternative (e.g. OR option)",
    )
    choice_group: str | None = Field(
        default=None,
        description="Grouping ID linking alternative choices (e.g. 'Q11')",
    )
    has_explicit_marks: bool = Field(
        default=True,
        description="True if marks were explicitly stated in the question paper text for this item",
    )
    declared_bt: str | None = Field(
        default=None,
        description="Bloom's Taxonomy level explicitly declared in the question paper text e.g. 'A1', 'B2'",
    )


class ExamScopeConfig(BaseModel):
    """Configuration defining the permitted syllabus unit scope and mapping rules."""

    pattern_name: str | None = Field(
        default=None,
        description="Name of the pattern e.g. 'CAT-1 (Unit I & II) - Standard'",
    )
    exam_type: str | None = Field(
        default=None,
        description="Category e.g. 'CAT-1', 'CAT-2', 'CAT-3', 'University'",
    )
    permitted_units: list[int] = Field(
        default_factory=list,
        description="Explicit list of permitted unit numbers, e.g. [1, 2]",
    )
    total_units: int = Field(default=5, description="Total units in course syllabus")


class CandidateTopicMatch(BaseModel):
    """Candidate topic retrieved from syllabus semantic index for question evaluation."""

    topic_id: str
    unit_number: int | None = None
    unit_title: str | None = None
    topic_title: str
    description: str
    similarity_score: float = Field(
        default=0.0,
        description="Internal retrieval similarity value (never exposed as compliance score)",
    )
    source_page: int | None = None
    co_identifiers: list[str] = Field(default_factory=list)
    is_unrecognized_unit: bool = False


class QuestionMappingResult(BaseModel):
    """Categorical evaluation result for a single question (No numerical scores)."""

    question_id: str
    question_text: str
    marks: float | None = None
    section: str | None = None
    question_number: str | None = None
    subquestion_id: str | None = None
    choice_group: str | None = None
    is_alternative: bool = False
    required_unit: int | None = Field(
        default=None, description="Prescribed syllabus unit from examination pattern"
    )
    matched_unit: int | None = Field(
        default=None, description="Identified syllabus unit from topic matching"
    )
    matched_topic: str | None = Field(
        default=None, description="Syllabus topic title matching this question"
    )
    course_outcome: str | None = Field(
        default=None,
        description="Course Outcome supported by syllabus evidence, or 'CO_NOT_AVAILABLE'",
    )
    status: AlignmentStatus = Field(
        ...,
        description="Categorical status: ALIGNED, MISMATCH, AMBIGUOUS, UNMAPPED, REVIEW_REQUIRED",
    )
    reason: str = Field(..., description="Short, understandable explanation for scrutinizer")
    evidence: str | None = Field(
        default=None, description="Supporting syllabus citation or topic content"
    )
    requires_human_review: bool = False
    candidate_topics: list[CandidateTopicMatch] = Field(default_factory=list)
    mapped_topics: list[CandidateTopicMatch] = Field(default_factory=list)
    error_message: str | None = None


class UnitChartItem(BaseModel):
    """Unit-level question distribution for Chart A (question counts only, no scores)."""

    unit_number: int
    unit_label: str
    question_count: int = 0
    question_group_count: int = 0
    question_ids: list[str] = Field(default_factory=list)
    is_permitted: bool = False


class COChartItem(BaseModel):
    """Course outcome aggregation for Chart B (question counts only, no scores)."""

    co_id: str
    question_count: int = 0
    question_ids: list[str] = Field(default_factory=list)


class StatusChartItem(BaseModel):
    """Alignment status aggregation for Chart C (question counts only, no scores)."""

    status: str
    question_count: int = 0
    question_ids: list[str] = Field(default_factory=list)


class BatchQuestionMappingRequest(BaseModel):
    """Payload for batch mapping questions against a syllabus."""

    syllabus_id: str = Field(..., description="Identifier of the ingested syllabus")
    scope_config: ExamScopeConfig = Field(
        ...,
        description="Examination scope policy configuration",
    )
    questions: list[QuestionItem] = Field(
        ...,
        description="List of examination questions to map and validate",
    )


class SyllabusCoverageReport(BaseModel):
    """Criterion 3 Syllabus Alignment and Unit-Wise Question Validation Report (No Scores)."""

    syllabus_id: str
    exam_pattern_name: str | None = None
    overall_status: str = Field(
        ..., description="Overall categorical status: ALIGNED, MISMATCH, or REVIEW_REQUIRED"
    )
    total_questions: int = Field(..., description="Total assessable question items")
    total_question_groups: int = Field(
        ..., description="Total distinct question groups (alternatives do not inflate count)"
    )
    aligned_count: int = Field(default=0, description="Questions matching prescribed unit")
    mismatch_count: int = Field(default=0, description="Questions violating prescribed unit")
    ambiguous_count: int = Field(default=0, description="Borderline or multi-topic questions")
    unmapped_count: int = Field(default=0, description="Questions not found in syllabus")
    review_required_count: int = Field(default=0, description="Questions requiring review")
    requires_human_review: bool = Field(
        ..., description="True if any question requires faculty scrutiny"
    )
    review_reasons: list[str] = Field(
        default_factory=list, description="Specific triggers requiring human scrutinizer review"
    )
    chart_prescribed_units: list[UnitChartItem] = Field(
        default_factory=list, description="Chart A: Questions by prescribed unit"
    )
    chart_course_outcomes: list[COChartItem] = Field(
        default_factory=list, description="Chart B: Questions by Course Outcome"
    )
    chart_status_distribution: list[StatusChartItem] = Field(
        default_factory=list, description="Chart C: Alignment status distribution"
    )
    results: list[QuestionMappingResult] = Field(
        default_factory=list, description="Question-by-question mapping table data"
    )
    limitations: list[str] = Field(
        default_factory=list, description="Documented known boundaries or limitations"
    )


# Alias for backward compatibility
SyllabusAlignmentReport = SyllabusCoverageReport
