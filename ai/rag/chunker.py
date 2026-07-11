"""
Document chunker — splits medical report text into overlapping chunks
with rich section-aware metadata.

Design goals:
- Preserve medical sections (lab results, diagnosis, medicines) together
  whenever they fit within the chunk size limit.
- Apply sliding-window overlap to avoid splitting key information across
  chunk boundaries.
- Tag every chunk with section, page, and positional metadata so the
  retriever and citation generator can reference the source precisely.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ------------------------------------------------------------------ #
# Section header patterns (used to detect natural boundaries)
# ------------------------------------------------------------------ #

_SECTION_HEADERS = re.compile(
    r"^(?:haematology|hematology|complete\s+blood\s+count|cbc|"
    r"biochemistry|clinical\s+chemistry|"
    r"lipid\s+profile|lipids|"
    r"liver\s+function|lft|"
    r"kidney\s+function|renal\s+function|"
    r"thyroid\s+function|thyroid|"
    r"coagulation|iron\s+studies|"
    r"urine\s+(?:analysis|examination|routine)|urinalysis|"
    r"serology|immunology|microbiology|"
    r"diagnosis|impression|assessment|clinical\s+(?:notes?|diagnosis)|"
    r"medications?|medicines?|prescription|treatment|"
    r"investigations?|test\s+results?|laboratory|"
    r"patient\s+(?:information|details?)|demographics?)\s*[:\-]?\s*$",
    re.IGNORECASE,
)


# ------------------------------------------------------------------ #
# Chunk data class
# ------------------------------------------------------------------ #

@dataclass
class DocumentChunk:
    """A single chunk of a medical document with full provenance metadata."""

    chunk_id:     str
    text:         str
    section:      str          # detected section name (e.g. "Haematology")
    page_number:  Optional[int]
    source_file:  str
    word_count:   int
    char_count:   int
    chunk_index:  int          # 0-based position among all chunks
    total_chunks: int = 0      # filled in after all chunks are created
    overlap_with_prev: bool = False

    def __post_init__(self) -> None:
        if not self.chunk_id:
            self.chunk_id = str(uuid.uuid4())


# ------------------------------------------------------------------ #
# Chunker
# ------------------------------------------------------------------ #

class DocumentChunker:
    """
    Splits medical report text into semantically-aware, overlapping chunks.

    Algorithm:
    1. Split text into lines, detecting section headers.
    2. Group lines into named sections.
    3. For each section, emit one chunk if it fits within ``max_words``; otherwise
       apply a sliding-window split with ``overlap_words`` of context.
    4. Attach chunk ID, section, page estimate, and positional metadata.
    """

    def __init__(
        self,
        max_words: int   = 0,
        overlap_words: int = 0,
    ) -> None:
        self._max_words     = max_words     or settings.CHUNK_SIZE_WORDS
        self._overlap_words = overlap_words or settings.CHUNK_OVERLAP_WORDS

    def chunk(
        self,
        text: str,
        source_file: str = "",
        document_id: str = "",
    ) -> List[DocumentChunk]:
        """
        Split ``text`` into overlapping chunks with metadata.

        Args:
            text:        Cleaned extracted text from Phase 2.
            source_file: Original filename (for citations).
            document_id: Document UUID (used to build chunk IDs).

        Returns:
            Ordered list of :class:`DocumentChunk` objects.
        """
        if not text or not text.strip():
            return []

        lines = [ln.rstrip() for ln in text.split("\n")]
        sections = self._detect_sections(lines)
        chunks: List[DocumentChunk] = []

        for section_name, section_lines in sections:
            section_chunks = self._chunk_section(
                section_lines, section_name, source_file, document_id
            )
            chunks.extend(section_chunks)

        # Assign sequential indices and total count
        for i, chunk in enumerate(chunks):
            chunk.chunk_index  = i
            chunk.total_chunks = len(chunks)

        logger.info(
            "Chunker: %d chunks from %d chars (max_words=%d, overlap=%d)",
            len(chunks), len(text), self._max_words, self._overlap_words,
        )
        return chunks

    # ---------------------------------------------------------------- #
    # Section detection
    # ---------------------------------------------------------------- #

    def _detect_sections(
        self, lines: List[str]
    ) -> List[tuple[str, List[str]]]:
        """
        Split lines into (section_name, lines) groups.

        Lines before the first named section are grouped as "Header".
        """
        sections: List[tuple[str, List[str]]] = []
        current_section = "Header"
        current_lines:   List[str] = []

        for line in lines:
            stripped = line.strip()
            if _SECTION_HEADERS.match(stripped):
                if current_lines:
                    sections.append((current_section, current_lines))
                current_section = stripped.title().rstrip(":").rstrip("-").strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_section, current_lines))

        return sections if sections else [("Document", lines)]

    # ---------------------------------------------------------------- #
    # Window-based chunking within a section
    # ---------------------------------------------------------------- #

    def _chunk_section(
        self,
        lines:       List[str],
        section:     str,
        source_file: str,
        document_id: str,
    ) -> List[DocumentChunk]:
        """Split a single section's lines into chunks."""
        text = "\n".join(lines).strip()
        if not text:
            return []

        words = text.split()
        total_words = len(words)

        # Section fits in one chunk — keep it whole
        if total_words <= self._max_words:
            return [self._make_chunk(text, section, source_file, document_id, is_overlap=False)]

        # Sliding window
        chunks: List[DocumentChunk] = []
        start = 0

        while start < total_words:
            end  = min(start + self._max_words, total_words)
            chunk_text = " ".join(words[start:end])
            chunks.append(
                self._make_chunk(
                    chunk_text, section, source_file, document_id,
                    is_overlap=(start > 0),
                )
            )
            if end >= total_words:
                break
            start = end - self._overlap_words  # slide back by overlap

        return chunks

    @staticmethod
    def _make_chunk(
        text:        str,
        section:     str,
        source_file: str,
        document_id: str,
        is_overlap:  bool,
    ) -> DocumentChunk:
        chunk_id = f"{document_id or 'doc'}-{uuid.uuid4().hex[:8]}"
        words    = text.split()
        return DocumentChunk(
            chunk_id=chunk_id,
            text=text.strip(),
            section=section,
            page_number=None,       # Phase 2 does not yet preserve per-chunk pages
            source_file=source_file,
            word_count=len(words),
            char_count=len(text),
            chunk_index=0,          # set later
            overlap_with_prev=is_overlap,
        )


# Module-level singleton
document_chunker = DocumentChunker()
