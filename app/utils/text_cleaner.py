"""
Text cleaning utilities for post-processing extracted and OCR-generated text.

All transforms are applied in a fixed, deterministic order.
"""

from __future__ import annotations

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Pre-compiled patterns (compiled once at import time)
# ------------------------------------------------------------------ #

# Long runs of underscores, pipes, or dots — common table/form artefacts
_ARTIFACTS = re.compile(r"[|]{2,}|_{3,}|\.{4,}")

# Multiple horizontal whitespace within a line
_MULTI_SPACE = re.compile(r"[ \t]+")

# Hyphenated line break → merge the two word halves
_HYPHEN_BREAK = re.compile(r"-\n")

# Single newline that should be a word-space (not a paragraph break)
# A "paragraph break" is defined as ≥ 2 consecutive newlines
_SINGLE_NL = re.compile(r"(?<!\n)\n(?!\n)")

# Three or more consecutive newlines → collapse to two
_EXCESS_NL = re.compile(r"\n{3,}")

# Slash surrounded by optional spaces (unit notation: "g / dL" → "g/dL")
_UNIT_SLASH = re.compile(r"(\w)\s*/\s*(\w)")

# Non-printable / control characters (except newline and tab)
_NON_PRINTABLE = re.compile(r"[^\x09\x0A\x20-\x7E\u00C0-\u024F]")


def clean_text(text: str, preserve_line_breaks: bool = False) -> str:
    """
    Normalise and clean text extracted from a medical document.

    Transformations applied (in order):
    1. **Unicode normalisation** (NFKC) — resolves ligatures, halfwidth chars, etc.
    2. **Artefact removal** — strips OCR table-rule characters (``____``, ``||||``, ...).
    3. **Hyphenated line-break merging** — ``hemo-\\nglobin`` → ``hemoglobin``.
    4. **Single newline → space** — only when ``preserve_line_breaks=False`` (OCR output).
       When ``True`` (digital PDFs), single newlines are kept so the lab extractor
       can read the multi-line structure.
    5. **Excess newlines** — 3+ consecutive newlines become 2.
    6. **Multiple spaces/tabs** → single space per line.
    7. **Per-line strip** — trims leading/trailing whitespace from each line.
    8. **Unit slash normalisation** — ``mg / dL`` → ``mg/dL``.
    9. **Non-printable character removal** — strips control characters.

    Args:
        text:                  Raw text from a PDF extractor or OCR engine.
        preserve_line_breaks:  When ``True``, single newlines are kept intact.
                               Use for digital PDF text where line structure is meaningful.
                               Default ``False`` preserves original OCR-merging behaviour.

    Returns:
        Cleaned, normalised text string. Returns ``""`` for empty/None input.
    """
    if not text:
        return ""

    original_len = len(text)

    text = unicodedata.normalize("NFKC", text)
    text = _ARTIFACTS.sub(" ", text)
    text = _HYPHEN_BREAK.sub("", text)

    if not preserve_line_breaks:
        text = _SINGLE_NL.sub(" ", text)

    text = _EXCESS_NL.sub("\n\n", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _UNIT_SLASH.sub(r"\1/\2", text)
    text = _NON_PRINTABLE.sub("", text)

    result = text.strip()
    logger.debug("clean_text: %d → %d chars (preserve_lines=%s)", original_len, len(result), preserve_line_breaks)
    return result
