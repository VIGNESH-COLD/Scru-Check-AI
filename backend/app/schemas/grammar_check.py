"""Pydantic schemas and categorical types for Criterion 6: Grammar, Spelling, and Sentence Formation.

Enforces institutional linguistic scrutiny:
- Spelling mistakes (excluding academic/technical terms)
- Grammatical errors (subject-verb agreement, tense, articles, prepositions)
- Sentence construction and formation
- Missing or incorrect punctuation
- Clarity and difficult-to-understand wording
- Ambiguity and multiple possible interpretations
- Incomplete or fragmented sentences

Strict Zero-Score policy: purely categorical statuses (PASS, FLAG, REVIEW_REQUIRED).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GrammarIssueCategory(StrEnum):
    """Categorical classification of linguistic issues."""

    SPELLING = "SPELLING"
    GRAMMAR = "GRAMMAR"
    SENTENCE_STRUCTURE = "SENTENCE_STRUCTURE"
    PUNCTUATION = "PUNCTUATION"
    CLARITY = "CLARITY"
    AMBIGUITY = "AMBIGUITY"
    INCOMPLETE_SENTENCE = "INCOMPLETE_SENTENCE"


class GrammarStatus(StrEnum):
    """Strict categorical scrutiny verdicts (Zero-Score policy)."""

    PASS = "PASS"
    FLAG = "FLAG"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class GrammarIssue(BaseModel):
    """Specific linguistic issue identified in a question."""

    category: GrammarIssueCategory = Field(
        ...,
        description="Linguistic issue category (SPELLING, GRAMMAR, SENTENCE_STRUCTURE, PUNCTUATION, CLARITY, AMBIGUITY, INCOMPLETE_SENTENCE)",
    )
    original_text: str | None = Field(
        default=None,
        description="Sentence or clause containing the issue",
    )
    problematic_text: str = Field(
        ...,
        description="Exact problematic word, phrase, or clause identified",
    )
    explanation: str = Field(
        ...,
        description="Detailed academic explanation of the linguistic error",
    )
    suggested_correction: str = Field(
        ...,
        description="Suggested replacement phrasing or corrected sentence",
    )


class QuestionGrammarEvaluation(BaseModel):
    """Linguistic and grammatical evaluation of an individual examination question."""

    question_id: str = Field(..., description="Question identifier e.g. 'Q1' or 'Q11(a)'")
    question_number: str | None = Field(default=None, description="Top-level number e.g. '1', '11'")
    subquestion_id: str | None = Field(default=None, description="Subdivision label e.g. 'a', 'a(i)'")
    section: str = Field(default="Part A", description="Section header e.g. 'Part A'")
    marks: float = Field(default=2.0, description="Marks allocated to the question")
    original_text: str = Field(..., description="Original question statement text")
    status: GrammarStatus = Field(
        default=GrammarStatus.PASS,
        description="Verdict: 'PASS', 'FLAG', or 'REVIEW_REQUIRED'",
    )
    issues: list[GrammarIssue] = Field(
        default_factory=list,
        description="Itemized linguistic issues identified",
    )
    suggested_full_text: str | None = Field(
        default=None,
        description="Suggested full question statement with corrections applied",
    )
    requires_human_review: bool = Field(
        default=False,
        description="True if human faculty review is needed for clarity or ambiguous intent",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Academic context notes or technical preservation reasons",
    )


class GrammarCheckReport(BaseModel):
    """Comprehensive Scrutiny Report for Criterion 6: Grammar, Spelling, and Sentence Formation."""

    is_compliant: bool = Field(
        ...,
        description="True if zero linguistic flags are present",
    )
    overall_status: GrammarStatus = Field(
        ...,
        description="'PASS', 'FLAG', or 'REVIEW_REQUIRED'",
    )
    total_questions_examined: int = Field(
        default=0,
        description="Total questions scrutinized for language and grammar",
    )
    questions_with_issues_count: int = Field(
        default=0,
        description="Count of questions containing one or more linguistic issues",
    )
    clean_questions_count: int = Field(
        default=0,
        description="Count of questions with zero grammar or spelling issues",
    )
    issues_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of issues count by category (SPELLING, GRAMMAR, etc.)",
    )
    questions: list[QuestionGrammarEvaluation] = Field(
        default_factory=list,
        description="Question-by-question linguistic evaluations",
    )
    human_review_triggers: list[str] = Field(
        default_factory=list,
        description="Consolidated list of human review triggers or blocking reasons",
    )
    llm_provider_used: str | None = Field(
        default=None,
        description="Name of the LLM provider and model that scrutinized this paper",
    )


class GrammarCheckRequest(BaseModel):
    """API request model for standalone grammar scrutiny."""

    questions: list[Any] = Field(
        ...,
        description="List of structured QuestionItem models to scrutinize",
    )
    course_context: str | None = Field(
        default=None,
        description="Optional course title or academic subject name",
    )

