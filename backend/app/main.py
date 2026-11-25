import io
import logging
import re
import sys

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.blooms_taxonomy import (
    BloomsTaxonomyCheckRequest,
    BloomsTaxonomyReport,
)
from app.schemas.grammar_check import (
    GrammarCheckReport,
    GrammarCheckRequest,
)
from app.schemas.mark_distribution import (
    MarkDistributionCheckRequest,
    MarkDistributionReport,
)
from app.schemas.question_mapping import (
    BatchQuestionMappingRequest,
    ExamScopeConfig,
    SyllabusCoverageReport,
)
from app.schemas.repetition_risk import (
    RepetitionRiskCheckRequest,
    RepetitionRiskReport,
)
from app.schemas.syllabus import IngestionResponse, RetrievalResponse
from app.services.blooms_taxonomy import blooms_taxonomy_validator
from app.services.file_validator import (
    ValidatedUpload,
    file_validator,
)
from app.services.grammar_checker import grammar_checker
from app.services.llm_service import llm_service
from app.services.mark_distribution import mark_distribution_validator
from app.services.pdf_generator import generate_scrutiny_pdf
from app.services.question_parser import question_parser
from app.services.repetition_risk import repetition_risk_analyzer
from app.services.report_store import UUID_REGEX, get_report, save_report
from app.services.syllabus_mapper import syllabus_mapper
from app.services.syllabus_retriever import (
    syllabus_ingestion_service,
    syllabus_retriever,
)
from app.services.text_extractor import extractor
from app.services.vector_store import get_syllabus_vector_store
from format_compliance import FormatComplianceReport, checker, compute_unified_scrutiny_score
from regulation import RegulationCheckResult, check_regulation

# Configure root logging to output INFO to stdout so uvicorn terminal shows scrutiny logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

logger = logging.getLogger("scrucheck.api")

app = FastAPI(
    title="Institutional Question Paper Scrutiny API",
    version="0.1.0",
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
)

# 1. CORS Configuration (Strict Origins, no wildcards when credentials allowed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# 2. Security Headers Middleware (OWASP Top 10 A05: Security Misconfiguration)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce strict defensive security headers on all API responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'; object-src 'none';"
    )
    return response


# 3. Global Request Body Size Limiter Middleware
@app.middleware("http")
async def enforce_max_content_length(request: Request, call_next):
    """Reject payloads exceeding configured maximum upload ceiling before buffering."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            cl = int(content_length)
            if cl > settings.MAX_UPLOAD_SIZE_BYTES:
                max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large ({cl} bytes). Maximum allowed is {max_mb:.0f}MB."
                    },
                )
        except ValueError:
            pass
    return await call_next(request)


# 4. Global Exception Handler (OWASP Top 10 A05: Prevent Stack Trace Leaks)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Prevent unhandled system exceptions and internal tracebacks from leaking to API clients."""
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred while processing the request."},
    )


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Institutional Question Paper Scrutiny Checker",
        "docs": "/docs",
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/v1/scrutiny/patterns")
async def get_exam_patterns():
    """Return all question paper pattern categories (CAT-1, CAT-2, CAT-3, University)
    and their sub-patterns loaded from backend/patterns/.
    """
    return checker.get_pattern_categories()


