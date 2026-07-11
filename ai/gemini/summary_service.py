"""
Summary Service — generates an AI-powered executive summary of a medical report.

Input:  ParsedReport + ReportAnalysisResult (Phase 3 + Phase 4 outputs)
Output: SummaryResponse (structured JSON summary from Gemini)
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from ai.gemini.gemini_client import GeminiClient, gemini_client
from ai.gemini.prompt_templates import strict_retry_prompt, summary_prompt
from ai.gemini.response_validator import ResponseValidator, extract_json, response_validator
from app.schemas.ai import AbnormalTestExplanation, SummaryResponse
from app.schemas.analysis import ReportAnalysisResult
from app.schemas.report import ParsedReport

logger = logging.getLogger(__name__)


class SummaryService:
    """
    Generates structured, AI-powered summaries of medical reports.

    Gemini receives only pre-structured JSON from Phase 3 and Phase 4 —
    never raw PDFs, never OCR output, never unstructured text.
    """

    def __init__(
        self,
        gemini: Optional[GeminiClient] = None,
        validator: Optional[ResponseValidator] = None,
    ) -> None:
        self._gemini    = gemini    or gemini_client
        self._validator = validator or response_validator

    async def summarise(
        self,
        report: ParsedReport,
        analysis: Optional[ReportAnalysisResult] = None,
    ) -> SummaryResponse:
        """
        Generate a structured executive summary using Gemini.

        Args:
            report:   Structured report from Phase 3 ``/parse``.
            analysis: Clinical analysis from Phase 4 ``/analyze`` (optional).

        Returns:
            :class:`~app.schemas.ai.SummaryResponse` with all summary fields.
        """
        prompt = summary_prompt(report, analysis)

        # First attempt
        result = await self._gemini.generate(prompt)
        is_valid, reason = self._validator.validate(result.text, report)

        # Retry once with stricter prompt if validation fails
        if not is_valid:
            logger.warning("Summary validation failed (%s) — retrying", reason)
            retry_p = strict_retry_prompt(prompt, reason)
            result  = await self._gemini.generate(retry_p)
            is_valid, reason = self._validator.validate(result.text, report)
            if not is_valid:
                logger.error("Summary still invalid after retry: %s", reason)
                # Fall back to a minimal safe summary
                return self._fallback_summary(report, analysis, result.tokens_used)

        data = extract_json(result.text)
        if not data:
            logger.warning("Could not parse JSON from summary response — using fallback")
            return self._fallback_summary(report, analysis, result.tokens_used)

        return self._build_response(data, result.tokens_used)

    def _build_response(self, data: dict, tokens: int) -> SummaryResponse:
        """Construct SummaryResponse from parsed Gemini JSON."""
        # Parse abnormal_tests list
        abnormal: List[AbnormalTestExplanation] = []
        for item in data.get("abnormal_tests", []):
            if isinstance(item, dict):
                abnormal.append(AbnormalTestExplanation(
                    test_name=item.get("test_name", "Unknown"),
                    value=item.get("value"),
                    unit=item.get("unit"),
                    status=item.get("status"),
                    explanation=item.get("explanation", ""),
                ))

        return SummaryResponse(
            executive_summary=data.get("executive_summary", "Summary not available."),
            patient_summary=data.get("patient_summary", "Patient summary not available."),
            important_findings=data.get("important_findings", []),
            abnormal_tests=abnormal,
            medicines=data.get("medicines", []),
            diagnosis=data.get("diagnosis", []),
            follow_up=data.get("follow_up", []),
            model_used=__import__("app.config.settings", fromlist=["get_settings"]).get_settings().GEMINI_MODEL,
            tokens_used=tokens,
        )

    def _fallback_summary(
        self,
        report: ParsedReport,
        analysis: Optional[ReportAnalysisResult],
        tokens: int,
    ) -> SummaryResponse:
        """Return a minimal safe summary when Gemini fails or produces invalid output."""
        test_names = [t.test_name for t in report.tests[:5]]
        return SummaryResponse(
            executive_summary=(
                "An AI summary could not be generated for this report. "
                "Please review the structured report data directly."
            ),
            patient_summary=(
                "We were unable to generate a patient-friendly summary at this time. "
                "Please consult your healthcare provider for interpretation."
            ),
            important_findings=test_names,
            medicines=[m.name for m in report.medicines],
            diagnosis=report.diagnosis,
            follow_up=["Consult your healthcare provider for a full interpretation."],
            tokens_used=tokens,
        )


# Module-level singleton
summary_service = SummaryService()
