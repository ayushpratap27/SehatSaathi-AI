"""
Analysis endpoint — Phase 4 implementation.

POST /api/v1/analysis/analyze  — full medical analysis of a ParsedReport.

GET placeholder routes remain for future database-backed document retrieval.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from app.schemas.analysis import ReportAnalysisResult
from app.schemas.report import ParsedReport

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{document_id}/entities", summary="Extract medical entities")
async def get_entities(document_id: str) -> dict:
    """
    Return medical entities (diseases, medications, procedures, symptoms)
    extracted from the report.

    Args:
        document_id: UUID of the document.

    Returns:
        Placeholder response until Phase 3 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "entities": [],
        "message": "Medical NER — coming in Phase 3",
    }


@router.get("/{document_id}/lab-values", summary="Get lab test results")
async def get_lab_values(document_id: str) -> dict:
    """
    Return extracted laboratory test values with normal/abnormal classification.

    Args:
        document_id: UUID of the document.

    Returns:
        Placeholder response until Phase 3 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "lab_values": [],
        "message": "Lab value extraction — coming in Phase 3",
    }


@router.get("/{document_id}/explain", summary="Explain report in simple language")
async def explain_report(document_id: str) -> dict:
    """
    Return a patient-friendly explanation of the report content.

    Args:
        document_id: UUID of the document.

    Returns:
        Placeholder response until Phase 5 implementation.
    """
    return {
        "success": True,
        "document_id": document_id,
        "message": "AI explanation — coming in Phase 5",
    }


# ------------------------------------------------------------------ #
# Phase 4 — Medical Analysis endpoint
# ------------------------------------------------------------------ #

@router.post(
    "/analyze",
    response_model=ReportAnalysisResult,
    summary="Analyse a structured medical report",
    description=(
        "Takes a ``ParsedReport`` JSON (output of ``POST /api/v1/report/parse``) "
        "and returns a complete medical analysis: per-test status, insights, "
        "risk level, summary, and general recommendations.\n\n"
        "**This endpoint does NOT diagnose diseases or prescribe treatments.** "
        "All analysis is purely informational, based on comparison with "
        "configurable reference ranges."
    ),
)
async def analyze_report(report: ParsedReport) -> ReportAnalysisResult:
    """
    Run the Phase 4 clinical analysis pipeline on a parsed report.

    Pipeline:
    1. Resolve gender/age-specific reference ranges from the knowledge base.
    2. Determine status per test (Normal/Low/High/Critical etc.).
    3. Detect critical values.
    4. Generate plain-language insights.
    5. Aggregate counts (normal/abnormal/critical).
    6. Derive overall risk level.
    7. Generate summary and recommendations.

    Args:
        report: Output of ``POST /api/v1/report/parse``.

    Returns:
        :class:`~app.schemas.analysis.ReportAnalysisResult` with full analysis.
    """
    from ai.analysis.report_analyzer import report_analyzer  # noqa: PLC0415

    logger.info(
        "Analyze request: patient=%s tests=%d",
        report.patient.name or "Unknown",
        len(report.tests),
    )

    result: ReportAnalysisResult = await run_in_threadpool(
        report_analyzer.analyze, report
    )
    return result
