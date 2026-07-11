"""
Token counter — estimates and tracks Gemini token usage.

The Google GenAI SDK returns exact token counts in response metadata.
This module provides helpers to estimate pre-request tokens and
accumulate usage statistics for logging.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Approximate characters per token for Gemini (rough heuristic)
_CHARS_PER_TOKEN: float = 4.0


def estimate_tokens(text: str) -> int:
    """
    Estimate the token count of a text string without calling the API.

    Uses a character-based heuristic (4 chars ≈ 1 token).
    Not exact — use only for pre-flight checks and logging.

    Args:
        text: Input text string.

    Returns:
        Estimated token count (integer).
    """
    return max(1, int(len(text) / _CHARS_PER_TOKEN))


@dataclass
class TokenUsage:
    """Accumulated token usage across multiple Gemini calls."""

    prompt_tokens:   int = 0
    response_tokens: int = 0
    total_tokens:    int = 0
    call_count:      int = 0

    def add(self, prompt: int, response: int, total: int) -> None:
        """Record usage from one API call."""
        self.prompt_tokens   += prompt
        self.response_tokens += response
        self.total_tokens    += total or (prompt + response)
        self.call_count      += 1

    def log(self, context: str = "") -> None:
        """Log a summary of accumulated usage."""
        label = f"[{context}] " if context else ""
        logger.info(
            "%sToken usage: %d calls | %d prompt + %d response = %d total",
            label,
            self.call_count,
            self.prompt_tokens,
            self.response_tokens,
            self.total_tokens,
        )
