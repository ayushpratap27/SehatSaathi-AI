"""
Embedding Service — generates dense vector embeddings using the Gemini
text-embedding-004 model via the official Google GenAI SDK.

Two task types are used:
  RETRIEVAL_DOCUMENT  — for indexing document chunks
  RETRIEVAL_QUERY     — for embedding user questions at query time

Embeddings are returned as float32 NumPy arrays, ready for FAISS.
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
    Generates text embeddings using the Gemini Embedding API.

    The service initialises the Google GenAI client lazily on first use
    so it can be imported anywhere without requiring a configured API key
    at import time (supporting tests that mock the API).
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model   = settings.GEMINI_EMBEDDING_MODEL
        self._dim     = settings.GEMINI_EMBEDDING_DIMENSION
        self._client  = None

    # ---------------------------------------------------------------- #
    # Initialisation
    # ---------------------------------------------------------------- #

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is not configured. "
                    "Set it in your .env file to use the embedding service."
                )
            from google import genai  # noqa: PLC0415
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    # ---------------------------------------------------------------- #
    # Core embedding
    # ---------------------------------------------------------------- #

    def _embed_text(self, text: str, task_type: str) -> np.ndarray:
        """
        Call the Gemini Embedding API synchronously (run in thread pool).

        Args:
            text:      Input text to embed.
            task_type: "RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY".

        Returns:
            Float32 NumPy array of shape ``(dim,)``.
        """
        from google.genai import types  # noqa: PLC0415

        client = self._get_client()
        response = client.models.embed_content(
            model=self._model,
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        values = response.embeddings[0].values
        return np.array(values, dtype=np.float32)

    # ---------------------------------------------------------------- #
    # Public API (sync — wrapped async by callers)
    # ---------------------------------------------------------------- #

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of document chunks.

        Args:
            texts: List of chunk text strings.

        Returns:
            Float32 array of shape ``(len(texts), dim)``.
        """
        t0 = time.perf_counter()
        embeddings: List[np.ndarray] = []

        for i, text in enumerate(texts):
            if not text.strip():
                # Zero vector for empty chunks
                embeddings.append(np.zeros(self._dim, dtype=np.float32))
                continue
            emb = self._embed_text(text, "RETRIEVAL_DOCUMENT")
            embeddings.append(emb)
            if (i + 1) % 10 == 0:
                logger.debug("Embedded %d/%d chunks…", i + 1, len(texts))

        matrix = np.vstack(embeddings) if embeddings else np.empty((0, self._dim), dtype=np.float32)
        elapsed = time.perf_counter() - t0
        logger.info(
            "EmbeddingService: %d document vectors in %.2fs (dim=%d)",
            len(texts), elapsed, self._dim,
        )
        return matrix

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single user query.

        Args:
            query: The user's question.

        Returns:
            Float32 array of shape ``(dim,)``.
        """
        if not query.strip():
            return np.zeros(self._dim, dtype=np.float32)
        emb = self._embed_text(query, "RETRIEVAL_QUERY")
        logger.debug("EmbeddingService: query embedded (dim=%d)", len(emb))
        return emb

    @property
    def dimension(self) -> int:
        """Embedding dimension."""
        return self._dim


# Module-level singleton
embedding_service = EmbeddingService()
