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

_SYSTEM_PREAMBLE = """You are a medical report assistant.

STRICT RULES:
1. Answer using ONLY the retrieved context below — do NOT use external knowledge.
2. If the answer is not in the context, respond exactly:
   "The uploaded report does not contain enough information to answer this question."
3. Never diagnose diseases or recommend medicines.
4. Always end your answer with: "Please consult your healthcare provider."
5. Keep answers concise and patient-friendly.
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
            # No context — return a prompt that forces the "not available" answer
            return (
                f"{_SYSTEM_PREAMBLE}\n\n"
                "RETRIEVED CONTEXT:\n(No relevant context was found in the report.)\n\n"
                f"QUESTION: {question}\n\n"
                "Answer exactly: \"The uploaded report does not contain enough "
                "information to answer this question.\""
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
            "Answer using ONLY the retrieved context. "
            "If the answer is not there, say the report does not contain enough information."
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
