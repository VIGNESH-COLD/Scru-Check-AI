"""
Marks & Time Distribution Analyzer Module
Academic scrutiny algorithm for university question paper validation.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import re
import math


# ── Configuration Constants ───────────────────────────────────────────────────

# Valid individual question mark allocations
VALID_MARKS: Set[int] = {2, 13, 15, 16}

# Expected time ranges per mark value (min_mins, max_mins)
MARK_TIME_RANGES: Dict[int, Tuple[int, int]] = {
    2: (2, 7),
    13: (18, 28),
    15: (28, 36),
    16: (36, 45),
}

# Expected answer length per mark value (min_words, max_words, min_pages, max_pages)
EXPECTED_WORD_COUNT: Dict[int, Dict[str, Any]] = {
    2: {"min_words": 40, "max_words": 80, "min_pages": 0.5, "max_pages": 1.0, "label": "40-80 words (~0.5-1 page)"},
    13: {"min_words": 300, "max_words": 500, "min_pages": 3.0, "max_pages": 4.0, "label": "300-500 words (~3-4 pages)"},
    15: {"min_words": 500, "max_words": 700, "min_pages": 4.0, "max_pages": 5.0, "label": "500-700 words (~4-5 pages)"},
    16: {"min_words": 700, "max_words": 900, "min_pages": 5.0, "max_pages": 6.0, "label": "700-900 words (~5-6 pages)"},
}

# Examination time configurations (duration, reading_time, revision_time, net_writing_time)
EXAM_CONFIG: Dict[int, Dict[str, Any]] = {
    100: {
        "duration": 180,
        "reading_time": 15,
        "revision_time": 15,
        "net_writing_time": 150,
        "allocation_per_mark": 1.5,  # 150 net writing mins / 100 marks
    },
    50: {
        "duration": 90,
        "reading_time": 10,
        "revision_time": 10,
        "net_writing_time": 70,
        "allocation_per_mark": 1.4,  # 70 net writing mins / 50 marks
    },
}

# Average student writing speed (words per minute)
WRITING_SPEED_WPM: float = 18.0

# Bloom taxonomy verb mapping dictionary
BLOOM_VERB_MAP: Dict[str, Tuple[float, List[str]]] = {
    "Remember": (1.0, [
        "define", "list", "state", "name", "recall", "write down", "mention", "identify",
        "enumerate", "tabulate"
    ]),
    "Understand": (1.25, [
        "explain", "describe", "discuss", "summarize", "outline", "interpret", "classify",
        "elaborate", "comment"
    ]),
    "Apply": (1.5, [
        "apply", "solve", "calculate", "compute", "demonstrate", "illustrate", "construct",
        "implement", "derive", "prove", "draw", "sketch"
    ]),
    "Analyze": (1.75, [
        "analyze", "compare", "contrast", "differentiate", "distinguish", "examine",
        "break down", "categorize"
    ]),
    "Evaluate": (2.0, [
        "evaluate", "justify", "critique", "assess", "argue", "rate", "validate",
        "defend", "recommend"
    ]),
    "Create": (2.2, [
        "design", "formulate", "synthesize", "compose", "devise", "invent", "architecture",
        "develop"
    ]),
}

# Stopwords for technical concept extraction
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what", "which",
    "this", "that", "these", "those", "then", "just", "so", "than", "such", "both",
    "through", "about", "against", "between", "into", "throughout", "during", "before",
    "after", "above", "below", "to", "from", "up", "upon", "down", "in", "out", "on",
    "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "s", "t", "can", "will", "just", "don", "should", "now", "explain", "describe",
    "discuss", "illustrate", "enumerate", "elaborate", "differentiate", "compare",
    "contrast", "analyze", "evaluate", "justify", "recommend", "design", "develop",
    "derive", "prove", "comment", "tabulate", "draw", "sketch", "construct", "validate",
    "define", "list", "state", "name", "recall", "write", "mention", "identify",
    "question", "part", "section", "marks", "max", "maximum", "total", "note", "answer"
}


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class TimeBreakdown:
    """Detailed explainable time breakdown in minutes."""
    expected_words: int
    writing_time_mins: float
    thinking_time_mins: float
    diagram_time_mins: float
    programming_time_mins: float
    numerical_time_mins: float
    case_study_time_mins: float
    final_estimated_mins: int


@dataclass
class QuestionFeatureVector:
    """Feature vector representing question cognitive complexity & structure."""
    bloom_level: str
    action_verb: str
    concept_count: int
    concepts_list: List[str]
    cognitive_task_count: int
    expected_answer_depth: str
    has_diagram: bool
    has_numerical: bool
    has_programming: bool
    has_case_study: bool
    is_optional: bool
    choice_group: Optional[str]
    expected_diagrams: int
    expected_formulas: int
    expected_algorithms: int
    expected_tables: int


# ── Mark & Arithmetic Validator ───────────────────────────────────────────────

class MarkValidator:
    """
    Validates section arithmetic, paper total marks, valid question mark values,
    and handles single-source mark extraction and section resolution.
    """
    VALID_MARKS = VALID_MARKS

    @staticmethod
    def get_question_text(question: Dict[str, Any]) -> str:
        """
        Extract clean, non-duplicated question text.
        Avoids text + full_text concatenation duplication.
        """
        if "_cached_clean_text" in question:
            return question["_cached_clean_text"]

        text = question.get("text") or question.get("full_text") or ""
        clean = text.strip()
        question["_cached_clean_text"] = clean
        return clean

    def extract_explicit_marks(self, text: str) -> Optional[int]:
        """
        Extract explicit mark allocation from text.
        Supports:
          - [2 Marks], (2 Marks), 2 Marks
          - Marks : 2, Maximum Marks : 2, Max Marks : 2
          - [2], (2) at end of line
        Rejects negative or malformed marks.
        """
        # Reject explicit negative signs
        if re.search(r'-\s*\d+\s*Marks?', text, re.IGNORECASE):
            return None

        patterns = [
            r'\[(\d+)\s*Marks?\]',
            r'\((\d+)\s*Marks?\)',
            r'Max(?:imum)?\s*Marks?\s*[:=]?\s*(\d+)',
            r'Marks?\s*[:=]?\s*(\d+)',
            r'(\d+)\s*Marks?',
            r'\[(\d+)\]\s*$',
            r'\((\d+)\)\s*$',
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                val = int(match.group(1))
                if 1 <= val <= 100:
                    return val
        return None

    def validate_arithmetic(
        self, raw_text: str, pattern_obj: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate section arithmetic.
        Matches patterns like 'Part A: 10x2=20', '10 × 2 =20', '10 X 2 =20', '10*2=20'.
        Case-insensitive and handles all spacing and section name variations.
        """
        sections = []
        issues = []

        if not raw_text and pattern_obj and isinstance(pattern_obj, dict) and "sections" in pattern_obj:
            for s in pattern_obj["sections"]:
                q_count = s.get("questions", 0)
                m_each = s.get("marks_per_question", 0)
                sec_tot = s.get("total", q_count * m_each)
                expected = q_count * m_each
                is_valid = (expected == sec_tot)
                issue_msg = None
                if not is_valid:
                    issue_msg = f"Arithmetic Error: {q_count} × {m_each} = {sec_tot}. Expected: {expected}"
                    issues.append(f"❌ {issue_msg}")
                sections.append({
                    "name": s.get("name", ""),
                    "questions": q_count,
                    "marks_each": m_each,
                    "total": sec_tot,
                    "expected_total": expected,
                    "valid_arithmetic": is_valid,
                    "issue": issue_msg
                })
            return sections, issues

        # Capture section header name if present before equation
        matches = re.finditer(r'(?:([\(\[]?(?:PART|SECTION)\s+[A-Z0-9]+[\)\]]?)\s*[:=-]?)?\s*(\d+)\s*[x×X\*]\s*(\d+)\s*=\s*(\d+)', raw_text, re.IGNORECASE)
        found_any = False
        for match in matches:
            found_any = True
            sec_name = (match.group(1) or "").strip()
            questions_count, marks_each, section_total = int(match.group(2)), int(match.group(3)), int(match.group(4))
            expected = questions_count * marks_each
            is_valid = (expected == section_total)
            issue_msg = None
            if not is_valid:
                issue_msg = f"Arithmetic Error: {questions_count} × {marks_each} = {section_total}. Expected: {expected}"
                issues.append(f"❌ {issue_msg}")
            sections.append({
                "name": sec_name,
                "questions": questions_count,
                "marks_each": marks_each,
                "total": section_total,
                "expected_total": expected,
                "valid_arithmetic": is_valid,
                "issue": issue_msg
            })

        if not found_any and pattern_obj and isinstance(pattern_obj, dict) and "sections" in pattern_obj:
            for s in pattern_obj["sections"]:
                q_count = s.get("questions", 0)
                m_each = s.get("marks_per_question", 0)
                sec_tot = s.get("total", q_count * m_each)
                expected = q_count * m_each
                is_valid = (expected == sec_tot)
                issue_msg = None
                if not is_valid:
                    issue_msg = f"Arithmetic Error: {q_count} × {m_each} = {sec_tot}. Expected: {expected}"
                    issues.append(f"❌ {issue_msg}")
                sections.append({
                    "name": s.get("name", ""),
                    "questions": q_count,
                    "marks_each": m_each,
                    "total": sec_tot,
                    "expected_total": expected,
                    "valid_arithmetic": is_valid,
                    "issue": issue_msg
                })

        return sections, issues

    def validate_mark_values(
        self, sections: List[Dict[str, Any]], questions: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Validate that all question marks belong strictly to {2, 13, 15, 16}.
        """
        issues = []
        for s in sections:
            m = s.get("marks_each")
            if m and m not in self.VALID_MARKS:
                issues.append(
                    f"❌ Invalid mark allocation ({m} marks per question). "
                    f"Only 2, 13, 15 and 16 mark questions are permitted."
                )

        for q in questions:
            q_text = self.get_question_text(q)
            q_num = q.get("number") or q.get("question_number") or q.get("label") or "?"
            explicit = self.extract_explicit_marks(q_text)
            if explicit is not None and explicit not in self.VALID_MARKS:
                issues.append(
                    f"❌ Question {q_num} contains {explicit} marks. "
                    f"Only 2, 13, 15 and 16 mark questions are permitted."
                )

        return issues

    def validate_total_marks(
        self, total_marks: int, pattern_obj: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Optional[str]]:
        """
        Support ONLY 100-mark and 50-mark papers.
        100 marks -> Expected Duration = 180 minutes.
        50 marks -> Expected Duration = 90 minutes.
        """
        if total_marks in EXAM_CONFIG:
            return EXAM_CONFIG[total_marks]["duration"], None
        else:
            issue = f"❌ Invalid total marks ({total_marks}). Only 100-mark (180 mins) and 50-mark (90 mins) papers are supported."
            duration = 180 if total_marks > 75 else 90
            return duration, issue

    def resolve_question_section(
        self, q_index: int, question: Dict[str, Any], raw_text: str, sections: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Resolve question section using parser metadata, explicit boundary headers, or mark matching.
        NEVER guess or default to sections[0] when unassigned and ambiguous.
        Returns (section_dict_or_None, is_certain).
        """
        q_text = self.get_question_text(question)
        explicit_marks = self.extract_explicit_marks(q_text)

        # 1. Use parser metadata if present
        meta_sec = str(question.get("section") or question.get("section_name") or "").strip().upper()
        if meta_sec and sections:
            for s in sections:
                sec_name = s.get("name", "").upper()
                if sec_name and (sec_name in meta_sec or meta_sec in sec_name):
                    return s, True
                if (s.get("marks_each") == 2 and "A" in meta_sec) or (s.get("marks_each") in [13, 15, 16] and "B" in meta_sec):
                    return s, True

        # 2. Check explicit boundary headers preceding question or in prompt
        sec_header_match = re.search(r'\b(PART\s+[A-Z]|SECTION\s+[A-Z0-9]+)\b', q_text, re.IGNORECASE)
        if sec_header_match and sections:
            hdr = sec_header_match.group(1).upper()
            for s in sections:
                sec_name = s.get("name", "").upper()
                if sec_name and (sec_name in hdr or hdr in sec_name):
                    return s, True
                if (s.get("marks_each") == 2 and "A" in hdr) or (s.get("marks_each") in [13, 15, 16] and "B" in hdr):
                    return s, True

        # Scan raw_text for section headers appearing before this question
        if raw_text:
            part_a_pos = raw_text.upper().find("PART A")
            part_b_pos = raw_text.upper().find("PART B")
            q_pos = raw_text.find(q_text[:20]) if len(q_text) >= 20 else -1
            if q_pos != -1 and sections:
                if part_b_pos != -1 and q_pos >= part_b_pos:
                    for s in sections:
                        if s.get("marks_each", 0) >= 13 or "B" in s.get("name", "").upper():
                            return s, True
                elif part_a_pos != -1 and q_pos >= part_a_pos:
                    for s in sections:
                        if s.get("marks_each", 0) == 2 or "A" in s.get("name", "").upper():
                            return s, True

        # 3. Match section by explicit mark value if unambiguous
        if explicit_marks and sections:
            matching_secs = [s for s in sections if s.get("marks_each") == explicit_marks]
            if len(matching_secs) == 1:
                return matching_secs[0], True
            elif len(sections) == 1 and sections[0].get("marks_each") == explicit_marks:
                return sections[0], True

        # 4. If section cannot be determined automatically, return None
        return None, False


# ── Complexity Estimator ─────────────────────────────────────────────────────

class ComplexityEstimator:
    """
    Extracts feature vector, academic technical concepts, expected answer artifacts,
    and estimates explainable answering time using WRITING_SPEED_WPM.
    """

    def extract_concepts(self, question: Dict[str, Any], text: str) -> List[str]:
        """
        Extract academic concepts preferred order:
        1. Parser metadata (if available)
        2. Technical noun phrases / terms
        3. Fallback tokenizer filtering stopwords
        """
        # 1. Parser metadata
        if "concepts" in question and isinstance(question["concepts"], list):
            return question["concepts"]
        if "keywords" in question and isinstance(question["keywords"], list):
            return question["keywords"]

        # 2. Multi-word technical noun phrases & domain terms
        clean_text = re.sub(r'\[.*?\]|\(.*?\)|Q\d+\.?', '', text)
        noun_phrases = re.findall(r'\b[A-Z][a-zA-Z0-9_-]+(?:\s+[A-Z][a-zA-Z0-9_-]+)*\b', clean_text)
        filtered_np = [
            np for np in noun_phrases
            if np.upper() not in {"Q1", "Q2", "Q3", "Q4", "Q5", "PART", "SECTION", "MARKS", "NOTE", "ANSWER", "OR"}
        ]

        if len(filtered_np) >= 1:
            return list(dict.fromkeys(filtered_np))

        # 3. Fallback tokenizer
        tokens = re.findall(r'\b[a-zA-Z]{3,}\b', clean_text.lower())
        concepts = [t for t in tokens if t not in STOPWORDS]
        return list(dict.fromkeys(concepts))[:6]

    def extract_feature_vector(self, question: Dict[str, Any], assigned_marks: int) -> QuestionFeatureVector:
        """Construct feature vector for a question."""
        text = MarkValidator.get_question_text(question)
        text_lower = text.lower()

        # 1 & 2. Bloom level and Action verb from BLOOM_VERB_MAP
        bloom_level, action_verb, _ = self._detect_bloom(text_lower)

        # 3. Concepts
        concepts_list = self.extract_concepts(question, text)
        concept_count = max(1, len(concepts_list))

        # 4. Cognitive task count
        cognitive_task_count = self._detect_cognitive_tasks(text_lower)

        # 5. Choice / Optional detection
        is_optional, choice_group = self._detect_choice_options(question, text_lower)

        # 6. Expected answer depth
        if assigned_marks <= 2:
            expected_answer_depth = "Concise"
        elif assigned_marks <= 13:
            expected_answer_depth = "Moderate" if bloom_level in ["Remember", "Understand"] else "Detailed"
        else:
            expected_answer_depth = "Detailed" if bloom_level in ["Remember", "Understand"] else "Comprehensive"

        # 7-10. Specific requirements & artifact counts
        has_diagram = self._has_keywords(text_lower, [
            "diagram", "draw", "sketch", "architecture", "flowchart", "schematic", "figure", "circuit", "block diagram"
        ])
        has_numerical = self._has_keywords(text_lower, [
            "calculate", "solve", "compute", "determine", "find the value", "evaluate the expression", "equation", "formula"
        ])
        has_programming = self._has_keywords(text_lower, [
            "write a program", "code", "algorithm", "function", "pseudocode", "script", "java", "python", "c++", "sql", "html"
        ])
        has_case_study = self._has_keywords(text_lower, [
            "case study", "scenario", "analyze the situation", "given the system"
        ])

        expected_diagrams = 1 if has_diagram else 0
        expected_formulas = 2 if has_numerical else 0
        expected_algorithms = 1 if has_programming else 0
        expected_tables = 1 if "tabulate" in text_lower or "compare" in text_lower else 0

        return QuestionFeatureVector(
            bloom_level=bloom_level,
            action_verb=action_verb,
            concept_count=concept_count,
            concepts_list=concepts_list,
            cognitive_task_count=cognitive_task_count,
            expected_answer_depth=expected_answer_depth,
            has_diagram=has_diagram,
            has_numerical=has_numerical,
            has_programming=has_programming,
            has_case_study=has_case_study,
            is_optional=is_optional,
            choice_group=choice_group,
            expected_diagrams=expected_diagrams,
            expected_formulas=expected_formulas,
            expected_algorithms=expected_algorithms,
            expected_tables=expected_tables
        )

    def estimate_time_and_length(
        self, fv: QuestionFeatureVector, assigned_marks: int, question_text: str
    ) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
        """
        Estimate explainable answering time using WRITING_SPEED_WPM and expected answer artifacts.
        Returns (final_estimated_mins, answer_length_dict, time_breakdown_dict).
        """
        target_mark = assigned_marks if assigned_marks in EXPECTED_WORD_COUNT else (
            2 if assigned_marks <= 5 else (13 if assigned_marks <= 14 else (15 if assigned_marks == 15 else 16))
        )
        length_info = EXPECTED_WORD_COUNT.get(target_mark, EXPECTED_WORD_COUNT[2])

        # Target word count midpoint
        expected_words = int((length_info["min_words"] + length_info["max_words"]) / 2)

        # 1. Writing time = words / WRITING_SPEED_WPM
        writing_time_mins = expected_words / WRITING_SPEED_WPM

        # 2. Thinking time = writing_time * (bloom_multiplier - 1.0)
        bloom_mult = BLOOM_VERB_MAP.get(fv.bloom_level, (1.25, []))[0]
        thinking_time_mins = writing_time_mins * max(bloom_mult - 1.0, 0.2)

        # 3. Domain & artifact times
        diagram_time_mins = 6.0 if fv.has_diagram else 0.0
        programming_time_mins = 6.0 if fv.has_programming else 0.0
        numerical_time_mins = 5.0 if fv.has_numerical else 0.0
        case_study_time_mins = 7.0 if fv.has_case_study else 0.0

        if fv.cognitive_task_count > 1:
            thinking_time_mins += (fv.cognitive_task_count - 1) * 2.0

        total_time_mins = (
            writing_time_mins + thinking_time_mins + diagram_time_mins +
            programming_time_mins + numerical_time_mins + case_study_time_mins
        )

        # Minimum required thresholds for 2m/13m questions with heavy artifacts
        if assigned_marks <= 2:
            if fv.has_diagram or fv.has_programming or fv.has_case_study:
                final_estimated_mins = max(round(total_time_mins), 14)
            else:
                final_estimated_mins = round(total_time_mins)
        elif assigned_marks >= 13:
            clean_prompt = re.sub(r'\[.*?\]|\(.*?\)|Q\d+\.?', '', question_text).strip()
            words = clean_prompt.split()
            if not fv.has_diagram and not fv.has_programming and not fv.has_numerical and not fv.has_case_study and fv.bloom_level in ["Remember", "Understand"]:
                if len(words) <= 10 or fv.bloom_level == "Remember":
                    final_estimated_mins = 5
                else:
                    final_estimated_mins = max(round(total_time_mins), 20)
            else:
                final_estimated_mins = max(round(total_time_mins), 20)
        else:
            final_estimated_mins = round(total_time_mins)

        final_estimated_mins = int(final_estimated_mins)

        tb = TimeBreakdown(
            expected_words=expected_words,
            writing_time_mins=round(writing_time_mins, 1),
            thinking_time_mins=round(thinking_time_mins, 1),
            diagram_time_mins=diagram_time_mins,
            programming_time_mins=programming_time_mins,
            numerical_time_mins=numerical_time_mins,
            case_study_time_mins=case_study_time_mins,
            final_estimated_mins=final_estimated_mins
        )

        expected_answer_length = {
            "words": f"{length_info['min_words']}-{length_info['max_words']} words",
            "pages": f"{length_info['min_pages']}-{length_info['max_pages']} pages",
            "label": length_info["label"],
            "min_words": length_info["min_words"],
            "max_words": length_info["max_words"],
            "expected_diagrams": fv.expected_diagrams,
            "expected_formulas": fv.expected_formulas,
            "expected_algorithms": fv.expected_algorithms,
            "expected_tables": fv.expected_tables,
        }

        return final_estimated_mins, expected_answer_length, tb.__dict__

    def _detect_bloom(self, text_lower: str) -> Tuple[str, str, float]:
        for level, (mult, verbs) in BLOOM_VERB_MAP.items():
            for verb in verbs:
                if re.search(r'\b' + re.escape(verb) + r'\b', text_lower):
                    return level, verb, mult
        return "Understand", "explain", 1.25

    def _detect_cognitive_tasks(self, text_lower: str) -> int:
        task_count = 1
        # Check compound action verbs
        compound_patterns = [
            r'\b(explain|discuss|draw|design|analyze)\s+(and|or|&)\s+(compare|contrast|justify|evaluate|recommend|explain)\b',
            r'\billustrate\s+with\s+examples\b',
            r'\bdraw\s+(and|&)\s+explain\b',
            r'\bdesign\s+(and|&)\s+develop\b',
        ]
        for p in compound_patterns:
            if re.search(p, text_lower):
                task_count += 1

        subq = len(re.findall(r'\([a-d]\)|\b[ivx]+\)', text_lower))
        if subq > 0:
            task_count += subq

        return min(task_count, 4)

    def _detect_choice_options(self, question: Dict[str, Any], text_lower: str) -> Tuple[bool, Optional[str]]:
        """Detect optional choice questions (OR, Attempt any one, Answer any 5)."""
        is_optional = False
        choice_group = None

        if "is_optional" in question:
            is_optional = bool(question["is_optional"])
            choice_group = question.get("choice_group")
            return is_optional, choice_group

        if re.search(r'\b(or|attempt any one|answer any\s+\w+)\b', text_lower):
            is_optional = True

        q_num = str(question.get("number") or question.get("question_number") or "")
        match_or = re.search(r'(\d+)\s*\([ab]\)\s*or\s*\d+\s*\([ab]\)', text_lower)
        if match_or:
            is_optional = True
            choice_group = f"Q{q_num}_choice"

        return is_optional, choice_group

    @staticmethod
    def _has_keywords(text_lower: str, keywords: List[str]) -> bool:
        return any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in keywords)


