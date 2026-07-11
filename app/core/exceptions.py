"""
Custom exception classes and global FastAPI exception handlers.

Centralising exception handling here keeps endpoint code clean and
ensures every error response follows a consistent JSON envelope.
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Custom exception types
# --------------------------------------------------------------------------- #

class SehatSaathiException(Exception):
    """Base exception for all SehatSaathi-AI application errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentNotFoundException(SehatSaathiException):
    """Raised when a requested document does not exist."""

    def __init__(self, document_id: str) -> None:
        super().__init__(
            message=f"Document '{document_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnsupportedFileTypeException(SehatSaathiException):
    """Raised when an uploaded file type is not supported."""

    def __init__(self, mime_type: str) -> None:
        super().__init__(
            message=f"File type '{mime_type}' is not supported. Upload PDF, PNG, JPG, or TIFF.",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


class FileTooLargeException(SehatSaathiException):
    """Raised when an uploaded file exceeds the configured size limit."""

    def __init__(self, max_mb: int) -> None:
        super().__init__(
            message=f"File exceeds the maximum allowed size of {max_mb} MB.",
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        )


class InvalidFileException(SehatSaathiException):
    """Raised when an uploaded file is empty, corrupted, or mislabelled."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Invalid file: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PDFExtractionException(SehatSaathiException):
    """Raised when both PDF parsers (PyMuPDF and pdfplumber) fail."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            message=f"Could not extract text from '{filename}': {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class OCRFailedException(SehatSaathiException):
    """Raised when the OCR engine fails to process a document."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            message=f"OCR failed for '{filename}': {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# --------------------------------------------------------------------------- #
# Error response helper
# --------------------------------------------------------------------------- #

def _error_response(status_code: int, message: str, detail: Any = None) -> Dict[str, Any]:
    """Build a consistent error JSON envelope."""
    body: Dict[str, Any] = {"success": False, "message": message}
    if detail is not None:
        body["detail"] = detail
    return body


# --------------------------------------------------------------------------- #
# Exception handlers — registered on the FastAPI app instance
# --------------------------------------------------------------------------- #

def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach all global exception handlers to the FastAPI application.

    Call this once during app creation, before the app starts serving requests.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(SehatSaathiException)
    async def sehat_saathi_exception_handler(
        request: Request, exc: SehatSaathiException
    ) -> JSONResponse:
        logger.warning("Application error on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_response(exc.status_code, exc.message),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        logger.warning("HTTP %s on %s: %s", exc.status_code, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_response(exc.status_code, str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "An unexpected error occurred. Please try again later.",
            ),
        )
