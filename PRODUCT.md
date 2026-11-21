# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are individual faculty members and course instructors at Anna University-affiliated and autonomous engineering institutions. They use ScruCheckAI while drafting, refining, and validating examination question papers to ensure 100% compliance with institutional standards prior to departmental scrutiny and submission to the Controller of Examinations (CoE).

## Product Purpose

ScruCheckAI empowers educators to author rigorous, error-free, and fully compliant examination question papers. It eliminates the friction of manual scrutiny by automating institutional format checking, mark arithmetic, Bloom's Taxonomy cognitive validation, syllabus coverage verification, and repetition detection. Beyond passive auditing, it actively assists instructors with automated remediation—suggesting clear, balanced question revisions and compliant alternatives.

## Positioning

Automated academic remediation paired with deterministic institutional compliance. Unlike generic AI chatbots or basic document linters, ScruCheckAI enforces official Anna University regulations (Regulations 2021 & 2023) and exam patterns (CAT-1, CAT-2, CAT-3, University). It detects defects—such as cognitive level disparity in OR-choice pairs, Wh-question overuse, mark imbalances, and syllabus misalignment—and directly provides ready-to-use, academically sound replacement questions.

## Operating Context

- **Academic Calendar:** Used during periodic Continuous Assessment Test (CAT) drafting cycles and end-semester university examination preparation.
- **Document Formats:** Ingests Question Papers (.pdf, .docx) and Course Syllabi (.pdf, .docx).
- **Execution Environment:** Web browser interface with both high-contrast Light mode and low-glare Dark mode for extended faculty review sessions.
- **Reporting Deliverable:** Generates tamper-evident, publication-grade, strictly PDF-only official scrutiny reports.

## Capabilities and Constraints

- **Confirmed Capabilities:**
  - Automated 10-point institutional scrutiny rubric:
    1. Institutional Header & Pattern Format Compliance
    2. Mandatory Examination Details Verification (Course Code, Subject Name, Degree/Branch, Semester, Duration, Max Marks)
    3. Syllabus Alignment & Unit Distribution
    4. Mark Distribution & Subdivision Arithmetic
    5. Bloom's Taxonomy Cognitive Level Validation (K1–K6 distribution, OR-choice cognitive parity, Wh-question avoidance)
    6. Language, Clarity, and Grammar Verification (preserving technical terms)
    7. Scientific, Mathematical, and Technical Notation Integrity
    8. Course Outcome (CO) Mapping Verification
    9. Repetition & Conceptual Overlap Detection
    10. Institutional Approval Verdict Calculation
  - Automated Remediation: Context-aware suggestions for defective questions, cognitive rebalancing for either/or pairs, and grammar corrections.
  - Hybrid Evaluation Architecture: Primary LLM with automatic fallback providers (Groq / Gemini) and offline heuristic rule engines.
- **Durable Constraints:**
  - Strictly PDF-only report export (DOCX, HTML, or Word exports are strictly prohibited).
  - Categorical compliance indicators without arbitrary percentage grading for qualitative criteria.
  - Offline resilience: System must remain fully functional with local rule-based heuristics when external cloud LLM connections fail.
- **Open / Undecided:**
  - Future LMS/ERP integrations (Canvas, Moodle) and batch departmental submission workflows.

## Brand Commitments

- **Product Name:** ScruCheckAI
- **Tagline / Subtitle:** Institutional Question Paper Scrutiny Platform • Anna University Compliance
- **Voice & Tone:** Authoritative, academic, constructive, precise, and supportive of faculty craft.
- **Visual Identity:** Clean institutional aesthetic utilizing deep teal brand grounding with vibrant amber action accents, rounded container architecture, and comprehensive light/dark operational support.

## Evidence on Hand

- Standard Anna University Question Paper patterns (`backend/patterns/cat1_patterns.json`, `cat2_patterns.json`, `cat3_patterns.json`, `university_patterns.json`).
- Production backend test suite verifying all 10 scrutiny criteria (`backend/tests/`).
- ReportLab-based PDF generation engine producing verified institutional scrutiny documents (`backend/app/services/pdf_generator.py`).

## Product Principles

1. **Remediation Over Passive Criticism:** Never just flag a defect; provide faculty with concrete, academically rigorous phrasing, cognitive rebalancing, or replacement questions.
2. **Deterministic Regulatory Integrity:** Institutional rules on marks, duration, sections, and unit balance are non-negotiable and strictly validated.
3. **Preserve Academic Lexicon:** Technical terms, scientific formulas, programming nomenclature, and domain-specific acronyms must never be misclassified as grammatical or spelling errors.
4. **Official, Unalterable Artifacts:** All scrutiny outputs destined for institutional records must ship strictly as standardized, unalterable PDF reports.

## Accessibility & Inclusion

- Adherence to WCAG 2.1 AA color contrast standards across both Light and Dark themes.
- Full keyboard accessibility with visible focus rings and accessible keyboard controls (`Enter`/`Space`) for interactive selectors.
- Redundant status cues: Every status indicator pairs color coding with explicit textual labels and icons.
