"""
Diagram & Symbol Checker
Two-branch scoring logic:
  - Branch A (images present):  Evaluate embedded diagram/image visibility → 100 or 0
  - Branch B (no images):       Evaluate symbol rendering/clarity in text  → 100 or 0
"""

import re
from typing import Dict, Any, List


# Symbols that should render correctly in exam papers
SYMBOL_PATTERNS = [
    # Mathematical operators
    (r'[≤≥≠≈∞∑∏∫∂√±×÷]', 'mathematical operator'),
    # Greek letters (common in science/engineering)
    (r'[αβγδεζηθλμνξπρστφψω]', 'Greek letter (lowercase)'),
    (r'[ΑΒΓΔΕΖΗΘΛΜΝΞΠΡΣΤΦΨΩ]', 'Greek letter (uppercase)'),
    # Logic / set symbols
    (r'[∀∃∈∉⊂⊃∪∩¬∧∨⊕]', 'logic/set symbol'),
    # Arrows
    (r'[←→↑↓↔⇒⇔]', 'arrow symbol'),
    # Encoding anomalies (replacement characters that indicate broken rendering)
    (r'[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]', 'broken/unrendered character'),
]

# Common broken-render indicators in extracted text
BROKEN_SYMBOL_INDICATORS = [
    r'\?\?+',           # ?? or ??? where a symbol should be
    r'□+',              # □□ placeholder boxes
    r'\[image\]',       # [image] inline substitution
    r'\[formula\]',     # [formula] substitution
    r'#+\s*ERROR',      # #ERROR from spreadsheet exports
    r'\ufffd+',         # Unicode replacement character
]


class DiagramChecker:
    """
    Checks diagram and symbol usage.
    ADVISORY.
    """

    async def analyze(self, question_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Two-branch diagram/symbol analysis.

        Branch A – Paper has embedded images:
            Score 100 if all images are valid and visible, else 0.

        Branch B – Paper has no embedded images:
            Score 100 if no broken-symbol indicators found, else 0.
        """
        raw_text = question_paper.get("raw_text", "")
        image_info: Dict[str, Any] = question_paper.get("image_info", {})

        has_images = image_info.get("has_images", False)

        if has_images:
            return self._evaluate_image_quality(image_info, raw_text)
        else:
            # Check if the paper has any technical symbols worth evaluating
            has_symbols = any(re.search(pat, raw_text) for pat, _ in SYMBOL_PATTERNS[:-1])
            if has_symbols:
                return self._evaluate_symbol_visibility(raw_text)
            else:
                # No images AND no special symbols — truly N/A, exclude from averaging
                return {
                    "criterion": "diagrams_symbols",
                    "section": "quality",
                    "status": "PASS",
                    "score": None,   # N/A — excluded from quality average
                    "remarks": "N/A — No diagrams or technical symbols detected in this paper.",
                    "confidence": 1.0,
                    "rule_triggered": "NO_DIAGRAMS_OR_SYMBOLS",
                    "evidence": {"mode": "not_applicable", "has_images": False, "has_symbols": False},
                    "baseline": "N/A",
                    "suggestion": "No diagram or symbol evaluation required for this paper.",
                }

    # ──────────────────────────────────────────────
    # Branch A: Image quality evaluation
    # ──────────────────────────────────────────────
    def _evaluate_image_quality(
        self, image_info: Dict[str, Any], raw_text: str
    ) -> Dict[str, Any]:
        """Score 100 if all embedded images are valid; 0 if any are broken/missing."""
        total = image_info.get("image_count", 0) + image_info.get("broken_images", 0)
        broken = image_info.get("broken_images", 0)
        valid = image_info.get("image_count", 0)

        issues: List[str] = []
        if broken > 0:
            issues.append(
                f"{broken} embedded image(s) are broken or have zero dimensions "
                f"and may not render correctly in the exam paper."
            )

        # Also check for figure references that have no corresponding embedded image
        fig_refs = re.findall(r'Fig(?:ure)?\.?\s*\d+', raw_text, re.IGNORECASE)
        if fig_refs and valid == 0:
            issues.append(
                f"{len(fig_refs)} figure reference(s) found in text but no valid "
                f"images detected — figures may be missing."
            )

        score = 100 if not issues else 0
        status = "PASS" if score == 100 else "WARNING"

        remarks = (
            "; ".join(issues) if issues
            else f"All {valid} embedded image(s) are properly rendered and clearly visible. ✅"
        )

        return {
            "criterion": "diagrams_symbols",
            "section": "quality",
            "status": status,
            "score": score,
            "remarks": f"Score: {score}/100. {'Issues detected with embedded images.' if issues else 'All images clear and visible.'}",
            "confidence": 0.9,
            "rule_triggered": "IMAGE_QUALITY_CHECK",
            "evidence": {
                "mode": "image_quality",
                "total_images_detected": total,
                "valid_images": valid,
                "broken_images": broken,
                "figure_references_in_text": fig_refs,
                "issues": issues,
            },
            "baseline": "All embedded diagrams/images must be clearly visible and properly embedded.",
            "suggestion": remarks,
        }

    # ──────────────────────────────────────────────
    # Branch B: Symbol visibility evaluation
    # ──────────────────────────────────────────────
    def _evaluate_symbol_visibility(self, raw_text: str) -> Dict[str, Any]:
        """Score 100 if all symbols render cleanly; 0 if broken indicators detected."""
        issues: List[str] = []
        broken_found: List[str] = []

        # Check for broken-render indicators
        for pattern in BROKEN_SYMBOL_INDICATORS:
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            if matches:
                broken_found.extend(matches[:3])   # show up to 3 examples
                issues.append(
                    f"Broken rendering pattern '{pattern}' detected "
                    f"({len(matches)} occurrence(s))."
                )

        # Detect valid special symbols present (for reporting)
        valid_symbols_found: List[str] = []
        for pattern, label in SYMBOL_PATTERNS[:-1]:  # exclude the broken-char pattern
            if re.search(pattern, raw_text):
                valid_symbols_found.append(label)

        score = 100 if not issues else 0
        status = "PASS" if score == 100 else "WARNING"

        remarks = (
            "; ".join(issues) if issues
            else "No broken symbol indicators detected. All mathematical and technical symbols appear to render correctly. ✅"
        )

        return {
            "criterion": "diagrams_symbols",
            "section": "quality",
            "status": status,
            "score": score,
            "remarks": f"Score: {score}/100. {'Broken symbols detected.' if issues else 'All symbols rendered correctly.'}",
            "confidence": 0.88,
            "rule_triggered": "SYMBOL_VISIBILITY_CHECK",
            "evidence": {
                "mode": "symbol_visibility",
                "has_images": False,
                "valid_symbol_types_found": list(set(valid_symbols_found)),
                "broken_patterns_detected": broken_found,
                "issues": issues,
            },
            "baseline": "Mathematical, scientific, and technical symbols must render correctly.",
            "suggestion": remarks,
        }
