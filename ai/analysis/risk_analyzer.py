"""
Risk Analyzer — classifies the overall risk level of a medical report
and generates a plain-language summary.
"""

from __future__ import annotations

import logging

from ai.analysis.medical_rules import RiskLevel
from app.schemas.analysis import AnalysisSummary

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    Determines overall report risk level and generates a summary sentence.

    Risk levels (ascending severity):
    - Normal   : All tests within normal range
    - Low      : 1 abnormal finding
    - Moderate : 2–4 abnormal findings
    - High     : ≥5 abnormal findings
    - Critical : Any critical finding
    """

    def get_risk_level(self, summary: AnalysisSummary) -> str:
        """
        Return the overall risk level for this report.

        Args:
            summary: Aggregated analysis counts.

        Returns:
            One of the ``RiskLevel`` constants.
        """
        if summary.critical > 0:
            return RiskLevel.CRITICAL
        if summary.abnormal >= 5:
            return RiskLevel.HIGH
        if summary.abnormal >= 2:
            return RiskLevel.MODERATE
        if summary.abnormal >= 1:
            return RiskLevel.LOW
        return RiskLevel.NORMAL

    def generate_summary(
        self,
        summary: AnalysisSummary,
        risk_level: str,
    ) -> str:
        """
        Generate a plain-language summary of the report.

        IMPORTANT: This summary makes NO diagnoses and NO clinical
        recommendations. It only states counts of abnormal values.

        Args:
            summary:    Aggregated test counts.
            risk_level: Derived risk level string.

        Returns:
            A 1–3 sentence summary string.
        """
        total    = summary.total_tests
        abnormal = summary.abnormal
        critical = summary.critical
        unknown  = summary.unknown

        parts: list[str] = []

        if total == 0:
            return "No laboratory test results were found in this report."

        if abnormal == 0 and critical == 0:
            parts.append(
                f"All {total} analysed laboratory values are within "
                "normal reference ranges."
            )
        else:
            parts.append(
                f"{abnormal} of {total} laboratory value(s) are outside "
                "the normal reference range."
            )

        if critical > 0:
            parts.append(
                f"⚠️ {critical} value(s) are at a critical level and may "
                "require urgent clinical evaluation."
            )
        elif risk_level == RiskLevel.HIGH:
            parts.append(
                "Multiple abnormal findings are present. Clinical review "
                "is advisable."
            )

        if unknown > 0:
            parts.append(
                f"{unknown} test(s) could not be matched to the reference "
                "knowledge base and were not analysed."
            )

        return " ".join(parts)


# Module-level singleton
risk_analyzer = RiskAnalyzer()