# ── Time Estimator ────────────────────────────────────────────────────────────

class TimeEstimator:
    """
    Evaluates individual question time allocation, smallest range/midpoint deviation
    for suggested marks, choice path duration, confidence scoring, and exam duration.
    """

    @staticmethod
    def calculate_allocated_time(assigned_marks: int, total_marks: int = 100) -> int:
        """Calculate allocated net writing time for a question."""
        config = EXAM_CONFIG.get(total_marks, EXAM_CONFIG[100])
        per_mark = config["allocation_per_mark"]
        return max(1, int(round(assigned_marks * per_mark)))

    @staticmethod
    def calculate_suggested_marks(estimated_time: int) -> int:
        """
        Select mark allocation (2, 13, 15, or 16) with the SMALLEST DEVIATION
        from configured MARK_TIME_RANGES midpoints or boundaries.
        """
        best_mark = 2
        min_deviation = float("inf")

        for mark, (r_min, r_max) in MARK_TIME_RANGES.items():
            if r_min <= estimated_time <= r_max:
                return mark  # Exact fit inside range

            midpoint = (r_min + r_max) / 2.0
            deviation = abs(estimated_time - midpoint)
            if deviation < min_deviation:
                min_deviation = deviation
                best_mark = mark

        return best_mark

    def evaluate_question(
        self,
        question: Dict[str, Any],
        assigned_marks: int,
        total_marks: int,
        fv: QuestionFeatureVector,
        estimated_time: int,
        answer_length: Dict[str, Any],
        time_breakdown: Dict[str, Any],
        section_certainty: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate question against MARK_TIME_RANGES and compute per-question confidence.
        """
        q_text = MarkValidator.get_question_text(question)
        q_num = question.get("number") or question.get("question_number") or question.get("label") or "?"

        allocated_time = self.calculate_allocated_time(assigned_marks, total_marks)
        suggested_marks = self.calculate_suggested_marks(estimated_time)
        diff = abs(estimated_time - allocated_time)

        range_min, range_max = MARK_TIME_RANGES.get(assigned_marks, (2, 7) if assigned_marks <= 2 else (18, 45))

        status = "PASS"
        reason = "Question complexity and time allocation are within expected limits."

        if not section_certainty:
            status = "UNKNOWN"
            reason = "Unable to determine question section automatically. Manual verification required."
        elif estimated_time > range_max:
            status = "FAIL"
            reason = (
                f"Question complexity exceeds the allotted marks. "
                f"The question requires approximately {estimated_time} minutes to answer (expected range for {assigned_marks} marks: {range_min}-{range_max} mins) "
                f"but only {allocated_time} minutes writing time are allocated. "
                f"Either simplify the question or increase the marks."
            )
        elif estimated_time < range_min:
            status = "FAIL"
            reason = (
                f"Question is too simple for a {assigned_marks}-mark answer. "
                f"Requires approximately {estimated_time} minutes (expected range for {assigned_marks} marks: {range_min}-{range_max} mins). "
                f"Reduce the marks or increase the question complexity."
            )

        # Confidence calculation (0.0 to 1.0)
        feature_completeness = 1.0 if (q_text and fv.bloom_level) else 0.7
        sec_confidence = 1.0 if section_certainty else 0.5
        complexity_confidence = 1.0 if fv.concept_count >= 1 else 0.8
        confidence = round((feature_completeness * 0.4) + (sec_confidence * 0.4) + (complexity_confidence * 0.2), 2)

        return {
            "question_number": q_num,
            "question_text": q_text,
            "assigned_marks": assigned_marks,
            "suggested_marks": suggested_marks,
            "allocated_time": allocated_time,
            "estimated_time": estimated_time,
            "difference": diff,
            "status": status,
            "reason": reason,
            "confidence": confidence,
            "is_optional": fv.is_optional,
            "choice_group": fv.choice_group,
            "bloom_level": fv.bloom_level,
            "detected_action_verb": fv.action_verb,
            "diagram_required": fv.has_diagram,
            "programming_required": fv.has_programming,
            "numerical_required": fv.has_numerical,
            "case_study": fv.has_case_study,
            "task_count": fv.cognitive_task_count,
            "expected_answer_length": answer_length,
            "time_breakdown": time_breakdown,
        }

    def evaluate_overall_paper_time(
        self, total_estimated_time: int, expected_duration: int
    ) -> Tuple[str, str, float]:
        """
        Evaluates compulsory paper duration against expected exam duration.
        Rules:
        Difference <= 10%: PASS (<= 198 mins for 180m paper)
        Difference >10% and <=20%: WARNING (199 to 216 mins for 180m paper)
        Difference >20%: FAIL (> 216 mins for 180m paper)
        """
        diff_mins = abs(total_estimated_time - expected_duration)
        diff_pct = (diff_mins / max(expected_duration, 1)) * 100.0

        if diff_pct <= 10.0:
            return "PASS", "Overall paper time estimation aligns well with examination duration.", diff_pct
        elif diff_pct <= 20.0:
            return (
                "WARNING",
                f"Estimated exam duration ({total_estimated_time} mins) deviates moderately from expected duration ({expected_duration} mins).",
                diff_pct
            )
        else:
            return (
                "FAIL",
                "The paper cannot reasonably be completed by an average student within the examination duration.",
                diff_pct
            )


# ── Main Marks Analyzer Orchestrator ──────────────────────────────────────────

class MarksAnalyzer:
    """
    Main Marks & Time Distribution Analyzer.
    Coordinates mark validation, feature vector construction, cognitive time estimation,
    optional question path handling, confidence scoring, and report generation.
    """

    def __init__(self):
        self.validator = MarkValidator()
        self.complexity_estimator = ComplexityEstimator()
        self.time_estimator = TimeEstimator()

    async def analyze(
        self, question_paper: Dict[str, Any], pattern: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Analyze mark distribution and time balance."""
        raw_text = question_paper.get("raw_text", "")
        questions = question_paper.get("questions", [])
        pattern_obj = pattern if isinstance(pattern, dict) else None

        # Empty paper check
        if not questions and not raw_text:
            return {
                "criterion": "mark_distribution",
                "section": "mandatory",
                "status": "FAIL",
                "remarks": "❌ Question paper contains no readable content or questions.",
                "confidence": 0.0,
                "rule_triggered": "EMPTY_PAPER",
                "evidence": {
                    "sections": [],
                    "total_marks": 0,
                    "estimated_time_mins": 0,
                    "expected_duration_mins": 180,
                    "overall_time_status": "FAIL",
                    "issues": ["❌ Question paper contains no readable content or questions."],
                    "question_evaluations": [],
                    "failed_questions": [],
                },
                "baseline": "Expected: 100 marks, 180 minutes",
                "suggestion": "Please upload a valid question paper document.",
            }

        issues = []

        # 1. Section Arithmetic Check
        sections, arithmetic_issues = self.validator.validate_arithmetic(raw_text, pattern_obj)
        issues.extend(arithmetic_issues)

        # Determine paper total marks
        total_marks = 0
        if sections:
            total_marks = sum(s.get("total", 0) for s in sections)
        elif pattern_obj and "total_marks" in pattern_obj:
            total_marks = pattern_obj["total_marks"]
        else:
            match = re.search(r'(?:Max|Total)\s*Marks?\s*[:=]?\s*(\d+)', raw_text, re.IGNORECASE)
            total_marks = int(match.group(1)) if match else 100

        # 2. Total Marks Validation (Only 100 or 50)
        expected_duration, total_marks_issue = self.validator.validate_total_marks(total_marks, pattern_obj)
        if total_marks_issue:
            issues.append(total_marks_issue)

        # 3. Valid Question Mark Values Check (Only 2, 13, 15, 16)
        invalid_mark_issues = self.validator.validate_mark_values(sections, questions)
        issues.extend(invalid_mark_issues)

        # 4. Question Level Validation & Section Resolution
        question_evaluations = []
        failed_questions = []
        compulsory_estimated_time = 0
        choice_groups_seen: Set[str] = set()

        for i, q in enumerate(questions):
            q_text = self.validator.get_question_text(q)
            assigned = self.validator.extract_explicit_marks(q_text)

            sec, sec_certain = self.validator.resolve_question_section(i, q, raw_text, sections)

            if assigned is None:
                if sec and sec.get("marks_each"):
                    assigned = sec["marks_each"]
                else:
                    assigned = 2

            fv = self.complexity_estimator.extract_feature_vector(q, assigned)
            est_time, answer_length, tb = self.complexity_estimator.estimate_time_and_length(fv, assigned, q_text)

            eval_res = self.time_estimator.evaluate_question(
                q, assigned, total_marks, fv, est_time, answer_length, tb, sec_certain
            )
            question_evaluations.append(eval_res)

            # Compulsory vs Optional paper duration calculation
            if not fv.is_optional:
                compulsory_estimated_time += est_time
            else:
                cg = fv.choice_group or f"cg_{i}"
                if cg not in choice_groups_seen:
                    choice_groups_seen.add(cg)
                    compulsory_estimated_time += est_time

            if eval_res["status"] in ["FAIL", "UNKNOWN"]:
                failed_questions.append(eval_res)
                q_num = eval_res["question_number"]
                issues.append(f"❌ Question {q_num}: {eval_res['reason']}")

        # Calculate overall paper estimated duration
        total_estimated_time = compulsory_estimated_time if question_evaluations else self._fallback_estimate_time(sections)

        # 5. Overall Paper Time Evaluation
        time_status, time_reason, diff_pct = self.time_estimator.evaluate_overall_paper_time(
            total_estimated_time, expected_duration
        )
        if time_status != "PASS":
            prefix = "❌" if time_status == "FAIL" else "⚠️"
            issues.append(f"{prefix} Overall Exam Duration: {time_reason}")

        # Determine overall status and confidence
        has_critical_failure = (
            any("❌" in i for i in issues) or
            len(arithmetic_issues) > 0 or
            len(invalid_mark_issues) > 0 or
            total_marks_issue is not None or
            any(q["status"] in ["FAIL", "UNKNOWN"] for q in question_evaluations) or
            time_status == "FAIL"
        )

        if has_critical_failure:
            status = "FAIL"
        elif time_status == "WARNING":
            status = "WARNING"
        else:
            status = "PASS"

        avg_confidence = (
            round(sum(q.get("confidence", 1.0) for q in question_evaluations) / max(len(question_evaluations), 1), 2)
            if question_evaluations else 1.0
        )

        remarks = "; ".join(issues) if issues else "Mark distribution and time estimation are within expected limits."

        return {
            "criterion": "mark_distribution",
            "section": "mandatory",
            "status": status,
            "remarks": remarks,
            "confidence": avg_confidence,
            "rule_triggered": "MARKS_VALIDATION",
            "evidence": {
                "sections": sections,
                "total_marks": total_marks,
                "estimated_time_mins": total_estimated_time,
                "expected_duration_mins": expected_duration,
                "overall_time_status": time_status,
                "issues": issues,
                "question_evaluations": question_evaluations,
                "failed_questions": failed_questions,
            },
            "baseline": f"Expected: {total_marks} marks, {expected_duration} minutes",
            "suggestion": remarks,
        }

    def _fallback_estimate_time(self, sections: List[Dict[str, Any]]) -> int:
        """Fallback section time estimation when individual questions are unavailable."""
        total = 0.0
        for section in sections:
            marks = section.get("marks_each", 2)
            count = section.get("questions", 0)
            if marks <= 2:
                time_each = marks * 1.5
            elif marks <= 8:
                time_each = marks * 2.0
            else:
                time_each = marks * 2.5
            total += time_each * count
        return int(round(total))
