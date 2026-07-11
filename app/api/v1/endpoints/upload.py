"""
Upload endpoint — Phase 2 implementation.

Accepts a multipart file upload, validates it, stores it in
``data/uploads/`` with a UUID-based filename, and returns metadata.
No text extraction happens here; use ``POST /api/v1/report/extract``
for that.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, File, UploadFile

from app.config.settings import get_settings
from app.schemas.document import UploadResponse
from app.utils.file_manager import generate_unique_filename, save_file
from app.utils.validators import validate_upload_file

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.post(
    "/",
    response_model=UploadResponse,
    summary="Upload a medical report",
    description=(
        "Upload a medical report file (PDF, PNG, JPG, JPEG, TIFF). "
        "The file is validated, stored with a UUID filename, and the "
        "upload metadata is returned. To extract text, call "
        "`POST /api/v1/report/extract`."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="Medical report file — PDF or image"),
) -> UploadResponse:
    """
    Store an uploaded medical report and return its metadata.

    Validates:
    - File extension (PDF, PNG, JPG, JPEG, TIFF)
    - File size (≤ ``MAX_UPLOAD_SIZE_MB`` MB)
    - Non-empty content
    - Magic-byte signature (basic corruption check)
    """
    original_filename = file.filename or "unknown"
    logger.info("Upload request: '%s'", original_filename)

    content = await validate_upload_file(file)

    saved_filename = generate_unique_filename(original_filename)
    save_file(content, settings.UPLOAD_DIR, saved_filename)

    logger.info(
        "Stored '%s' as '%s' (%d bytes)",
        original_filename, saved_filename, len(content),
    )

    return UploadResponse(
        original_filename=original_filename,
        saved_filename=saved_filename,
        file_size=len(content),
        upload_timestamp=datetime.now(tz=timezone.utc),
        status="uploaded",
    )


@router.get(
    "/status/{document_id}",
    summary="Get document processing status",
)
async def get_upload_status(document_id: str) -> dict:
    """
    Return the processing status of an uploaded document.

    Full async status tracking (PENDING → PROCESSING → DONE) will be
    added in Phase 3 when database integration is active.
    """
    return {
        "document_id": document_id,
        "status": "stored",
        "message": "Async processing status tracking — coming in Phase 3",
    }
