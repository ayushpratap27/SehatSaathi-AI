"""
Patient information extractor.

Extracts demographic details from the report header using regex patterns.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from app.schemas.report import PatientInfo
from app.utils import regex_patterns as P
from app.utils.normalizer import normalize_gender

logger = logging.getLogger(__name__)

# Explicit label→value patterns for structured report headers
_NAME_PATTERNS = [
    # "Patient Name: John Doe" — stop before known field labels or digits
    re.compile(
        r"patient\s*(?:name|'s\s*name)?\s*[:/]\s*"
        r"([A-Za-z][A-Za-z\s\.]{1,50}?)"
        r"(?=\s*(?:Age|Gender|Sex|DOB|D\.O\.B|Date|ID|Mobile|Phone|\d|$|\n))",
        re.IGNORECASE,
    ),
    re.compile(
        r"name\s*[:/]\s*"
        r"([A-Za-z][A-Za-z\s\.]{1,50}?)"
        r"(?=\s*(?:Age|Gender|Sex|DOB|Date|\d|$|\n))",
        re.IGNORECASE,
    ),
    re.compile(r"^name\s+([A-Za-z][A-Za-z\s\.]{1,60})$", re.IGNORECASE | re.MULTILINE),
]

_AGE_LABEL = re.compile(r"(?:age|yrs?\.?|years?)\s*[:/]?\s*(\d{1,3})", re.IGNORECASE)
_DOB_LABEL = re.compile(
    r"(?:d\.?o\.?b\.?|date\s+of\s+birth|dob)\s*[:/]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
    re.IGNORECASE,
)
_GENDER_LABEL = re.compile(
    r"(?:sex|gender)\s*[:/]?\s*(male|female|m\.?|f\.?|transgender|other)",
    re.IGNORECASE,
)
_PATIENT_ID = re.compile(
    r"(?:patient\s*(?:id|no\.?|number)|pid|mrd\s*(?:no\.?)?|uhid|registration\s*(?:no\.?)?|"
    r"opd\s*no\.?|ipd\s*no\.?|lab\s*(?:id|no\.?))\s*[:/]?\s*([A-Z0-9\-/]{2,20})",
    re.IGNORECASE,
)
_MOBILE = re.compile(
    r"(?:mob(?:ile)?|phone|contact|cell)\s*[:/]?\s*(\+?[\d\s\-\(\)]{8,16})",
    re.IGNORECASE,
)
_HOSP_NO = re.compile(
    r"(?:hospital\s*(?:no\.?|number)|inpatient\s*no\.?|bed\s*no\.?)\s*[:/]?\s*([A-Z0-9\-/]{2,20})",
    re.IGNORECASE,
)


def _extract_name(text: str) -> Optional[str]:
    for pat in _NAME_PATTERNS:
        m = pat.search(text)
        if m:
            # Take only the first line of the match — prevents capturing across newlines
            name = m.group(1).strip().split("\n")[0].strip()
            # Exclude obviously wrong matches (section headers, long phrases)
            if 2 <= len(name.split()) <= 5 and not any(
                kw in name.lower() for kw in ("hospital", "lab", "report", "department")
            ):
                return name.title()
    return None


def _extract_age(text: str) -> Optional[int]:
    # Try "Age: 45" style first
    m = _AGE_LABEL.search(text)
    if m:
        try:
            age = int(m.group(1))
            if 0 < age < 130:
                return age
        except ValueError:
            pass
    # Try "45/M" or "45/F" shorthand
    m = P.AGE_GENDER_SLASH.search(text)
    if m:
        try:
            age = int(m.group(1))
            if 0 < age < 130:
                return age
        except ValueError:
            pass
    return None


def _extract_gender(text: str) -> Optional[str]:
    m = _GENDER_LABEL.search(text)
    if m:
        return normalize_gender(m.group(1))
    # Try "45/M" shorthand
    m = P.AGE_GENDER_SLASH.search(text)
    if m:
        return normalize_gender(m.group(2))
    # Standalone "Male" / "Female" — restrict to header lines only to avoid
    # false matches from gender-specific reference ranges (e.g. "Male: 13.5–17.5")
    header_lines = "\n".join(text.split("\n")[:6])
    for pat in (
        re.compile(r"\b(male)\b", re.IGNORECASE),
        re.compile(r"\b(female)\b", re.IGNORECASE),
    ):
        m = pat.search(header_lines)
        if m:
            return normalize_gender(m.group(1))
    return None


def _extract_patient_id(text: str) -> Optional[str]:
    m = _PATIENT_ID.search(text)
    return m.group(1).strip() if m else None


def _extract_mobile(text: str) -> Optional[str]:
    m = _MOBILE.search(text)
    if m:
        return re.sub(r"\s+", "", m.group(1))
    # Bare 10-digit Indian mobile
    m = re.search(r"\b([6-9]\d{9})\b", text)
    return m.group(1) if m else None


def _extract_hospital_number(text: str) -> Optional[str]:
    m = _HOSP_NO.search(text)
    return m.group(1).strip() if m else None


def _extract_dob(text: str) -> Optional[str]:
    m = _DOB_LABEL.search(text)
    return m.group(1).strip() if m else None


class PatientExtractor:
    """
    Extracts patient demographic information from medical report text.

    All fields default to ``None`` when not found — partial extraction
    never raises an error.
    """

    def extract(self, text: str) -> PatientInfo:
        """
        Parse patient information from cleaned report text.

        Args:
            text: Cleaned text output from Phase 2.

        Returns:
            :class:`~app.schemas.report.PatientInfo` instance.
        """
        # Work on the first 1500 characters (patient info is always at the top)
        header = text[:1500]

        name      = _extract_name(header)
        age       = _extract_age(header)
        gender    = _extract_gender(header)
        dob       = _extract_dob(header)
        pid       = _extract_patient_id(header)
        mobile    = _extract_mobile(header)
        hosp_no   = _extract_hospital_number(header)

        info = PatientInfo(
            name=name,
            age=age,
            gender=gender,
            date_of_birth=dob,
            patient_id=pid,
            mobile=mobile,
            hospital_number=hosp_no,
        )
        logger.debug("PatientExtractor: %s", info.model_dump(exclude_none=True))
        return info


# Module-level singleton
patient_extractor = PatientExtractor()
