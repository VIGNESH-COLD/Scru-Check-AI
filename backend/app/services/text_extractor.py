from pathlib import Path
from typing import Any

import docx
import pymupdf as fitz
import pytesseract
from PIL import Image


class TextExtractor:
    """Unified document text extractor supporting PDF (PyMuPDF), DOCX (python-docx),

    and OCR (pytesseract). Strictly restricted to .pdf and .docx documents for security.
    """

    @staticmethod
    def is_ocr_available() -> bool:
        """Check if Tesseract binary is available on system PATH."""
        try:
            _ = pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    @classmethod
    def extract_from_pdf(cls, file_path: str | Path, max_pages: int = 100) -> dict[str, Any]:
        """Extract text page-by-page from a PDF using PyMuPDF with page count limits."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        doc = fitz.open(str(file_path))
        pages_content = []
        total_text_length = 0

        try:
            if len(doc) > max_pages:
                raise ValueError(
                    f"PDF document exceeds maximum allowed length: contains {len(doc)} pages, "
                    f"maximum allowed is {max_pages} pages."
                )

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text("text").strip()
                pages_content.append(
                    {
                        "page": page_num + 1,
                        "char_count": len(page_text),
                        "text": page_text,
                    }
                )
                total_text_length += len(page_text)

            metadata = {
                "format": "PDF",
                "engine": "PyMuPDF (fitz)",
                "total_pages": len(doc),
                "total_characters": total_text_length,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
            }
        finally:
            doc.close()

        return {
            "metadata": metadata,
            "pages": pages_content,
            "full_text": "\n\n".join(p["text"] for p in pages_content if p["text"]),
        }

    @classmethod
    def extract_from_docx(cls, file_path: str | Path) -> dict[str, Any]:
        """Extract text from Word Document (.docx) using python-docx."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {file_path}")

        if file_path.suffix.lower() != ".docx":
            raise ValueError(
                f"Unsupported format '{file_path.suffix}'. Only modern XML Word documents (.docx) are permitted."
            )

        doc = docx.Document(str(file_path))
        paragraphs = []
        tables_data = []

        # Extract text paragraphs
        for idx, p in enumerate(doc.paragraphs):
            text = p.text.strip()
            if text:
                paragraphs.append(
                    {
                        "index": idx + 1,
                        "style": p.style.name if p.style else "Normal",
                        "text": text,
                    }
                )

        # Extract tables
        for t_idx, table in enumerate(doc.tables):
            table_rows = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                table_rows.append(row_cells)
            if table_rows:
                tables_data.append(
                    {
                        "table_index": t_idx + 1,
                        "rows_count": len(table_rows),
                        "data": table_rows,
                    }
                )

        full_text_parts = [p["text"] for p in paragraphs]
        for t in tables_data:
            table_str = "\n".join(" | ".join(cell for cell in row) for row in t["data"])
            full_text_parts.append(f"[Table {t['table_index']}]\n{table_str}")

        metadata = {
            "format": "DOCX",
            "engine": "python-docx",
            "total_paragraphs": len(paragraphs),
            "total_tables": len(tables_data),
            "total_characters": sum(len(p["text"]) for p in paragraphs),
        }

        return {
            "metadata": metadata,
            "paragraphs": paragraphs,
            "tables": tables_data,
            "full_text": "\n\n".join(full_text_parts),
        }

    @classmethod
    def extract_from_image_ocr(cls, file_path: str | Path) -> dict[str, Any]:
        """Extract text from an image or scanned document using Tesseract OCR."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        if not cls.is_ocr_available():
            return {
                "metadata": {
                    "format": "IMAGE_OCR",
                    "engine": "pytesseract",
                    "status": "tesseract_binary_not_found",
                    "hint": "Install Tesseract OCR binary on Windows via: winget install UB-Mannheim.TesseractOCR",
                },
                "full_text": "",
            }

        with Image.open(str(file_path)) as img:
            extracted_text = pytesseract.image_to_string(img).strip()

        return {
            "metadata": {
                "format": "IMAGE_OCR",
                "engine": "pytesseract",
                "status": "success",
                "total_characters": len(extracted_text),
            },
            "full_text": extracted_text,
        }

    @classmethod
    def extract(cls, file_path: str | Path) -> dict[str, Any]:
        """Auto-detect format and extract text. Strictly restricted to .pdf and .docx."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            return cls.extract_from_pdf(path)
        elif ext == ".docx":
            return cls.extract_from_docx(path)
        else:
            raise ValueError(
                f"Strict security policy violation: File format '{ext}' is not permitted. "
                "Only PDF (.pdf) and Word (.docx) documents are permitted. "
                "Formats like PNG, JPG, JPEG, TXT, DOC, ZIP, and all others are strictly rejected."
            )


extractor = TextExtractor()
