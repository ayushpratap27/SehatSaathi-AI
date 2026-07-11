"""
Document processing service.

Orchestrates the full pipeline for converting an uploaded medical document
into clean, machine-readable text:

    PDF  →  PyMuPDF / pdfplumber  →  (if scanned) PaddleOCR  →  clean_text
    Image  →  PaddleOCR  →  clean_text

This service has no network I/O and no database access.  It only reads the
file at the supplied path, processes it, and returns a structured result.
Callers are responsible for saving files beforehand and cleaning up afterwards.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from app.schemas.document import ExtractionResult
from app.utils.text_cleaner import clean_text

logger = logging.getLogger(__name__)

# Extensions that go through the PDF extraction pipeline
_PDF_EXTENSIONS: frozenset[str] = frozenset({".pdf"})

# Extensions that go directly through OCR
_IMAGE_EXTENSIONS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".tiff", ".tif",
})


class DocumentService:
    """
    Routes documents to the correct extraction pipeline and returns
    a clean, structured :class:`~app.schemas.document.ExtractionResult`.
    """

    def process(
        self,
        file_path: "str | Path",
        original_filename: str,
    ) -> ExtractionResult:
        """
        Extract and clean text from a saved medical document.

        Args:
            file_path:         Absolute path to the file on disk.
            original_filename: Original filename as submitted by the client
                               (used only for the response payload — it is
                               never used for filesystem access).

        Returns:
            A populated :class:`~app.schemas.document.ExtractionResult`.

        Raises:
            ValueError:  Unsupported file extension.
            RuntimeError: Both PDF parsers failed, or OCR is unavailable.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        t0 = time.perf_counter()
        logger.info("Processing '%s' (ext=%s)", original_filename, ext)

        if ext in _PDF_EXTENSIONS:
            result = self._process_pdf(path, original_filename)
        elif ext in _IMAGE_EXTENSIONS:
            result = self._process_image(path, original_filename)
        else:
            raise ValueError(f"Unsupported file type: '{ext}'")

        elapsed = time.perf_counter() - t0
        logger.info(
            "Done '%s': %d chars, %d words, method=%s, %.2fs",
            original_filename, result.characters, result.words,
            result.extraction_method, elapsed,
        )
        return result

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _process_pdf(
        self, path: Path, original_filename: str
    ) -> ExtractionResult:
        """Handle PDF files — digital text first, OCR fallback for scans."""
        from ai.preprocessing.pdf_extractor import extract_pdf  # noqa: PLC0415

        extraction = extract_pdf(path)
        text: str = extraction["text"]
        pages: int = extraction["pages"]
        is_scanned: bool = extraction["is_scanned"]
        method: str = extraction.get("extraction_method", "pymupdf")

        if is_scanned:
            logger.info("Scanned PDF detected → OCR: '%s'", original_filename)
            text, method = self._run_ocr_on_pdf(path)

        cleaned = clean_text(text)
        return self._build_result(original_filename, pages, is_scanned, cleaned, method)

    def _process_image(
        self, path: Path, original_filename: str
    ) -> ExtractionResult:
        """Handle image files directly via PaddleOCR."""
        from ai.ocr.ocr_engine import OCREngine  # noqa: PLC0415

        engine = OCREngine.get_instance()
        raw_text = engine.extract_from_image_path(path)
        cleaned = clean_text(raw_text)
        return self._build_result(
            original_filename,
            pages=1,
            is_scanned=True,
            text=cleaned,
            method="paddleocr",
        )

    def _run_ocr_on_pdf(self, path: Path) -> "tuple[str, str]":
        """Run OCR on a scanned PDF; returns (text, method)."""
        from ai.ocr.ocr_engine import OCREngine  # noqa: PLC0415

        engine = OCREngine.get_instance()
        ocr_result = engine.extract_from_pdf(path)
        return ocr_result["text"], "paddleocr"

    @staticmethod
    def _build_result(
        filename: str,
        pages: int,
        is_scanned: bool,
        text: str,
        method: str,
    ) -> ExtractionResult:
        """Assemble an ExtractionResult from processed components."""
        words = len(text.split()) if text.strip() else 0
        return ExtractionResult(
            filename=filename,
            pages=pages,
            is_scanned=is_scanned,
            text=text,
            characters=len(text),
            words=words,
            extraction_method=method,
        )


# Module-level singleton — import and call `.process()` directly
document_service = DocumentService()
