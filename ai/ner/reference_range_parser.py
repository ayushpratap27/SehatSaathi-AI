"""
Reference range parser and status derivation for lab test results.

Supports numeric ranges, one-sided bounds, and qualitative expectations.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional, Union

from app.utils import regex_patterns as P

logger = logging.getLogger(__name__)

# Critical thresholds — values outside these multipliers of the range boundary
# are elevated to "Critical" status
_CRITICAL_LOW_FACTOR = 0.5   # value < min * 0.5  → Critical
_CRITICAL_HIGH_FACTOR = 2.0  # value > max * 2.0  → Critical


@dataclass
class ReferenceRange:
    """
    Parsed representation of a lab reference range string.

    Attributes:
        raw:             Original string as found in the report.
        low:             Lower bound (inclusive) for numeric ranges.
        high:            Upper bound (inclusive) for numeric ranges.
        is_qualitative:  True when the range is a word expectation (Negative, etc.).
        expected:        Expected value for qualitative ranges (lower-cased).
    """

    raw: str
    low: Optional[float] = field(default=None)
    high: Optional[float] = field(default=None)
    is_qualitative: bool = False
    expected: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Factory / parsing
    # ------------------------------------------------------------------ #

    @classmethod
    def from_string(cls, raw: str) -> "ReferenceRange":
        """
        Parse a reference range string into a ``ReferenceRange`` instance.

        Supported formats:
        - ``13.5-17.5``  or  ``13.5–17.5``
        - ``< 100``  /  ``<= 100``  /  ``≤ 100``
        - ``> 40``   /  ``>= 40``   /  ``≥ 40``
        - ``Upto 100`` / ``Up to 40``
        - ``Negative`` / ``Positive`` / ``Reactive`` / ``Non-Reactive``
        - ``Normal`` / ``Abnormal``

        Args:
            raw: The raw reference range string.

        Returns:
            Populated :class:`ReferenceRange` instance.
        """
        obj = cls(raw=raw.strip())
        text = raw.strip()

        # --- Numeric range ---
        m = P.RANGE_NUMERIC.match(text)
        if m:
            obj.low  = float(m.group("low"))
            obj.high = float(m.group("high"))
            return obj

        # --- Less-than ---
        m = P.RANGE_LESS_THAN.match(text)
        if m:
            obj.high = float(m.group("max"))
            return obj

        # --- Greater-than ---
        m = P.RANGE_GREATER_THAN.match(text)
        if m:
            obj.low = float(m.group("min"))
            return obj

        # --- "Upto X" ---
        m = P.RANGE_UPTO.match(text)
        if m:
            obj.high = float(m.group("max"))
            return obj

        # --- Qualitative ---
        if P.RANGE_QUALITATIVE.match(text):
            obj.is_qualitative = True
            # Normalize "Non-Reactive" → "non-reactive", "Non Reactive" → same
            obj.expected = re.sub(r"[-\s]+", "-", text.lower())
            return obj

        # Unrecognised format — keep raw for display only
        logger.debug("Unrecognised reference range format: %r", raw)
        return obj

    # ------------------------------------------------------------------ #
    # Status derivation
    # ------------------------------------------------------------------ #

    def get_status(self, value: Union[float, str, None]) -> str:
        """
        Derive the clinical status of a result against this reference range.

        Args:
            value: The observed value (numeric float or qualitative string).

        Returns:
            One of: ``Normal``, ``High``, ``Low``, ``Critical``,
            ``Positive``, ``Negative``, ``Abnormal``, ``Unknown``.
        """
        if value is None:
            return "Unknown"

        # --- Qualitative comparison ---
        if self.is_qualitative and self.expected:
            val_normalised = re.sub(r"[-\s]+", "-", str(value).lower().strip())
            if val_normalised == self.expected:
                return "Normal"
            # Map specific expected/actual combos to meaningful labels
            if self.expected == "negative":
                return "Positive" if val_normalised == "positive" else "Abnormal"
            if self.expected in ("non-reactive",):
                # Use exact match, NOT substring: "reactive" in "non-reactive" is True
                return "Reactive" if val_normalised == "reactive" else "Abnormal"
            return "Abnormal"

        # --- Numeric comparison ---
        try:
            fval = float(value)
        except (TypeError, ValueError):
            return "Unknown"

        if self.low is not None and self.high is not None:
            spread = self.high - self.low
            if fval < self.low:
                # Critical when value is far below the range (> 30% of range spread)
                if spread > 0 and (self.low - fval) / spread >= _CRITICAL_LOW_FACTOR:
                    return "Critical"
                return "Low"
            if fval > self.high:
                # Critical when value is far above the range (> 30% of range spread)
                if spread > 0 and (fval - self.high) / spread >= _CRITICAL_HIGH_FACTOR:
                    return "Critical"
                return "High"
            return "Normal"

        if self.low is not None:      # only lower bound (> X)
            return "Low" if fval < self.low else "Normal"

        if self.high is not None:     # only upper bound (< X)
            if fval > self.high:
                return "Critical" if self.high > 0 and fval > self.high * (1 + _CRITICAL_HIGH_FACTOR) else "High"
            return "Normal"

        return "Unknown"

    # ------------------------------------------------------------------ #
    # Convenience
    # ------------------------------------------------------------------ #

    def __bool__(self) -> bool:
        """True when the range was successfully parsed (has bounds or qualitative)."""
        return (
            self.low is not None
            or self.high is not None
            or self.is_qualitative
        )


def parse_reference_range(raw: str) -> ReferenceRange:
    """
    Module-level convenience wrapper around :meth:`ReferenceRange.from_string`.

    Args:
        raw: Raw reference range string.

    Returns:
        :class:`ReferenceRange` instance.
    """
    return ReferenceRange.from_string(raw)


def derive_status(
    value: Union[float, str, None],
    reference_range_str: Optional[str],
) -> Optional[str]:
    """
    Given a value and a raw reference range string, return a status label.

    Args:
        value:               Observed lab result.
        reference_range_str: Reference range as found in the report.

    Returns:
        Status string or ``None`` if reference range is absent.
    """
    if not reference_range_str:
        return None
    rr = parse_reference_range(reference_range_str)
    if not rr:
        return None
    return rr.get_status(value)
