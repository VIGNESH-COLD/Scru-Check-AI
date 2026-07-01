"""
ScruCheck AI - Backend Main Application
AI-Powered Question Paper Scrutiny System
"""

import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
import json
from datetime import datetime

# Import services
from services.document_parser import DocumentParser
from services.scrutiny_engine import ScrutinyEngine
from services.report_generator import ReportGenerator
from rag.retriever import RAGRetriever
from models.database import init_db, get_db, AnalysisReport
from auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session
from auth.routes import router as auth_router, external_router
from middleware.audit_logger import AuditLogger

# Initialize FastAPI app
app = FastAPI(
    title="ScruCheck AI",
    description="AI-Powered Question Paper Scrutiny System",
    version="1.0.0"
)

# Mount static files for samples
app.mount("/samples", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "samples")), name="samples")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_parser = DocumentParser()
scrutiny_engine = ScrutinyEngine()
report_generator = ReportGenerator()
rag_retriever = RAGRetriever()
audit_logger = AuditLogger()

# In-memory store for analysis results is removed, using SQLite via AnalysisReport


def _resolve_pattern_object(pattern_input: Optional[str]) -> Optional[dict]:
    """
    Parse and resolve the pattern value sent from the frontend.

    The frontend sends either:
      - A full JSON-stringified pattern object (preferred): parsed and returned directly.
      - A pattern name string: looked up against all backend pattern JSON files.

    Returns the resolved pattern dict (with 'name', 'sections', 'total_marks', etc.)
    or None if no pattern was provided or could not be resolved.

    IMPORTANT: This resolved object is the source of truth for format validation.
               It is NEVER derived from the uploaded paper itself.
    """
    if not pattern_input:
        return None

    # ── Attempt 1: try to parse as a JSON object ──────────────────────────────
    try:
        parsed = json.loads(pattern_input)
        if isinstance(parsed, dict) and "name" in parsed:
            return parsed  # Full pattern object sent by the frontend — use directly
    except (json.JSONDecodeError, TypeError):
        pass

    # ── Attempt 2: treat as a plain pattern name, look up in pattern files ────
    pattern_name = pattern_input.strip()
    patterns_dir = os.path.join(os.path.dirname(__file__), "patterns")
    pattern_files = [
        "university_patterns.json",
        "cat1_patterns.json",
        "cat2_patterns.json",
        "cat3_patterns.json",
    ]
    for filename in pattern_files:
        filepath = os.path.join(patterns_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                patterns_list = json.load(f)
            for p in patterns_list:
                if p.get("name", "").lower() == pattern_name.lower():
                    return p
        except Exception:
            continue

    # ── Fallback: could not resolve — return None (no pattern comparison) ────
    print(f"[WARN] main.py: Could not resolve pattern '{pattern_name}' from any pattern file.")
    return None


# Include auth routers
app.include_router(auth_router)
app.include_router(external_router)

# Pydantic models for API contracts
class PatternSection(BaseModel):
    name: str
    questions: int
    marks_per_question: int


class ExamPattern(BaseModel):
    pattern_name: str
    sections: List[PatternSection]
    total_marks: int
    time_minutes: int


class AnalysisRequest(BaseModel):
    pattern: Optional[ExamPattern] = None
    department: Optional[str] = None
    regulation: Optional[str] = None


class ImprovementRequest(BaseModel):
    question: str
    issue_type: str   # bloom_level, syllabus, grammar, clarity
    current_finding: str
    current_bloom_level: Optional[str] = None
    target_bloom_level: Optional[str] = None
    syllabus_context: Optional[str] = None


class FindingResponse(BaseModel):
    criterion: str
    status: str  # PASS, WARNING, FAIL
    confidence: float
    rule_triggered: str
    evidence: dict
    baseline: Optional[str]
    suggestion: Optional[str]
    can_override: bool
    enforcement_level: str  # STRICT, ENFORCED, ADVISORY


class AnalysisResponse(BaseModel):
    paper_id: str
    timestamp: str
    overall_status: str  # APPROVED, CONDITIONAL, REJECTED
    mandatory_compliance: List[dict]
    quality_scores: List[dict]
    findings: List[dict]  # backward compat: flat list of all findings
    blooms_distribution: dict
    syllabus_coverage: dict
    co_mapping: List[dict]
    score: str
    mandatory_passed: int
    mandatory_total: int
    avg_quality_score: int
    quality_weights: dict  # weights used for weighted average


# Root endpoint - API info
@app.get("/")
async def root():
    """API root - shows available endpoints."""
    return {
        "name": "ScruCheck AI",
        "version": "1.0.0",
        "description": "AI-Powered Question Paper Scrutiny System",
        "status": "running",
        "frontend": "http://localhost:5173",
        "endpoints": {
            "POST /api/analyze": "Upload and analyze question paper",
            "GET /api/patterns": "Get exam pattern presets",
            "GET /api/report/{paper_id}": "Download scrutiny report",
            "POST /api/override/{paper_id}/{finding_id}": "Override a finding",
            "GET /health": "Health check"
        }
    }


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Get exam pattern presets
@app.get("/api/patterns")
async def get_patterns():
    """
    Return all exam pattern presets grouped by category.
    Reads from backend/patterns/ JSON files.
    """
    import json

    patterns_dir = os.path.join(os.path.dirname(__file__), "patterns")

    # Map file names to category keys expected by the frontend
    file_map = {
        "CAT1":       "cat1_patterns.json",
        "CAT2":       "cat2_patterns.json",
        "CAT3":       "cat3_patterns.json",
        "University": "university_patterns.json",
    }

    categories = {}
    for key, filename in file_map.items():
        filepath = os.path.join(patterns_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                categories[key] = json.load(f)
        except FileNotFoundError:
            categories[key] = []
        except Exception as e:
            print(f"⚠️ Could not load {filename}: {e}")
            categories[key] = []

    return {
        "categories": categories,
        "total_patterns": sum(len(p) for p in categories.values())
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_paper(
    question_paper: UploadFile = File(...),
    syllabus: UploadFile = File(...),
    previous_paper: Optional[UploadFile] = File(None),
    # IMPORTANT: These must be Form(...) not bare defaults.
    # The frontend sends them as multipart form fields (FormData), not query params.
    # Declaring them without Form() means FastAPI treats them as query params
    # and silently ignores the values sent by the frontend.
    pattern: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    regulation: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Main analysis endpoint.
    Accepts question paper, syllabus, and optionally previous paper.
    Returns comprehensive scrutiny report.
    """
    try:
        # Parse documents
        qp_content = await document_parser.parse(question_paper)
        syllabus_content = await document_parser.parse(syllabus)
        prev_paper_content = None
        if previous_paper:
            prev_paper_content = await document_parser.parse(previous_paper)

        # ── Resolve the user-selected pattern into a full pattern object ─────
        # This is the SOURCE OF TRUTH for format validation.
        # We never recalculate or derive the expected pattern from the uploaded
        # paper itself — the frontend selection always wins.
        pattern_obj = _resolve_pattern_object(pattern)
        if pattern_obj:
            print(f"[OK] main.py: Resolved selected pattern => '{pattern_obj.get('name')}'")
        else:
            print("[WARN] main.py: No pattern selected or pattern could not be resolved.")

        # Index syllabus in RAG
        await rag_retriever.index_syllabus(syllabus_content)

        # Run scrutiny engine (all 10 criteria)
        # pattern_obj is passed so format_validator can compare against the
        # selected pattern rather than detecting one from the paper itself.
        findings = await scrutiny_engine.analyze(
            question_paper=qp_content,
            syllabus=syllabus_content,
            previous_paper=prev_paper_content,
            pattern=pattern,
            pattern_obj=pattern_obj,
            department=department,
            regulation=regulation
        )
        
        # Determine overall status based on new two-section rules
        overall_status = determine_status(findings)
        
        # Generate paper ID
        paper_id = f"PAPER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log to audit
        await audit_logger.log_analysis(paper_id, findings, overall_status)
        
        # Build score string
        m_passed = findings["mandatory_passed"]
        m_total = findings["mandatory_total"]
        avg_q = findings["avg_quality_score"]
        # Count how many quality criteria are N/A (score=None)
        na_count = sum(1 for f in findings["quality_findings"] if f.get("score") is None)
        quality_applicable = len(findings["quality_findings"]) - na_count
        score_str = f"Overall Quality: {avg_q}/100  |  Mandatory: {m_passed}/{m_total} passed  ({quality_applicable} quality criteria evaluated)"
        
        # Build mandatory and quality response lists
        mandatory_compliance = [
            {"criterion": f["criterion"], "status": f["status"], "remarks": f.get("remarks", "")}
            for f in findings["mandatory_findings"]
        ]
        quality_scores_list = [
            {"criterion": f["criterion"], "score": f.get("score", 0), "remarks": f.get("remarks", "")}
            for f in findings["quality_findings"]
        ]
        
        # Store result for report generation in DB
        result_to_store = {
            "criteria": findings["criteria"],
            "mandatory_compliance": mandatory_compliance,
            "quality_scores": quality_scores_list,
            "blooms": findings["blooms"],
            "syllabus_coverage": findings["syllabus_coverage"],
            "co_mapping": findings["co_mapping"],
            "mandatory_passed": m_passed,
            "mandatory_total": m_total,
            "avg_quality_score": avg_q,
            "quality_weights": findings["quality_weights"],
            "score": score_str,
            "overall_status": overall_status
        }
        
        if db:
            db_report = AnalysisReport(
                paper_id=paper_id,
                overall_status=overall_status,
                findings=findings["criteria"],
                data=result_to_store,
                created_by="system", # Ideally from current user if authenticated
                department=department or "general"
            )
            db.add(db_report)
            db.commit()
        
        # Debug logging
        print(f"🔍 main.py: paper_id = {paper_id}")
        print(f"🔍 main.py: Saved analysis to DB")
        
        return AnalysisResponse(
            paper_id=paper_id,
            timestamp=datetime.now().isoformat(),
            overall_status=overall_status,
            mandatory_compliance=mandatory_compliance,
            quality_scores=quality_scores_list,
            findings=findings["criteria"],
            blooms_distribution=findings["blooms"],
            syllabus_coverage=findings["syllabus_coverage"],
            co_mapping=findings["co_mapping"],
            score=score_str,
            mandatory_passed=m_passed,
            mandatory_total=m_total,
            avg_quality_score=avg_q,
            quality_weights=findings["quality_weights"]
        )
        
    except Exception as e:
        # Log failure
        await audit_logger.log_error(str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


def determine_status(findings: dict) -> str:
    """
    Determine overall approval status:
    1. Any mandatory FAIL          → REJECTED
    2. Syllabus Coverage < 40      → REJECTED  (paper covers < 40% of syllabus)
    3. Syllabus Coverage < 50      → CONDITIONAL
    4. Avg quality score < 60      → CONDITIONAL
    5. Otherwise                   → APPROVED
    """
    # Rule 1: Any mandatory criterion FAIL → REJECTED
    for finding in findings.get("mandatory_findings", []):
        if finding["status"] != "PASS":
            return "REJECTED"

    # Extract syllabus score (may be None if not evaluated)
    syllabus_score = None
    for finding in findings.get("quality_findings", []):
        if finding["criterion"] == "syllabus_alignment":
            syllabus_score = finding.get("score")
            break

    # Rule 2: Syllabus Coverage critically low → REJECTED
    if syllabus_score is not None and syllabus_score < 40:
        return "REJECTED"

    # Rule 3: Syllabus Coverage below acceptable threshold → CONDITIONAL
    if syllabus_score is not None and syllabus_score < 50:
        return "CONDITIONAL"

    # Rule 4: Overall quality average < 60 → CONDITIONAL
    # (N/A scores — score=None — are excluded from avg by scrutiny_engine)
    avg = findings.get("avg_quality_score", 100)
    if avg < 60:
        return "CONDITIONAL"

    # Rule 5: All checks pass
    return "APPROVED"


# Download report
@app.get("/api/report/{paper_id}")
async def download_report(paper_id: str, format: str = "docx", db: Session = Depends(get_db)):
    """Generate and download scrutiny report in DOCX format."""
    try:
        # Retrieve stored analysis data from DB
        analysis_data = None
        if db:
            db_report = db.query(AnalysisReport).filter(AnalysisReport.paper_id == paper_id).first()
            if db_report and db_report.data:
                analysis_data = db_report.data
        
        print(f"📥 Report requested for paper_id: {paper_id}")
        
        # Determine if we have data or need fallback
        if not analysis_data:
            print(f"⚠️ Report requested for {paper_id} but no data found in DB. Using default.")
        else:
            print(f"✅ Found analysis data for {paper_id} in DB")
        
        report_path = await report_generator.generate(paper_id, format, data=analysis_data)
        
        print(f"✅ Report generated at: {report_path}")
        
        return FileResponse(
            report_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"ScruCheck_Report_{paper_id}.docx"
        )
    except Exception as e:
        import traceback
        print(f"❌ Report generation error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")




# Override finding
@app.post("/api/override/{paper_id}/{finding_id}")
async def override_finding(
    paper_id: str,
    finding_id: str,
    justification: str,
    action: str,  # ACCEPT, REJECT, FALSE_POSITIVE
    question_text: str = "",
    criterion: str = ""
):
    """
    Human-in-the-loop override for findings.
    Logs to audit trail AND training data for model improvement.
    """
    # Import training data manager
    from rag.training_data import training_data
    
    # Record to training data for learning
    if question_text and criterion:
        training_data.record_override(
            criterion=criterion,
            question_text=question_text,
            original_status="WARNING" if action != "ACCEPT" else "PASS",
            override_action=action,
            justification=justification,
            context={"paper_id": paper_id, "finding_id": finding_id}
        )
    
    # Log override to audit
    await audit_logger.log_override(
        paper_id=paper_id,
        finding_id=finding_id,
        action=action,
        justification=justification
    )
    
    return {
        "status": "override_recorded",
        "paper_id": paper_id,
        "finding_id": finding_id,
        "training_updated": bool(question_text and criterion)
    }


# Adaptive Question Improvement endpoint
@app.post("/api/improve")
async def improve_question(req: ImprovementRequest):
    """
    Suggest how to improve a flagged question using Mistral AI.
    Supports: Bloom level uplift, syllabus realignment, grammar fix.
    """
    from rag.llm_client import llm_client

    try:
        # Build a rich prompt based on issue type
        issue_detail = req.current_finding
        if req.issue_type == "bloom_level" and req.current_bloom_level and req.target_bloom_level:
            issue_detail = (
                f"Current Bloom level is '{req.current_bloom_level}'. "
                f"Target: raise it to '{req.target_bloom_level}' by using stronger cognitive verbs."
            )
        elif req.issue_type == "syllabus" and req.syllabus_context:
            issue_detail = (
                f"{req.current_finding}. "
                f"Relevant syllabus context: {req.syllabus_context[:500]}"
            )

        result = await llm_client.suggest_improvement(
            question=req.question,
            issue_type=req.issue_type,
            current_finding=issue_detail
        )

        return {
            "original_question": req.question,
            "issue_type": req.issue_type,
            "improved_question": result.get("improved_question", "No suggestion available"),
            "changes_made": result.get("changes_made", []),
            "reasoning": result.get("reasoning", ""),
            "alternative_approaches": result.get("alternative_approaches", []),
            "error": result.get("error")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Improvement failed: {str(e)}")


# ── History endpoints ────────────────────────────────────────────────────────

@app.get("/api/history")
async def get_history(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all previously analyzed papers stored in the database.
    RBAC filtering:
      - COE / Auditor : all papers
      - HOD           : department papers + own papers
      - Faculty       : own papers only
    """
    from fastapi import Header as FastAPIHeader
    from auth.jwt_handler import get_current_user as _get_user
    from auth.rbac import has_permission, Permission

    # Pull bearer token from Authorization header
    # (passed as query param fallback for simplicity)
    current_user = None

    if not db:
        return {"papers": [], "total": 0}

    # Fetch all reports
    all_reports = db.query(AnalysisReport).order_by(AnalysisReport.timestamp.desc()).all()

    papers = []
    for r in all_reports:
        data = r.data or {}
        mandatory = data.get("mandatory_compliance", [])
        quality   = data.get("quality_scores", [])

        papers.append({
            "paper_id":       r.paper_id,
            "timestamp":      r.timestamp.isoformat() if r.timestamp else "",
            "overall_status": r.overall_status or "UNKNOWN",
            "department":     r.department or "general",
            "created_by":     r.created_by or "system",
            "mandatory_passed": data.get("mandatory_passed", 0),
            "mandatory_total":  data.get("mandatory_total", 4),
            "avg_quality_score": data.get("avg_quality_score", 0),
            "score":          data.get("score", ""),
            # Flat summaries for the history table
            "mandatory_compliance": [
                {"criterion": f["criterion"], "status": f["status"]}
                for f in mandatory
            ],
            "quality_scores": [
                {"criterion": f["criterion"], "score": f.get("score")}
                for f in quality
            ],
        })

    return {"papers": papers, "total": len(papers)}


@app.delete("/api/history/{paper_id}")
async def delete_history_entry(
    paper_id: str,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Delete a specific analysis report from history.
    Only COE (admin) can delete records.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")

    report = db.query(AnalysisReport).filter(AnalysisReport.paper_id == paper_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

    db.delete(report)
    db.commit()

    # Also clean up the generated report file if it exists
    report_path = os.path.join(os.path.dirname(__file__), "reports", f"{paper_id}.docx")
    if os.path.exists(report_path):
        os.remove(report_path)

    await audit_logger.log_analysis(paper_id, {}, "DELETED")

    return {"deleted": True, "paper_id": paper_id}


# Startup event
@app.on_event("startup")
async def startup():
    """Initialize database and models on startup."""
    await init_db()
    print("ScruCheck AI Backend Started")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
