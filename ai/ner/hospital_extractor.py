"""
Hospital / diagnostic laboratory information extractor.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from app.schemas.report import HospitalInfo
from app.utils import regex_patterns as P

logger = logging.getLogger(__name__)

_HOSP_NAME_LABEL = re.compile(
    r"(?:hospital|clinic|laboratory|lab|diagnostic|centre|center|pathology)\s*(?:name)?\s*[:/]\s*"
    r"([A-Za-z][A-Za-z\s\-&,\.]{2,80})",
    re.IGNORECASE,
)
_ADDRESS_LABEL = re.compile(
    r"(?:address|location)\s*[:/]\s*(.{10,200}?)(?:\n|$)",
    re.IGNORECASE,
)
_DEPARTMENT_LABEL = re.compile(
    r"(?:department|dept\.?|ward|unit)\s*[:/]\s*([A-Za-z][A-Za-z\s\-&]{2,60})",
    re.IGNORECASE,
)
_ACCREDITATION = re.compile(
    r"(?:nabl|nabh|iso|cap|jci|accreditation|reg(?:\.|\s)?no\.?)\s*[:/]?\s*([A-Z0-9\-/]{3,30})",
    re.IGNORECASE,
)


def _find_hospital_name(text: str) -> Optional[str]:
    """Try label-based then keyword-based detection."""
    # Label-based
    m = _HOSP_NAME_LABEL.search(text)
    if m:
        name = m.group(1).strip().split("\n")[0].strip()
        if len(name) > 3:
            return name

    # The hospital name often appears in the very first few lines
    header_lines = [ln.strip() for ln in text[:800].split("\n") if ln.strip()]
    for line in header_lines[:6]:
        if P.HOSPITAL_KEYWORDS.search(line):
            # Return the full line as the hospital name (strip labels)
            name = re.sub(r"^(?:hospital|laboratory|lab|clinic)\s*[:/]\s*", "", line, flags=re.IGNORECASE).strip()
            if len(name) > 3:
                return name

    return None


class HospitalExtractor:
    """Extracts hospital / lab facility details from the report header."""

    def extract(self, text: str) -> HospitalInfo:
        """
        Parse hospital information from cleaned report text.

        Args:
            text: Full cleaned report text.

        Returns:
            :class:`~app.schemas.report.HospitalInfo` instance.
        """
        name:    Optional[str] = _find_hospital_name(text)
        address: Optional[str] = None
        dept:    Optional[str] = None
        reg_no:  Optional[str] = None

        m = _ADDRESS_LABEL.search(text)
        if m:
            address = m.group(1).strip()

        m = _DEPARTMENT_LABEL.search(text)
        if m:
            dept = m.group(1).strip().title()

        m = _ACCREDITATION.search(text)
        if m:
            reg_no = m.group(1).strip()

        info = HospitalInfo(name=name, address=address, department=dept, registration_number=reg_no)
        logger.debug("HospitalExtractor: %s", info.model_dump(exclude_none=True))
        return info


hospital_extractor = HospitalExtractor()