@app.post("/api/v1/scrutiny/check-format", response_model=FormatComplianceReport)
async def check_question_paper_format(
    file: UploadFile = File(..., description="Question paper document (PDF or DOCX only)"),
    syllabus_file: UploadFile = File(
        ..., description="Required syllabus document (PDF or DOCX only)"
    ),
    exam_type: str | None = Form(
        None, description="Category, e.g. 'CAT-1', 'CAT-2', 'CAT-3', 'University'"
    ),
    pattern_name: str | None = Form(
        None, description="Specific pattern name, e.g. 'CAT-1 (Unit I & II) - Standard'"
    ),
    expected_regulation_year: int | None = Form(
        None, description="Optional expected regulation year, e.g. 2023"
    ),
):
    """Check uploaded question paper for strict institutional format compliance
    and pattern matching based on user-selected exam pattern. Strictly accepts ONLY PDF and DOCX.
    Requires both a question paper and a syllabus document.
    """
    if not syllabus_file or not syllabus_file.filename:
        raise HTTPException(
            status_code=422,
            detail="Both question paper and syllabus files are required to start scrutiny.",
        )

    llm_service.reset_run_log()
    validated_qp = await file_validator.validate_upload(file, is_syllabus=False)
    validated_s: ValidatedUpload = await file_validator.validate_upload(syllabus_file, is_syllabus=True)

    try:
        extraction_result = await run_in_threadpool(extractor.extract, validated_qp.temp_path)
        full_text = extraction_result.get("full_text", "")
        if not full_text.strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable text from the uploaded document.",
            )

        report = await run_in_threadpool(
            checker.check_compliance,
            full_text,
            exam_type=exam_type,
            pattern_name=pattern_name,
            expected_regulation_year=expected_regulation_year,
        )
        report.qp_filename = validated_qp.sanitized_filename

        parsed_questions = []
        try:
            parsed_questions = await run_in_threadpool(question_parser.parse_from_text, full_text)
        except Exception as e:
            logger.warning("Question parsing encountered error: %s", e)

        if validated_s and validated_s.temp_path.exists():
            s_result = await run_in_threadpool(extractor.extract, validated_s.temp_path)
            s_text = s_result.get("full_text", "")
            report.syllabus_filename = validated_s.sanitized_filename
            report.syllabus_extracted_text = s_text

            # Automatically ingest syllabus and perform Criterion 3 Syllabus Alignment (No Scores)
            try:
                course_code_header = report.header_checks.get("course_code")
                extracted_code = (
                    course_code_header.extracted_value
                    if course_code_header and course_code_header.found
                    else None
                )
                clean_s_id = re.sub(r"[^A-Za-z0-9_-]", "_", extracted_code or "uploaded_syllabus")

                # Ingest syllabus
                await syllabus_ingestion_service.ingest_file(
                    file_path=validated_s.temp_path,
                    syllabus_id=clean_s_id,
                    course_code=extracted_code,
                )

                if parsed_questions:
                    scope_config = ExamScopeConfig(
                        pattern_name=pattern_name,
                        exam_type=exam_type,
                    )
                    report.syllabus_alignment = await syllabus_mapper.map_questions_batch(
                        questions=parsed_questions,
                        syllabus_id=clean_s_id,
                        scope_config=scope_config,
                    )
            except Exception as e:
                # Log error but do not fail the overall format check
                logger.warning("Criterion 3 automatic syllabus mapping encountered error: %s", e)

        # Automatically execute Criterion 4 Mark & Time Distribution Scrutiny (Strict Zero-Score)
        try:
            if parsed_questions:
                syllabus_topics: dict[str, str] = {}
                learning_outcomes: dict[str, str] = {}
                if report.syllabus_alignment and report.syllabus_alignment.results:
                    for res in report.syllabus_alignment.results:
                        if res.matched_topic:
                            syllabus_topics[res.question_id] = res.matched_topic
                        if res.course_outcome and res.course_outcome != "CO_NOT_AVAILABLE":
                            learning_outcomes[res.question_id] = res.course_outcome

                course_context_str: str | None = None
                course_code_header = report.header_checks.get("course_code")
                if course_code_header and course_code_header.found and course_code_header.extracted_value:
                    course_context_str = course_code_header.extracted_value
                elif exam_type:
                    course_context_str = exam_type

                report.mark_distribution = await mark_distribution_validator.evaluate_paper(
                    questions=parsed_questions,
                    course_context=course_context_str,
                    syllabus_topics_by_qid=syllabus_topics,
                    learning_outcomes_by_qid=learning_outcomes,
                )
        except Exception as e:
            logger.warning("Criterion 4 Mark and Time Distribution evaluation encountered error: %s", e)

        # Automatically execute Criterion 9 Repetition Risk Scrutiny (Strict Zero-Score)
        try:
            if parsed_questions:
                report.repetition_risk = await run_in_threadpool(
                    repetition_risk_analyzer.analyze_paper,
                    current_questions=parsed_questions,
                )
        except Exception as e:
            logger.warning("Criterion 9 Repetition Risk evaluation encountered error: %s", e)

        # Automatically execute Criterion 5 Bloom's Taxonomy Scrutiny
        try:
            if parsed_questions:
                report.blooms_taxonomy = await blooms_taxonomy_validator.evaluate_paper(
                    questions=parsed_questions,
                )
        except Exception as e:
            logger.warning("Criterion 5 Bloom's Taxonomy evaluation encountered error: %s", e)

        # Automatically execute Criterion 6 Grammar, Spelling and Sentence Formation Scrutiny
        try:
            if parsed_questions:
                course_ctx: str | None = None
                course_code_hdr = report.header_checks.get("course_code")
                if course_code_hdr and course_code_hdr.found and course_code_hdr.extracted_value:
                    course_ctx = course_code_hdr.extracted_value
                elif exam_type:
                    course_ctx = exam_type

                report.grammar_check = await grammar_checker.scrutinize_paper(
                    questions=parsed_questions,
                    course_context=course_ctx,
                )
        except Exception as e:
            logger.warning("Criterion 6 Grammar Scrutiny encountered error: %s", e)

        # Compute unified 7-criteria weighted compliance score
        unified_score, score_breakdown = compute_unified_scrutiny_score(report)
        report.compliance_score = unified_score
        report.score_breakdown = score_breakdown

        # Record delivering LLM provider summary and display terminal report
        llm_summary = llm_service.get_run_summary()
        report.llm_provider_used = llm_summary.get("summary_label", "Local Rule-Based Fallback")
        llm_service.print_final_summary()

        await run_in_threadpool(save_report, report)
        return report
    finally:
        validated_qp.cleanup()
        if validated_s:
            validated_s.cleanup()


