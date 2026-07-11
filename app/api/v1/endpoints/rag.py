"""
RAG API endpoints — Phase 6.

POST /api/v1/rag/index   — chunk, embed, and index a document
POST /api/v1/rag/search  — retrieve relevant chunks for a query
POST /api/v1/rag/chat    — full RAG Q&A with citations
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from ai.rag.chunker import document_chunker
from ai.rag.embedding_service import embedding_service
from ai.rag.rag_chat_service import rag_chat_service
from ai.rag.vector_store import vector_store_manager
from app.config.settings import get_settings
from app.schemas.rag import (
    RAGChatRequest,
    RAGChatResponse,
    RAGIndexRequest,
    RAGIndexResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGSearchResultItem,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


# ------------------------------------------------------------------ #
# Index
# ------------------------------------------------------------------ #

@router.post(
    "/index",
    response_model=RAGIndexResponse,
    summary="Create a FAISS index from extracted report text",
    description=(
        "Chunks the extracted text, generates Gemini embeddings for each chunk, "
        "and stores the FAISS index on disk under ``data/vector_stores/``. "
        "Call this once per document before using ``/rag/search`` or ``/rag/chat``."
    ),
)
async def index_document(request: RAGIndexRequest) -> RAGIndexResponse:
    """
    Build and persist a FAISS vector index for one document.

    Args:
        request.text:        Extracted text from ``POST /api/v1/report/extract``.
        request.document_id: UUID that will identify this index.
        request.source_file: Original filename (used in citations).
    """
    logger.info("RAG index: doc=%s len=%d chars", request.document_id, len(request.text))

    # 1. Chunk
    chunks = await run_in_threadpool(
        document_chunker.chunk,
        request.text,
        request.source_file,
        request.document_id,
    )
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No text chunks could be extracted from the provided text.",
        )

    # 2. Embed
    try:
        texts = [c.text for c in chunks]
        embeddings = await run_in_threadpool(embedding_service.embed_documents, texts)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    # 3. Index
    dim = embeddings.shape[1] if embeddings.ndim == 2 else settings.GEMINI_EMBEDDING_DIMENSION
    vector_store_manager.create(
        document_id=request.document_id,
        embeddings=embeddings,
        chunks=chunks,
        dimension=dim,
    )

    logger.info(
        "RAG index complete: doc=%s chunks=%d dim=%d",
        request.document_id, len(chunks), dim,
    )
    return RAGIndexResponse(
        document_id=request.document_id,
        chunks_indexed=len(chunks),
        embedding_dimension=dim,
        message=f"Successfully indexed {len(chunks)} chunks.",
    )


# ------------------------------------------------------------------ #
# Search
# ------------------------------------------------------------------ #

@router.post(
    "/search",
    response_model=RAGSearchResponse,
    summary="Retrieve relevant chunks for a query",
    description=(
        "Embeds the question and searches the FAISS index for the most "
        "similar document chunks. No Gemini generation happens here — "
        "use ``/rag/chat`` for a grounded answer."
    ),
)
async def search_chunks(request: RAGSearchRequest) -> RAGSearchResponse:
    """
    Retrieve top-K chunks most relevant to the query.

    Requires the document to be indexed first via ``POST /rag/index``.
    """
    from ai.rag.retriever import retriever  # noqa: PLC0415

    if not vector_store_manager.exists(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No index found for document '{request.document_id}'. "
                "Please call POST /api/v1/rag/index first."
            ),
        )

    threshold = request.similarity_threshold or settings.RAG_SIMILARITY_THRESHOLD
    results = await retriever.retrieve(
        question=request.question,
        document_id=request.document_id,
        top_k=request.top_k,
        threshold=threshold,
    )

    items = [
        RAGSearchResultItem(
            chunk_id=r.chunk.chunk_id,
            text=r.chunk.text,
            section=r.chunk.section,
            page_number=r.chunk.page_number,
            score=round(r.score, 4),
            chunk_index=r.chunk.chunk_index,
        )
        for r in results
    ]

    return RAGSearchResponse(
        question=request.question,
        document_id=request.document_id,
        results=items,
        total_retrieved=len(items),
    )


# ------------------------------------------------------------------ #
# Chat
# ------------------------------------------------------------------ #

@router.post(
    "/chat",
    response_model=RAGChatResponse,
    summary="Ask a question answered with RAG",
    description=(
        "Full RAG pipeline: embeds the question, retrieves relevant chunks, "
        "reranks them, builds a grounded prompt, sends it to Gemini, and returns "
        "the answer with source citations. "
        "Gemini never receives the full report — only the top-K retrieved chunks."
    ),
)
async def rag_chat(request: RAGChatRequest) -> RAGChatResponse:
    """
    Answer a question about an indexed medical report.

    Pipeline:
    1. Embed query (Gemini text-embedding-004)
    2. FAISS similarity search → top-K chunks
    3. Rerank (dedup + section boost)
    4. Build grounded prompt (context + question + history)
    5. Generate answer with Gemini 2.5 Flash
    6. Return answer + citations + confidence

    Requires the document to be indexed via ``POST /rag/index``.
    """
    if not vector_store_manager.exists(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No index found for document '{request.document_id}'. "
                "Please call POST /api/v1/rag/index first."
            ),
        )

    return await rag_chat_service.chat(
        question=request.question,
        document_id=request.document_id,
        conversation_history=request.conversation_history or [],
        top_k=request.top_k,
    )
