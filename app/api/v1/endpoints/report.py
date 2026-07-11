"""
Report endpoint — Phase 3: /parse endpoint added.

Phase 2: POST /extract   — text extraction from file
Phase 3: POST /parse     — full structured JSON from file or plain text
GET routes remain as placeholders until Phase 4+ (database integration).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.config.settings import get_settings
from app.core.exceptions import OCRFailedException, PDFExtractionException
from app.schemas.document import ExtractionResult
from app.schemas.report import ParsedReport
from app.services.document_service import document_service
from app.utils.file_manager import (
    delete_file,
    generate_unique_filename,
    save_file,
)
from app.utils.validators import validate_upload_file

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.get("/{document_id}", summary="Get processed report data")
async def get_report(document_id: str) -> dict:
    """
    Return structured data extracted from a processed medical report.

    Args:
        document_id: UUID of the document.

    Returns:
        Placeholder response until Phase 3/5 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "message": "Report retrieval — coming in Phase 3",
    }


@router.get("/{document_id}/summary", summary="Get plain-language report summary")
async def get_report_summary(document_id: str) -> dict:
    """
    Return an AI-generated plain-language summary of the report.

    Args:
        document_id: UUID of the document.

    Returns:
        Placeholder response until Phase 5 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "message": "Report summarization — coming in Phase 5",
    }


@router.get("/", summary="List all reports")
async def list_reports() -> dict:
    """
    Return a paginated list of all reports for the current user.

    Returns:
        Placeholder response until Phase 2/8 implementation.
    """
    return {
        "success": True,
        "reports": [],
        "message": "Report listing — coming in Phase 2",
    }


# ------------------------------------------------------------------ #
# Phase 2 — Text Extraction endpoint
# ------------------------------------------------------------------ #

@router.post(
    "/extract",
    response_model=ExtractionResult,
    summary="Extract text from a medical report",
    description=(
        "Upload a medical report (PDF or image). The document is validated, "
        "stored temporarily, processed through the extraction pipeline "
        "(PyMuPDF → pdfplumber → PaddleOCR as needed), and the cleaned text "
        "is returned. The temp file is deleted after processing."
    ),
)
async def extract_text(
    file: UploadFile = File(..., description="Medical report — PDF or image"),
) -> ExtractionResult:
    """
    Extract and return clean machine-readable text from a medical document.

    Pipeline:
    1. Validate file (extension, size, magic bytes).
    2. Save to ``data/temp/`` with a UUID filename.
    3. Route to the correct processor:
       - **Digital PDF** → PyMuPDF (fallback: pdfplumber)
       - **Scanned PDF** → PaddleOCR on each rendered page
       - **Image** → PaddleOCR
    4. Clean extracted text (normalise whitespace, units, artefacts).
    5. Delete temp file.
    6. Return :class:`~app.schemas.document.ExtractionResult`.
    """
    original_filename = file.filename or "unknown"
    logger.info("Extract request: '%s'", original_filename)

    # --- Validate ---
    content = await validate_upload_file(file)

    # --- Save to temp ---
    temp_filename = generate_unique_filename(original_filename)
    temp_path = save_file(content, settings.TEMP_DIR, temp_filename)

    # --- Process (blocking I/O → run in thread pool) ---
    try:
        result: ExtractionResult = await run_in_threadpool(
            document_service.process, temp_path, original_filename
        )
    except RuntimeError as exc:
        raise PDFExtractionException(original_filename, str(exc)) from exc
    except Exception as exc:
        raise OCRFailedException(original_filename, str(exc)) from exc
    finally:
        # Always clean up temp file, even on error
        delete_file(temp_path)

    logger.info(
        "Extraction complete: '%s' — %d chars, %d words, method=%s",
        original_filename, result.characters, result.words, result.extraction_method,
    )
    return result


# ------------------------------------------------------------------ #
# Phase 3 — Structured Parsing endpoint
# ------------------------------------------------------------------ #

@router.post(
    "/parse",
    response_model=ParsedReport,
    summary="Parse a medical report into structured JSON",
    description=(
        "Upload a medical report (PDF or image) **or** submit extracted text. "
        "The document is processed through the Phase 2 extraction pipeline if a "
        "file is provided, then all Phase 3 extractors run to return a fully "
        "structured JSON report with patient info, lab tests, diagnosis, and "
        "medicines."
    ),
)
async def parse_report(
    file: Optional[UploadFile] = File(default=None, description="PDF or image file"),
    text: Optional[str] = Form(default=None, description="Pre-extracted text (from /extract)"),
) -> ParsedReport:
    """
    Return a fully structured medical report as JSON.

    Accepts **either** a file upload or plain text (not both required).

    Pipeline:
    1. If ``file`` provided: validate → save to temp → extract text (Phase 2).
    2. If ``text`` provided: use directly.
    3. Run all Phase 3 extractors via ``build_report()``.
    4. Delete temp file (if created).
    5. Return :class:`~app.schemas.report.ParsedReport`.
    """
    from ai.ner.json_builder import build_report  # noqa: PLC0415

    if file is None and not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either a 'file' or 'text' parameter.",
        )

    cleaned_text: str = ""
    temp_path = None

    # --- Source 1: file ---
    if file is not None:
        original_filename = file.filename or "unknown"
        logger.info("Parse request (file): '%s'", original_filename)

        content = await validate_upload_file(file)
        temp_filename = generate_unique_filename(original_filename)
        temp_path = save_file(content, settings.TEMP_DIR, temp_filename)

        try:
            extraction: ExtractionResult = await run_in_threadpool(
                document_service.process, temp_path, original_filename
            )
            cleaned_text = extraction.text
        except RuntimeError as exc:
            raise PDFExtractionException(original_filename, str(exc)) from exc
        except Exception as exc:
            raise OCRFailedException(original_filename, str(exc)) from exc
        finally:
            if temp_path:
                delete_file(temp_path)

    # --- Source 2: raw text ---
    else:
        cleaned_text = text  # type: ignore[assignment]
        logger.info("Parse request (text): %d chars", len(cleaned_text))

    if not cleaned_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract any text from the provided input.",
        )

    # --- Run Phase 3 extraction pipeline ---
    report: ParsedReport = await run_in_threadpool(build_report, cleaned_text)

    logger.info(
        "Parse complete: tests=%d diagnoses=%d medicines=%d",
        len(report.tests), len(report.diagnosis), len(report.medicines),
    )
    return report
