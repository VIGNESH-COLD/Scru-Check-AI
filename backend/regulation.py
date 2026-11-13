import re
from pathlib import Path

from pydantic import BaseModel, Field


class RegulationCheckResult(BaseModel):
    """Result of checking regulation code on a question paper."""

    is_accepted: bool = Field(
        description="True if question paper has valid regulation code, False if rejected"
    )
    status: str = Field(
        description="'ACCEPTED' if regulation code is present, 'REJECTED' if missing"
    )
    regulation_code: str | None = Field(
        default=None,
        description="Standardized regulation string, e.g. '[Regulations 2023]'",
    )
    regulation_year: int | None = Field(
        default=None,
        description="Extracted 4-digit regulation year, e.g. 2023",
    )
    raw_match: str | None = Field(
        default=None,
        description="Exact raw text match from document",
    )
    message: str = Field(
        description="Human-readable decision explanation",
    )


class RegulationChecker:
    """Validator for Institutional Question Paper Regulation Code.

    Checks if a question paper explicitly declares a regulation code
    such as '[Regulations 2023]', '(Regulations 2021)', or 'Regulations 2023'.
    Returns ACCEPTED if present, REJECTED if missing.
    """

    # Comprehensive regex patterns matching:
    # 1. Bracketed: [Regulations 2023], (Regulations 2023), [Regulation 2021], (Regulation 2021)
    # 2. Short form: [R-2023], (R-2021), [R 2023], (R2023)
    # 3. Unbracketed line/phrase: Regulations 2023, Regulation: 2023, Regulations - 2023
    REGULATION_PATTERNS = [
        re.compile(
            r"(?:\[|\()\s*(?:Regulations?|Regulation)\s*[-–—:]?\s*([0-9]{4})\s*(?:\]|\))",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:\[|\()\s*R\s*[-–—:]?\s*([0-9]{4})\s*(?:\]|\))",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:Regulations?|Regulation)\s*[:.-]?\s*([0-9]{4})\b",
            re.IGNORECASE,
        ),
    ]

    def check(
        self,
        text: str,
        expected_year: int | str | None = None,
    ) -> RegulationCheckResult:
        """Check if regulation code is present in the question paper text.

        Args:
            text: Raw extracted text of the question paper.
            expected_year: Optional regulation year to enforce (e.g. 2023).

        Returns:
            RegulationCheckResult with status 'ACCEPTED' or 'REJECTED'.
        """
        if not text or not text.strip():
            return RegulationCheckResult(
                is_accepted=False,
                status="REJECTED",
                regulation_code=None,
                regulation_year=None,
                raw_match=None,
                message="REJECTED: Document contains no text to inspect for regulation code.",
            )

        # Institutional headers typically appear in the top 2500 characters
        sample_text = text[:2500]

        matched_raw = None
        matched_year = None

        for pattern in self.REGULATION_PATTERNS:
            match = pattern.search(sample_text)
            if match:
                matched_raw = match.group(0).strip()
                try:
                    matched_year = int(match.group(1))
                except (ValueError, IndexError):
                    matched_year = None
                break

        # Fallback search across the full text if not found in top sample
        if not matched_raw:
            for pattern in self.REGULATION_PATTERNS:
                match = pattern.search(text)
                if match:
                    matched_raw = match.group(0).strip()
                    try:
                        matched_year = int(match.group(1))
                    except (ValueError, IndexError):
                        matched_year = None
                    break

        if not matched_raw or matched_year is None:
            return RegulationCheckResult(
                is_accepted=False,
                status="REJECTED",
                regulation_code=None,
                regulation_year=None,
                raw_match=None,
                message="REJECTED: Missing regulation code. Question paper must declare a regulation code like [Regulations 2023].",
            )

        formatted_code = f"[Regulations {matched_year}]"

        # If specific year was expected, verify year match
        if expected_year is not None:
            exp_int = int(expected_year)
            if matched_year != exp_int:
                return RegulationCheckResult(
                    is_accepted=False,
                    status="REJECTED",
                    regulation_code=formatted_code,
                    regulation_year=matched_year,
                    raw_match=matched_raw,
                    message=f"REJECTED: Regulation year mismatch. Found {formatted_code}, but expected [Regulations {exp_int}].",
                )

        return RegulationCheckResult(
            is_accepted=True,
            status="ACCEPTED",
            regulation_code=formatted_code,
            regulation_year=matched_year,
            raw_match=matched_raw,
            message=f"ACCEPTED: Valid regulation code found '{matched_raw}' -> {formatted_code}.",
        )

    def check_document(
        self,
        file_path: Path | str,
        expected_year: int | str | None = None,
    ) -> RegulationCheckResult:
        """Extract text from document (PDF/DOCX/TXT) and verify regulation code."""
        from app.services.text_extractor import extractor

        extracted = extractor.extract(file_path)
        full_text = extracted.get("full_text", "")
        return self.check(full_text, expected_year=expected_year)


# Module-level instance and convenience function
checker = RegulationChecker()


def check_regulation(text: str, expected_year: int | str | None = None) -> RegulationCheckResult:
    """Convenience function to check if text contains valid regulation code."""
    return checker.check(text, expected_year=expected_year)
