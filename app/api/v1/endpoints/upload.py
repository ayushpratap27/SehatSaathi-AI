"""
Upload endpoint — Phase 1 placeholder.

Full implementation (file validation, secure storage, async processing)
will be added in Phase 2.
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/", summary="Upload a medical report")
async def upload_document() -> dict:
    """
    Accept a medical report file (PDF / PNG / JPG / TIFF).

    Returns:
        Placeholder response until Phase 2 implementation.
    """
    return {
        "success": True,
        "message": "Upload endpoint — coming in Phase 2",
        "endpoint": "POST /api/v1/upload/",
    }


@router.get("/status/{document_id}", summary="Get document processing status")
async def get_upload_status(document_id: str) -> dict:
    """
    Return the processing status of an uploaded document.

    Args:
        document_id: UUID of the uploaded document.

    Returns:
        Placeholder response until Phase 2 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "status": "placeholder",
        "message": "Status tracking — coming in Phase 2",
    }
