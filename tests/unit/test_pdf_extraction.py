"""
Unit tests for ai/preprocessing/pdf_extractor.py

Uses PyMuPDF to generate minimal in-memory PDFs without needing test fixtures
on disk.
"""

from __future__ import annotations

import pytest


def _make_digital_pdf() -> bytes:
    """Create a minimal digital PDF with enough text to be non-scanned."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        (
            "Patient: Jane Doe\n"
            "Date: 2026-07-11\n"
            "Hemoglobin: 13.2 g/dL  Reference: 12.0-16.0  Status: Normal\n"
            "WBC: 6.8 x10^3/uL  Reference: 4.5-11.0  Status: Normal\n"
        ),
        fontsize=11,
    )
    data = doc.write()
    doc.close()
    return data


def _make_empty_pdf() -> bytes:
    """Create a PDF page with no text (simulates a scanned document)."""
    import fitz

    doc = fitz.open()
    doc.new_page()  # blank page
    data = doc.write()
    doc.close()
    return data


# ------------------------------------------------------------------ #
# extract_with_pymupdf
# ------------------------------------------------------------------ #

class TestExtractWithPyMuPDF:
    def test_extracts_text_from_digital_pdf(self, tmp_path) -> None:
        from ai.preprocessing.pdf_extractor import extract_with_pymupdf

        pdf_bytes = _make_digital_pdf()
        p = tmp_path / "digital.pdf"
        p.write_bytes(pdf_bytes)

        result = extract_with_pymupdf(p)

        assert result["pages"] == 1
        assert "Hemoglobin" in result["text"]
        assert result["is_scanned"] is False

    def test_blank_page_detected_as_scanned(self, tmp_path) -> None:
        from ai.preprocessing.pdf_extractor import extract_with_pymupdf

        p = tmp_path / "blank.pdf"
        p.write_bytes(_make_empty_pdf())

        result = extract_with_pymupdf(p)
        assert result["is_scanned"] is True

    def test_returns_page_count(self, tmp_path) -> None:
        import fitz
        from ai.preprocessing.pdf_extractor import extract_with_pymupdf

        doc = fitz.open()
        for _ in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), "page content here with text", fontsize=12)
        p = tmp_path / "multi.pdf"
        p.write_bytes(doc.write())
        doc.close()

        result = extract_with_pymupdf(p)
        assert result["pages"] == 3


# ------------------------------------------------------------------ #
# extract_pdf (with fallback logic)
# ------------------------------------------------------------------ #

class TestExtractPDF:
    def test_digital_pdf_uses_pymupdf(self, tmp_path) -> None:
        from ai.preprocessing.pdf_extractor import extract_pdf

        p = tmp_path / "report.pdf"
        p.write_bytes(_make_digital_pdf())

        result = extract_pdf(p)

        assert result["extraction_method"] in ("pymupdf", "pdfplumber")
        assert len(result["text"].strip()) > 0
        assert result["is_scanned"] is False

    def test_result_has_required_keys(self, tmp_path) -> None:
        from ai.preprocessing.pdf_extractor import extract_pdf

        p = tmp_path / "report.pdf"
        p.write_bytes(_make_digital_pdf())
        result = extract_pdf(p)

        for key in ("text", "pages", "is_scanned", "extraction_method"):
            assert key in result
