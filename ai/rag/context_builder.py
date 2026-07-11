"""
Context Builder — assembles retrieved chunks into a grounded Gemini prompt.

Responsibilities:
- Merge reranked chunks into a numbered context block.
- Enforce a character budget so the prompt fits within Gemini's token window.
- Inject conversation history for multi-turn awareness.
- Embed medical safety guardrails (no diagnosis, no prescription).
"""

from __future__ import annotations

import logging
from typing import List

from ai.rag.vector_store import SearchResult
from app.config.settings import get_settings
from app.schemas.rag import ConversationTurn

logger = logging.getLogger(__name__)
settings = get_settings()

_SYSTEM_PREAMBLE = """You are SehatSaathi, a concise medical assistant that helps patients understand their health reports.

GUIDELINES:
1. Keep every answer to 3-5 sentences maximum. Be direct and to the point.
2. Use the patient's report context when available. For questions not in the report, answer from general medical knowledge.
3. Use plain, simple language. If you use a medical term, explain it in two words right after.
4. Be warm and reassuring.
5. Never diagnose or prescribe. End with "Please consult your doctor." only when relevant.
6. Never repeat yourself or pad the answer. One clear, short response.
"""

_NO_CONTEXT_ANSWER = (
    "The uploaded report does not contain enough information to answer this question."
)


class ContextBuilder:
    """
    Builds a Gemini-ready prompt from retrieved document chunks and
    optional conversation history.
    """

    def __init__(self, max_context_chars: int = 0) -> None:
        self._max_chars = max_context_chars or settings.RAG_MAX_CONTEXT_CHARS

    def build(
        self,
        question: str,
        results:  List[SearchResult],
        history:  List[ConversationTurn] | None = None,
    ) -> str:
        """
        Assemble the full prompt for Gemini.

        Args:
            question: The user's current question.
            results:  Reranked retrieval results.
            history:  Last N conversation turns (oldest first).

        Returns:
            A complete prompt string ready to send to Gemini.
        """
        if not results:
            # No context — let the LLM answer from general knowledge
            return (
                f"{_SYSTEM_PREAMBLE}\n\n"
                "NOTE: No specific information was found in the patient's uploaded report for this question.\n"
                "Answer in 2-3 short sentences using general medical knowledge. Be brief.\n\n"
                f"QUESTION: {question}\n"
            )

        context_block = self._build_context_block(results)
        history_block = self._build_history_block(history or [])

        prompt_parts = [_SYSTEM_PREAMBLE]

        if history_block:
            prompt_parts.append(history_block)

        prompt_parts.append(
            f"RETRIEVED CONTEXT FROM THE PATIENT'S REPORT:\n{context_block}"
        )
        prompt_parts.append(f"CURRENT QUESTION: {question}")
        prompt_parts.append(
            "Answer in 3-5 short sentences. Be direct — no repetition, no padding. "
            "Use plain language a non-medical person can understand."
        )

        return "\n\n".join(prompt_parts)

    def _build_context_block(self, results: List[SearchResult]) -> str:
        """Format chunks into a numbered, source-labelled block."""
        parts: List[str] = []
        total_chars = 0

        for i, result in enumerate(results, start=1):
            page_str    = f"Page {result.chunk.page_number}" if result.chunk.page_number else ""
            section_str = result.chunk.section
            source_line = " | ".join(filter(None, [section_str, page_str]))
            header      = f"[Context {i}: {source_line} | Score: {result.score:.2f}]"
            block       = f"{header}\n{result.chunk.text}"

            if total_chars + len(block) > self._max_chars:
                logger.debug("ContextBuilder: budget reached at chunk %d/%d", i, len(results))
                break

            parts.append(block)
            total_chars += len(block)

        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _build_history_block(history: List[ConversationTurn]) -> str:
        """Format prior conversation turns into a readable block."""
        if not history:
            return ""
        limit = settings.RAG_CONVERSATION_HISTORY_LIMIT
        trimmed = history[-limit:]  # keep only the most recent N turns
        lines = ["CONVERSATION HISTORY (use for context, not as new sources):"]
        for turn in trimmed:
            prefix = "Patient" if turn.role == "user" else "Assistant"
            lines.append(f"{prefix}: {turn.content}")
        return "\n".join(lines)


# Module-level singleton
context_builder = ContextBuilder()
