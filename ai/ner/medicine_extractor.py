"""
Medicine / prescription extractor.

Extracts medicine names, dosages, frequencies, and durations from
prescription sections, clinical notes, and inline mentions.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from app.schemas.report import MedicineInfo
from app.utils import regex_patterns as P

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Medicine name detection
# ------------------------------------------------------------------ #

# Common Indian/generic medicine brand patterns
_COMMON_MEDICINES = re.compile(
    r"\b((?:Tab(?:let)?|Cap(?:sule)?|Syr(?:up)?|Inj(?:ection)?|"
    r"Drops?|Cream|Gel|Ointment|Patch|Inhaler|Spray|Sachet)\s*\.?\s*"
    r"(?:of\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-zA-Z]+)?))",
    re.IGNORECASE,
)

# Generic API names (capitalize each word, no common word)
_GENERIC_MEDICINE = re.compile(
    r"\b([A-Z][a-z]{2,}(?:mycin|cillin|statin|prazole|olol|artan|pril|mab|nib|vir|zole|oxacin|"
    r"azole|cycline|zepam|dine|pine|amine|azine|dipine|triptan|dronate|"
    r"caine|actam|penem|oxetine|setron|lukast)\w*)\b",
)

# Frequency normalisation
_FREQ_NORMALISE: dict[str, str] = {
    "od": "Once daily",
    "once daily": "Once daily",
    "once a day": "Once daily",
    "1-0-0": "Once daily (morning)",
    "bd": "Twice daily",
    "bid": "Twice daily",
    "twice daily": "Twice daily",
    "twice a day": "Twice daily",
    "1-0-1": "Twice daily",
    "tds": "Three times daily",
    "tid": "Three times daily",
    "thrice daily": "Three times daily",
    "three times daily": "Three times daily",
    "1-1-1": "Three times daily",
    "qid": "Four times daily",
    "four times daily": "Four times daily",
    "sos": "As needed",
    "prn": "As needed",
    "as needed": "As needed",
    "hs": "At bedtime",
    "at bedtime": "At bedtime",
    "ac": "Before meals",
    "before meals": "Before meals",
    "pc": "After meals",
    "after meals": "After meals",
    "stat": "Immediately",
}

# Route normalisation
_ROUTE_KEYWORDS: dict[str, str] = {
    "oral": "Oral",
    "po": "Oral",
    "by mouth": "Oral",
    "iv": "Intravenous",
    "intravenous": "Intravenous",
    "im": "Intramuscular",
    "intramuscular": "Intramuscular",
    "sc": "Subcutaneous",
    "subcutaneous": "Subcutaneous",
    "topical": "Topical",
    "inhalation": "Inhalation",
    "sublingual": "Sublingual",
    "sl": "Sublingual",
    "rectal": "Rectal",
    "nasal": "Nasal",
    "optic": "Ophthalmic",
    "otic": "Otic",
}


def _normalise_frequency(raw: str) -> str:
    return _FREQ_NORMALISE.get(raw.lower().strip(), raw.strip().title())


def _normalise_route(raw: str) -> Optional[str]:
    return _ROUTE_KEYWORDS.get(raw.lower().strip())


def _extract_section_lines(text: str) -> List[str]:
    """Return lines from prescription / medication sections."""
    lines = text.split("\n")
    result: List[str] = []
    in_section = False

    for line in lines:
        stripped = line.strip()
        if P.SECTION_MEDICINE.match(stripped):
            in_section = True
            continue
        # Stop at the next major section header
        if in_section and (
            P.SECTION_LAB.match(stripped)
            or P.SECTION_DIAGNOSIS.match(stripped)
            or P.SECTION_PATIENT.match(stripped)
        ):
            break
        if in_section and stripped:
            result.append(stripped)

    return result


class MedicineExtractor:
    """Extracts medicine information from medical report text."""

    def extract(self, text: str) -> List[MedicineInfo]:
        """
        Parse medicine names, dosages, and administration details.

        Args:
            text: Cleaned report text from Phase 2.

        Returns:
            List of :class:`~app.schemas.report.MedicineInfo` instances.
        """
        medicines: List[MedicineInfo] = []
        seen_names: set[str] = set()

        # Strategy 1: Section-based extraction
        section_lines = _extract_section_lines(text)
        for line in section_lines:
            med = self._parse_medicine_line(line)
            if med and med.name.lower() not in seen_names:
                medicines.append(med)
                seen_names.add(med.name.lower())

        # Strategy 2: "Tab./Cap./Inj." prefix detection across whole text
        for m in _COMMON_MEDICINES.finditer(text):
            full_match = m.group(1).strip()
            name_part = m.group(2).strip() if m.group(2) else full_match
            # Get surrounding context for dosage/frequency
            start = m.start()
            context = text[start: start + 120]
            med = self._parse_medicine_line(context)
            if med:
                med_name_clean = name_part.title()
                if med_name_clean.lower() not in seen_names:
                    med.name = med_name_clean
                    medicines.append(med)
                    seen_names.add(med_name_clean.lower())

        # Strategy 3: Generic drug name scanning
        for m in _GENERIC_MEDICINE.finditer(text):
            drug = m.group(1).strip()
            if drug.lower() not in seen_names and len(drug) > 4:
                context = text[m.start(): m.start() + 120]
                dosage  = self._extract_dosage(context)
                freq    = self._extract_frequency(context)
                dur     = self._extract_duration(context)
                medicines.append(MedicineInfo(
                    name=drug.title(),
                    dosage=dosage,
                    frequency=freq,
                    duration=dur,
                ))
                seen_names.add(drug.lower())

        logger.info("MedicineExtractor: found %d medicines", len(medicines))
        return medicines

    def _parse_medicine_line(self, line: str) -> Optional[MedicineInfo]:
        """Extract a single MedicineInfo from a free-text line."""
        line = line.strip()
        if not line or len(line) < 3:
            return None

        # Strip form prefix ("Tab.", "Cap.", etc.) to get the drug name
        name_match = re.match(
            r"^(?:Tab(?:let)?|Cap(?:sule)?|Syr(?:up)?|Inj(?:ection)?|"
            r"Drops?|Cream|Gel|Ointment|Spray)\.?\s*",
            line,
            re.IGNORECASE,
        )
        name_start = name_match.end() if name_match else 0
        remainder  = line[name_start:]

        # Name is the first run of letters before digits or punctuation
        name_m = re.match(r"([A-Za-z][A-Za-z\s\-]{1,40}?)(?=\s+\d|\s*$)", remainder)
        if not name_m:
            return None
        name = name_m.group(1).strip()
        if len(name) < 2 or name.lower() in {"the", "and", "or", "of", "with"}:
            return None

        dosage   = self._extract_dosage(line)
        freq     = self._extract_frequency(line)
        duration = self._extract_duration(line)
        route    = self._extract_route(line)

        return MedicineInfo(
            name=name.title(),
            dosage=dosage,
            frequency=freq,
            duration=duration,
            route=route,
        )

    @staticmethod
    def _extract_dosage(text: str) -> Optional[str]:
        m = P.DOSAGE.search(text)
        return m.group(0).strip() if m else None

    @staticmethod
    def _extract_frequency(text: str) -> Optional[str]:
        m = P.FREQUENCY.search(text)
        return _normalise_frequency(m.group("freq")) if m else None

    @staticmethod
    def _extract_duration(text: str) -> Optional[str]:
        m = P.DURATION.search(text)
        return f"{m.group(1)} {m.group(2)}" if m else None

    @staticmethod
    def _extract_route(text: str) -> Optional[str]:
        for keyword, normalised in _ROUTE_KEYWORDS.items():
            if re.search(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE):
                return normalised
        return None


medicine_extractor = MedicineExtractor()
