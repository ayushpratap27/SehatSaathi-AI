"""
RAG Chat Service — orchestrates the complete RAG pipeline.

Full pipeline for one query:

    question
        ↓
    Retriever (embed query → FAISS search → top-K chunks)
        ↓
    Reranker (dedup + section boost → reorder)
        ↓
    ContextBuilder (build grounded Gemini prompt)
        ↓
    GeminiClient.generate()
        ↓
    CitationGenerator (source citations)
        ↓
    RAGChatResponse (answer + sources + confidence)
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from ai.gemini.gemini_client import GeminiClient, gemini_client
from ai.rag.citation_generator import CitationGenerator, citation_generator
from ai.rag.context_builder import ContextBuilder, context_builder
from ai.rag.embedding_service import EmbeddingService, embedding_service
from ai.rag.reranker import Reranker, reranker
from ai.rag.retriever import Retriever, retriever
from ai.rag.similarity_search import mean_similarity
from ai.rag.vector_store import VectorStoreManager, vector_store_manager
from app.config.settings import get_settings
from app.schemas.rag import ConversationTurn, RAGChatResponse

logger = logging.getLogger(__name__)
settings = get_settings()

_NO_CONTEXT_ANSWER = (
    "The uploaded report does not contain enough information to answer this question."
)


class RAGChatService:
    """
    End-to-end RAG Q&A over an indexed medical document.

    All components are injected via constructor so the service is easily
    testable with mocked sub-components.
    """

    def __init__(
        self,
        retriever_:       Optional[Retriever]           = None,
        reranker_:        Optional[Reranker]            = None,
        ctx_builder:      Optional[ContextBuilder]      = None,
        citation_gen:     Optional[CitationGenerator]   = None,
        gemini:           Optional[GeminiClient]        = None,
    ) -> None:
        self._retriever    = retriever_   or retriever
        self._reranker     = reranker_    or reranker
        self._ctx_builder  = ctx_builder  or context_builder
        self._citation_gen = citation_gen or citation_generator
        self._gemini       = gemini       or gemini_client

    async def chat(
        self,
        question:             str,
        document_id:          str,
        conversation_history: Optional[List[ConversationTurn]] = None,
        top_k:                int = 0,
    ) -> RAGChatResponse:
        """
        Answer a question grounded in the indexed report.

        Args:
            question:             User's natural-language question.
            document_id:          ID of the indexed FAISS document.
            conversation_history: Prior turns (oldest first, max 5).
            top_k:                Number of chunks to retrieve.

        Returns:
            :class:`~app.schemas.rag.RAGChatResponse` with answer, sources, and confidence.
        """
        t0 = time.perf_counter()
        logger.info("RAG chat: q=%r doc=%s", question[:80], document_id)

        k = top_k or settings.RAG_TOP_K

        # --- Step 1: Retrieve ---
        try:
            raw_results = await self._retriever.retrieve(
                question, document_id, top_k=k
            )
        except ValueError as exc:
            # No index for this document
            logger.warning("RAG: %s", exc)
            return RAGChatResponse(
                answer=str(exc),
                sources=[],
                retrieved_chunks=0,
                confidence=0.0,
            )

        if not raw_results:
            logger.info("RAG: no chunks above threshold → returning default answer")
            return RAGChatResponse(
                answer=_NO_CONTEXT_ANSWER,
                sources=[],
                retrieved_chunks=0,
                confidence=0.0,
            )

        # --- Step 2: Rerank ---
        reranked = self._reranker.rerank(raw_results)

        # --- Step 3: Build context + prompt ---
        prompt = self._ctx_builder.build(
            question=question,
            results=reranked,
            history=conversation_history,
        )

        # --- Step 4: Generate answer ---
        gemini_result = await self._gemini.generate(prompt)

        # --- Step 5: Citations & confidence ---
        sources     = self._citation_gen.generate(reranked)
        scores      = [r.score for r in reranked]
        confidence  = round(mean_similarity(scores), 4)

        elapsed = time.perf_counter() - t0
        logger.info(
            "RAG chat done: %.2fs | chunks=%d confidence=%.2f",
            elapsed, len(reranked), confidence,
        )

        return RAGChatResponse(
            answer=gemini_result.text.strip() or _NO_CONTEXT_ANSWER,
            sources=sources,
            retrieved_chunks=len(reranked),
            confidence=confidence,
        )


# Module-level singleton
rag_chat_service = RAGChatService()
