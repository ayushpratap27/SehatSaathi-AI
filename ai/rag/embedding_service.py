"""
Embedding Service — generates dense vector embeddings using sentence-transformers.

Previously used the Gemini text-embedding-004 API. Now uses a local
sentence-transformers model (all-MiniLM-L6-v2) which:
  - Requires no API key
  - Runs entirely on-device (CPU)
  - Produces 384-dimensional vectors
  - Is faster for small batches due to no network latency

The public interface (embed_documents / embed_query) is unchanged so the
rest of the RAG pipeline works without modification.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

import numpy as np

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """
    Generates text embeddings using a local sentence-transformers model.

    The model is loaded lazily on first use (downloads ~80 MB on first call,
    cached to disk by HuggingFace Hub afterward).

    Usage::

        emb = embedding_service.embed_query("What is my hemoglobin?")
        matrix = embedding_service.embed_documents(["chunk 1", "chunk 2"])
    """

    def __init__(self) -> None:
        self._model: Optional[object] = None
        self._model_name: str = settings.EMBEDDING_MODEL
        self._dim: int = settings.EMBEDDING_DIMENSION

    # ---------------------------------------------------------------- #
    # Initialisation
    # ---------------------------------------------------------------- #

    def _get_model(self):
        """Lazy-load the sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # noqa: PLC0415
                logger.info(
                    "Loading sentence-transformers model '%s' (first call may download ~80 MB)…",
                    self._model_name,
                )
                self._model = SentenceTransformer(self._model_name)
                logger.info("Embedding model ready: %s (dim=%d)", self._model_name, self._dim)
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is not installed. "
                    "Run: pip install sentence-transformers"
                ) from exc
        return self._model

    # ---------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------- #

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of document chunks for indexing.

        Args:
            texts: List of chunk text strings.

        Returns:
            Float32 array of shape ``(len(texts), dim)``.
            Vectors are L2-normalised (unit length).
        """
        t0 = time.perf_counter()
        model = self._get_model()

        # Filter empty texts — replace with zero vectors
        non_empty = [(i, t) for i, t in enumerate(texts) if t.strip()]
        result = np.zeros((len(texts), self._dim), dtype=np.float32)

        if non_empty:
            indices, valid_texts = zip(*non_empty)
            embeddings = model.encode(  # type: ignore[union-attr]
                list(valid_texts),
                normalize_embeddings=True,  # unit vectors → cosine sim = inner product
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            for array_idx, original_idx in enumerate(indices):
                result[original_idx] = embeddings[array_idx]

        elapsed = time.perf_counter() - t0
        logger.info(
            "EmbeddingService: %d document vectors in %.2fs (dim=%d, model=%s)",
            len(texts), elapsed, self._dim, self._model_name,
        )
        return result

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single user query for similarity search.

        Args:
            query: The user's question.

        Returns:
            Float32 array of shape ``(dim,)``, L2-normalised.
        """
        if not query.strip():
            return np.zeros(self._dim, dtype=np.float32)

        model = self._get_model()
        embedding = model.encode(  # type: ignore[union-attr]
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        logger.debug("EmbeddingService: query embedded (dim=%d)", self._dim)
        return embedding[0].astype(np.float32)

    @property
    def dimension(self) -> int:
        """Embedding vector dimension."""
        return self._dim


# Module-level singleton
embedding_service = EmbeddingService()
