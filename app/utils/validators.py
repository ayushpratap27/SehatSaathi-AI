"""
File validation utilities for uploaded medical documents.

Validates extension, size, emptiness, and magic-byte signatures
before any processing occurs.
"""

from __future__ import annotations

import logging
import os

from fastapi import HTTPException, UploadFile, status

from app.config.settings import get_settings
from app.core.exceptions import FileTooLargeException, UnsupportedFileTypeException

logger = logging.getLogger(__name__)

settings = get_settings()

# ------------------------------------------------------------------ #
# Allowed types
# ------------------------------------------------------------------ #

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({
    ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif",
})

# Magic byte signatures keyed by normalised type name
_MAGIC: dict[str, bytes] = {
    "pdf":      b"%PDF",
    "png":      b"\x89PNG",
    "jpeg":     b"\xff\xd8\xff",
    "tiff_le":  b"II*\x00",
    "tiff_be":  b"MM\x00*",
}

_EXT_TO_TYPE: dict[str, str] = {
    ".pdf":  "pdf",
    ".png":  "png",
    ".jpg":  "jpeg",
    ".jpeg": "jpeg",
    ".tiff": "tiff",
    ".tif":  "tiff",
}


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #

def _magic_ok(content: bytes, ext: str) -> bool:
    """Return True if the file's magic bytes match its extension."""
    t = _EXT_TO_TYPE.get(ext)
    if t == "pdf":
        return content[:4] == _MAGIC["pdf"]
    if t == "png":
        return content[:4] == _MAGIC["png"]
    if t == "jpeg":
        return content[:3] == _MAGIC["jpeg"]
    if t == "tiff":
        return content[:4] in (_MAGIC["tiff_le"], _MAGIC["tiff_be"])
    return True  # Unknown extension — allow through; upstream will reject


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #

async def validate_upload_file(file: UploadFile) -> bytes:
    """
    Validate an uploaded file and return its raw bytes.

    Checks performed (in order):
    1. Extension is in the allowed list.
    2. File is not empty.
    3. File size is within the configured ``MAX_UPLOAD_SIZE_MB`` limit.
    4. Magic bytes match the declared extension (catches corrupted / mislabelled files).

    Args:
        file: The FastAPI :class:`UploadFile` object from the request.

    Returns:
        Raw bytes of the file (the internal file pointer is reset to 0 after reading).

    Raises:
        :class:`~app.core.exceptions.UnsupportedFileTypeException`: Bad extension.
        :class:`~app.core.exceptions.FileTooLargeException`: File too large.
        :class:`fastapi.HTTPException` 400: Empty or corrupted file.
    """
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    # --- 1. Extension ---
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected '%s': unsupported extension '%s'", filename, ext)
        raise UnsupportedFileTypeException(ext)

    # --- 2 & 3. Read, check empty, check size ---
    content = await file.read()
    await file.seek(0)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        logger.warning(
            "Rejected '%s': %d bytes > %d MB limit",
            filename, len(content), settings.MAX_UPLOAD_SIZE_MB,
        )
        raise FileTooLargeException(settings.MAX_UPLOAD_SIZE_MB)

    # --- 4. Magic bytes ---
    if not _magic_ok(content, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File content does not match the declared extension '{ext}'. "
                "The file may be corrupted or mislabelled."
            ),
        )

    logger.debug("'%s' passed validation (%d bytes)", filename, len(content))
    return content
