"""
Chat Service — answers user questions grounded strictly in report data.

Gemini receives:
  - Structured JSON from Phase 3 (ParsedReport)
  - Clinical analysis JSON from Phase 4 (ReportAnalysisResult)
  - The user's plain-text question

Gemini NEVER receives raw PDFs, OCR output, or unstructured text.
Every answer is constrained to information present in the provided JSON.
"""

from __future__ import annotations

import logging
from typing import Optional

from ai.gemini.gemini_client import GeminiClient, gemini_client
from ai.gemini.prompt_templates import chat_prompt, strict_retry_prompt
from ai.gemini.response_validator import ResponseValidator, response_validator
from app.config.settings import get_settings
from app.schemas.ai import ChatResponse
from app.schemas.analysis import ReportAnalysisResult
from app.schemas.report import ParsedReport

logger = logging.getLogger(__name__)
_settings = get_settings()

_NOT_AVAILABLE = "This information is not available in the uploaded report."


class ChatService:
    """
    Answers natural-language questions about a patient's medical report.

    The service ensures every answer is grounded in the structured data
    and refuses to speculate, diagnose, or prescribe.
    """

    def __init__(
        self,
        gemini: Optional[GeminiClient] = None,
        validator: Optional[ResponseValidator] = None,
    ) -> None:
        self._gemini    = gemini    or gemini_client
        self._validator = validator or response_validator

    async def answer(
        self,
        question: str,
        report: ParsedReport,
        analysis: Optional[ReportAnalysisResult] = None,
    ) -> ChatResponse:
        """
        Generate a grounded answer to a user's question about their report.

        Args:
            question: The user's natural-language question.
            report:   Structured report (Phase 3 output).
            analysis: Clinical analysis (Phase 4 output, optional).

        Returns:
            :class:`~app.schemas.ai.ChatResponse` with a safe, grounded answer.
        """
        logger.info("Chat question: %r", question[:100])

        prompt = chat_prompt(question, report, analysis)
        result = await self._gemini.generate(prompt)

        is_valid, reason = self._validator.validate(result.text, report)

        if not is_valid:
            logger.warning("Chat response invalid (%s) — retrying", reason)
            retry_p = strict_retry_prompt(prompt, reason)
            result  = await self._gemini.generate(retry_p)
            is_valid, reason = self._validator.validate(result.text, report)

            if not is_valid:
                logger.error("Chat response still invalid after retry: %s", reason)
                return ChatResponse(
                    answer=(
                        "I was unable to generate a safe answer for this question. "
                        "Please consult your healthcare provider directly."
                    ),
                    tokens_used=result.tokens_used,
                )

        answer_text = result.text.strip()

        # Ensure the answer isn't empty
        if not answer_text:
            answer_text = _NOT_AVAILABLE

        return ChatResponse(
            answer=answer_text,
            model_used=_settings.GROQ_MODEL,
            tokens_used=result.tokens_used,
        )


# Module-level singleton
chat_service = ChatService()
