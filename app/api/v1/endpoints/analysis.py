"""
Analysis endpoint — Phase 1 placeholder.

Full implementation (lab value extraction, NER, abnormal value detection,
reference range comparison) will be added in Phases 3 and 5.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/{document_id}/entities", summary="Extract medical entities")
async def get_entities(document_id: str) -> dict:
    """
    Return medical entities (diseases, medications, procedures, symptoms)
    extracted from the report.

    Args:
        document_id: UUID of the document.

    Returns:
        Placeholder response until Phase 3 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "entities": [],
        "message": "Medical NER — coming in Phase 3",
    }


@router.get("/{document_id}/lab-values", summary="Get lab test results")
async def get_lab_values(document_id: str) -> dict:
    """
    Return extracted laboratory test values with normal/abnormal classification.

    Args:
        document_id: UUID of the document.

    Returns:
        Placeholder response until Phase 3 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "lab_values": [],
        "message": "Lab value extraction — coming in Phase 3",
    }


@router.get("/{document_id}/explain", summary="Explain report in simple language")
async def explain_report(document_id: str) -> dict:
    """
    Return a patient-friendly explanation of the report content.

    Args:
        document_id: UUID of the document.

    Returns:
        Placeholder response until Phase 5 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "message": "AI explanation — coming in Phase 5",
    }