@app.post("/api/v1/scrutiny/extract-syllabus")
async def extract_syllabus_text(
    file: UploadFile = File(..., description="Syllabus file (PDF or DOCX only)"),
):
    """Extract and return text from an uploaded syllabus document. Strictly accepts PDF and DOCX."""
    validated = await file_validator.validate_upload(file, is_syllabus=True)
    try:
        extraction_result = await run_in_threadpool(extractor.extract, validated.temp_path)
        full_text = extraction_result.get("full_text", "")
        return {
            "filename": validated.sanitized_filename,
            "char_count": len(full_text),
            "line_count": len(full_text.splitlines()) if full_text else 0,
            "extracted_text": full_text,
        }
    finally:
        validated.cleanup()


@app.post("/api/v1/scrutiny/check-regulation", response_model=RegulationCheckResult)
async def check_question_paper_regulation(
    file: UploadFile = File(..., description="Question paper file (PDF or DOCX only)"),
    expected_year: int | None = Form(
        None, description="Optional expected regulation year, e.g. 2023"
    ),
):
    """Check if uploaded question paper has a regulation code like [Regulations 2023].
    Returns ACCEPTED if found, REJECTED if missing. Strictly accepts PDF and DOCX.
    """
    validated = await file_validator.validate_upload(file, is_syllabus=False)
    try:
        extraction_result = await run_in_threadpool(extractor.extract, validated.temp_path)
        full_text = extraction_result.get("full_text", "")
        return await run_in_threadpool(check_regulation, full_text, expected_year=expected_year)
    finally:
        validated.cleanup()


# ============================================================================
# Criterion 3 Phase 1: Syllabus Ingestion & Semantic Retrieval Endpoints
# ============================================================================


@app.post("/api/v1/syllabus/ingest", response_model=IngestionResponse)
async def ingest_syllabus_endpoint(
    file: UploadFile = File(..., description="Syllabus file (PDF or DOCX only)"),
    syllabus_id: str | None = Form(None, description="Optional custom syllabus identifier"),
    course_code: str | None = Form(None, description="Optional course code e.g. CS3351"),
    course_title: str | None = Form(None, description="Optional course title"),
):
    """Parse syllabus, extract unit/topic/subtopic/CO structures, compute embeddings,
    and persistently index records into vector store. Strictly accepts PDF and DOCX.
    """
    if syllabus_id and not re.match(r"^[a-zA-Z0-9_\-]+$", syllabus_id.strip()):
        raise HTTPException(
            status_code=400,
            detail="Invalid syllabus_id: must contain only alphanumeric characters, underscores, and hyphens.",
        )

    validated = await file_validator.validate_upload(file, is_syllabus=True)
    try:
        result = await syllabus_ingestion_service.ingest_file(
            file_path=validated.temp_path,
            syllabus_id=syllabus_id.strip() if syllabus_id else None,
            course_code=course_code,
            course_title=course_title,
        )
        return result
    finally:
        validated.cleanup()


