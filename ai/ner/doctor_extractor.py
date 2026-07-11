"""
Doctor information extractor.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from app.schemas.report import DoctorInfo
from app.utils import regex_patterns as P

logger = logging.getLogger(__name__)

_DESIGNATION_PREFIXES = re.compile(
    r"\b(Dr\.?|Prof\.?|Doctor|Physician|Specialist)\b",
    re.IGNORECASE,
)
_NAME_AFTER_PREFIX = re.compile(
    r"(?:Dr\.?|Prof\.?|Doctor)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})",
    re.IGNORECASE,
)
_REG_NUMBER = re.compile(
    r"(?:reg(?:istration)?\s*(?:no\.?|number|#)|mci\s*no\.?|council\s*no\.?)\s*[:/]?\s*([A-Z0-9\-/]{3,20})",
    re.IGNORECASE,
)


class DoctorExtractor:
    """Extracts referring / treating doctor details from the report."""

    def extract(self, text: str) -> DoctorInfo:
        """
        Parse doctor information from cleaned report text.

        Args:
            text: Full cleaned report text.

        Returns:
            :class:`~app.schemas.report.DoctorInfo` instance.
        """
        name:            Optional[str] = None
        designation:     Optional[str] = None
        reg_number:      Optional[str] = None

        # Look for "Referred by / Consultant / Doctor: Dr. XYZ"
        m = P.REFERRED_BY.search(text)
        if m:
            raw = m.group(1).strip()
            # Strip any trailing designation/degree
            raw = re.sub(r"\s*(?:MBBS|MD|MS|DNB|DM|MCh|FRCS|MRCP).*$", "", raw, flags=re.IGNORECASE).strip()
            if 1 <= len(raw.split()) <= 5:
                name = raw.title()

        # Fall back to "Dr. XYZ" prefix scan
        if not name:
            m = _NAME_AFTER_PREFIX.search(text)
            if m:
                name = m.group(1).strip().title()

        # Designation (e.g., "Dr." prefix found)
        if _DESIGNATION_PREFIXES.search(text[:500]):
            designation = "Dr."

        # Registration number
        m = _REG_NUMBER.search(text)
        if m:
            reg_number = m.group(1).strip()

        info = DoctorInfo(name=name, designation=designation, registration_number=reg_number)
        logger.debug("DoctorExtractor: %s", info.model_dump(exclude_none=True))
        return info


doctor_extractor = DoctorExtractor()
