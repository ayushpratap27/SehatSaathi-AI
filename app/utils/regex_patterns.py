"""
Pre-compiled regex pattern library for medical report extraction.

All patterns are compiled once at import time.
Import the constants directly — never re-compile in hot paths.
"""

from __future__ import annotations

import re

# ------------------------------------------------------------------ #
# Age
# ------------------------------------------------------------------ #

# "Age: 45 Years", "Age/Sex: 45/M", "45 Yrs", "45Y", "45 yr old"
AGE = re.compile(
    r"""
    (?:age|yrs?|years?)\s*[:/]?\s*(\d{1,3})
    |
    (\d{1,3})\s*(?:yrs?|years?|y\.o\.?)
    |
    (?:age|yrs?)\s*/\s*(?:sex|gender)?\s*[:/]?\s*(\d{1,3})
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Also matches "45/M" or "45/F" (age/gender shorthand)
AGE_GENDER_SLASH = re.compile(
    r"\b(\d{1,3})\s*/\s*([MF])\b",
    re.IGNORECASE,
)

# ------------------------------------------------------------------ #
# Gender
# ------------------------------------------------------------------ #

# Standalone Male/Female/M/F labels
GENDER = re.compile(
    r"(?:sex|gender)\s*[:/]\s*(male|female|m|f|trans\w*|other)",
    re.IGNORECASE,
)

# Short forms on their own line or after age/sex
GENDER_SHORT = re.compile(r"\b(male|female)\b", re.IGNORECASE)
GENDER_INITIAL = re.compile(
    r"(?:sex|gender)\s*[:/]\s*([MF])\b",
    re.IGNORECASE,
)

# ------------------------------------------------------------------ #
# Date
# ------------------------------------------------------------------ #

# DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY-MM-DD
DATE_NUMERIC = re.compile(
    r"\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b"
    r"|"
    r"\b(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})\b",
)

# "11 July 2026", "11-Jul-2026", "Jul 11, 2026"
DATE_TEXTUAL = re.compile(
    r"\b(\d{1,2})\s*[-\s]?(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
    r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s*[-\s,]?\s*(\d{2,4})\b"
    r"|"
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
    r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2}),?\s*(\d{2,4})\b",
    re.IGNORECASE,
)

# ------------------------------------------------------------------ #
# Patient / Hospital identifiers
# ------------------------------------------------------------------ #

PATIENT_ID = re.compile(
    r"(?:patient\s+id|pid|mrd(?:\s+no)?|uhid|reg(?:istration)?\s*(?:no|#|number)?|"
    r"opd\s*no|ipd\s*no|lab\s*no)\s*[:/]?\s*([A-Z0-9\-/]+)",
    re.IGNORECASE,
)

MOBILE = re.compile(
    r"(?:mob(?:ile)?|ph(?:one)?|contact|cell)\s*[:/]?\s*(\+?[\d\s\-\(\)]{8,15})"
    r"|"
    r"\b(\+?91[-\s]?)?[6-9]\d{9}\b",
    re.IGNORECASE,
)

# ------------------------------------------------------------------ #
# Vitals
# ------------------------------------------------------------------ #

BLOOD_PRESSURE = re.compile(
    r"\b(?:BP|blood\s+pressure)\s*[:/]?\s*(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mm\s*Hg)?",
    re.IGNORECASE,
)

HEART_RATE = re.compile(
    r"\b(?:HR|heart\s+rate|pulse)\s*[:/]?\s*(\d{2,3})\s*(?:bpm|/min)?",
    re.IGNORECASE,
)

TEMPERATURE = re.compile(
    r"\b(?:temp(?:erature)?)\s*[:/]?\s*(\d{2,3}(?:\.\d)?)\s*(?:°?\s*[CF])?",
    re.IGNORECASE,
)

WEIGHT = re.compile(
    r"\b(?:wt|weight)\s*[:/]?\s*(\d{2,3}(?:\.\d{1,2})?)\s*(?:kg|lbs?)?",
    re.IGNORECASE,
)

HEIGHT = re.compile(
    r"\b(?:ht|height)\s*[:/]?\s*(\d{2,3}(?:\.\d{1,2})?)\s*(?:cm|m|ft|inches?)?",
    re.IGNORECASE,
)

SUGAR = re.compile(
    r"\b(?:FBS|RBS|blood\s+sugar|glucose)\s*[:/]?\s*(\d{2,3}(?:\.\d{1,2})?)\s*(?:mg/dL)?",
    re.IGNORECASE,
)

# ------------------------------------------------------------------ #
# Lab test value + unit
# ------------------------------------------------------------------ #

# Matches: "14.5 g/dL", "7200 /uL", "95 mg/dL", "11.2 x10^3/uL"
VALUE_UNIT = re.compile(
    r"^(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z/μµ%×][a-zA-Z0-9/μµ%·\-\.×\^]*)?$",
)

# Value in the middle of a line: "Hemoglobin: 14.5 g/dL"
INLINE_RESULT = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z\s\(\)\-/\.]{2,50}?)\s*[:\-]\s*"
    r"(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[a-zA-Z/μµ%][a-zA-Z0-9/μµ%·\-\.×\^]*(?:\s*[a-zA-Z0-9]+)?)?",
)

# ------------------------------------------------------------------ #
# Reference range
# ------------------------------------------------------------------ #

# "13.5-17.5" or "13.5–17.5" (with optional spaces)
RANGE_NUMERIC = re.compile(
    r"^(?P<low>\d+(?:\.\d+)?)\s*[-–—]\s*(?P<high>\d+(?:\.\d+)?)$"
)

# "< 100" or "<=100"
RANGE_LESS_THAN = re.compile(r"^[<≤]=?\s*(?P<max>\d+(?:\.\d+)?)$")

# "> 40" or ">=40"
RANGE_GREATER_THAN = re.compile(r"^[>≥]=?\s*(?P<min>\d+(?:\.\d+)?)$")

# "Up to 40", "Upto 100"
RANGE_UPTO = re.compile(r"^(?:up\s*to|upto)\s*(?P<max>\d+(?:\.\d+)?)$", re.IGNORECASE)

# Qualitative reference
RANGE_QUALITATIVE = re.compile(
    r"^(negative|positive|reactive|non[-\s]?reactive|normal|abnormal|absent|present)$",
    re.IGNORECASE,
)

# Inline reference range in parentheses: "(13.5-17.5)" or "[4000-11000]"
INLINE_RANGE = re.compile(
    r"[\(\[]\s*(?P<range>\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?)\s*[\)\]]"
)

# ------------------------------------------------------------------ #
# Section headers (used to locate report sections)
# ------------------------------------------------------------------ #

SECTION_PATIENT = re.compile(
    r"^(?:patient\s+(?:information|details?|data)|demographics?)\s*[:\-]?$",
    re.IGNORECASE,
)

SECTION_LAB = re.compile(
    r"^(?:haematology|hematology|biochemistry|serology|urinalysis|urine\s+(?:exam|analysis|routine)|"
    r"lipid\s+profile|liver\s+function|kidney\s+function|thyroid|coagulation|"
    r"immunology|microbiology|laboratory\s+(?:results?|findings?)|test\s+results?|"
    r"investigations?|reports?)\s*[:\-]?$",
    re.IGNORECASE,
)

SECTION_DIAGNOSIS = re.compile(
    r"^(?:diagnosis|impression|assessment|findings?|conclusion|"
    r"clinical\s+(?:notes?|impression|diagnosis|findings?)|"
    r"provisional\s+diagnosis|differential\s+diagnosis|"
    r"final\s+diagnosis)\s*[:\-]?$",
    re.IGNORECASE,
)

SECTION_MEDICINE = re.compile(
    r"^(?:medication|medicines?|prescription|drugs?|treatment|therapy|"
    r"rx|advised|advice|management)\s*[:\-]?$",
    re.IGNORECASE,
)

SECTION_DOCTOR = re.compile(
    r"^(?:referring\s+(?:doctor|physician)|consultant|doctor|dr\.?|physician)\s*[:\-]?$",
    re.IGNORECASE,
)

# ------------------------------------------------------------------ #
# Hospital / doctor name indicators
# ------------------------------------------------------------------ #

DOCTOR_PREFIX = re.compile(
    r"\b(?:Dr\.?|Prof\.?|Doctor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
    re.IGNORECASE,
)

REFERRED_BY = re.compile(
    r"(?:referred\s+by|consultant|treating\s+doctor|doctor|physician)\s*[:/]?\s*"
    r"(?:Dr\.?\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
    re.IGNORECASE,
)

HOSPITAL_KEYWORDS = re.compile(
    r"\b(?:hospital|clinic|laboratory|lab|diagnostic|medical\s+centre|"
    r"health\s+care|pathology|polyclinic|nursing\s+home)\b",
    re.IGNORECASE,
)

# ------------------------------------------------------------------ #
# Medicine / dosage patterns
# ------------------------------------------------------------------ #

MEDICINE_FORM = re.compile(
    r"\b(?:Tab(?:let)?|Cap(?:sule)?|Syr(?:up)?|Inj(?:ection)?|"
    r"Drops?|Cream|Ointment|Gel|Patch|Inhaler|Spray)\b\.?\s*"
    r"([A-Z][a-z]+(?:\s+[A-Za-z]+)*)",
    re.IGNORECASE,
)

DOSAGE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(?:mg|mcg|μg|g|ml|mL|units?|IU|mmol)\b",
    re.IGNORECASE,
)

FREQUENCY = re.compile(
    r"\b(?P<freq>once\s+daily|twice\s+daily|thrice\s+daily|"
    r"(?:1|2|3|4)\s*times?\s*(?:a\s*)?day|"
    r"OD|BD|TDS|QID|SOS|PRN|HS|AC|PC|STAT)\b",
    re.IGNORECASE,
)

DURATION = re.compile(
    r"(?:for|x)\s*(\d+)\s*(days?|weeks?|months?)",
    re.IGNORECASE,
)
