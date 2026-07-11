"""
Reranker — reorders retrieved chunks to surface the most clinically
relevant content before it is sent to Gemini.

The reranker performs three lightweight passes:
1. Deduplication — removes near-duplicate chunks (Jaccard similarity > 0.85).
2. Section boost  — elevates chunks from high-priority medical sections.
3. Final sort     — combines original FAISS score + section boost into a
                    weighted composite score.
"""

from __future__ import annotations

import logging
import re
from typing import List, Set

from ai.rag.vector_store import SearchResult

logger = logging.getLogger(__name__)

# Sections whose content should be prioritised when relevant to the question
_PRIORITY_SECTIONS: Set[str] = {
    "haematology", "hematology", "biochemistry", "diagnosis", "impression",
    "medicines", "medication", "prescription", "laboratory", "investigations",
    "thyroid", "lipid profile", "liver function", "kidney function",
    "complete blood count", "cbc",
}

_BOOST_FACTOR:  float = 0.10   # added to score for priority-section chunks
_DEDUP_THRESH:  float = 0.85   # Jaccard similarity above which chunks are merged


def _tokenise(text: str) -> Set[str]:
    """Lower-case word-level tokenisation for Jaccard overlap calculation."""
    return set(re.findall(r"\b[a-z0-9]+\b", text.lower()))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


class Reranker:
    """
    Reorders FAISS search results for better clinical relevance.

    The strategy is intentionally lightweight (O(n²) dedup on small lists)
    to keep latency minimal. A future phase may replace this with a
    cross-encoder model.
    """

    def rerank(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Reorder ``results`` for improved clinical relevance.

        Steps:
        1. Deduplicate near-identical chunks.
        2. Boost chunks from priority medical sections.
        3. Sort by composite score.

        Args:
            results: List of FAISS search results (already sorted by score).

        Returns:
            Reordered list (same or fewer elements after deduplication).
        """
        if len(results) <= 1:
            return results

        deduplicated = self._deduplicate(results)
        boosted      = self._boost_priority_sections(deduplicated)

        # Sort by final composite score descending
        boosted.sort(key=lambda r: r.score, reverse=True)

        logger.debug(
            "Reranker: %d → %d chunks after dedup + boost",
            len(results), len(boosted),
        )
        return boosted

    # ---------------------------------------------------------------- #
    # Deduplication
    # ---------------------------------------------------------------- #

    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove chunks with high text overlap with a higher-ranked chunk."""
        kept:  List[SearchResult] = []
        token_sets: List[Set[str]] = []

        for result in results:
            tokens = _tokenise(result.chunk.text)
            is_dup = any(
                _jaccard(tokens, existing) >= _DEDUP_THRESH
                for existing in token_sets
            )
            if not is_dup:
                kept.append(result)
                token_sets.append(tokens)

        return kept

    # ---------------------------------------------------------------- #
    # Section boosting
    # ---------------------------------------------------------------- #

    def _boost_priority_sections(
        self, results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Add a small score boost to chunks from clinically important sections.

        Modifies scores in-place on copies to avoid mutating the originals.
        """
        boosted: List[SearchResult] = []
        for result in results:
            section_lc = result.chunk.section.lower()
            is_priority = any(ps in section_lc for ps in _PRIORITY_SECTIONS)
            new_score = result.score + (_BOOST_FACTOR if is_priority else 0.0)
            # Create a shallow copy with the updated score
            updated = SearchResult(
                chunk=result.chunk,
                score=min(new_score, 1.0),   # cap at 1.0
                faiss_index=result.faiss_index,
            )
            boosted.append(updated)
        return boosted


# Module-level singleton
reranker = Reranker()
