"""
JSON builder — combines all Phase 3 extractors into one ParsedReport.

This is the single public entry point for the extraction pipeline:

    report = build_report(cleaned_text)
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from ai.ner.diagnosis_extractor import diagnosis_extractor
from ai.ner.doctor_extractor import doctor_extractor
from ai.ner.hospital_extractor import hospital_extractor
from ai.ner.lab_extractor import lab_extractor
from ai.ner.medicine_extractor import medicine_extractor
from ai.ner.patient_extractor import patient_extractor
from app.schemas.report import ParsedReport
from app.utils import regex_patterns as P

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Top-level date & sample type extraction (too small for own modules)
# ------------------------------------------------------------------ #

_REPORT_DATE_LABELS = re.compile(
    r"(?:report(?:ed)?\s*date|collection\s*date|sample\s*date|"
    r"test\s*date|date\s*of\s*(?:collection|report|test))\s*[:/]?\s*"
    r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})",
    re.IGNORECASE,
)

_SAMPLE_TYPE = re.compile(
    r"(?:specimen|sample(?:\s+type)?|material)\s*[:/]?\s*"
    r"(blood|serum|plasma|urine|stool|csf|sputum|swab|tissue|biopsy|"
    r"whole\s+blood|venous\s+blood|random\s+urine|mid-stream\s+urine)",
    re.IGNORECASE,
)


def _extract_report_date(text: str) -> Optional[str]:
    m = _REPORT_DATE_LABELS.search(text)
    if m:
        return m.group(1).strip()
    # Fallback: first date-like string in the document
    m = P.DATE_NUMERIC.search(text[:1000])
    if m:
        parts = [g for g in m.groups() if g]
        if parts:
            return "/".join(parts)
    return None


def _extract_sample_type(text: str) -> Optional[str]:
    m = _SAMPLE_TYPE.search(text)
    return m.group(1).strip().title() if m else None


# ------------------------------------------------------------------ #
# Main builder function
# ------------------------------------------------------------------ #

def build_report(text: str) -> ParsedReport:
    """
    Run all Phase 3 extractors on cleaned medical report text and return
    a fully structured :class:`~app.schemas.report.ParsedReport`.

    This function is the primary public API for Phase 3.

    Args:
        text: Cleaned text produced by the Phase 2 extraction pipeline.

    Returns:
        A :class:`~app.schemas.report.ParsedReport` instance.
    """
    t0 = time.perf_counter()
    logger.info("Building structured report from %d characters", len(text))

    patient  = patient_extractor.extract(text)
    hospital = hospital_extractor.extract(text)
    doctor   = doctor_extractor.extract(text)
    tests    = lab_extractor.extract(text)
    diag     = diagnosis_extractor.extract(text)
    meds     = medicine_extractor.extract(text)

    date        = _extract_report_date(text)
    sample_type = _extract_sample_type(text)

    report = ParsedReport(
        patient=patient,
        hospital=hospital,
        doctor=doctor,
        tests=tests,
        diagnosis=diag,
        medicines=meds,
        report_date=date,
        sample_type=sample_type,
    )

    elapsed = time.perf_counter() - t0
    logger.info(
        "Report built in %.2fs — tests=%d diagnoses=%d medicines=%d",
        elapsed, len(tests), len(diag), len(meds),
    )
    return report
