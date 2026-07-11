"""
Recommendation Engine — generates general, safe, evidence-free recommendations.

RULES (non-negotiable):
  ✔ Only general guidance
  ✔ Always recommend consulting a physician
  ✔ NEVER recommend specific medicines
  ✔ NEVER diagnose a disease
  ✔ NEVER suggest stopping a prescribed medication
"""

from __future__ import annotations

import logging
from typing import List

from ai.analysis.medical_rules import RiskLevel
from app.schemas.analysis import AnalysisSummary

logger = logging.getLogger(__name__)

# Standard recommendations always included
_ALWAYS = [
    "Consult your treating physician regarding these laboratory findings.",
    "Share this report with a qualified healthcare professional for proper interpretation.",
]

# Conditional recommendations added when applicable
_IF_CRITICAL = (
    "⚠️ One or more values are critically abnormal. "
    "Please seek medical attention promptly and do not delay evaluation."
)

_IF_MULTIPLE_ABNORMAL = (
    "Multiple abnormal values are present. "
    "A comprehensive clinical evaluation is recommended."
)

_IF_NORMAL = (
    "All values are within normal limits. "
    "Continue regular health check-ups as advised by your doctor."
)

_IF_UNKNOWN_TESTS = (
    "Some tests could not be evaluated against reference ranges. "
    "Please review these with your doctor."
)

_GENERAL_ADVICE = [
    "Follow any prescribed medications as directed by your physician.",
    "Repeat laboratory tests if advised by your healthcare provider.",
    "Maintain a balanced diet and adequate hydration unless otherwise instructed.",
]


class RecommendationEngine:
    """
    Generates a contextual list of general recommendations.

    Recommendations are purely advisory and informational — they do not
    constitute medical advice, diagnosis, or treatment.
    """

    def generate(
        self,
        summary: AnalysisSummary,
        risk_level: str,
        has_medicines: bool = False,
    ) -> List[str]:
        """
        Build a recommendation list tailored to the analysis findings.

        Args:
            summary:       Aggregate test counts.
            risk_level:    Overall risk level string.
            has_medicines: True if the report contains prescribed medicines.

        Returns:
            Ordered list of recommendation strings.
        """
        recs: List[str] = []

        # Critical first
        if summary.critical > 0 or risk_level == RiskLevel.CRITICAL:
            recs.append(_IF_CRITICAL)

        # Multiple abnormal
        if summary.abnormal >= 2 and risk_level in (RiskLevel.MODERATE, RiskLevel.HIGH):
            recs.append(_IF_MULTIPLE_ABNORMAL)

        # All normal
        if summary.abnormal == 0 and summary.critical == 0:
            recs.append(_IF_NORMAL)

        # Unknown tests
        if summary.unknown > 0:
            recs.append(_IF_UNKNOWN_TESTS)

        # Always-present recommendations
        recs.extend(_ALWAYS)

        # General lifestyle advice
        recs.extend(_GENERAL_ADVICE[:2])

        if has_medicines:
            recs.insert(
                len(recs) - 1,
                "Take medicines exactly as prescribed. "
                "Do not stop or change doses without consulting your doctor.",
            )

        return recs


# Module-level singleton
recommendation_engine = RecommendationEngine()
