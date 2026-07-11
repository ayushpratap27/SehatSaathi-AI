"""
Critical Value Detector — identifies lab results that cross clinically
significant critical thresholds requiring urgent attention.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Union

from ai.analysis.medical_rules import Status
from ai.analysis.reference_engine import CriticalThresholds

logger = logging.getLogger(__name__)

# Hard-coded safety net — these tests ALWAYS flag as critical regardless of
# the YAML config, because missed critical values are dangerous.
# Values are (test_name_lowercase_fragment, low_threshold, high_threshold).
_SAFETY_NET: list[tuple[str, Optional[float], Optional[float]]] = [
    ("hemoglobin",   7.0,    20.0),
    ("potassium",    2.5,    6.5),
    ("sodium",       120.0,  160.0),
    ("glucose",      50.0,   400.0),
    ("platelet",     20000,  None),
    ("wbc",          2000,   30000),
    ("creatinine",   None,   10.0),
    ("bilirubin",    None,   15.0),
]


def _safety_net_critical(
    test_name: str,
    value: Optional[float],
) -> Optional[str]:
    """
    Check if a value crosses a safety-net critical threshold.

    Returns the status string ("Critical Low" or "Critical High") or None.
    """
    if value is None:
        return None
    name_lower = test_name.lower()
    for fragment, low, high in _SAFETY_NET:
        if fragment in name_lower:
            if low is not None and value <= low:
                return Status.CRITICAL_LOW
            if high is not None and value >= high:
                return Status.CRITICAL_HIGH
    return None


class CriticalValueDetector:
    """
    Detects and flags lab results at clinically critical levels.

    Checks both the YAML-configured critical thresholds and the hard-coded
    safety-net values, taking the union of both.
    """

    def is_critical(
        self,
        test_name: str,
        value: Optional[Union[float, str]],
        critical: Optional[CriticalThresholds],
    ) -> bool:
        """
        Return True if the value is at a critical level.

        Args:
            test_name: Name of the test (used for safety-net lookup).
            value:     Observed value.
            critical:  Critical thresholds from the reference engine.

        Returns:
            True when the value is critically abnormal.
        """
        if value is None or isinstance(value, str):
            return False

        try:
            fval = float(value)
        except (TypeError, ValueError):
            return False

        # YAML config thresholds
        if critical:
            if critical.low is not None and fval <= critical.low:
                return True
            if critical.high is not None and fval >= critical.high:
                return True

        # Safety-net fallback
        return _safety_net_critical(test_name, fval) is not None

    def get_critical_tests(
        self,
        tests: List[dict],
    ) -> List[str]:
        """
        Filter a list of analysis result dicts to those that are critical.

        Args:
            tests: List of dicts with at least ``test_name`` and ``is_critical``.

        Returns:
            List of test names that have critical values.
        """
        return [t["test_name"] for t in tests if t.get("is_critical")]


# Module-level singleton
critical_value_detector = CriticalValueDetector()
