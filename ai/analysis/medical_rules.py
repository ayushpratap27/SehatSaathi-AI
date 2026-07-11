"""
Medical rules, thresholds, and constants for Phase 4 analysis.

All configurable values live here — never hardcode thresholds in logic modules.
"""

from __future__ import annotations

# ------------------------------------------------------------------ #
# Status labels
# ------------------------------------------------------------------ #

class Status:
    NORMAL        = "Normal"
    LOW           = "Low"
    HIGH          = "High"
    VERY_LOW      = "Very Low"
    VERY_HIGH     = "Very High"
    CRITICAL_LOW  = "Critical Low"
    CRITICAL_HIGH = "Critical High"
    BORDERLINE    = "Borderline"
    POSITIVE      = "Positive"
    NEGATIVE      = "Negative"
    ABNORMAL      = "Abnormal"
    UNKNOWN       = "Unknown"

    # Set of all "abnormal" statuses (not Normal and not Unknown)
    ABNORMAL_STATUSES: frozenset[str] = frozenset({
        LOW, HIGH, VERY_LOW, VERY_HIGH,
        CRITICAL_LOW, CRITICAL_HIGH, BORDERLINE,
        POSITIVE, NEGATIVE, ABNORMAL,
    })

    CRITICAL_STATUSES: frozenset[str] = frozenset({
        CRITICAL_LOW, CRITICAL_HIGH,
    })


# ------------------------------------------------------------------ #
# Risk levels
# ------------------------------------------------------------------ #

class RiskLevel:
    NORMAL   = "Normal"
    LOW      = "Low"
    MODERATE = "Moderate"
    HIGH     = "High"
    CRITICAL = "Critical"


# ------------------------------------------------------------------ #
# Deviation thresholds
# ------------------------------------------------------------------ #

# A value more than VERY_DEVIATION below the lower bound is "Very Low"
# (30% deviation from the boundary)
VERY_LOW_DEVIATION_FACTOR:  float = 0.30

# A value more than VERY_DEVIATION above the upper bound is "Very High"
VERY_HIGH_DEVIATION_FACTOR: float = 0.30

# Within this fraction of the boundary → "Borderline"
BORDERLINE_FRACTION: float = 0.05


# ------------------------------------------------------------------ #
# Risk level thresholds (based on abnormal/critical counts)
# ------------------------------------------------------------------ #

RISK_THRESHOLDS = {
    # (max_abnormal, max_critical) → risk_level
    # Evaluated top-down; first matching rule wins.
    "critical":  {"min_critical": 1},
    "high":      {"min_abnormal": 5},
    "moderate":  {"min_abnormal": 2},
    "low":       {"min_abnormal": 1},
    "normal":    {},
}
