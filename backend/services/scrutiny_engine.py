"""
Scrutiny Engine
Orchestrates all 9 analysis criteria with parallel execution.
Split into two sections:
  - Section 1: Mandatory Compliance (4 criteria, PASS/FAIL)
  - Section 2: Quality Scores (5 criteria, 0-100)
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import individual analyzers
from services.analyzers.format_validator import FormatValidator
from services.analyzers.regulation_checker import RegulationChecker
from services.analyzers.syllabus_mapper import SyllabusMapper
from services.analyzers.blooms_classifier import BloomsClassifier
from services.analyzers.marks_analyzer import MarksAnalyzer
from services.analyzers.grammar_checker import GrammarChecker
from services.analyzers.diagram_checker import DiagramChecker
from services.analyzers.permitted_aids_checker import PermittedAidsChecker
from services.analyzers.repetition_detector import RepetitionDetector


class ScrutinyEngine:
    """
    Main scrutiny orchestrator.
    Runs all 9 criteria in parallel and aggregates results.
    """
    
    # Section 1: Mandatory Compliance criteria
    MANDATORY_CRITERIA = [
        "format_compliance",
        "regulation_check",
        "mark_distribution",
        "permitted_aids",
    ]
    
    # Section 2: Quality Score criteria
    QUALITY_CRITERIA = [
        "syllabus_alignment",
        "blooms_taxonomy",
        "grammar_clarity",
        "repetition_check",
        "diagrams_symbols",
    ]

    # Weights for weighted quality average (must sum to 1.0)
    # Syllabus and Bloom's carry more academic weight.
    # N/A scores are excluded and remaining weights re-normalised automatically.
    QUALITY_WEIGHTS = {
        "syllabus_alignment": 0.35,
        "blooms_taxonomy":    0.25,
        "grammar_clarity":    0.15,
        "repetition_check":   0.15,
        "diagrams_symbols":   0.10,
    }
    
    # Confidence thresholds for quality criteria
    CONFIDENCE_THRESHOLDS = {
        "blooms_taxonomy": 0.70,
        "syllabus_alignment": 0.75,
        "repetition_check": 0.80,
        "grammar_clarity": 0.85,
    }
    
    def __init__(self):
        self.format_validator = FormatValidator()
        self.regulation_checker = RegulationChecker()
        self.syllabus_mapper = SyllabusMapper()
        self.blooms_classifier = BloomsClassifier()
        self.marks_analyzer = MarksAnalyzer()
        self.grammar_checker = GrammarChecker()
        self.diagram_checker = DiagramChecker()
        self.permitted_aids_checker = PermittedAidsChecker()
        self.repetition_detector = RepetitionDetector()
    
    async def analyze(
        self,
        question_paper: Dict[str, Any],
        syllabus: Dict[str, Any],
        previous_paper: Optional[Dict[str, Any]] = None,
        pattern: Optional[str] = None,
        department: Optional[str] = None,
        regulation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run all 9 scrutiny criteria in parallel.
        Returns aggregated findings split into mandatory + quality sections.
        """
        
        # Run all analyzers in parallel using asyncio.gather
        results = await asyncio.gather(
            # Section 1: Mandatory (4)
            self._run_with_fallback("format_compliance", 
                self.format_validator.analyze, question_paper, pattern),
            self._run_with_fallback("regulation_check",
                self.regulation_checker.analyze, question_paper, regulation, department),
            self._run_with_fallback("mark_distribution",
                self.marks_analyzer.analyze, question_paper, pattern),
            self._run_with_fallback("permitted_aids",
                self.permitted_aids_checker.analyze, question_paper),
            # Section 2: Quality (5)
            self._run_with_fallback("syllabus_alignment",
                self.syllabus_mapper.analyze, question_paper, syllabus, pattern),
            self._run_with_fallback("blooms_taxonomy",
                self.blooms_classifier.analyze, question_paper, syllabus, pattern),
            self._run_with_fallback("grammar_clarity",
                self.grammar_checker.analyze, question_paper),
            self._run_with_fallback("repetition_check",
                self.repetition_detector.analyze, question_paper, previous_paper),
            self._run_with_fallback("diagrams_symbols",
                self.diagram_checker.analyze, question_paper),
            return_exceptions=True
        )
        
        # Split results into mandatory and quality
        criterion_names = [
            # Section 1
            "format_compliance", "regulation_check", "mark_distribution", "permitted_aids",
            # Section 2
            "syllabus_alignment", "blooms_taxonomy", "grammar_clarity",
            "repetition_check", "diagrams_symbols"
        ]
        
        mandatory_findings = []
        quality_findings = []
        all_findings = []  # flat list for backward compat
        mandatory_passed = 0
        
        for i, result in enumerate(results):
            criterion = criterion_names[i]
            is_mandatory = criterion in self.MANDATORY_CRITERIA
            
            if isinstance(result, Exception):
                finding = self._create_fallback_finding(criterion, str(result), is_mandatory)
            else:
                finding = result
                # Apply confidence threshold filtering for quality criteria
                if not is_mandatory:
                    finding = self._apply_confidence_threshold(criterion, finding)
            
            # Inject a sample question for adaptive improvement in frontend
            sample_question = ""
            evidence = finding.get("evidence", {})
            if "out_of_syllabus" in evidence and evidence["out_of_syllabus"]:
                sample_question = evidence["out_of_syllabus"][0].get("text", "")
            elif "issues" in evidence and evidence["issues"]:
                first_issue = evidence["issues"][0]
                if isinstance(first_issue, dict):
                    sample_question = first_issue.get("text_sample", "") or first_issue.get("issue", "")
                elif isinstance(first_issue, str):
                    sample_question = first_issue
            elif criterion == "blooms_taxonomy":
                questions = question_paper.get("questions", [])
                if questions:
                    sample_question = questions[-1].get("text", "")

            if not sample_question and question_paper.get("questions"):
                sample_question = question_paper["questions"][0].get("text", "")
                
            if "evidence" not in finding:
                finding["evidence"] = {}
            finding["evidence"]["sample_question"] = sample_question

            if is_mandatory:
                if finding["status"] == "PASS":
                    mandatory_passed += 1
                mandatory_findings.append(finding)
            else:
                quality_findings.append(finding)
            
            all_findings.append(finding)
        
        # Extract Bloom's distribution from blooms result
        blooms_idx = criterion_names.index("blooms_taxonomy")
        syllabus_idx = criterion_names.index("syllabus_alignment")
        blooms_result = results[blooms_idx] if not isinstance(results[blooms_idx], Exception) else {}
        syllabus_result = results[syllabus_idx] if not isinstance(results[syllabus_idx], Exception) else {}

        # Build a question_number -> unit mapping from syllabus result
        syllabus_mappings = syllabus_result.get("evidence", {}).get("mappings", [])
        unit_by_question = {}
        for m in syllabus_mappings:
            qnum = m.get("question_number")
            unit = m.get("detected_unit") or m.get("unit")
            if qnum is not None and unit:
                unit_by_question[qnum] = unit

        # Rebuild co_mapping using ACTUAL syllabus unit assignments
        raw_co_mapping = blooms_result.get("co_mapping", [])
        fixed_co_mapping = []
        for entry in raw_co_mapping:
            new_entry = dict(entry)
            q_no_str = entry.get("question_no", "")
            try:
                q_num = int(q_no_str.replace("Q", "").strip())
            except ValueError:
                q_num = None

            if q_num is not None and q_num in unit_by_question:
                unit_name = unit_by_question[q_num]
                try:
                    unit_num = int(unit_name.replace("Unit", "").strip())
                    new_entry["co_mapped"] = f"CO{unit_num}"
                except ValueError:
                    pass
            fixed_co_mapping.append(new_entry)

        # Calculate weighted average quality score
        # N/A (score=None) criteria are excluded; remaining weights re-normalised.
        scored_findings = [f for f in quality_findings if f.get("score") is not None]
        total_weight = sum(self.QUALITY_WEIGHTS.get(f["criterion"], 0) for f in scored_findings)
        if scored_findings and total_weight > 0:
            weighted_sum = sum(
                f["score"] * self.QUALITY_WEIGHTS.get(f["criterion"], 0)
                for f in scored_findings
            )
            avg_quality_score = round(weighted_sum / total_weight)
        else:
            avg_quality_score = 0

        # Debug logging
        print(f"📊 ScrutinyEngine: mandatory_passed = {mandatory_passed}/4")
        qs_debug = [f"{f.get('criterion')}={f.get('score', '?')} (w={self.QUALITY_WEIGHTS.get(f.get('criterion', ''), 0)})" for f in quality_findings]
        print(f"📊 ScrutinyEngine: quality_scores = {qs_debug}")
        print(f"📊 ScrutinyEngine: weighted avg_quality_score = {avg_quality_score}")

        return {
            "criteria": all_findings,
            "mandatory_findings": mandatory_findings,
            "quality_findings": quality_findings,
            "mandatory_passed": mandatory_passed,
            "mandatory_total": len(self.MANDATORY_CRITERIA),
            "quality_scores": {f["criterion"]: f.get("score", 0) for f in quality_findings},
            "quality_weights": self.QUALITY_WEIGHTS,
            "avg_quality_score": avg_quality_score,
            "blooms": blooms_result.get("distribution", self._default_blooms()),
            "syllabus_coverage": syllabus_result.get("coverage", {}),
            "co_mapping": fixed_co_mapping
        }
    
    async def _run_with_fallback(self, criterion: str, func, *args):
        """Run analyzer with timeout and fallback."""
        try:
            return await asyncio.wait_for(func(*args), timeout=30.0)
        except asyncio.TimeoutError:
            is_mandatory = criterion in self.MANDATORY_CRITERIA
            return self._create_fallback_finding(criterion, "Analysis timeout", is_mandatory)
        except Exception as e:
            print(f"❌ Analyzer {criterion} failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            is_mandatory = criterion in self.MANDATORY_CRITERIA
            return self._create_fallback_finding(criterion, str(e), is_mandatory)
    
    def _create_fallback_finding(self, criterion: str, error: str, is_mandatory: bool = False) -> Dict[str, Any]:
        """Create fallback finding when analysis fails."""
        finding = {
            "criterion": criterion,
            "section": "mandatory" if is_mandatory else "quality",
            "status": "FAIL" if is_mandatory else "NOT_EVALUATED",
            "confidence": 0.0,
            "rule_triggered": "FALLBACK",
            "evidence": {"error": error},
            "baseline": None,
            "remarks": f"Analysis unavailable: {error}. Manual review recommended.",
            "suggestion": f"⚠️ Analysis unavailable: {error}. Manual review recommended.",
            "error_message": f"⚠️ Analysis unavailable: {error}"
        }
        if not is_mandatory:
            finding["score"] = 0
        return finding
    
    def _apply_confidence_threshold(self, criterion: str, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Apply confidence thresholds for quality criteria."""
        threshold = self.CONFIDENCE_THRESHOLDS.get(criterion, 0.0)
        
        if finding.get("confidence", 1.0) < threshold:
            finding["status"] = "UNCERTAIN"
            finding["remarks"] = f"Low confidence ({finding['confidence']:.2f}). Manual review recommended."
            finding["suggestion"] = f"❓ Low confidence ({finding['confidence']:.2f}). Manual review recommended."
        
        return finding
    
    def _default_blooms(self) -> Dict[str, int]:
        """Default Bloom's distribution."""
        return {
            "Remember": 0,
            "Understand": 0,
            "Apply": 0,
            "Analyze": 0,
            "Evaluate": 0,
            "Create": 0
        }
