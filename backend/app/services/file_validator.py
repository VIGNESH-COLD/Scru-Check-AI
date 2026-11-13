"""Strict Multi-Layer File Validation Service for Examination and Syllabus Documents.

Enforces technology-specific security controls:
1. Permitted formats: STRICTLY .pdf and .docx. All other formats (.doc, .txt, .png, .jpg, .zip, etc.) are rejected.
2. Magic byte / signature validation (%PDF- for PDF, PK\x03\x04 for DOCX).
3. MIME type verification and spoofing detection.
4. Non-empty file enforcement (> 0 bytes) and configurable file size limits (default 25 MB).
5. PDF security controls: Page count ceiling (50 for QP, 100 for syllabus), encrypted PDF rejection, PyMuPDF structure integrity.
6. DOCX security controls: Zip-slip path traversal check, required OOXML member verification ([Content_Types].xml, word/document.xml),
   and decompression bomb (zip bomb) ratio and uncompressed size ceilings.
7. Path traversal prevention: sanitize client filenames; generate cryptographically secure UUID server-side filenames.
8. Safe temporary storage outside web roots with guaranteed cleanup.
"""

from __future__ import annotations

import contextlib
import io
import logging
import os
import re
import tempfile
import uuid
import zipfile
from pathlib import Path

import docx
import pymupdf as fitz
from fastapi import HTTPException, UploadFile

from app.core.config import settings

logger = logging.getLogger("scrucheck.file_validator")

# Permitted extensions and their strict signatures
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# Magic byte signatures
PDF_MAGIC_BYTES = b"%PDF-"
ZIP_MAGIC_BYTES = b"PK\x03\x04"

# MIME type mapping
ALLOWED_MIME_TYPES = {
    ".pdf": [
        "application/pdf",
        "application/x-pdf",
        "application/acrobat",
        "applications/vnd.pdf",
        "text/pdf",
    ],
    ".docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/x-zip-compressed",
        "application/octet-stream",
    ],
}

# Resource limits
DEFAULT_MAX_FILE_SIZE_BYTES = getattr(settings, "MAX_UPLOAD_SIZE_BYTES", 25 * 1024 * 1024)  # 25 MB
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_DOCX_COMPRESSION_RATIO = 10.0  # Max 10:1 ratio
DEFAULT_MAX_QP_PDF_PAGES = 50
DEFAULT_MAX_SYLLABUS_PDF_PAGES = 100


class FileValidationError(HTTPException):
    """Specific HTTP 400 validation error for rejected uploads."""

    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(status_code=status_code, detail=detail)


