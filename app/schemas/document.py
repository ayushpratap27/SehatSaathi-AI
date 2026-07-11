"""
Pydantic schemas for document upload and text extraction responses.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Returned after a file is successfully uploaded and stored."""

    original_filename: str = Field(..., description="Filename provided by the client")
    saved_filename: str = Field(..., description="UUID-based filename used for storage")
    file_size: int = Field(..., description="File size in bytes")
    upload_timestamp: datetime = Field(..., description="UTC timestamp of the upload")
    status: str = Field(default="uploaded")

    model_config = {
        "json_schema_extra": {
            "example": {
                "original_filename": "blood_test.pdf",
                "saved_filename": "3f2504e0-4f89-11d3-9a0c-0305e82c3301.pdf",
                "file_size": 204800,
                "upload_timestamp": "2026-07-11T10:00:00Z",
                "status": "uploaded",
            }
        }
    }


class ExtractionResult(BaseModel):
    """Returned after text is extracted from a medical document."""

    filename: str = Field(..., description="Original filename")
    pages: int = Field(..., description="Number of pages (1 for images)")
    is_scanned: bool = Field(
        ..., description="True when document was detected as scanned/image-based"
    )
    text: str = Field(..., description="Extracted and cleaned text")
    characters: int = Field(..., description="Character count in extracted text")
    words: int = Field(..., description="Word count in extracted text")
    extraction_method: str = Field(
        ..., description="Method used: pymupdf | pdfplumber | paddleocr"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "blood_test.pdf",
                "pages": 6,
                "is_scanned": False,
                "text": "Patient Name: John Doe\nHemoglobin: 14.5 g/dL...",
                "characters": 5230,
                "words": 812,
                "extraction_method": "pymupdf",
            }
        }
    }
