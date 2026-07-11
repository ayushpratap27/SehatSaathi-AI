"""
Laboratory test result extractor.

Implements three complementary strategies applied in order:
  1. Multi-line state machine  — handles the format shown in the Phase 3 spec
  2. Inline colon pattern      — "Hemoglobin: 14.5 g/dL (13.5-17.5)"
  3. Tab/space table pattern   — "Hemoglobin  14.5  g/dL  13.5-17.5"

Results are deduplicated and status is derived for each test that has a
reference range.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from ai.ner.reference_range_parser import derive_status
from app.schemas.report import LabTest
from app.utils import regex_patterns as P
from app.utils.normalizer import normalize_test_name, normalize_unit

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Constants
# ------------------------------------------------------------------ #

# Words that are NOT test names even though they appear alone on a line
_NON_TEST_WORDS: frozenset[str] = frozenset({
    "result", "results", "reference", "normal", "unit", "units", "range",
    "method", "remark", "remarks", "remarks", "flag", "flags", "status",
    "test", "tests", "investigation", "investigations", "haematology",
    "hematology", "biochemistry", "serology", "microbiology", "urinalysis",
    "patient", "name", "age", "gender", "sex", "date", "hospital", "doctor",
    "sample", "collected", "received", "reported", "specimen",
    "diagnosis", "impression", "finding", "prescription", "medicine",
    "high", "low", "abnormal", "critical", "positive", "negative",
    "report", "page", "value", "observed", "parameter",
})

# Section headers indicating we've entered a lab section
_LAB_SECTION_HEADERS = re.compile(
    r"^(?:haematology|hematology|biochemistry|serology|immunology|urinalysis|"
    r"urine\s+(?:exam|routine|analysis)|lipid|liver\s+function|kidney|"
    r"thyroid|coagulation|complete\s+blood|cbc|blood\s+count|"
    r"investigations?|test\s+results?|laboratory\s+results?)\b",
    re.IGNORECASE,
)

# Reference label lines: "Reference", "Ref Range", "Normal Range", "Biological Ref"
_REF_LABEL = re.compile(
    r"^(?:ref(?:erence)?(?:\s+range)?|normal\s+(?:range|value)|"
    r"biological\s+ref(?:erence)?(?:\s+interval)?)\s*[:/]?$",
    re.IGNORECASE,
)

# Status flags appended in parentheses: "(H)", "(L)", "(↑)", "(A)"
# Requires at least one whitespace before the flag so unit suffixes like 'L' in 'g/dL' are preserved.
_STATUS_SUFFIX = re.compile(r"\s+[\(\[]?\s*([HLACNHhLlAa↑↓\*]{1,3})\s*[\)\]]?\s*$")

# Unit-only line (e.g., "g/dL" or "/uL")
_UNIT_ONLY = re.compile(r"^[a-zA-Z/%×μµ][a-zA-Z0-9/%×μµ·\-\.^]{0,20}$")


# ------------------------------------------------------------------ #
# Helper functions
# ------------------------------------------------------------------ #

def _is_test_name_line(line: str) -> bool:
    """
    Return True if a line looks like a standalone test name.

    Heuristics:
    - No leading digits (not a value line)
    - 2–60 characters
    - Not in the exclusion word list
    - Not a date
    - Not purely punctuation
    """
    stripped = line.strip()
    if not stripped or len(stripped) < 2 or len(stripped) > 70:
        return False
    if stripped[0].isdigit():
        return False
    if stripped.lower() in _NON_TEST_WORDS:
        return False
    # Reject pure-symbol or reference-range lines
    if re.match(r"^[\d\s\-–/\.%<>≤≥±]+$", stripped):
        return False
    # Reject section headers
    if _LAB_SECTION_HEADERS.match(stripped):
        return False
    # Must start with a letter
    return bool(re.match(r"^[A-Za-z]", stripped))


def _parse_value_unit(line: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extract a numeric value and optional unit from a line.

    Returns:
        (value_float, unit_str) or (None, None) if the line is not a result.
    """
    line = line.strip()
    # Remove trailing status flags before parsing
    line = _STATUS_SUFFIX.sub("", line).strip()

    m = P.VALUE_UNIT.match(line)
    if m:
        try:
            val = float(m.group("value"))
            unit = normalize_unit(m.group("unit") or "")
            return val, unit or None
        except ValueError:
            pass
    return None, None


