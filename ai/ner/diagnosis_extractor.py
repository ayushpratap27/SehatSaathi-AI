"""
Diagnosis / clinical impression extractor.

Extracts diagnosis statements, clinical impressions, assessments,
findings, and symptoms from structured report sections.
"""

from __future__ import annotations

import logging
import re
from typing import List

from app.utils import regex_patterns as P

logger = logging.getLogger(__name__)

# All patterns that introduce a diagnosis value
_DIAGNOSIS_LABELS = re.compile(
    r"(?:diagnosis|impression|assessment|finding|conclusion|"
    r"clinical\s+(?:diagnosis|impression|notes?|finding)|"
    r"provisional\s+diagnosis|differential\s+diagnosis|"
    r"final\s+diagnosis|clinical\s+diagnosis)\s*[:/]",
    re.IGNORECASE,
)

# Lines containing disease/condition keywords (fallback heuristic)
_DISEASE_KEYWORDS = re.compile(
    r"\b(?:anemia|anaemia|diabetes|hypertension|infection|fever|"
    r"deficiency|syndrome|disease|disorder|carcinoma|malignancy|"
    r"thyroid|hypothyroid|hyperthyroid|hepatitis|malaria|typhoid|"
    r"tuberculosis|tb\b|pneumonia|asthma|copd|failure|insufficiency|"
    r"stone|calculus|obstruction|stenosis|polyp|cyst|tumor|tumour|"
    r"fracture|sprain|arthritis|gout|lupus|psoriasis|eczema|"
    r"hypothyroidism|hyperthyroidism|hyperglycemia|dyslipidemia)\b",
    re.IGNORECASE,
)


def _extract_section_diagnoses(text: str) -> List[str]:
    """Extract diagnoses from labeled sections."""
    diagnoses: List[str] = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Check for section header
        if P.SECTION_DIAGNOSIS.match(line):
            # Collect subsequent lines until next section header or blank+header
            i += 1
            while i < len(lines):
                content = lines[i].strip()
                if not content:
                    i += 1
                    continue
                # Stop at next major section
                if (
                    P.SECTION_LAB.match(content)
                    or P.SECTION_MEDICINE.match(content)
                    or P.SECTION_PATIENT.match(content)
                    or P.SECTION_DOCTOR.match(content)
                ):
                    break
                # Skip lines that look like labels
                if P.SECTION_DIAGNOSIS.match(content):
                    i += 1
                    continue
                diagnoses.append(content)
                i += 1
            continue

        # Check for inline "Diagnosis: Iron Deficiency Anemia"
        m = _DIAGNOSIS_LABELS.search(line)
        if m:
            remainder = line[m.end():].strip()
            if remainder:
                diagnoses.append(remainder)
            else:
                # Value on next line
                if i + 1 < len(lines) and lines[i + 1].strip():
                    diagnoses.append(lines[i + 1].strip())
                    i += 2
                    continue

        i += 1

    return diagnoses


def _extract_keyword_diagnoses(text: str) -> List[str]:
    """
    Fallback: collect lines that contain disease/condition keywords
    but are not lab test result lines (no numeric values).
    """
    results: List[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # Skip lines that are obviously lab result lines (have numbers + units)
        if re.search(r"\d+(?:\.\d+)?\s*(?:g/dL|mg/dL|/uL|mmol)", stripped, re.IGNORECASE):
            continue
        if _DISEASE_KEYWORDS.search(stripped) and len(stripped) < 120:
            results.append(stripped)
    return results


class DiagnosisExtractor:
    """
    Extracts diagnosis statements from medical report text.

    Uses labeled-section detection first, then falls back to
    keyword-based scanning.
    """

    def extract(self, text: str) -> List[str]:
        """
        Parse diagnosis statements from cleaned report text.

        Args:
            text: Cleaned report text from Phase 2.

        Returns:
            Deduplicated list of diagnosis strings.
        """
        diagnoses: List[str] = []

        # Primary: section-based
        section_diagnoses = _extract_section_diagnoses(text)
        diagnoses.extend(section_diagnoses)

        # Fallback: keyword scan if nothing found in sections
        if not diagnoses:
            diagnoses.extend(_extract_keyword_diagnoses(text))

        # Clean and deduplicate
        cleaned: List[str] = []
        seen: set[str] = set()
        for d in diagnoses:
            d = d.strip().rstrip(".,;:")
            if d and d.lower() not in seen and len(d) > 2:
                cleaned.append(d)
                seen.add(d.lower())

        logger.info("DiagnosisExtractor: found %d entries", len(cleaned))
        return cleaned


diagnosis_extractor = DiagnosisExtractor()
