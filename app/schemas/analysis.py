"""
Pydantic schemas for Phase 4 — Medical Analysis Engine output.

These models represent the final analysis result returned by
``POST /api/v1/report/analyze``.
"""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Per-test analysis
# ------------------------------------------------------------------ #

class TestAnalysisResult(BaseModel):
    """Analysis result for a single laboratory test."""

    test_name: str = Field(..., description="Normalised test name")
    value: Optional[Union[float, str]] = Field(None, description="Observed value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range: Optional[str] = Field(
        None, description="Resolved reference range used for analysis"
    )
    source_reference: Optional[str] = Field(
        None, description="Reference range as stated in the original report"
    )
    status: str = Field(
        ...,
        description=(
            "Clinical status: Normal | Low | High | Very Low | Very High | "
            "Critical Low | Critical High | Borderline | Positive | Negative | Unknown"
        ),
    )
    is_abnormal: bool = Field(..., description="True when status is not Normal")
    is_critical: bool = Field(
        ..., description="True when value crosses a critical threshold"
    )
    insight: str = Field(
        ..., description="Plain-language explanation of this finding"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "test_name": "Hemoglobin",
            "value": 12.4,
            "unit": "g/dL",
            "reference_range": "13.5-17.5",
            "status": "Low",
            "is_abnormal": True,
            "is_critical": False,
            "insight": (
                "Hemoglobin (12.4 g/dL) is below the normal reference range "
                "(13.5–17.5 g/dL). Low hemoglobin may indicate reduced "
                "oxygen-carrying capacity of the blood."
            ),
        }
    }}


# ------------------------------------------------------------------ #
# Summary counts
# ------------------------------------------------------------------ #

class AnalysisSummary(BaseModel):
    """Aggregate counts across all analysed tests."""

    total_tests: int = Field(..., description="Total number of tests analysed")
    normal: int = Field(..., description="Tests within the normal range")
    abnormal: int = Field(..., description="Tests outside the normal range")
    critical: int = Field(..., description="Tests at critical levels")
    high: int = Field(..., description="Tests above the normal range")
    low: int = Field(..., description="Tests below the normal range")
    unknown: int = Field(
        ..., description="Tests without a resolvable reference range"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "total_tests": 18,
            "normal": 14,
            "abnormal": 4,
            "critical": 1,
            "high": 2,
            "low": 2,
            "unknown": 0,
        }
    }}


# ------------------------------------------------------------------ #
# Root response schema
# ------------------------------------------------------------------ #

DISCLAIMER = (
    "⚠️ MEDICAL DISCLAIMER: This analysis is generated automatically based "
    "on laboratory values only. It is intended for informational purposes and "
    "does NOT constitute a medical diagnosis, treatment recommendation, or "
    "medical advice. Always consult a qualified healthcare professional for "
    "the interpretation of laboratory results and clinical decision-making."
)


class ReportAnalysisResult(BaseModel):
    """
    Complete medical analysis result returned by ``POST /api/v1/report/analyze``.
    """

    patient: dict = Field(
        default_factory=dict, description="Patient demographic summary"
    )
    tests: List[TestAnalysisResult] = Field(
        default_factory=list, description="Per-test analysis results"
    )
    analysis: AnalysisSummary = Field(
        ..., description="Aggregate summary counts"
    )
    abnormal_findings: List[str] = Field(
        default_factory=list,
        description="Test names with abnormal (non-critical) values",
    )
    critical_findings: List[str] = Field(
        default_factory=list,
        description="Test names with critical values requiring urgent attention",
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Formatted insight strings for all abnormal/critical tests",
    )
    risk_level: str = Field(
        ...,
        description="Overall risk category: Normal | Low | Moderate | High | Critical",
    )
    summary: str = Field(..., description="Plain-language summary of the report")
    recommendations: List[str] = Field(
        default_factory=list,
        description="General recommendations (no diagnosis, no prescription)",
    )
    disclaimer: str = Field(
        default=DISCLAIMER,
        description="Medical disclaimer — always included in the response",
    )

    model_config = {"json_schema_extra": {
        "example": {
            "patient": {"name": "John Doe", "age": 45, "gender": "Male"},
            "analysis": {
                "total_tests": 2,
                "normal": 0,
                "abnormal": 2,
                "critical": 0,
                "high": 1,
                "low": 1,
                "unknown": 0,
            },
            "risk_level": "Moderate",
            "summary": "2 of 2 laboratory values are outside normal reference ranges.",
            "recommendations": [
                "Consult your treating physician regarding these laboratory findings.",
            ],
        }
    }}
