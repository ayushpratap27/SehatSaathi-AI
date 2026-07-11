"""
Similarity search utilities — cosine similarity and top-K filtering.

Used by the retriever and reranker to compute and compare vector distances.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def normalize_l2(vectors: np.ndarray) -> np.ndarray:
    """
    L2-normalise a matrix of row vectors in-place.

    After normalisation, inner-product search (IndexFlatIP) in FAISS
    is equivalent to cosine similarity.

    Args:
        vectors: Float32 array of shape ``(n, dim)``.

    Returns:
        The same array, normalised in-place.
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)   # prevent division by zero
    vectors /= norms
    return vectors


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1-D vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Similarity score in [−1, 1] (higher = more similar).
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def top_k_by_score(
    items: List[Tuple[object, float]],
    k: int,
    threshold: float = 0.0,
) -> List[Tuple[object, float]]:
    """
    Filter and sort ``items`` by score, returning at most ``k`` results
    above ``threshold``.

    Args:
        items:     List of (item, score) pairs.
        k:         Maximum number of results.
        threshold: Minimum score to include (items below are discarded).

    Returns:
        Up to ``k`` (item, score) pairs, sorted descending by score.
    """
    filtered = [(item, score) for item, score in items if score >= threshold]
    filtered.sort(key=lambda x: x[1], reverse=True)
    return filtered[:k]


def mean_similarity(scores: List[float]) -> float:
    """Return the mean of a list of similarity scores, or 0.0 for empty."""
    return float(np.mean(scores)) if scores else 0.0
