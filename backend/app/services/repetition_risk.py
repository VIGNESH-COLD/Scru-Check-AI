"""Repetition Risk Scrutiny Service (Criterion 9).

Identifies duplicate or substantially similar questions:
1. Within the paper (Internal repetition risk).
2. Across previous-year examination papers (Historical repetition risk).

Employs dual-stage scrutiny:
- Stage 1: Deterministic textual normalization and token-overlap (Jaccard similarity).
- Stage 2: Dense semantic embeddings via SentenceTransformer (all-MiniLM-L6-v2).

Strict Zero-Score Constraint:
- Returns strictly categorical statuses: PASS, FLAG, REVIEW_REQUIRED.
- Returns categorical similarity classes: DUPLICATE, SUBSTANTIALLY_SIMILAR, MODERATE_SIMILARITY, UNIQUE.
- Zero numerical compliance scores, similarity floats, or percentages are returned in the report.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence

import numpy as np

from app.schemas.question_mapping import QuestionItem
from app.schemas.repetition_risk import (
    QuestionRepetitionEvaluation,
    RepetitionMatch,
    RepetitionRiskReport,
    RepetitionStatus,
    RepetitionType,
    SimilarityCategory,
)
from app.services.embedding_service import SentenceTransformerEmbeddingService, embedding_service

logger = logging.getLogger("scrucheck.repetition_risk")

# Regex to strip question numbering, prefixes, and punctuation noise
Q_PREFIX_REGEX = re.compile(
    r"^(?:(?:Q(?:uestion)?\s*)?[0-9]{1,2}\s*[\.:\)]\s*(?:\([a-d]\)|[a-d][\.:\)])?\s*(?:\([ivx0-9]+\)|[ivx0-9]+[\.:\)])?|\([a-d]\)|\([ivx0-9]+\))\s*",
    re.IGNORECASE,
)
MARKS_NOISE_REGEX = re.compile(
    r"(?:\[|\()\s*[0-9]{1,2}(?:\.[0-9]+)?\s*(?:Marks?|marks?|MARKS?|M)?\s*(?:\]|\))\s*$",
    re.IGNORECASE,
)
PUNCT_REGEX = re.compile(r"[^\w\s]")

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "what", "which", "who", "whom", "this", "that", "these",
    "those", "it", "its", "as", "if", "from", "briefly", "short", "note", "discuss",
    "explain", "describe", "state", "define", "write", "give", "illustrate",
}


def clean_question_text(raw_text: str) -> str:
    """Normalize question statement for reliable similarity analysis."""
    text = raw_text.strip()
    text = Q_PREFIX_REGEX.sub("", text).strip()
    text = MARKS_NOISE_REGEX.sub("", text).strip()
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize_content_words(text: str) -> set[str]:
    """Extract lowercased alphanumeric content words excluding common stop words."""
    cleaned = PUNCT_REGEX.sub(" ", text.lower())
    tokens = {word for word in cleaned.split() if len(word) > 2 and word not in STOP_WORDS}
    return tokens


def compute_jaccard_overlap(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Calculate Jaccard index between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union) if union else 0.0


class RepetitionRiskAnalyzer:
    """Scrutiny engine for Criterion 9: Repetition Risk."""

    def __init__(self, embedder: SentenceTransformerEmbeddingService | None = None) -> None:
        self.embedder = embedder or embedding_service

    def analyze_paper(
        self,
        current_questions: Sequence[QuestionItem],
        previous_year_questions: Sequence[QuestionItem] | None = None,
        previous_year_filename: str | None = None,
    ) -> RepetitionRiskReport:
        """Run full Criterion 9 scrutiny on current questions against themselves and optional PYQ."""
        if not current_questions:
            return RepetitionRiskReport(
                overall_status=RepetitionStatus.PASS,
                total_questions_evaluated=0,
                pass_count=0,
                flag_count=0,
                review_required_count=0,
                internal_duplicates_count=0,
                historical_duplicates_count=0,
                has_previous_year_paper=bool(previous_year_questions),
                previous_year_filename=previous_year_filename,
                previous_year_questions_count=len(previous_year_questions or []),
                summary="No questions were provided for repetition risk scrutiny.",
                evaluations=[],
            )

        n_cur = len(current_questions)
        cur_cleaned = [clean_question_text(q.text) for q in current_questions]
        cur_tokens = [tokenize_content_words(t) for t in cur_cleaned]

        pyq_list = list(previous_year_questions or [])
        n_pyq = len(pyq_list)
        pyq_cleaned = [clean_question_text(q.text) for q in pyq_list]
        pyq_tokens = [tokenize_content_words(t) for t in pyq_cleaned]

        # Generate dense embeddings for semantic analysis (with graceful lexical fallback)
        all_texts = cur_cleaned + pyq_cleaned
        try:
            raw_embeddings = self.embedder.get_text_embeddings(all_texts)
            embeddings = np.array(raw_embeddings, dtype=np.float32)
            cur_embeddings = embeddings[:n_cur]
            pyq_embeddings = embeddings[n_cur:] if n_pyq > 0 else np.empty((0, embeddings.shape[1]), dtype=np.float32)
            internal_sim = np.dot(cur_embeddings, cur_embeddings.T)
            historical_sim = np.dot(cur_embeddings, pyq_embeddings.T) if n_pyq > 0 else None
        except Exception as exc:
            logger.warning("Dense embedding unavailable in RepetitionRiskAnalyzer; using lexical fallback: %s", exc)
            internal_sim = np.zeros((n_cur, n_cur), dtype=np.float32)
            historical_sim = np.zeros((n_cur, n_pyq), dtype=np.float32) if n_pyq > 0 else None

        evaluations: list[QuestionRepetitionEvaluation] = []
        internal_flags_count = 0
        historical_flags_count = 0

        for i, q_cur in enumerate(current_questions):
            q_id = q_cur.question_id
            matches: list[RepetitionMatch] = []

            # 1. Check Internal Repetition (within current paper)
            for j in range(n_cur):
                if i == j:
                    continue

                q_other = current_questions[j]
                # If both are same choice group alternatives e.g. 6(a) and 6(b), allow comparison
                t_cur = cur_cleaned[i]
                t_other = cur_cleaned[j]

                # Check exact text identity
                is_exact = (t_cur.lower() == t_other.lower()) and len(t_cur) > 5
                jaccard = compute_jaccard_overlap(cur_tokens[i], cur_tokens[j])
                v_sim = float(internal_sim[i, j])

                cat: SimilarityCategory | None = None
                exp = ""

                if is_exact or jaccard >= 0.80:
                    cat = SimilarityCategory.DUPLICATE
                    exp = f"Duplicate question text with question {q_other.question_id} in the same paper: '{t_other[:90]}'."
                elif v_sim >= 0.78 or (v_sim >= 0.73 and jaccard >= 0.30) or jaccard >= 0.50:
                    cat = SimilarityCategory.SUBSTANTIALLY_SIMILAR
                    exp = f"Substantially similar cognitive demand and question topic to question {q_other.question_id} in the same paper: '{t_other[:90]}'."
                elif v_sim >= 0.65 and (jaccard >= 0.20 or v_sim >= 0.70):
                    cat = SimilarityCategory.MODERATE_SIMILARITY
                    exp = f"Moderate conceptual overlap with question {q_other.question_id} in the same paper: '{t_other[:90]}'."

                if cat is not None:
                    matches.append(
                        RepetitionMatch(
                            source_question_id=q_id,
                            target_question_id=q_other.question_id,
                            repetition_type=RepetitionType.INTERNAL,
                            similarity_category=cat,
                            target_paper_label="Current Paper",
                            source_text_snippet=q_cur.text[:120] + ("..." if len(q_cur.text) > 120 else ""),
                            target_text_snippet=q_other.text[:120] + ("..." if len(q_other.text) > 120 else ""),
                            explanation=exp,
                        )
                    )

            # 2. Check Historical Repetition (across previous year paper)
            if n_pyq > 0 and historical_sim is not None:
                pyq_label = previous_year_filename or "Previous Year Paper"
                for k in range(n_pyq):
                    q_pyq = pyq_list[k]
                    t_cur = cur_cleaned[i]
                    t_pyq = pyq_cleaned[k]

                    is_exact = (t_cur.lower() == t_pyq.lower()) and len(t_cur) > 5
                    jaccard = compute_jaccard_overlap(cur_tokens[i], pyq_tokens[k])
                    v_sim = float(historical_sim[i, k])

                    cat = None
                    exp = ""

                    pyq_id_display = f"PYQ-{q_pyq.question_id}"
                    if is_exact or jaccard >= 0.80:
                        cat = SimilarityCategory.DUPLICATE
                        exp = f"Duplicate question repeated verbatim from {pyq_label} (matches {pyq_id_display}: '{t_pyq[:90]}')."
                    elif v_sim >= 0.78 or (v_sim >= 0.73 and jaccard >= 0.30) or jaccard >= 0.50:
                        cat = SimilarityCategory.SUBSTANTIALLY_SIMILAR
                        exp = f"Substantially similar question to {pyq_id_display} in {pyq_label}: '{t_pyq[:90]}'."
                    elif v_sim >= 0.65 and (jaccard >= 0.20 or v_sim >= 0.70):
                        cat = SimilarityCategory.MODERATE_SIMILARITY
                        exp = f"Moderate conceptual overlap with {pyq_id_display} from {pyq_label}: '{t_pyq[:90]}'."

                    if cat is not None:
                        matches.append(
                            RepetitionMatch(
                                source_question_id=q_id,
                                target_question_id=pyq_id_display,
                                repetition_type=RepetitionType.HISTORICAL,
                                similarity_category=cat,
                                target_paper_label=pyq_label,
                                source_text_snippet=q_cur.text[:120] + ("..." if len(q_cur.text) > 120 else ""),
                                target_text_snippet=q_pyq.text[:120] + ("..." if len(q_pyq.text) > 120 else ""),
                                explanation=exp,
                            )
                        )

            # Determine highest severity match for this question
            # Severity order: DUPLICATE (FLAG) > SUBSTANTIALLY_SIMILAR (FLAG) > MODERATE_SIMILARITY (REVIEW_REQUIRED) > UNIQUE (PASS)
            duplicates = [m for m in matches if m.similarity_category == SimilarityCategory.DUPLICATE]
            substantial = [m for m in matches if m.similarity_category == SimilarityCategory.SUBSTANTIALLY_SIMILAR]
            moderate = [m for m in matches if m.similarity_category == SimilarityCategory.MODERATE_SIMILARITY]

            if duplicates:
                top_match = duplicates[0]
                status = RepetitionStatus.FLAG
                sim_cat = SimilarityCategory.DUPLICATE
                rep_type = top_match.repetition_type
                matched_id = top_match.target_question_id
                matched_paper = top_match.target_paper_label
                matched_snippet = top_match.target_text_snippet
                reason = top_match.explanation
                req_review = False
                if rep_type == RepetitionType.INTERNAL:
                    internal_flags_count += 1
                else:
                    historical_flags_count += 1
            elif substantial:
                top_match = substantial[0]
                status = RepetitionStatus.FLAG
                sim_cat = SimilarityCategory.SUBSTANTIALLY_SIMILAR
                rep_type = top_match.repetition_type
                matched_id = top_match.target_question_id
                matched_paper = top_match.target_paper_label
                matched_snippet = top_match.target_text_snippet
                reason = top_match.explanation
                req_review = False
                if rep_type == RepetitionType.INTERNAL:
                    internal_flags_count += 1
                else:
                    historical_flags_count += 1
            elif moderate:
                top_match = moderate[0]
                status = RepetitionStatus.REVIEW_REQUIRED
                sim_cat = SimilarityCategory.MODERATE_SIMILARITY
                rep_type = top_match.repetition_type
                matched_id = top_match.target_question_id
                matched_paper = top_match.target_paper_label
                matched_snippet = top_match.target_text_snippet
                reason = f"Potential repetition risk: {top_match.explanation} Human review recommended."
                req_review = True
            else:
                status = RepetitionStatus.PASS
                sim_cat = SimilarityCategory.UNIQUE
                rep_type = RepetitionType.NONE
                matched_id = None
                matched_paper = None
                matched_snippet = None
                reason = "Unique question Statement"
                req_review = False

            evaluations.append(
                QuestionRepetitionEvaluation(
                    question_id=q_id,
                    section=q_cur.section,
                    assigned_marks=q_cur.marks,
                    status=status,
                    similarity_category=sim_cat,
                    repetition_type=rep_type,
                    matched_question_id=matched_id,
                    matched_paper_label=matched_paper,
                    matched_text_snippet=matched_snippet,
                    matches=matches,
                    reason=reason,
                    requires_human_review=req_review,
                )
            )

        # Sort evaluations by question natural order
        def sort_key(e: QuestionRepetitionEvaluation) -> tuple[int, str]:
            nums = re.findall(r"\d+", e.question_id)
            num = int(nums[0]) if nums else 999
            return (num, e.question_id)

        evaluations.sort(key=sort_key)

        pass_count = sum(1 for e in evaluations if e.status == RepetitionStatus.PASS)
        flag_count = sum(1 for e in evaluations if e.status == RepetitionStatus.FLAG)
        review_count = sum(1 for e in evaluations if e.status == RepetitionStatus.REVIEW_REQUIRED)

        if flag_count > 0:
            overall_status = RepetitionStatus.FLAG
            if historical_flags_count > 0:
                summary = (
                    f"Repetition risk scrutiny flagged {flag_count} non-compliant question(s): "
                    f"{internal_flags_count} internal repetition(s) within the paper, and "
                    f"{historical_flags_count} historical repetition(s) across previous-year papers."
                )
            else:
                summary = (
                    f"Repetition risk scrutiny flagged {flag_count} non-compliant question(s) with "
                    f"internal duplicate(s) or substantial conceptual overlap within the paper."
                )
        elif review_count > 0:
            overall_status = RepetitionStatus.REVIEW_REQUIRED
            summary = (
                f"Repetition risk scrutiny identified {review_count} question(s) with moderate conceptual overlap "
                "requiring human scrutiny review."
            )
        else:
            overall_status = RepetitionStatus.PASS
            summary = (
                f"All {n_cur} question(s) are distinct and unique within the current paper. "
                "Zero duplicate or substantially similar questions detected."
            )

        return RepetitionRiskReport(
            overall_status=overall_status,
            total_questions_evaluated=n_cur,
            pass_count=pass_count,
            flag_count=flag_count,
            review_required_count=review_count,
            internal_duplicates_count=internal_flags_count,
            historical_duplicates_count=historical_flags_count,
            has_previous_year_paper=bool(previous_year_questions),
            previous_year_filename=previous_year_filename,
            previous_year_questions_count=n_pyq,
            summary=summary,
            evaluations=evaluations,
        )


repetition_risk_analyzer = RepetitionRiskAnalyzer()
