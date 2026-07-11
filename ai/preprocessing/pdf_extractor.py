"""
PDF text extraction using PyMuPDF (primary) and pdfplumber (fallback).

Both extractors return the same dictionary schema so callers can treat them
interchangeably. ``extract_pdf`` tries PyMuPDF first and falls back to
pdfplumber if extraction fails or yields too little content.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# A page with fewer than this many characters is treated as "mostly image"
_MIN_CHARS_PER_PAGE: int = 50

# If this fraction of pages are empty, the whole document is scanned
_SCANNED_EMPTY_PAGE_RATIO: float = 0.5


# ------------------------------------------------------------------ #
# Scanned detection
# ------------------------------------------------------------------ #

def _detect_scanned(pages_text: List[str], page_image_counts: List[int]) -> bool:
    """
    Decide whether a PDF is image-based (scanned) or has selectable text.

    A PDF is treated as scanned when:
    - The average character count per page is below ``_MIN_CHARS_PER_PAGE``, OR
    - More than half of its pages have fewer than ``_MIN_CHARS_PER_PAGE`` chars.

    Args:
        pages_text:        List of raw text strings, one per page.
        page_image_counts: Number of embedded images per page (PyMuPDF only).

    Returns:
        ``True`` when the PDF should be sent to the OCR pipeline.
    """
    total = len(pages_text)
    if total == 0:
        return True

    stripped = [t.strip() for t in pages_text]
    total_chars = sum(len(s) for s in stripped)
    avg_chars = total_chars / total
    empty_pages = sum(1 for s in stripped if len(s) < _MIN_CHARS_PER_PAGE)

    is_scanned = (
        avg_chars < _MIN_CHARS_PER_PAGE
        or (empty_pages / total) > _SCANNED_EMPTY_PAGE_RATIO
    )

    logger.debug(
        "Scanned detection: avg_chars=%.1f empty=%d/%d → %s",
        avg_chars, empty_pages, total, is_scanned,
    )
    return is_scanned


# ------------------------------------------------------------------ #
# PyMuPDF extractor
# ------------------------------------------------------------------ #

def extract_with_pymupdf(pdf_path: "str | Path") -> Dict[str, Any]:
    """
    Extract text from a PDF using PyMuPDF (fitz).

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dict with keys: ``text``, ``pages``, ``is_scanned``,
        ``metadata``, ``pages_text``.

    Raises:
        Exception: Propagated as-is; callers decide whether to fall back.
    """
    import fitz  # PyMuPDF  # noqa: PLC0415

    path = Path(pdf_path)
    logger.info("PyMuPDF extracting: %s", path.name)

    doc = fitz.open(str(path))
    pages_text: List[str] = []
    page_image_counts: List[int] = []

    for page in doc:
        pages_text.append(page.get_text("text"))
        page_image_counts.append(len(page.get_images()))

    full_text = "\n\n".join(pages_text)
    metadata: Dict[str, Any] = dict(doc.metadata) if doc.metadata else {}
    doc.close()

    is_scanned = _detect_scanned(pages_text, page_image_counts)
    logger.info(
        "PyMuPDF: %d pages, %d chars, scanned=%s",
        len(pages_text), len(full_text), is_scanned,
    )
    return {
        "text": full_text,
        "pages": len(pages_text),
        "is_scanned": is_scanned,
        "metadata": metadata,
        "pages_text": pages_text,
    }


# ------------------------------------------------------------------ #
# pdfplumber fallback
# ------------------------------------------------------------------ #

def extract_with_pdfplumber(pdf_path: "str | Path") -> Dict[str, Any]:
    """
    Extract text from a PDF using pdfplumber.

    Useful for complex layouts and embedded table structures.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dict with keys: ``text``, ``pages``, ``is_scanned``,
        ``metadata``, ``pages_text``.

    Raises:
        Exception: Propagated as-is.
    """
    import pdfplumber  # noqa: PLC0415

    path = Path(pdf_path)
    logger.info("pdfplumber extracting: %s", path.name)

    pages_text: List[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")

    full_text = "\n\n".join(pages_text)
    is_scanned = _detect_scanned(pages_text, [0] * len(pages_text))

    logger.info(
        "pdfplumber: %d pages, %d chars, scanned=%s",
        len(pages_text), len(full_text), is_scanned,
    )
    return {
        "text": full_text,
        "pages": len(pages_text),
        "is_scanned": is_scanned,
        "metadata": {},
        "pages_text": pages_text,
    }


# ------------------------------------------------------------------ #
# Public entry point
# ------------------------------------------------------------------ #

def extract_pdf(pdf_path: "str | Path") -> Dict[str, Any]:
    """
    Extract text from a PDF with automatic fallback.

    Tries PyMuPDF first. Falls back to pdfplumber when:
    - PyMuPDF raises an exception, OR
    - PyMuPDF returns fewer than 10 non-whitespace characters.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dict with ``text``, ``pages``, ``is_scanned``, ``metadata``,
        ``pages_text``, and ``extraction_method`` (``"pymupdf"`` or
        ``"pdfplumber"``).

    Raises:
        RuntimeError: When both methods fail.
    """
    result: "Dict[str, Any] | None" = None
    pymupdf_err: "Exception | None" = None

    # --- Primary: PyMuPDF ---
    try:
        result = extract_with_pymupdf(pdf_path)
        result["extraction_method"] = "pymupdf"
    except Exception as exc:
        pymupdf_err = exc
        logger.warning("PyMuPDF failed for '%s': %s", pdf_path, exc)

    # Fall back when PyMuPDF yielded no meaningful text
    if result is None or len(result.get("text", "").strip()) < 10:
        try:
            logger.info("Falling back to pdfplumber for: %s", pdf_path)
            result = extract_with_pdfplumber(pdf_path)
            result["extraction_method"] = "pdfplumber"
        except Exception as exc:
            logger.error("pdfplumber also failed for '%s': %s", pdf_path, exc)
            if result is None:
                raise RuntimeError(
                    f"Both PyMuPDF and pdfplumber failed to parse '{Path(pdf_path).name}'."
                ) from exc

    return result  # type: ignore[return-value]
