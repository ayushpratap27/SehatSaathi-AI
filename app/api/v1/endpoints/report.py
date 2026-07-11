"""
Report endpoint — Phase 1 placeholder.

Full implementation (structured report data, entity extraction, summaries)
will be added in Phases 3 and 5.
"""

from fastapi import APIRouter

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