def _parse_inline_range(line: str) -> Optional[str]:
    """Extract an inline reference range like '(13.5-17.5)' from a line."""
    m = P.INLINE_RANGE.search(line)
    return m.group("range") if m else None


def _is_reference_range_line(line: str) -> bool:
    """Return True if a line looks like a standalone reference range."""
    stripped = line.strip()
    return bool(
        P.RANGE_NUMERIC.match(stripped)
        or P.RANGE_LESS_THAN.match(stripped)
        or P.RANGE_GREATER_THAN.match(stripped)
        or P.RANGE_UPTO.match(stripped)
        or P.RANGE_QUALITATIVE.match(stripped)
    )


def _clean_test_name(name: str) -> str:
    """Strip common trailing junk from test names."""
    name = re.sub(r"\s*[\(\[]\s*$", "", name).strip()  # trailing open paren
    name = re.sub(r"\s*:$", "", name).strip()           # trailing colon
    return name


def _build_lab_test(
    raw_name: str,
    value: Optional[float],
    unit: Optional[str],
    ref_raw: Optional[str],
    method: Optional[str] = None,
) -> LabTest:
    """Create a LabTest with normalised name and derived status."""
    clean_name = normalize_test_name(_clean_test_name(raw_name))
    status: Optional[str] = derive_status(value, ref_raw) if ref_raw else None

    # If value is None but ref is qualitative, status may still be unknown
    return LabTest(
        test_name=clean_name,
        value=value,
        unit=unit,
        reference_range=ref_raw,
        method=method,
        status=status,
    )


# ------------------------------------------------------------------ #
# Extraction strategies
# ------------------------------------------------------------------ #

def _extract_multiline(lines: List[str]) -> List[LabTest]:
    """
    State-machine parser for multi-line formatted tests.

    Handles the format from the Phase 3 spec::

        Hemoglobin
        12.4 g/dL
        Reference
        13.5–17.5

    Also handles::

        Hemoglobin
        12.4
        g/dL
        13.5-17.5
    """
    tests: List[LabTest] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if _is_test_name_line(line):
            test_name = line
            value: Optional[float] = None
            unit: Optional[str] = None
            ref: Optional[str] = None

            j = i + 1

            # Next non-empty line: try value+unit
            while j < n and not lines[j].strip():
                j += 1

            if j < n:
                val, u = _parse_value_unit(lines[j])
                if val is not None:
                    value, unit = val, u
                    # Check for inline reference range on same line
                    ref = _parse_inline_range(lines[j])
                    j += 1

                    # If no unit yet, check if next line is a unit
                    if not unit and j < n and _UNIT_ONLY.match(lines[j].strip()):
                        unit = normalize_unit(lines[j].strip())
                        j += 1

                    # Skip "Reference" label line
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and _REF_LABEL.match(lines[j].strip()):
                        j += 1

                    # Next non-empty line: reference range?
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and not ref and _is_reference_range_line(lines[j].strip()):
                        ref = lines[j].strip()
                        j += 1

                    tests.append(_build_lab_test(test_name, value, unit, ref))
                    i = j
                    continue

        i += 1

    return tests


