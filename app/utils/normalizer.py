"""
Medical report normalization utilities.

Converts abbreviations, alternate spellings, and colloquial names
to canonical forms used throughout the extraction pipeline.
"""

from __future__ import annotations

import re

# ------------------------------------------------------------------ #
# Test name canonicalization map
# ------------------------------------------------------------------ #

_TEST_NAME_MAP: dict[str, str] = {
    # Haematology
    "hb": "Hemoglobin",
    "haemoglobin": "Hemoglobin",
    "hemoglobin": "Hemoglobin",
    "hgb": "Hemoglobin",
    "hgb%": "Hemoglobin",
    "rbc": "RBC Count",
    "red blood cell": "RBC Count",
    "red blood cells": "RBC Count",
    "red cell count": "RBC Count",
    "wbc": "WBC Count",
    "white blood cell": "WBC Count",
    "white blood cells": "WBC Count",
    "white cell count": "WBC Count",
    "tlc": "WBC Count",
    "total leukocyte count": "WBC Count",
    "total wbc count": "WBC Count",
    "platelet": "Platelet Count",
    "platelets": "Platelet Count",
    "plt": "Platelet Count",
    "thrombocyte count": "Platelet Count",
    "pc": "Platelet Count",
    "hct": "Hematocrit",
    "pcv": "Hematocrit",
    "packed cell volume": "Hematocrit",
    "haematocrit": "Hematocrit",
    "mcv": "MCV",
    "mean corpuscular volume": "MCV",
    "mch": "MCH",
    "mean corpuscular hemoglobin": "MCH",
    "mchc": "MCHC",
    "mean corpuscular hemoglobin concentration": "MCHC",
    "rdw": "RDW",
    "rdw-cv": "RDW",
    "mpv": "MPV",
    "mean platelet volume": "MPV",
    "esr": "ESR",
    "erythrocyte sedimentation rate": "ESR",
    # Chemistry
    "glucose": "Glucose",
    "blood sugar": "Glucose",
    "fbs": "Fasting Blood Sugar",
    "fasting blood glucose": "Fasting Blood Sugar",
    "rbs": "Random Blood Sugar",
    "ppbs": "Post-Prandial Blood Sugar",
    "2hpp": "Post-Prandial Blood Sugar",
    "hba1c": "HbA1c",
    "a1c": "HbA1c",
    "glycosylated hemoglobin": "HbA1c",
    "glycated hemoglobin": "HbA1c",
    "creatinine": "Creatinine",
    "serum creatinine": "Creatinine",
    "urea": "Blood Urea",
    "blood urea": "Blood Urea",
    "bun": "Blood Urea Nitrogen",
    "blood urea nitrogen": "Blood Urea Nitrogen",
    "uric acid": "Uric Acid",
    "serum uric acid": "Uric Acid",
    "sodium": "Sodium",
    "serum sodium": "Sodium",
    "na": "Sodium",
    "potassium": "Potassium",
    "serum potassium": "Potassium",
    "k": "Potassium",
    "chloride": "Chloride",
    "serum chloride": "Chloride",
    "cl": "Chloride",
    "bicarbonate": "Bicarbonate",
    "hco3": "Bicarbonate",
    "calcium": "Calcium",
    "serum calcium": "Calcium",
    "ca": "Calcium",
    "phosphorus": "Phosphorus",
    "phosphate": "Phosphorus",
    "serum phosphorus": "Phosphorus",
    "magnesium": "Magnesium",
    "serum magnesium": "Magnesium",
    # Liver
    "alt": "ALT",
    "sgpt": "ALT",
    "alanine aminotransferase": "ALT",
    "alanine transaminase": "ALT",
    "ast": "AST",
    "sgot": "AST",
    "aspartate aminotransferase": "AST",
    "aspartate transaminase": "AST",
    "alp": "Alkaline Phosphatase",
    "alkaline phosphatase": "Alkaline Phosphatase",
    "ggt": "GGT",
    "gamma gt": "GGT",
    "total bilirubin": "Total Bilirubin",
    "bilirubin total": "Total Bilirubin",
    "direct bilirubin": "Direct Bilirubin",
    "bilirubin direct": "Direct Bilirubin",
    "indirect bilirubin": "Indirect Bilirubin",
    "bilirubin indirect": "Indirect Bilirubin",
    "albumin": "Albumin",
    "serum albumin": "Albumin",
    "total protein": "Total Protein",
    "protein total": "Total Protein",
    "globulin": "Globulin",
    "a/g ratio": "A/G Ratio",
    # Lipids
    "cholesterol": "Total Cholesterol",
    "total cholesterol": "Total Cholesterol",
    "tc": "Total Cholesterol",
    "ldl": "LDL Cholesterol",
    "ldl cholesterol": "LDL Cholesterol",
    "ldl-c": "LDL Cholesterol",
    "hdl": "HDL Cholesterol",
    "hdl cholesterol": "HDL Cholesterol",
    "hdl-c": "HDL Cholesterol",
    "vldl": "VLDL Cholesterol",
    "triglycerides": "Triglycerides",
    "triglyceride": "Triglycerides",
    "tg": "Triglycerides",
    "serum triglycerides": "Triglycerides",
    # Thyroid
    "tsh": "TSH",
    "thyroid stimulating hormone": "TSH",
    "t3": "T3",
    "triiodothyronine": "T3",
    "t4": "T4",
    "thyroxine": "T4",
    "free t3": "Free T3",
    "ft3": "Free T3",
    "free t4": "Free T4",
    "ft4": "Free T4",
    # Iron studies
    "serum iron": "Serum Iron",
    "iron": "Serum Iron",
    "tibc": "TIBC",
    "total iron binding capacity": "TIBC",
    "ferritin": "Ferritin",
    "serum ferritin": "Ferritin",
    "transferrin": "Transferrin",
    "transferrin saturation": "Transferrin Saturation",
    # Inflammatory
    "crp": "CRP",
    "c-reactive protein": "CRP",
    "c reactive protein": "CRP",
    # Coagulation
    "pt": "Prothrombin Time",
    "prothrombin time": "Prothrombin Time",
    "inr": "INR",
    "aptt": "APTT",
    "activated partial thromboplastin time": "APTT",
    # Urine
    "urine protein": "Urine Protein",
    "urine glucose": "Urine Glucose",
    "urine sugar": "Urine Glucose",
    "urine ketones": "Urine Ketones",
    "urine ph": "Urine pH",
    "urine specific gravity": "Urine Specific Gravity",
}