@app.get("/api/v1/syllabus/retrieve", response_model=RetrievalResponse)
async def retrieve_syllabus_topics_endpoint(
    query: str,
    top_k: int = 5,
    syllabus_id: str | None = None,
    unit_number: int | None = None,
):
    """Retrieve top candidate topics (default top 5) with similarity scores and metadata
    for a given query text.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
    if top_k < 1 or top_k > 20:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 20.")
    if syllabus_id and not re.match(r"^[a-zA-Z0-9_\-]+$", syllabus_id.strip()):
        raise HTTPException(
            status_code=400,
            detail="Invalid syllabus_id: must contain only alphanumeric characters, underscores, and hyphens.",
        )

    return await syllabus_retriever.retrieve_top_topics(
        query=query,
        top_k=top_k,
        syllabus_id=syllabus_id.strip() if syllabus_id else None,
        unit_number=unit_number,
    )


@app.delete("/api/v1/syllabus/{syllabus_id}")
async def delete_syllabus_index_endpoint(syllabus_id: str):
    """Delete all indexed topics for a syllabus ID to ensure clean re-ingestion repeatability."""
    cleaned_id = syllabus_id.strip()
    if not re.match(r"^[a-zA-Z0-9_\-]+$", cleaned_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid syllabus_id: must contain only alphanumeric characters, underscores, and hyphens.",
        )

    store = get_syllabus_vector_store()
    deleted_count = await store.delete_syllabus(cleaned_id)
    return {
        "status": "success",
        "syllabus_id": cleaned_id,
        "deleted_records": deleted_count,
    }


@app.post("/api/v1/syllabus/map-questions", response_model=SyllabusCoverageReport)
async def map_questions_endpoint(request: BatchQuestionMappingRequest):
    """Batch map examination questions against an ingested syllabus,
    determine scope compliance, compute coverage %, and evaluate human-review gates.
    """
    if not request.syllabus_id or not request.syllabus_id.strip():
        raise HTTPException(status_code=400, detail="syllabus_id cannot be empty.")

    cleaned_id = request.syllabus_id.strip()
    if not re.match(r"^[a-zA-Z0-9_\-]+$", cleaned_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid syllabus_id: must contain only alphanumeric characters, underscores, and hyphens.",
        )

    report = await syllabus_mapper.map_questions_batch(
        questions=request.questions,
        syllabus_id=cleaned_id,
        scope_config=request.scope_config,
    )
    return report


@app.post("/api/v1/scrutiny/check-mark-distribution", response_model=MarkDistributionReport)
async def check_mark_distribution_endpoint(request: MarkDistributionCheckRequest):
    """Scrutinize examination questions for Criterion 4: Mark and Time Distribution.
    Uses LLM API for Part A 2-mark question cognitive depth and complexity assessment.
    Uses deterministic Python rules for Part B/C 2-mark misplacement and subdivision limits (<= 2 PASS, > 2 FLAG)
    with independent evaluation of OR choices.
    """
    llm_service.reset_run_log()
    rep = await mark_distribution_validator.evaluate_paper(
        questions=request.questions,
        course_context=request.course_context,
    )
    llm_service.print_final_summary()
    return rep


@app.post("/api/v1/scrutiny/check-repetition-risk", response_model=RepetitionRiskReport)
async def check_repetition_risk_endpoint(request: RepetitionRiskCheckRequest):
    """Scrutinize examination questions for Criterion 9: Repetition Risk.
    Identifies duplicate or substantially similar questions within the current paper
    and, when provided, across previous-year examination papers.
    Strict Zero-Score: returns purely categorical status with no numerical scores.
    """
    if not request.questions:
        raise HTTPException(
            status_code=400,
            detail="The 'questions' list cannot be empty. Please provide parsed examination questions.",
        )
    return await run_in_threadpool(
        repetition_risk_analyzer.analyze_paper,
        current_questions=request.questions,
    )


@app.post("/api/v1/scrutiny/check-blooms-taxonomy", response_model=BloomsTaxonomyReport)
async def check_blooms_taxonomy_endpoint(request: BloomsTaxonomyCheckRequest):
    """Scrutinize examination questions for Criterion 5: Bloom's Taxonomy.
    Enforces:
    1. Declared BT level (A1/A2/B1/B2/C1/C2) mentioned against each question & verified.
    2. Knowledge level parity between 'either' and 'or' choices.
    3. Avoidance of open-ended Wh-questions (What, When, Where, Who, Why, Which).
    4. UG distribution targets (Category A: 50%, Category B: 30-35%, Category C: remaining).
    Strict Zero-Score policy: returns purely categorical status with no numerical scores.
    """
    if not request.questions:
        raise HTTPException(
            status_code=400,
            detail="The 'questions' list cannot be empty. Please provide parsed examination questions.",
        )
    return await blooms_taxonomy_validator.evaluate_paper(
        questions=request.questions,
    )


@app.post("/api/v1/scrutiny/check-grammar", response_model=GrammarCheckReport)
async def check_grammar_endpoint(request: GrammarCheckRequest):
    """Scrutinize examination questions for Criterion 6: Grammar, Spelling, and Sentence Formation.
    Uses LLM semantic and linguistic analysis to detect spelling mistakes, grammatical errors,
    sentence construction defects, punctuation errors, clarity issues, ambiguity, and incomplete sentences.
    Preserves academic and technical terminology (e.g. Big-O, NP-Complete, LIFO).
    Strict Zero-Score policy: returns purely categorical status with no numerical scores.
    """
    if not request.questions:
        raise HTTPException(
            status_code=400,
            detail="The 'questions' list cannot be empty. Please provide parsed examination questions.",
        )
    llm_service.reset_run_log()
    validated_questions = question_parser.parse_from_list(request.questions)
    rep = await grammar_checker.scrutinize_paper(
        questions=validated_questions,
        course_context=request.course_context,
    )
    llm_service.print_final_summary()
    return rep


# ---------------------------------------------------------------------------
# PDF Report Download Endpoints (Strictly PDF-Only)
# ---------------------------------------------------------------------------


async def _build_pdf_download_response(report: FormatComplianceReport) -> StreamingResponse:
    """Helper to generate PDF bytes and return a streaming response with proper headers."""
    try:
        pdf_bytes = await run_in_threadpool(generate_scrutiny_pdf, report)
    except Exception as e:
        logger.error("Failed to generate PDF for report %s: %s", report.report_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the scrutiny PDF report.",
        ) from e

    # Clean Subject Code & Exam Type for Content-Disposition filename
    subject_item = report.exam_details.items.get("subject_code") if (report.exam_details and getattr(report.exam_details, "items", None)) else None
    subject_code = (
        getattr(subject_item, "extracted_value", None)
        if subject_item
        else getattr(report.header_checks.get("course_code"), "extracted_value", None)
        if (report.header_checks and "course_code" in report.header_checks and getattr(report.header_checks["course_code"], "found", False))
        else "Course"
    )
    clean_subj = re.sub(r"[^A-Za-z0-9_-]", "_", str(subject_code or "Course")).strip("_")
    clean_exam = re.sub(r"[^A-Za-z0-9_-]", "_", str(report.selected_category or "Exam")).strip("_")
    filename = f"ScruCheck_AI_{clean_subj}_{clean_exam}_Scrutiny_Report.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/api/v1/reports/{report_id}/download")
async def download_scrutiny_report_pdf(report_id: str):
    """Retrieve completed scrutiny results by report_id and download a formatted PDF.

    Strict requirement: PDF is the ONLY supported format.
    """
    if not UUID_REGEX.match(report_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid report ID format. Must be a valid UUID.",
        )

    report = await run_in_threadpool(get_report, report_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Scrutiny report '{report_id}' was not found or has expired.",
        )

    return await _build_pdf_download_response(report)


@app.post("/api/v1/reports/download-pdf")
async def download_scrutiny_report_pdf_from_payload(report: FormatComplianceReport):
    """Generate and download a PDF scrutiny report directly from a report payload.

    Provides fallback support if in-memory cache was cycled.
    Strict requirement: PDF is the ONLY supported format.
    """
    await run_in_threadpool(save_report, report)
    return await _build_pdf_download_response(report)
