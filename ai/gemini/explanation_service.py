"""
Explanation Service — generates plain-language explanations for every
medical entity in a report (lab tests, medicines, diagnoses).

Input:  ParsedReport + ReportAnalysisResult
Output: ExplanationResponse with per-item explanations
"""

from __future__ import annotations

import logging
from typing import List, Optional

from ai.gemini.gemini_client import GeminiClient, gemini_client
from ai.gemini.prompt_templates import explanation_prompt, strict_retry_prompt
from ai.gemini.response_validator import ResponseValidator, extract_json, response_validator
from app.config.settings import get_settings
from app.schemas.ai import ExplanationItem, ExplanationResponse
from app.schemas.analysis import ReportAnalysisResult
from app.schemas.report import ParsedReport

_settings = get_settings()

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Generates simple, patient-friendly explanations for medical report entities.

    Covers:
    - Abnormal/critical lab tests (value + context)
    - Diagnoses listed in the report
    - Medicines mentioned in the report
    """

    def __init__(
        self,
        gemini: Optional[GeminiClient] = None,
        validator: Optional[ResponseValidator] = None,
    ) -> None:
        self._gemini    = gemini    or gemini_client
        self._validator = validator or response_validator

    async def explain(
        self,
        report: ParsedReport,
        analysis: Optional[ReportAnalysisResult] = None,
    ) -> ExplanationResponse:
        """
        Generate explanations for all entities in the report.

        Args:
            report:   Structured report from Phase 3.
            analysis: Clinical analysis from Phase 4 (optional).

        Returns:
            :class:`~app.schemas.ai.ExplanationResponse`.
        """
        prompt = explanation_prompt(report, analysis)

        result = await self._gemini.generate(prompt)
        is_valid, reason = self._validator.validate(result.text, report)

        if not is_valid:
            logger.warning("Explanation validation failed (%s) — retrying", reason)
            retry_p = strict_retry_prompt(prompt, reason)
            result  = await self._gemini.generate(retry_p)
            is_valid, reason = self._validator.validate(result.text, report)
            if not is_valid:
                logger.error("Explanation still invalid after retry: %s", reason)
                return self._fallback_explanations(report, result.tokens_used)

        data = extract_json(result.text)
        if not data:
            return self._fallback_explanations(report, result.tokens_used)

        items: List[ExplanationItem] = []
        for entry in data.get("explanations", []):
            if isinstance(entry, dict):
                items.append(ExplanationItem(
                    term=entry.get("term", "Unknown"),
                    category=entry.get("category", "medical_term"),
                    value=entry.get("value"),
                    explanation=entry.get("explanation", "Explanation not available."),
                ))

        return ExplanationResponse(
            explanations=items,
            model_used=_settings.GROQ_MODEL,
            tokens_used=result.tokens_used,
        )

    def _fallback_explanations(
        self, report: ParsedReport, tokens: int
    ) -> ExplanationResponse:
        """Return minimal explanations when Gemini fails."""
        items: List[ExplanationItem] = []

        for test in report.tests:
            if test.status and test.status not in ("Normal", "Unknown"):
                items.append(ExplanationItem(
                    term=test.test_name,
                    category="lab_test",
                    value=f"{test.value} {test.unit or ''}".strip() if test.value else None,
                    explanation=(
                        f"{test.test_name} is a laboratory test. "
                        "Please consult your healthcare provider for interpretation."
                    ),
                ))

        for diag in report.diagnosis:
            items.append(ExplanationItem(
                term=diag,
                category="diagnosis",
                explanation="Please consult your healthcare provider for details about this finding.",
            ))

        for med in report.medicines:
            items.append(ExplanationItem(
                term=med.name,
                category="medicine",
                explanation="Please consult your healthcare provider for information about this medicine.",
            ))

        return ExplanationResponse(
            explanations=items,
            tokens_used=tokens,
        )


# Module-level singleton
explanation_service = ExplanationService()