# ------------------------------------------------------------------ #
# Unit canonicalization map
# ------------------------------------------------------------------ #

_UNIT_MAP: dict[str, str] = {
    "g%": "g/dL",
    "gm%": "g/dL",
    "gm/dl": "g/dL",
    "g/dl": "g/dL",
    "mg/dl": "mg/dL",
    "mg%": "mg/dL",
    "meq/l": "mEq/L",
    "meq/dl": "mEq/dL",
    "mmol/l": "mmol/L",
    "iu/l": "IU/L",
    "u/l": "U/L",
    "ku/l": "kU/L",
    "ng/dl": "ng/dL",
    "ng/ml": "ng/mL",
    "pg/ml": "pg/mL",
    "ug/dl": "μg/dL",
    "μg/dl": "μg/dL",
    "miu/ml": "mIU/mL",
    "uiu/ml": "μIU/mL",
    "μiu/ml": "μIU/mL",
    "/cumm": "/uL",
    "cells/cumm": "/uL",
    "cells/ul": "/uL",
    "/ul": "/uL",
    "thou/ul": "×10³/uL",
    "lacs/cumm": "×10³/uL",
    "x10^3/ul": "×10³/uL",
    "10^3/ul": "×10³/uL",
    "x10^6/ul": "×10⁶/uL",
    "10^6/ul": "×10⁶/uL",
    "fl": "fL",
    "mm/hr": "mm/hr",
    "mm/1sthour": "mm/hr",
    "mm/1st hour": "mm/hr",
    "mmhg": "mmHg",
    "°c": "°C",
    "°f": "°F",
    "g/l": "g/L",
    "mcg/dl": "μg/dL",
    "mcg/ml": "μg/mL",
    "msec": "ms",
    "seconds": "sec",
    "sec": "sec",
}

# ------------------------------------------------------------------ #
# Gender normalization
# ------------------------------------------------------------------ #

_GENDER_MAP: dict[str, str] = {
    "m": "Male",
    "male": "Male",
    "man": "Male",
    "boy": "Male",
    "f": "Female",
    "female": "Female",
    "woman": "Female",
    "girl": "Female",
    "t": "Other",
    "trans": "Other",
    "transgender": "Other",
    "other": "Other",
}

# ------------------------------------------------------------------ #
# Status symbol normalization (arrow/flag → text)
# ------------------------------------------------------------------ #

_STATUS_SYMBOLS: dict[str, str] = {
    "↑": "High",
    "↓": "Low",
    "H": "High",
    "L": "Low",
    "N": "Normal",
    "*": "Critical",
    "HH": "Critical",
    "LL": "Critical",
    "A": "Abnormal",
}

# ------------------------------------------------------------------ #
# Public normalization functions
# ------------------------------------------------------------------ #

def normalize_test_name(name: str) -> str:
    """
    Return the canonical form of a lab test name.

    Performs an exact lowercase lookup first, then strips punctuation
    and retries. Falls back to title-cased original if no match is found.

    Args:
        name: Raw test name from the report.

    Returns:
        Canonical test name string.
    """
    if not name:
        return name
    key = name.lower().strip()
    if key in _TEST_NAME_MAP:
        return _TEST_NAME_MAP[key]
    # Strip punctuation and retry
    key_clean = re.sub(r"[^a-z0-9\s]", "", key).strip()
    if key_clean in _TEST_NAME_MAP:
        return _TEST_NAME_MAP[key_clean]
    # Try fuzzy match if rapidfuzz is available
    try:
        from rapidfuzz import process, fuzz  # noqa: PLC0415
        result = process.extractOne(
            key, _TEST_NAME_MAP.keys(), scorer=fuzz.ratio, score_cutoff=88
        )
        if result:
            return _TEST_NAME_MAP[result[0]]
    except ImportError:
        pass
    return name.strip().title()


def normalize_unit(unit: str) -> str:
    """
    Return the canonical SI unit string.

    Args:
        unit: Raw unit string from the report.

    Returns:
        Normalised unit or the original (stripped) if unknown.
    """
    if not unit:
        return unit
    key = unit.lower().strip()
    return _UNIT_MAP.get(key, unit.strip())


def normalize_gender(raw: str) -> str:
    """
    Return "Male", "Female", or "Other" for any gender abbreviation.

    Args:
        raw: Raw gender string (M, F, Male, female, etc.).

    Returns:
        Canonical gender string.
    """
    if not raw:
        return raw
    return _GENDER_MAP.get(raw.lower().strip(), raw.strip().title())


def normalize_status_symbol(symbol: str) -> str:
    """Convert arrow/flag symbols to text status labels."""
    return _STATUS_SYMBOLS.get(symbol.strip(), symbol.strip())
