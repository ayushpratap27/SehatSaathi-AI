"""
Report endpoint — Phase 2: extract endpoint implemented.

GET routes remain as placeholders until Phase 3 (database + NER).
POST /extract is the main Phase 2 deliverable.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, UploadFile
from starlette.concurrency import run_in_threadpool

from app.config.settings import get_settings
from app.core.exceptions import OCRFailedException, PDFExtractionException
from app.schemas.document import ExtractionResult
from app.services.document_service import document_service
from app.utils.file_manager import (
    cleanup_temp_files,
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
