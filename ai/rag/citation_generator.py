"""
Citation Generator — produces source citations for retrieved chunks.

Each citation tells the user exactly where in their report the answer
came from: section, page (if available), similarity score, and a short
text preview.
"""

from __future__ import annotations

import logging
from typing import List

from ai.rag.vector_store import SearchResult
from app.schemas.rag import CitationSource

logger = logging.getLogger(__name__)

_PREVIEW_LEN = 120   # characters for the text preview


class CitationGenerator:
    """Converts retrieval results into user-facing citation objects."""

    def generate(self, results: List[SearchResult]) -> List[CitationSource]:
        """
        Build a :class:`~app.schemas.rag.CitationSource` for every result.

        Args:
            results: Reranked list of FAISS search results.

        Returns:
            List of citation objects (one per retrieved chunk).
        """
        citations: List[CitationSource] = []
        seen_previews: set[str] = set()

        for result in results:
            preview = result.chunk.text[:_PREVIEW_LEN].strip()
            # Deduplicate citations with identical preview text
            if preview in seen_previews:
                continue
            seen_previews.add(preview)

            citations.append(CitationSource(
                page=result.chunk.page_number,
                section=result.chunk.section,
                score=round(result.score, 4),
                preview=preview,
            ))

        logger.debug("CitationGenerator: %d citations", len(citations))
        return citations


# Module-level singleton
citation_generator = CitationGenerator()
