"""
Chat endpoint — Phase 1 placeholder.

Full implementation (RAG-based Q&A, session management, source traceability)
will be added in Phase 6.
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/session", summary="Create a new chat session")
async def create_session() -> dict:
    """
    Create a new chat session linked to an uploaded document.

    Returns:
        Placeholder response until Phase 6 implementation.
    """
    return {
        "success": True,
        "message": "Chat sessions — coming in Phase 6",
    }


@router.post("/session/{session_id}/message", summary="Send a message to the chat")
async def send_message(session_id: str) -> dict:
    """
    Send a user question and receive an AI-generated answer grounded
    in the uploaded report.

    Args:
        session_id: UUID of the active chat session.

    Returns:
        Placeholder response until Phase 6 implementation.
    """
    return {
        "success": True,
        "session_id": session_id,
        "message": "RAG-based chat — coming in Phase 6",
    }


@router.get("/session/{session_id}/history", summary="Get chat history")
async def get_history(session_id: str) -> dict:
    """
    Return the full message history for a chat session.

    Args:
        session_id: UUID of the chat session.

    Returns:
        Placeholder response until Phase 6 implementation.
    """
    return {
        "success": True,
        "session_id": session_id,
        "history": [],
        "message": "Chat history — coming in Phase 6",
    }


@router.delete("/session/{session_id}", summary="Delete a chat session")
async def delete_session(session_id: str) -> dict:
    """
    Permanently delete a chat session and its message history.

    Args:
        session_id: UUID of the chat session.

    Returns:
        Placeholder response until Phase 6 implementation.
    """
    return {
        "success": True,
        "session_id": session_id,
        "message": "Session deletion — coming in Phase 6",
    }
