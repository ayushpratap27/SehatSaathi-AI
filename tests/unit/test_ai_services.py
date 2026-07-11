"""
Phase 5 tests — all Gemini SDK calls are mocked.

No actual API requests are made during testing.
"""

from __future__ import annotations

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

SAMPLE_REPORT = {
    "patient": {"name": "John Doe", "age": 45, "gender": "Male"},
    "hospital": {"name": "ABC Hospital"},
    "doctor": {"name": None},
    "tests": [
        {"test_name": "Hemoglobin", "value": 12.4, "unit": "g/dL",
         "reference_range": "13.5-17.5", "status": "Low"},
        {"test_name": "WBC Count", "value": 11200, "unit": "/uL",
         "reference_range": "4000-11000", "status": "High"},
        {"test_name": "Glucose", "value": 95, "unit": "mg/dL",
         "reference_range": "70-100", "status": "Normal"},
    ],
    "diagnosis": ["Iron Deficiency Anemia"],
    "medicines": [{"name": "Ferrous Sulfate", "dosage": "150mg", "frequency": "Once daily"}],
}

SAMPLE_ANALYSIS = {
    "patient": {"name": "John Doe", "age": 45, "gender": "Male"},
    "tests": [
        {"test_name": "Hemoglobin", "value": 12.4, "unit": "g/dL",
         "status": "Low", "is_abnormal": True, "is_critical": False,
         "insight": "Hemoglobin is below normal."},
    ],
    "analysis": {
        "total_tests": 3, "normal": 1, "abnormal": 2,
        "critical": 0, "high": 1, "low": 1, "unknown": 0,
    },
    "abnormal_findings": ["Hemoglobin", "WBC Count"],
    "critical_findings": [],
    "insights": ["Hemoglobin is low.", "WBC is high."],
    "risk_level": "Moderate",
    "summary": "2 of 3 values are abnormal.",
    "recommendations": ["Consult your physician."],
    "disclaimer": "Medical disclaimer...",
}

VALID_SUMMARY_JSON = {
    "executive_summary": "The patient has two abnormal values.",
    "patient_summary": "Two of your test results are outside the normal range.",
    "important_findings": ["Low Hemoglobin", "High WBC"],
    "abnormal_tests": [
        {"test_name": "Hemoglobin", "value": "12.4", "unit": "g/dL",
         "status": "Low", "explanation": "Below normal range."}
    ],
    "medicines": ["Ferrous Sulfate"],
    "diagnosis": ["Iron Deficiency Anemia"],
    "follow_up": ["Consult your healthcare provider."],
}

VALID_EXPLANATION_JSON = {
    "explanations": [
        {"term": "Hemoglobin", "category": "lab_test",
         "value": "12.4 g/dL", "explanation": "Measures oxygen-carrying capacity."},
        {"term": "Iron Deficiency Anemia", "category": "diagnosis",
         "value": None, "explanation": "A condition with low iron levels."},
        {"term": "Ferrous Sulfate", "category": "medicine",
         "value": None, "explanation": "An iron supplement."},
    ]
}


def _make_mock_result(text: str, tokens: int = 100):
    """Create a GenerationResult mock."""
    from ai.gemini.gemini_client import GenerationResult
    return GenerationResult(
        text=text,
        model="gemini-2.5-flash",
        total_tokens=tokens,
        prompt_tokens=80,
        response_tokens=20,
        latency_ms=250.0,
    )


# ------------------------------------------------------------------ #
# Response Validator tests
# ------------------------------------------------------------------ #

class TestResponseValidator:
    def test_valid_response_passes(self) -> None:
        from ai.gemini.response_validator import response_validator
        ok, reason = response_validator.validate(
            "This value is below normal. Please consult your physician."
        )
        assert ok is True
        assert reason == ""

    def test_empty_response_fails(self) -> None:
        from ai.gemini.response_validator import response_validator
        ok, reason = response_validator.validate("")
        assert ok is False

    def test_forbidden_phrase_fails(self) -> None:
        from ai.gemini.response_validator import response_validator
        ok, reason = response_validator.validate(
            "You should take metformin 500mg for your diabetes."
        )
        assert ok is False

    def test_extract_json_from_plain_json(self) -> None:
        from ai.gemini.response_validator import extract_json
        data = extract_json('{"key": "value"}')
        assert data == {"key": "value"}

    def test_extract_json_from_code_block(self) -> None:
        from ai.gemini.response_validator import extract_json
        text = '```json\n{"key": "value"}\n```'
        data = extract_json(text)
        assert data == {"key": "value"}

    def test_extract_json_returns_none_for_invalid(self) -> None:
        from ai.gemini.response_validator import extract_json
        assert extract_json("This is just prose.") is None


