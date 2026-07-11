"""
Insight Generator — produces plain-language explanations for each
lab test result.

IMPORTANT: Generated text NEVER diagnoses, prescribes, or replaces
professional medical advice.  All insights are purely informational,
based solely on the observed value vs the reference range.
"""

from __future__ import annotations

import logging
from typing import Optional, Union

from ai.analysis.medical_rules import Status
from ai.analysis.reference_engine import NumericRange, TestConfig

logger = logging.getLogger(__name__)

_DISCLAIMER_SUFFIX = (
    " This finding should be interpreted by a qualified healthcare professional."
)


class InsightGenerator:
    """
    Generates a single plain-language insight string per lab test.

    The generator uses the status, reference range, and test description
    (from the YAML config, where available) to build informative but
    safe explanations.
    """

    def generate(
        self,
        test_name: str,
        value: Optional[Union[float, str]],
        unit: Optional[str],
        status: str,
        ref_range: Optional[NumericRange],
        test_config: Optional[TestConfig] = None,
    ) -> str:
        """
        Build a plain-language insight for one test result.

        Args:
            test_name:   Normalised test name.
            value:       Observed value.
            unit:        Unit of measurement.
            status:      Status label from the StatusEngine.
            ref_range:   Resolved reference range (may be None).
            test_config: Full test config (used for description).

        Returns:
            A single human-readable insight string.
        """
        value_str   = self._format_value(value, unit)
        range_str   = ref_range.as_string() if ref_range else None
        range_label = f" (reference: {range_str} {unit or ''})" if range_str else ""

        if status == Status.NORMAL:
            return (
                f"{test_name} ({value_str}) is within the normal reference range"
                f"{range_label}."
            )

        if status == Status.BORDERLINE:
            return (
                f"{test_name} ({value_str}) is at the borderline of the normal "
                f"reference range{range_label}.{_DISCLAIMER_SUFFIX}"
            )

        if status == Status.CRITICAL_LOW:
            return (
                f"⚠️ CRITICAL: {test_name} ({value_str}) is critically low"
                f"{range_label}. This value may require immediate clinical "
                f"attention.{_DISCLAIMER_SUFFIX}"
            )

        if status == Status.CRITICAL_HIGH:
            return (
                f"⚠️ CRITICAL: {test_name} ({value_str}) is critically elevated"
                f"{range_label}. This value may require immediate clinical "
                f"attention.{_DISCLAIMER_SUFFIX}"
            )

        if status == Status.VERY_LOW:
            return (
                f"{test_name} ({value_str}) is significantly below the normal "
                f"reference range{range_label}.{_DISCLAIMER_SUFFIX}"
            )

        if status == Status.VERY_HIGH:
            return (
                f"{test_name} ({value_str}) is significantly above the normal "
                f"reference range{range_label}.{_DISCLAIMER_SUFFIX}"
            )

        if status == Status.LOW:
            return (
                f"{test_name} ({value_str}) is below the normal reference range"
                f"{range_label}.{_DISCLAIMER_SUFFIX}"
            )

        if status == Status.HIGH:
            return (
                f"{test_name} ({value_str}) is above the normal reference range"
                f"{range_label}.{_DISCLAIMER_SUFFIX}"
            )

        if status == Status.POSITIVE:
            return (
                f"{test_name} result is Positive. The expected result is Negative."
                f"{_DISCLAIMER_SUFFIX}"
            )

        if status == Status.NEGATIVE:
            return (
                f"{test_name} result is Negative."
            )

        if status == Status.ABNORMAL:
            return (
                f"{test_name} ({value_str}) is reported as Abnormal."
                f"{_DISCLAIMER_SUFFIX}"
            )

        # Unknown — no reference range available
        return (
            f"{test_name} ({value_str}) was recorded. "
            "No reference range is available for this test in the current knowledge base."
        )

    @staticmethod
    def _format_value(
        value: Optional[Union[float, str]], unit: Optional[str]
    ) -> str:
        """Format value + unit into a readable string."""
        if value is None:
            return "N/A"
        unit_str = f" {unit}" if unit else ""
        if isinstance(value, float):
            # Remove trailing zeros for clean display
            v = f"{value:g}"
        else:
            v = str(value)
        return f"{v}{unit_str}"


# Module-level singleton
insight_generator = InsightGenerator()
