"""
FAISS Vector Store — manages document chunk embeddings and metadata.

Each document gets its own FAISS index, persisted to disk so it survives
application restarts. The ``VectorStoreManager`` acts as a registry that
loads indexes on demand and caches them in memory.

Index type: ``IndexFlatIP`` (inner product)
After L2-normalising all embeddings, inner product = cosine similarity,
giving scores in [0, 1] for unit vectors.
"""

from __future__ import annotations

import logging
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from ai.rag.chunker import DocumentChunk
from ai.rag.similarity_search import normalize_l2
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ------------------------------------------------------------------ #
# Search result
# ------------------------------------------------------------------ #

@dataclass
class SearchResult:
    """One chunk returned by a FAISS similarity search."""
    chunk: DocumentChunk
    score: float          # cosine similarity (0–1)
    faiss_index: int      # position in the FAISS index


# ------------------------------------------------------------------ #
# Per-document vector store
# ------------------------------------------------------------------ #

class VectorStore:
    """
    Wraps a FAISS ``IndexFlatIP`` index for one document.

    The index stores L2-normalised embeddings; searching is therefore
    equivalent to cosine similarity.
    """

    def __init__(self, dimension: int) -> None:
        import faiss  # noqa: PLC0415
        self._dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._chunks: List[DocumentChunk] = []

    # ---------------------------------------------------------------- #
    # Add
    # ---------------------------------------------------------------- #

    def add(self, embeddings: np.ndarray, chunks: List[DocumentChunk]) -> None:
        """
        Add embeddings + chunks to the index.

        Args:
            embeddings: Float32 array ``(n, dim)``.
            chunks:     Matching :class:`DocumentChunk` list (len == n).
        """
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        emb = embeddings.astype(np.float32).copy()
        normalize_l2(emb)
        self._index.add(emb)
        self._chunks.extend(chunks)
        logger.debug("VectorStore: added %d vectors (total=%d)", len(chunks), len(self._chunks))

    # ---------------------------------------------------------------- #
    # Search
    # ---------------------------------------------------------------- #

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        threshold: float = 0.0,
    ) -> List[SearchResult]:
        """
        Retrieve the top-K most similar chunks.

        Args:
            query_embedding: Float32 array ``(dim,)`` or ``(1, dim)``.
            k:               Number of neighbours.
            threshold:       Minimum cosine score to include.

        Returns:
            List of :class:`SearchResult` sorted by score descending.
        """
        if self._index.ntotal == 0:
            logger.warning("VectorStore: search on empty index")
            return []

        q = query_embedding.astype(np.float32).copy()
        if q.ndim == 1:
            q = q.reshape(1, -1)
        normalize_l2(q)

        k = min(k, self._index.ntotal)
        scores, indices = self._index.search(q, k)

        results: List[SearchResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or float(score) < threshold:
                continue
            results.append(SearchResult(
                chunk=self._chunks[idx],
                score=float(score),
                faiss_index=int(idx),
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results

    # ---------------------------------------------------------------- #
    # Persistence
    # ---------------------------------------------------------------- #

    def save(self, path: str) -> None:
        """
        Save the FAISS index and chunk metadata to ``path.*`` files.

        Creates two files:
        - ``<path>.faiss`` — FAISS binary index
        - ``<path>.chunks.pkl`` — pickled chunk list
        """
        import faiss  # noqa: PLC0415
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        faiss.write_index(self._index, f"{path}.faiss")
        with open(f"{path}.chunks.pkl", "wb") as fh:
            pickle.dump(self._chunks, fh)
        logger.info("VectorStore saved: %d vectors → %s", self._index.ntotal, path)

    @classmethod
    def load(cls, path: str) -> "VectorStore":
        """
        Load a VectorStore from ``path.*`` files saved by :meth:`save`.

        Args:
            path: Base path (without extension).

        Returns:
            Loaded :class:`VectorStore`.

        Raises:
            FileNotFoundError: If the FAISS or chunks file is missing.
        """
        import faiss  # noqa: PLC0415
        faiss_path  = f"{path}.faiss"
        chunks_path = f"{path}.chunks.pkl"

        if not os.path.exists(faiss_path):
            raise FileNotFoundError(f"FAISS index not found: {faiss_path}")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks metadata not found: {chunks_path}")

        index = faiss.read_index(faiss_path)
        with open(chunks_path, "rb") as fh:
            chunks: List[DocumentChunk] = pickle.load(fh)

        vs = cls.__new__(cls)
        vs._dimension = index.d
        vs._index     = index
        vs._chunks    = chunks
        logger.info("VectorStore loaded: %d vectors from %s", index.ntotal, path)
        return vs

    def delete(self, path: str) -> None:
        """Remove persisted index files from disk."""
        for ext in (".faiss", ".chunks.pkl"):
            p = Path(f"{path}{ext}")
            if p.exists():
                p.unlink()
                logger.debug("Deleted: %s", p)

    # ---------------------------------------------------------------- #
    # Properties
    # ---------------------------------------------------------------- #

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal

    @property
    def dimension(self) -> int:
        return self._dimension


# ------------------------------------------------------------------ #
# Manager (multi-document registry)
# ------------------------------------------------------------------ #

class VectorStoreManager:
    """
    Registry for per-document VectorStore instances.

    Stores indexes in memory and on disk under ``storage_dir``.
    Automatically loads from disk on first access if not in memory.
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._dir: str  = storage_dir or settings.VECTOR_STORE_DIR
        self._cache: Dict[str, VectorStore] = {}
        Path(self._dir).mkdir(parents=True, exist_ok=True)

    def _path(self, document_id: str) -> str:
        return str(Path(self._dir) / document_id)

    # ---------------------------------------------------------------- #
    # CRUD
    # ---------------------------------------------------------------- #

    def create(
        self,
        document_id: str,
        embeddings: np.ndarray,
        chunks: List[DocumentChunk],
        dimension: int,
    ) -> VectorStore:
        """Create a new VectorStore, add data, persist, and cache it."""
        vs = VectorStore(dimension)
        vs.add(embeddings, chunks)
        vs.save(self._path(document_id))
        self._cache[document_id] = vs
        return vs

    def get(self, document_id: str) -> Optional[VectorStore]:
        """
        Return the VectorStore for ``document_id``, loading from disk if needed.

        Returns ``None`` if no index exists for this document.
        """
        if document_id in self._cache:
            return self._cache[document_id]
        path = self._path(document_id)
        if os.path.exists(f"{path}.faiss"):
            try:
                vs = VectorStore.load(path)
                self._cache[document_id] = vs
                return vs
            except Exception as exc:
                logger.error("Failed to load index for %s: %s", document_id, exc)
        return None

    def delete(self, document_id: str) -> bool:
        """Delete a VectorStore from memory and disk."""
        self._cache.pop(document_id, None)
        path = self._path(document_id)
        try:
            vs = VectorStore.__new__(VectorStore)
            vs.delete(path)
            return True
        except Exception:
            return False

    def exists(self, document_id: str) -> bool:
        """Return True if an index exists for ``document_id``."""
        return (
            document_id in self._cache
            or os.path.exists(f"{self._path(document_id)}.faiss")
        )


# Module-level singleton
vector_store_manager = VectorStoreManager()
