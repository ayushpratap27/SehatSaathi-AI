"""
Pydantic schemas for Phase 5 — Gemini AI endpoints.

Defines request and response shapes for:
  POST /api/v1/ai/summary
  POST /api/v1/ai/explain
  POST /api/v1/ai/chat
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.analysis import ReportAnalysisResult
from app.schemas.report import ParsedReport

# ------------------------------------------------------------------ #
# Shared metadata fields
# ------------------------------------------------------------------ #

_DISCLAIMER = (
    "⚠️ This AI-generated response is for informational purposes only. "
    "It is based solely on the data in the uploaded report and does NOT "
    "constitute medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare professional."
)


# ------------------------------------------------------------------ #
# Summary
# ------------------------------------------------------------------ #

class SummaryRequest(BaseModel):
    """Input for the executive summary endpoint."""

    report: ParsedReport = Field(..., description="Structured report from Phase 3 /parse")
    analysis: Optional[ReportAnalysisResult] = Field(
        None, description="Clinical analysis from Phase 4 /analyze (optional but recommended)"
    )


class AbnormalTestExplanation(BaseModel):
    """Plain-language explanation of one abnormal test result."""

    test_name: str
    value: Optional[Union[float, str]] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    explanation: str


class SummaryResponse(BaseModel):
    """Structured AI-generated summary of a medical report."""

    executive_summary: str = Field(..., description="3–5 sentence overview")
    patient_summary: str = Field(..., description="Patient-friendly plain-language summary")
    important_findings: List[str] = Field(default_factory=list)
    abnormal_tests: List[AbnormalTestExplanation] = Field(default_factory=list)
    medicines: List[str] = Field(default_factory=list)
    diagnosis: List[str] = Field(default_factory=list)
    follow_up: List[str] = Field(
        default_factory=list,
        description="General follow-up suggestions (no medical prescriptions)"
    )
    disclaimer: str = Field(default=_DISCLAIMER)
    model_used: str = Field(default="gemini-2.5-flash")
    tokens_used: Optional[int] = None


# ------------------------------------------------------------------ #
# Explanation
# ------------------------------------------------------------------ #

class ExplanationRequest(BaseModel):
    """Input for the medical explanation endpoint."""

    report: ParsedReport
    analysis: Optional[ReportAnalysisResult] = None


class ExplanationItem(BaseModel):
    """Plain-language explanation of one medical entity."""

    term: str = Field(..., description="Medical term, test name, medicine, or diagnosis")
    category: str = Field(
        ...,
        description="One of: lab_test | medicine | diagnosis | medical_term"
    )
    value: Optional[str] = Field(None, description="Observed value if applicable")
    explanation: str = Field(..., description="Plain-language explanation")


class ExplanationResponse(BaseModel):
    """All explanations for entities found in the report."""

    explanations: List[ExplanationItem] = Field(default_factory=list)
    disclaimer: str = Field(default=_DISCLAIMER)
    model_used: str = Field(default="gemini-2.5-flash")
    tokens_used: Optional[int] = None


# ------------------------------------------------------------------ #
# Chat
# ------------------------------------------------------------------ #

class ChatRequest(BaseModel):
    """Input for the grounded chat endpoint."""

    question: str = Field(..., min_length=3, description="User's question about the report")
    report: ParsedReport = Field(..., description="Structured report data (context)")
    analysis: Optional[ReportAnalysisResult] = Field(
        None, description="Clinical analysis data (additional context)"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "question": "Which values are abnormal in my report?",
            "report": {"patient": {}, "tests": [], "diagnosis": [], "medicines": []},
        }
    }}


class ChatResponse(BaseModel):
    """Grounded answer to a user question about their report."""

    answer: str = Field(..., description="AI-generated answer grounded in the report data")
    disclaimer: str = Field(default=_DISCLAIMER)
    model_used: str = Field(default="gemini-2.5-flash")
    tokens_used: Optional[int] = None


# ------------------------------------------------------------------ #
# Health
# ------------------------------------------------------------------ #

class AIHealthResponse(BaseModel):
    """Gemini API connectivity status."""

    status: str
    model: str
    message: str
    api_key_configured: bool
