"""
Pydantic schemas for Phase 6 — RAG pipeline API.

Defines request/response shapes for:
  POST /api/v1/rag/index   — create FAISS index from extracted text
  POST /api/v1/rag/search  — retrieve relevant chunks for a query
  POST /api/v1/rag/chat    — full RAG Q&A with citations
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

_DISCLAIMER = (
    "⚠️ This AI-generated response is grounded in the retrieved report context only. "
    "It does NOT constitute medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare professional."
)


# ------------------------------------------------------------------ #
# Index endpoint
# ------------------------------------------------------------------ #

class RAGIndexRequest(BaseModel):
    """Request to build a FAISS index from extracted report text."""

    text: str = Field(..., min_length=10, description="Extracted report text (from /report/extract)")
    document_id: str = Field(..., description="Unique ID for this document (UUID recommended)")
    source_file: str = Field(default="", description="Original filename (for citations)")


class RAGIndexResponse(BaseModel):
    """Result of the indexing operation."""

    document_id: str
    chunks_indexed: int = Field(..., description="Number of chunks stored in the index")
    embedding_dimension: int
    status: str = "indexed"
    message: str = ""


# ------------------------------------------------------------------ #
# Search endpoint
# ------------------------------------------------------------------ #

class RAGSearchRequest(BaseModel):
    """Request to retrieve relevant chunks for a query."""

    question: str = Field(..., min_length=2)
    document_id: str
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: Optional[float] = Field(
        None,
        description="Override the default similarity threshold (0.0–1.0)",
    )


class RAGSearchResultItem(BaseModel):
    """One retrieved chunk with its metadata and similarity score."""

    chunk_id: str
    text: str
    section: str
    page_number: Optional[int]
    score: float = Field(..., description="Cosine similarity score (0–1)")
    chunk_index: int


class RAGSearchResponse(BaseModel):
    """All retrieved chunks for a query."""

    question: str
    document_id: str
    results: List[RAGSearchResultItem] = Field(default_factory=list)
    total_retrieved: int


# ------------------------------------------------------------------ #
# Chat endpoint
# ------------------------------------------------------------------ #

class ConversationTurn(BaseModel):
    """One turn in the conversation history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class RAGChatRequest(BaseModel):
    """Request to ask a question answered with RAG."""

    question: str = Field(..., min_length=2)
    document_id: str
    conversation_history: List[ConversationTurn] = Field(
        default_factory=list,
        description="Up to 5 prior turns for context (role: user | assistant)",
    )
    top_k: int = Field(default=5, ge=1, le=20)

    model_config = {"json_schema_extra": {
        "example": {
            "question": "Which values are abnormal?",
            "document_id": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
            "conversation_history": [],
        }
    }}


class CitationSource(BaseModel):
    """Source citation for one retrieved chunk."""

    page: Optional[int]
    section: str
    score: float = Field(..., description="Cosine similarity (0–1)")
    preview: str = Field(..., description="First 120 characters of the chunk")


class RAGChatResponse(BaseModel):
    """Grounded answer with source citations."""

    answer: str
    sources: List[CitationSource] = Field(default_factory=list)
    retrieved_chunks: int
    confidence: float = Field(..., description="Mean similarity score of retrieved chunks (0–1)")
    disclaimer: str = Field(default=_DISCLAIMER)

    model_config = {"json_schema_extra": {
        "example": {
            "answer": "Your Hemoglobin is 12.4 g/dL, which is below the normal range (13.5–17.5).",
            "sources": [{"page": 2, "section": "Haematology", "score": 0.94, "preview": "Hemoglobin 12.4 g/dL..."}],
            "retrieved_chunks": 3,
            "confidence": 0.89,
        }
    }}
