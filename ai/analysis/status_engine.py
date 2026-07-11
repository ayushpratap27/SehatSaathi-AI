"""
Status Engine — determines the clinical status of a lab value against
a resolved reference range.

Returns one of the 11 status labels defined in ``medical_rules.Status``.
"""

from __future__ import annotations

import logging
import re
from typing import Optional, Union

from ai.analysis.medical_rules import (
    BORDERLINE_FRACTION,
    VERY_HIGH_DEVIATION_FACTOR,
    VERY_LOW_DEVIATION_FACTOR,
    Status,
)
from ai.analysis.reference_engine import CriticalThresholds, NumericRange

logger = logging.getLogger(__name__)

# Qualitative result → expected normal value mapping
_QUALITATIVE_NORMAL: dict[str, str] = {
    "negative":     "negative",
    "non-reactive": "non-reactive",
    "normal":       "normal",
    "absent":       "absent",
}

_QUALITATIVE_ABNORMAL_LABELS: dict[str, str] = {
    "positive":  Status.POSITIVE,
    "reactive":  Status.POSITIVE,
    "abnormal":  Status.ABNORMAL,
    "present":   Status.ABNORMAL,
}


class StatusEngine:
    """
    Determines the clinical status of a single lab result.

    Status priority (highest to lowest):
      Critical Low / Critical High → Very Low / Very High → Low / High
      → Borderline → Normal → Unknown
    """

    def get_status(
        self,
        value: Optional[Union[float, str]],
        ref_range: Optional[NumericRange],
        critical: Optional[CriticalThresholds] = None,
    ) -> str:
        """
        Return the status label for a lab result.

        Args:
            value:     Observed value (numeric or qualitative string).
            ref_range: Resolved reference range from the knowledge base.
            critical:  Critical thresholds, if available.

        Returns:
            One of the ``Status`` string constants.
        """
        if value is None:
            return Status.UNKNOWN

        # --- Qualitative values ---
        if isinstance(value, str):
            return self._qualitative(value)

        # --- Numeric values ---
        try:
            fval = float(value)
        except (TypeError, ValueError):
            return self._qualitative(str(value))

        if ref_range is None:
            return Status.UNKNOWN

        # 1. Critical checks (highest priority)
        if critical:
            if critical.low is not None and fval <= critical.low:
                return Status.CRITICAL_LOW
            if critical.high is not None and fval >= critical.high:
                return Status.CRITICAL_HIGH

        low  = ref_range.min
        high = ref_range.max

        if low is None and high is None:
            return Status.UNKNOWN

        # 2. Below lower bound
        if low is not None and fval < low:
            deviation = (low - fval) / low if low != 0 else 0
            return Status.VERY_LOW if deviation >= VERY_LOW_DEVIATION_FACTOR else Status.LOW

        # 3. Above upper bound
        if high is not None and fval > high:
            deviation = (fval - high) / high if high != 0 else 0
            return Status.VERY_HIGH if deviation >= VERY_HIGH_DEVIATION_FACTOR else Status.HIGH

        # 4. Borderline checks (near the boundary but within range)
        if low is not None and high is not None:
            spread = high - low
            if spread > 0 and fval < low + spread * BORDERLINE_FRACTION:
                return Status.BORDERLINE
            if spread > 0 and fval > high - spread * BORDERLINE_FRACTION:
                return Status.BORDERLINE

        return Status.NORMAL

    @staticmethod
    def _qualitative(value: str) -> str:
        """Map a qualitative string result to a status label."""
        normalised = re.sub(r"[-\s]+", "-", value.lower().strip())
        if normalised in _QUALITATIVE_NORMAL:
            return Status.NORMAL
        return _QUALITATIVE_ABNORMAL_LABELS.get(normalised, Status.UNKNOWN)

    @staticmethod
    def is_abnormal(status: str) -> bool:
        """Return True when the status indicates an abnormal result."""
        return status in Status.ABNORMAL_STATUSES

    @staticmethod
    def is_critical(status: str) -> bool:
        """Return True when the status is a critical level."""
        return status in Status.CRITICAL_STATUSES


# Module-level singleton
status_engine = StatusEngine()
