"""
Chat endpoint — legacy placeholder.

The production chat implementation is at:
  POST /api/v1/rag/chat       — RAG-grounded Q&A with citations
  POST /api/v1/ai/chat        — Direct LLM chat (non-RAG)
  POST /api/v1/ai/summary     — AI executive summary
"""

from fastapi import APIRouter

router = APIRouter()

# All routes in this file are deprecated.
# Routing is kept so the prefix /chat does not return 404.
# Use /rag/chat or /ai/chat instead.