def _extract_inline(lines: List[str]) -> List[LabTest]:
    """
    Parse lines of the form::

        Hemoglobin: 14.5 g/dL (13.5-17.5)
        WBC: 7200 /uL
        Glucose: 95 mg/dL  Reference: 70-100
    """
    tests: List[LabTest] = []

    # Full inline pattern: Name: Value Unit (Range)
    _FULL = re.compile(
        r"^(?P<name>[A-Za-z][A-Za-z\s\(\)\-/\.]{1,50}?)\s*:\s*"
        r"(?P<value>\d+(?:\.\d+)?)\s*"
        r"(?P<unit>[a-zA-Z/μµ%×][a-zA-Z0-9/μµ%·\-\.×\^]*)?"
        r"(?:\s*(?:\(|Ref(?:erence)?\s*[:/]?\s*)"
        r"(?P<ref>\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?|"
        r"[<>≤≥]\s*\d+(?:\.\d+)?|"
        r"(?:negative|positive|reactive|non-reactive|normal|abnormal))"
        r"[\)]?)?",
        re.IGNORECASE,
    )

    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = _FULL.match(line)
        if m:
            name = m.group("name").strip()
            if name.lower() in _NON_TEST_WORDS or len(name) < 2:
                continue
            try:
                value: Optional[float] = float(m.group("value"))
            except (TypeError, ValueError):
                value = None
            unit  = normalize_unit(m.group("unit") or "")
            ref   = m.group("ref")
            tests.append(_build_lab_test(name, value, unit or None, ref))

    return tests


def _extract_table(lines: List[str]) -> List[LabTest]:
    """
    Parse tabular format::

        Hemoglobin    14.5    g/dL    13.5-17.5
        WBC           7200    /uL     4000-11000

    Columns are separated by 2+ spaces or tab characters.
    """
    tests: List[LabTest] = []
    _SPLIT = re.compile(r"\t|(?:  +)")

    for line in lines:
        cols = [c.strip() for c in _SPLIT.split(line) if c.strip()]
        if len(cols) < 2:
            continue

        # Column 0: test name
        name = cols[0]
        if not _is_test_name_line(name) or name.lower() in _NON_TEST_WORDS:
            continue

        # Column 1: value (and optionally unit)
        val, unit = _parse_value_unit(cols[1])
        if val is None:
            continue

        # Column 2: unit (if not already parsed with value)
        if not unit and len(cols) > 2 and not _is_reference_range_line(cols[2]):
            unit = normalize_unit(cols[2])

        # Last column: reference range
        ref: Optional[str] = None
        for col in reversed(cols[2:]):
            if _is_reference_range_line(col):
                ref = col
                break

        tests.append(_build_lab_test(name, val, unit or None, ref))

    return tests


# ------------------------------------------------------------------ #
# Main extractor class
# ------------------------------------------------------------------ #

class LabExtractor:
    """
    Multi-strategy laboratory test extractor.

    Runs three strategies in priority order and deduplicates results.
    The strategy with the most hits is preferred, with the others filling
    in tests that were missed.
    """

    def extract(self, text: str) -> List[LabTest]:
        """
        Extract all lab test results from cleaned medical report text.

        Args:
            text: Cleaned report text from Phase 2.

        Returns:
            List of :class:`~app.schemas.report.LabTest` instances.
        """
        lines = text.split("\n")
        stripped_lines = [ln.strip() for ln in lines]

        multiline_tests = _extract_multiline(stripped_lines)
        inline_tests    = _extract_inline(stripped_lines)
        table_tests     = _extract_table(stripped_lines)

        # Merge: multiline → inline → table (in priority order)
        seen:  Dict[str, LabTest] = {}
        for test in multiline_tests + inline_tests + table_tests:
            key = test.test_name.lower()
            if key not in seen:
                seen[key] = test
            else:
                # Prefer the entry with more information
                existing = seen[key]
                if (test.reference_range and not existing.reference_range) or (
                    test.value is not None and existing.value is None
                ):
                    seen[key] = test

        results = list(seen.values())
        logger.info("LabExtractor: found %d tests", len(results))
        return results


lab_extractor = LabExtractor()