class FilePayloadLimitError(HTTPException):
    """HTTP 413 Payload Too Large error."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=413, detail=detail)


class ValidatedUpload:
    """Wrapper holding safely validated file content and temporary disk path."""

    def __init__(
        self,
        sanitized_filename: str,
        extension: str,
        content_bytes: bytes,
        temp_path: Path,
        page_count: int | None = None,
    ) -> None:
        self.sanitized_filename = sanitized_filename
        self.extension = extension
        self.content_bytes = content_bytes
        self.temp_path = temp_path
        self.page_count = page_count
        self.size_bytes = len(content_bytes)

    def cleanup(self) -> None:
        """Safely remove the temporary file if it exists."""
        try:
            if self.temp_path and self.temp_path.exists():
                os.remove(self.temp_path)
                logger.debug("Cleaned up temporary file: %s", self.temp_path)
        except Exception as exc:
            logger.warning("Failed to remove temporary file %s: %s", self.temp_path, exc)


class FileValidator:
    """Multi-layer validation engine for uploaded examination and syllabus files."""

    @staticmethod
    def sanitize_filename(filename: str | None) -> str:
        """Strip directory traversal sequences and unsafe characters from filenames."""
        if not filename:
            return "unnamed_document"
        # Take basename only to prevent path traversal
        base = os.path.basename(filename.strip().replace("\\", "/"))
        # Strip dangerous characters, keeping letters, digits, dots, underscores, dashes
        clean = re.sub(r"[^\w\.\-]", "_", base)
        # Prevent multiple consecutive dots or hidden files
        clean = re.sub(r"\.{2,}", ".", clean)
        clean = clean.lstrip(".")
        return clean or "unnamed_document"

    @classmethod
    async def validate_upload(
        cls,
        upload_file: UploadFile,
        is_syllabus: bool = False,
        max_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ) -> ValidatedUpload:
        """Validate an UploadFile through all security layers and write to a safe temp file.

        Layers:
        1. Extension check (.pdf and .docx only).
        2. Size and non-empty check.
        3. Magic byte signature verification.
        4. MIME type validation with mismatch rejection.
        5. Deep parser structure & security checks (PDF page limits, DOCX zip-bomb & path traversal checks).
        6. Generation of cryptographically random UUID filename in system temp directory.
        """
        raw_filename = upload_file.filename or ""
        sanitized_name = cls.sanitize_filename(raw_filename)
        ext = os.path.splitext(sanitized_name)[1].lower()

        # Layer 1: Extension check
        if not ext:
            raise FileValidationError(
                "Uploaded file has no extension. Only PDF (.pdf) and Word (.docx) files are permitted."
            )
        if ext not in ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"File format '{ext}' is not permitted. Only PDF (.pdf) and Word (.docx) files are allowed. "
                "Formats like PNG, JPG, JPEG, TXT, DOC, ZIP, and others are strictly rejected."
            )

        # Layer 2: Read content chunk-by-chunk with size enforcement
        content = await cls._read_with_size_limit(upload_file, max_size_bytes)
        file_size = len(content)

        if file_size == 0:
            raise FileValidationError("Uploaded file is empty (0 bytes). Please upload a valid document.")

        # Layer 3: Magic byte signature verification
        cls._verify_magic_bytes(content, ext)

        # Layer 4: MIME type validation
        claimed_mime = (upload_file.content_type or "").strip().lower()
        cls._verify_mime_type(claimed_mime, ext)

        # Layer 5: Deep document structure validation
        max_pages = DEFAULT_MAX_SYLLABUS_PDF_PAGES if is_syllabus else DEFAULT_MAX_QP_PDF_PAGES
        page_count: int | None = None

        if ext == ".pdf":
            page_count = cls._validate_pdf_structure(content, max_pages=max_pages)
        elif ext == ".docx":
            cls._validate_docx_structure(content)

        # Layer 6: Safe server-side temp file generation
        # Cryptographically secure random UUID filename outside public directories
        temp_dir = tempfile.gettempdir()
        safe_filename = f"scrucheck_{uuid.uuid4().hex}{ext}"
        temp_path = Path(temp_dir) / safe_filename

        try:
            temp_path.write_bytes(content)
        except Exception as exc:
            logger.error("Failed to write validated temp file: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to store upload for processing.") from exc

        return ValidatedUpload(
            sanitized_filename=sanitized_name,
            extension=ext,
            content_bytes=content,
            temp_path=temp_path,
            page_count=page_count,
        )

    @classmethod
    async def _read_with_size_limit(
        cls,
        upload_file: UploadFile,
        max_bytes: int,
        chunk_size: int = 1024 * 1024,
    ) -> bytes:
        """Stream chunks from upload_file, enforcing size ceiling before buffering entire payload."""
        buffer = bytearray()
        total_read = 0

        # Reset pointer if supported
        with contextlib.suppress(Exception):
            await upload_file.seek(0)

        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            total_read += len(chunk)
            if total_read > max_bytes:
                max_mb = max_bytes / (1024 * 1024)
                raise FilePayloadLimitError(
                    f"Uploaded file exceeds maximum permitted size of {max_mb:.0f}MB."
                )
            buffer.extend(chunk)

        return bytes(buffer)

    @classmethod
    def _verify_magic_bytes(cls, content: bytes, ext: str) -> None:
        """Verify file header magic bytes match the claimed format."""
        if ext == ".pdf":
            # PDF must start with %PDF- (standard allows up to first 1024 bytes for preamble,
            # but institutional PDFs should start with %PDF-)
            if not content.startswith(PDF_MAGIC_BYTES) and PDF_MAGIC_BYTES not in content[:1024]:
                raise FileValidationError(
                    "Invalid PDF file: Missing standard '%PDF-' file signature header."
                )
        elif ext == ".docx" and not content.startswith(ZIP_MAGIC_BYTES):
            raise FileValidationError(
                "Invalid DOCX file: Missing standard PK zip signature header. "
                "Note: Legacy binary .doc files are not supported; please save as .docx."
            )

    @classmethod
    def _verify_mime_type(cls, claimed_mime: str, ext: str) -> None:
        """Verify claimed MIME type is compatible with extension, rejecting obvious mismatches."""
        if not claimed_mime:
            return  # Allow when client does not send MIME type, relying on verified magic bytes

        # Check for explicit malicious mismatches (e.g., claiming image/png or text/html with .pdf)
        if ext == ".pdf":
            if any(forbidden in claimed_mime for forbidden in ["image/", "text/html", "application/x-msdownload", "video/"]):
                raise FileValidationError(
                    f"MIME type mismatch: '{claimed_mime}' is not a valid PDF MIME type."
                )
        elif ext == ".docx" and any(forbidden in claimed_mime for forbidden in ["image/", "text/html", "application/x-msdownload", "video/", "text/plain"]):
            raise FileValidationError(
                f"MIME type mismatch: '{claimed_mime}' is not a valid Word (.docx) MIME type."
            )

    @classmethod
    def _validate_pdf_structure(cls, content: bytes, max_pages: int) -> int:
        """Deep PDF integrity validation using PyMuPDF.

        Verifies document is not corrupt, not password-encrypted, and does not exceed page limit.
        """
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise FileValidationError(
                f"Corrupt or malformed PDF: PyMuPDF could not parse document ({exc})."
            ) from exc

        try:
            if doc.is_encrypted:
                raise FileValidationError(
                    "Password-protected or encrypted PDF documents cannot be scrutinized. "
                    "Please upload an unencrypted document."
                )

            total_pages = len(doc)
            if total_pages == 0:
                raise FileValidationError("PDF document contains 0 pages.")

            if total_pages > max_pages:
                raise FileValidationError(
                    f"PDF document exceeds permitted length: contains {total_pages} pages, "
                    f"maximum allowed is {max_pages} pages."
                )

            return total_pages
        finally:
            doc.close()

    @classmethod
    def _validate_docx_structure(cls, content: bytes) -> None:
        """Deep DOCX validation.

        Verifies valid zip structure, checks for Zip Slip directory traversal,
        confirms required WordprocessingML parts ([Content_Types].xml, word/document.xml),
        and verifies zip-bomb safety thresholds.
        """
        try:
            bio = io.BytesIO(content)
            with zipfile.ZipFile(bio, "r") as zf:
                total_uncompressed = 0
                compressed_size = len(content)

                namelist = zf.namelist()

                # Confirm it is an actual DOCX (contains [Content_Types].xml and word/document.xml)
                if "[Content_Types].xml" not in namelist:
                    raise FileValidationError(
                        "Invalid DOCX document: Missing '[Content_Types].xml'. "
                        "The archive is not a valid OpenXML Word document."
                    )
                if not any(name.startswith("word/") for name in namelist):
                    raise FileValidationError(
                        "Invalid DOCX document: Missing 'word/' document parts. "
                        "The archive is not a valid OpenXML Word document."
                    )

                # Inspect every member entry for zip-slip and zip-bomb attacks
                for member in zf.infolist():
                    m_name = member.filename
                    # Zip Slip directory traversal check
                    if ".." in m_name or m_name.startswith("/") or m_name.startswith("\\"):
                        raise FileValidationError(
                            f"Suspicious path in DOCX archive member '{m_name}' (potential directory traversal attack)."
                        )

                    total_uncompressed += member.file_size

                    # Check max uncompressed size ceiling
                    if total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                        max_mb = MAX_DOCX_UNCOMPRESSED_BYTES / (1024 * 1024)
                        raise FileValidationError(
                            f"DOCX document exceeds safe uncompressed size limit ({max_mb:.0f}MB). Potential zip bomb."
                        )

                # Check compression ratio ceiling to defeat zip bombs
                if compressed_size > 0:
                    ratio = total_uncompressed / compressed_size
                    if total_uncompressed > 5 * 1024 * 1024 and ratio > MAX_DOCX_COMPRESSION_RATIO:
                        raise FileValidationError(
                            f"DOCX document has an excessive compression ratio ({ratio:.1f}:1). Potential decompression bomb."
                        )

            # Confirm python-docx can parse the document without crashing
            bio.seek(0)
            doc = docx.Document(bio)
            # Ensure basic accessibility
            _ = len(doc.paragraphs)
        except FileValidationError:
            raise
        except Exception as exc:
            raise FileValidationError(
                f"Corrupt or malformed DOCX file: Could not parse document structure ({exc})."
            ) from exc


file_validator = FileValidator()
