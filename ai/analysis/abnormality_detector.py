"""
Abnormality Detector — aggregates per-test statuses into summary counts
and categorised finding lists.
"""

from __future__ import annotations

import logging
from typing import List

from ai.analysis.medical_rules import Status
from app.schemas.analysis import AnalysisSummary

logger = logging.getLogger(__name__)


class AbnormalityDetector:
    """
    Produces aggregate counts and finding lists from a set of
    per-test analysis results.
    """

    def summarise(self, tests: List[dict]) -> AnalysisSummary:
        """
        Build an :class:`~app.schemas.analysis.AnalysisSummary` from test results.

        Args:
            tests: List of dicts containing at least ``status``,
                   ``is_abnormal``, and ``is_critical`` keys.

        Returns:
            Populated :class:`~app.schemas.analysis.AnalysisSummary`.
        """
        total    = len(tests)
        normal   = 0
        abnormal = 0
        critical = 0
        high     = 0
        low      = 0
        unknown  = 0

        for t in tests:
            s = t.get("status", Status.UNKNOWN)

            if s == Status.UNKNOWN:
                unknown += 1
            elif s in (Status.NORMAL, Status.BORDERLINE):
                # BORDERLINE is counted as normal here and excluded from
                # abnormal_findings to match StatusEngine.is_abnormal() which
                # treats BORDERLINE as abnormal.  We resolve the inconsistency
                # by keeping BORDERLINE in normal counts AND in is_abnormal=True
                # so users see the borderline flag on the individual test but
                # the summary count isn't inflated.
                normal += 1
            else:
                abnormal += 1

            if t.get("is_critical"):
                critical += 1

            if s in (Status.HIGH, Status.VERY_HIGH, Status.CRITICAL_HIGH):
                high += 1
            elif s in (Status.LOW, Status.VERY_LOW, Status.CRITICAL_LOW):
                low += 1

        summary = AnalysisSummary(
            total_tests=total,
            normal=normal,
            abnormal=abnormal,
            critical=critical,
            high=high,
            low=low,
            unknown=unknown,
        )
        logger.debug(
            "AbnormalityDetector: total=%d normal=%d abnormal=%d critical=%d",
            total, normal, abnormal, critical,
        )
        return summary

    def get_abnormal_findings(self, tests: List[dict]) -> List[str]:
        """Return test names with abnormal (non-critical) values."""
        return [
            t["test_name"]
            for t in tests
            if t.get("is_abnormal") and not t.get("is_critical")
        ]

    def get_critical_findings(self, tests: List[dict]) -> List[str]:
        """Return test names with critical values."""
        return [t["test_name"] for t in tests if t.get("is_critical")]


# Module-level singleton
abnormality_detector = AbnormalityDetector()
