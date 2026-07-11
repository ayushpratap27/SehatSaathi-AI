"""
AI endpoints — Phase 5 Gemini-powered summary, explanation, and chat.

POST /api/v1/ai/summary   — executive summary of a parsed report
POST /api/v1/ai/explain   — plain-language explanations for all entities
POST /api/v1/ai/chat      — grounded Q&A against the report
GET  /api/v1/ai/health    — Gemini API connectivity check
GET  /api/v1/ai/stream    — streaming summary demo (SSE)
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from ai.gemini.chat_service import chat_service
from ai.gemini.explanation_service import explanation_service
from ai.gemini.gemini_client import GeminiConfigException, gemini_client
from ai.gemini.prompt_templates import summary_prompt
from ai.gemini.summary_service import summary_service
from app.schemas.ai import (
    AIHealthResponse,
    ChatRequest,
    ChatResponse,
    ExplanationRequest,
    ExplanationResponse,
    SummaryRequest,
    SummaryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ------------------------------------------------------------------ #
# Health
# ------------------------------------------------------------------ #

@router.get(
    "/health",
    response_model=AIHealthResponse,
    summary="Check Gemini API connectivity",
)
async def ai_health() -> AIHealthResponse:
    """
    Verify that the Gemini API key is configured and the API is reachable.

    Returns HTTP 200 in all cases — check the ``status`` field in the body.
    """
    result = await gemini_client.health_check()
    return AIHealthResponse(**result)


# ------------------------------------------------------------------ #
# Summary
# ------------------------------------------------------------------ #

@router.post(
    "/summary",
    response_model=SummaryResponse,
    summary="Generate an AI-powered executive summary",
    description=(
        "Takes a ``ParsedReport`` (Phase 3) and optional ``ReportAnalysisResult`` "
        "(Phase 4) and returns a structured AI-generated summary. "
        "Gemini receives only the structured JSON — never raw PDFs."
    ),
)
async def generate_summary(request: SummaryRequest) -> SummaryResponse:
    """
    Generate a structured executive summary of the medical report.

    The AI summary includes:
    - Executive overview (medical professional language)
    - Patient-friendly plain-language summary
    - Key important findings
    - Abnormal test explanations
    - Medicines and diagnoses from the report
    - General follow-up suggestions

    Gemini is strictly grounded — it uses ONLY data from the provided JSON.
    """
    logger.info(
        "Summary request: patient=%s tests=%d",
        request.report.patient.name or "Unknown",
        len(request.report.tests),
    )
    return await summary_service.summarise(request.report, request.analysis)


# ------------------------------------------------------------------ #
# Explanation
# ------------------------------------------------------------------ #

@router.post(
    "/explain",
    response_model=ExplanationResponse,
    summary="Generate plain-language explanations for report entities",
    description=(
        "Explains every abnormal lab test, diagnosis, and medicine in the report "
        "in simple, patient-friendly language. "
        "No external knowledge is used — only the provided report data."
    ),
)
async def generate_explanations(request: ExplanationRequest) -> ExplanationResponse:
    """
    Generate plain-language explanations for:
    - Each abnormal or critical lab test
    - Each diagnosis in the report
    - Each medicine mentioned (what it's used for, not prescription advice)

    All explanations are grounded in the uploaded report data.
    """
    logger.info(
        "Explain request: patient=%s items=%d tests, %d diagnoses, %d medicines",
        request.report.patient.name or "Unknown",
        len(request.report.tests),
        len(request.report.diagnosis),
        len(request.report.medicines),
    )
    return await explanation_service.explain(request.report, request.analysis)


# ------------------------------------------------------------------ #
# Chat
# ------------------------------------------------------------------ #

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a question about your medical report",
    description=(
        "Answers natural-language questions strictly grounded in the provided "
        "report data. If the answer cannot be found in the report, the AI responds: "
        "'This information is not available in the uploaded report.'"
    ),
)
async def chat_with_report(request: ChatRequest) -> ChatResponse:
    """
    Answer a user's question about their medical report.

    Gemini is constrained to use ONLY the provided report JSON.
    It will not speculate, diagnose, prescribe, or use external knowledge.

    Example questions:
    - "Which values are abnormal?"
    - "What does my WBC value mean?"
    - "What medicines are mentioned in my report?"
    - "Summarize this report for me."
    """
    logger.info("Chat request: question=%r", request.question[:80])
    return await chat_service.answer(
        question=request.question,
        report=request.report,
        analysis=request.analysis,
    )


# ------------------------------------------------------------------ #
# Streaming (SSE)
# ------------------------------------------------------------------ #

@router.post(
    "/stream/summary",
    summary="Stream an AI summary (Server-Sent Events)",
    response_class=StreamingResponse,
    description=(
        "Returns a streaming Server-Sent Events (SSE) response. "
        "Each event contains a text chunk from the Gemini response. "
        "Connect with ``EventSource`` or ``fetch()`` with ``text/event-stream``."
    ),
)
async def stream_summary(request: SummaryRequest) -> StreamingResponse:
    """
    Stream the executive summary as Server-Sent Events.

    Useful for progressive rendering in the frontend while Gemini generates
    the full response.
    """
    prompt = summary_prompt(request.report, request.analysis)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in gemini_client.stream(prompt):
                # SSE format: "data: <text>\n\n"
                safe_chunk = chunk.replace("\n", " ")
                yield f"data: {safe_chunk}\n\n"
        except GeminiConfigException as exc:
            yield f"data: [ERROR] {exc.message}\n\n"
        except Exception as exc:
            logger.error("Streaming error: %s", exc)
            yield "data: [ERROR] Streaming failed. Please use the non-streaming endpoint.\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
