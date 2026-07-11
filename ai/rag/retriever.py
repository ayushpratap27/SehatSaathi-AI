"""
Retriever — embeds a user query and fetches the most relevant document
chunks from the FAISS vector store.

Pipeline:
  question → EmbeddingService (RETRIEVAL_QUERY) → FAISS search → top-K chunks
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from starlette.concurrency import run_in_threadpool

from ai.rag.embedding_service import EmbeddingService, embedding_service
from ai.rag.vector_store import SearchResult, VectorStore, VectorStoreManager, vector_store_manager
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_NO_CONTEXT_MSG = (
    "The uploaded report does not contain enough information to answer this question."
)


class Retriever:
    """
    Retrieves the most relevant document chunks for a natural-language query.

    Dependency-injectable: pass custom ``embedder`` and ``manager`` in tests.
    """

    def __init__(
        self,
        embedder: Optional[EmbeddingService] = None,
        manager:  Optional[VectorStoreManager] = None,
    ) -> None:
        self._embedder = embedder or embedding_service
        self._manager  = manager  or vector_store_manager

    async def retrieve(
        self,
        question:   str,
        document_id: str,
        top_k:      int   = 0,
        threshold:  float = 0.0,
    ) -> List[SearchResult]:
        """
        Find the top-K chunks most relevant to ``question``.

        Args:
            question:    User's natural-language question.
            document_id: ID of the indexed document to search.
            top_k:       Number of chunks to retrieve (defaults to settings).
            threshold:   Minimum similarity score (defaults to settings).

        Returns:
            List of :class:`~ai.rag.vector_store.SearchResult` sorted by
            score descending. Empty list when no relevant chunks are found.

        Raises:
            ValueError: If no index exists for ``document_id``.
        """
        k   = top_k   or settings.RAG_TOP_K
        thr = threshold or settings.RAG_SIMILARITY_THRESHOLD

        vs: Optional[VectorStore] = self._manager.get(document_id)
        if vs is None:
            raise ValueError(
                f"No FAISS index found for document '{document_id}'. "
                "Please call POST /api/v1/rag/index first."
            )

        t0 = time.perf_counter()
        # Embed query in thread pool (sync SDK → non-blocking)
        query_emb = await run_in_threadpool(self._embedder.embed_query, question)
        embed_time = time.perf_counter() - t0

        t1 = time.perf_counter()
        results = vs.search(query_emb, k=k, threshold=thr)
        search_time = time.perf_counter() - t1

        logger.info(
            "Retriever: q=%r | doc=%s | embed=%.2fs search=%.2fs | "
            "top_k=%d threshold=%.2f → %d results",
            question[:60], document_id,
            embed_time, search_time,
            k, thr, len(results),
        )
        return results


# Module-level singleton
retriever = Retriever()
