from typing import Any

from pydantic import BaseModel, Field


class SyllabusTopicRecord(BaseModel):
    """Structured representation of a single syllabus topic chunk with rich metadata."""

    topic_id: str = Field(..., description="Unique deterministic identifier for this topic chunk")
    syllabus_id: str = Field(..., description="Identifier of the syllabus document or course")
    course_code: str | None = Field(
        default=None, description="Course code if identified e.g. CS3351"
    )
    course_title: str | None = Field(default=None, description="Course title if identified")
    unit_number: int | None = Field(
        default=None,
        description="1-based unit number, or None if unrecognized / preamble",
    )
    unit_title: str = Field(
        default="UNASSIGNED / MISSING UNIT",
        description="Unit title / heading or fallback description",
    )
    raw_unit_heading: str | None = Field(
        default=None,
        description="Raw matched unit heading line from the document",
    )
    topic_title: str = Field(..., description="Primary topic or concept title")
    subtopics: list[str] = Field(
        default_factory=list,
        description="Specific subtopics or detailed breakdown concepts under this topic",
    )
    content: str = Field(
        ...,
        description="Full searchable text chunk combining unit, topic, and subtopics",
    )
    co_identifiers: list[str] = Field(
        default_factory=list,
        description="Explicitly declared Course Outcome identifiers (e.g. ['CO1']). Empty if absent.",
    )
    source_page: int | None = Field(
        default=None,
        description="1-based page number where this topic appears in the source document",
    )
    source_file: str | None = Field(
        default=None,
        description="Filename or path of the source document",
    )
    is_unrecognized_unit: bool = Field(
        default=False,
        description="Flag indicating missing or unrecognized unit heading",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional arbitrary metadata (e.g. paragraph offset, font style)",
    )


class ParsedSyllabus(BaseModel):
    """Complete parsed syllabus output containing structured topics and extraction statistics."""

    syllabus_id: str
    file_name: str | None = None
    file_type: str | None = None
    course_code: str | None = None
    course_title: str | None = None
    regulation: str | None = None
    total_units_found: int = 0
    total_topics_found: int = 0
    has_unrecognized_units: bool = False
    topics: list[SyllabusTopicRecord] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class TopicSearchResult(BaseModel):
    """Candidate topic matched during semantic retrieval."""

    topic: SyllabusTopicRecord
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    rank: int = Field(..., description="1-based retrieval ranking")


class RetrievalResponse(BaseModel):
    """Response containing top candidate topics for a search query."""

    query: str
    total_candidates: int
    results: list[TopicSearchResult]


class IngestionResponse(BaseModel):
    """Status report for a syllabus ingestion operation."""

    syllabus_id: str
    course_code: str | None = None
    course_title: str | None = None
    indexed_records_count: int
    units_indexed: list[int]
    unrecognized_units_count: int
    status: str = "success"