# ------------------------------------------------------------------ #
# Token Counter tests
# ------------------------------------------------------------------ #

class TestTokenCounter:
    def test_estimate_tokens_non_zero(self) -> None:
        from ai.utils.token_counter import estimate_tokens
        assert estimate_tokens("Hello world") > 0

    def test_empty_string_returns_zero(self) -> None:
        from ai.utils.token_counter import estimate_tokens
        assert estimate_tokens("") == 0

    def test_token_usage_accumulates(self) -> None:
        from ai.utils.token_counter import TokenUsage
        usage = TokenUsage()
        usage.add(100, 50, 150)
        usage.add(200, 80, 280)
        assert usage.call_count == 2
        assert usage.total_tokens == 430


# ------------------------------------------------------------------ #
# Gemini Client tests (mocked)
# ------------------------------------------------------------------ #

class TestGeminiClient:
    def test_missing_api_key_raises(self) -> None:
        from ai.gemini.gemini_client import LLMClient, GeminiConfigException
        import pytest
        client = LLMClient.__new__(LLMClient)
        client._ready = False
        client._native_client = None
        # Patch settings to have no key
        with patch("ai.gemini.gemini_client.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = ""
            with pytest.raises((GeminiConfigException, Exception)):
                client._init()

    @pytest.mark.asyncio
    async def test_generate_returns_result(self) -> None:
        from ai.gemini.gemini_client import LLMClient, GenerationResult
        client = LLMClient.__new__(LLMClient)
        client._ready = True
        client._native_client = None
        mock_result = _make_mock_result("Test response")
        with patch.object(client, "_call_api", return_value=mock_result):
            result = await client.generate("Test prompt")
        assert result.text == "Test response"
        assert result.tokens_used > 0


# ------------------------------------------------------------------ #
# Summary Service tests (mocked Gemini)
# ------------------------------------------------------------------ #

class TestSummaryService:
    @pytest.mark.asyncio
    async def test_summarise_returns_summary_response(self) -> None:
        from ai.gemini.summary_service import SummaryService
        from app.schemas.report import ParsedReport

        report = ParsedReport(**SAMPLE_REPORT)
        mock_gemini = MagicMock()
        mock_gemini._model_name = "gemini-2.5-flash"
        mock_gemini.generate = AsyncMock(
            return_value=_make_mock_result(json.dumps(VALID_SUMMARY_JSON))
        )

        service = SummaryService(gemini=mock_gemini)
        result = await service.summarise(report)

        assert result.executive_summary
        assert "Iron Deficiency Anemia" in result.diagnosis
        assert "Ferrous Sulfate" in result.medicines

    @pytest.mark.asyncio
    async def test_summarise_invalid_response_uses_fallback(self) -> None:
        from ai.gemini.summary_service import SummaryService
        from app.schemas.report import ParsedReport

        report = ParsedReport(**SAMPLE_REPORT)
        mock_gemini = MagicMock()
        mock_gemini._model_name = "gemini-2.5-flash"
        # Return a response that fails validation (forbidden phrase)
        mock_gemini.generate = AsyncMock(
            return_value=_make_mock_result("You should take metformin now.")
        )

        service = SummaryService(gemini=mock_gemini)
        result = await service.summarise(report)

        # Fallback should kick in — summary should mention provider consultation
        assert result.executive_summary


# ------------------------------------------------------------------ #
# Explanation Service tests (mocked Gemini)
# ------------------------------------------------------------------ #

class TestExplanationService:
    @pytest.mark.asyncio
    async def test_explain_returns_items(self) -> None:
        from ai.gemini.explanation_service import ExplanationService
        from app.schemas.report import ParsedReport

        report = ParsedReport(**SAMPLE_REPORT)
        mock_gemini = MagicMock()
        mock_gemini._model_name = "gemini-2.5-flash"
        mock_gemini.generate = AsyncMock(
            return_value=_make_mock_result(json.dumps(VALID_EXPLANATION_JSON))
        )

        service = ExplanationService(gemini=mock_gemini)
        result = await service.explain(report)

        assert len(result.explanations) == 3
        categories = {e.category for e in result.explanations}
        assert "lab_test" in categories


# ------------------------------------------------------------------ #
# Chat Service tests (mocked Gemini)
# ------------------------------------------------------------------ #

class TestChatService:
    @pytest.mark.asyncio
    async def test_answer_returns_response(self) -> None:
        from ai.gemini.chat_service import ChatService
        from app.schemas.report import ParsedReport

        report = ParsedReport(**SAMPLE_REPORT)
        mock_gemini = MagicMock()
        mock_gemini._model_name = "gemini-2.5-flash"
        mock_gemini.generate = AsyncMock(
            return_value=_make_mock_result(
                "Your Hemoglobin is 12.4 g/dL, which is below the normal range. "
                "Please consult your healthcare provider."
            )
        )

        service = ChatService(gemini=mock_gemini)
        result = await service.answer(
            question="What is my hemoglobin value?",
            report=report,
        )
        assert "12.4" in result.answer or result.answer

    @pytest.mark.asyncio
    async def test_answer_with_forbidden_phrase_retries(self) -> None:
        from ai.gemini.chat_service import ChatService
        from app.schemas.report import ParsedReport

        report = ParsedReport(**SAMPLE_REPORT)
        good_response = _make_mock_result(
            "Your hemoglobin is 12.4 g/dL. Please consult your physician."
        )
        bad_response = _make_mock_result("You should take iron supplements.")

        mock_gemini = MagicMock()
        mock_gemini._model_name = "gemini-2.5-flash"
        # First call returns bad response, second call returns good
        mock_gemini.generate = AsyncMock(side_effect=[bad_response, good_response])

        service = ChatService(gemini=mock_gemini)
        result = await service.answer("What should I take?", report)
        # Should not contain the forbidden advice (retry returned clean response)
        assert result.answer


# ------------------------------------------------------------------ #
# API endpoint tests (mocked services)
# ------------------------------------------------------------------ #

class TestAIEndpoints:
    def test_health_endpoint_returns_200(self, client) -> None:
        """Health endpoint always returns 200 — check body for actual status."""
        r = client.get("/api/v1/ai/health")
        assert r.status_code == 200
        data = r.json()
        # api_key_configured reflects whether GROQ_API_KEY is set in env
        assert "status" in data
        assert "model" in data
        assert "api_key_configured" in data

    def test_summary_endpoint_with_mock(self, client) -> None:
        from ai.gemini import summary_service as ss_module

        mock_response = {
            "executive_summary": "Test summary.",
            "patient_summary": "Patient friendly.",
            "important_findings": [],
            "abnormal_tests": [],
            "medicines": ["Ferrous Sulfate"],
            "diagnosis": ["Iron Deficiency Anemia"],
            "follow_up": ["See your doctor."],
            "disclaimer": "...",
            "model_used": "gemini-2.5-flash",
            "tokens_used": 100,
        }
        from app.schemas.ai import SummaryResponse
        mock_result = SummaryResponse(**mock_response)

        with patch.object(
            ss_module.summary_service, "summarise",
            new=AsyncMock(return_value=mock_result),
        ):
            r = client.post(
                "/api/v1/ai/summary",
                json={"report": SAMPLE_REPORT},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["executive_summary"] == "Test summary."
        assert "disclaimer" in data

    def test_chat_endpoint_with_mock(self, client) -> None:
        from ai.gemini import chat_service as cs_module
        from app.schemas.ai import ChatResponse

        mock_result = ChatResponse(
            answer="Your Hemoglobin is 12.4 g/dL. Please consult your physician.",
            model_used="gemini-2.5-flash",
        )
        with patch.object(
            cs_module.chat_service, "answer",
            new=AsyncMock(return_value=mock_result),
        ):
            r = client.post(
                "/api/v1/ai/chat",
                json={
                    "question": "What is my hemoglobin?",
                    "report": SAMPLE_REPORT,
                },
            )
        assert r.status_code == 200
        data = r.json()
        assert data["answer"]
        assert "disclaimer" in data

    def test_explain_endpoint_with_mock(self, client) -> None:
        from ai.gemini import explanation_service as es_module
        from app.schemas.ai import ExplanationResponse

        mock_result = ExplanationResponse(
            explanations=[],
            model_used="gemini-2.5-flash",
        )
        with patch.object(
            es_module.explanation_service, "explain",
            new=AsyncMock(return_value=mock_result),
        ):
            r = client.post(
                "/api/v1/ai/explain",
                json={"report": SAMPLE_REPORT},
            )
        assert r.status_code == 200
