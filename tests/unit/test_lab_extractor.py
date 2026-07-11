"""
Unit tests for ai/ner/lab_extractor.py and reference range parser.
"""

from __future__ import annotations

import pytest

from ai.ner.lab_extractor import LabExtractor
from ai.ner.reference_range_parser import ReferenceRange, derive_status

extractor = LabExtractor()


# ------------------------------------------------------------------ #
# Reference range parser
# ------------------------------------------------------------------ #

class TestReferenceRangeParser:
    def test_parse_numeric_range(self) -> None:
        rr = ReferenceRange.from_string("13.5-17.5")
        assert rr.low == 13.5
        assert rr.high == 17.5

    def test_parse_em_dash_range(self) -> None:
        rr = ReferenceRange.from_string("13.5\u201317.5")
        assert rr.low == 13.5
        assert rr.high == 17.5

    def test_parse_less_than(self) -> None:
        rr = ReferenceRange.from_string("< 100")
        assert rr.high == 100.0
        assert rr.low is None

    def test_parse_greater_than(self) -> None:
        rr = ReferenceRange.from_string("> 40")
        assert rr.low == 40.0
        assert rr.high is None

    def test_parse_upto(self) -> None:
        rr = ReferenceRange.from_string("Upto 200")
        assert rr.high == 200.0

    def test_parse_qualitative_negative(self) -> None:
        rr = ReferenceRange.from_string("Negative")
        assert rr.is_qualitative is True
        assert rr.expected == "negative"

    def test_parse_qualitative_non_reactive(self) -> None:
        rr = ReferenceRange.from_string("Non-Reactive")
        assert rr.is_qualitative is True


class TestStatusDerivation:
    def test_normal_in_range(self) -> None:
        assert derive_status(14.5, "13.5-17.5") == "Normal"

    def test_low_below_range(self) -> None:
        assert derive_status(12.0, "13.5-17.5") == "Low"

    def test_high_above_range(self) -> None:
        assert derive_status(11200, "4000-11000") == "High"

    def test_critical_very_low(self) -> None:
        # 2.0 < 13.5 * 0.5 = 6.75 → Critical
        assert derive_status(2.0, "13.5-17.5") == "Critical"

    def test_critical_very_high(self) -> None:
        # 30000 > 11000 * 2 = 22000 → Critical
        assert derive_status(30000, "4000-11000") == "Critical"

    def test_qualitative_normal(self) -> None:
        assert derive_status("Negative", "Negative") == "Normal"

    def test_qualitative_abnormal(self) -> None:
        assert derive_status("Positive", "Negative") == "Positive"

    def test_none_reference_returns_none(self) -> None:
        assert derive_status(10.0, None) is None


# ------------------------------------------------------------------ #
# Lab extractor
# ------------------------------------------------------------------ #

class TestLabExtractor:
    def test_multiline_format(self) -> None:
        text = (
            "Hemoglobin\n12.4 g/dL\nReference\n13.5-17.5\n\n"
            "WBC\n11200 /uL\nReference\n4000-11000\n"
        )
        tests = extractor.extract(text)
        names = [t.test_name for t in tests]
        assert "Hemoglobin" in names
        assert "WBC Count" in names

    def test_lab_values_extracted(self) -> None:
        text = "Hemoglobin\n12.4 g/dL\nReference\n13.5-17.5\n"
        tests = extractor.extract(text)
        hb = next((t for t in tests if t.test_name == "Hemoglobin"), None)
        assert hb is not None
        assert hb.value == 12.4
        assert hb.unit == "g/dL"

    def test_status_low_detected(self) -> None:
        text = "Hemoglobin\n12.4 g/dL\nReference\n13.5-17.5\n"
        tests = extractor.extract(text)
        hb = next((t for t in tests if t.test_name == "Hemoglobin"), None)
        assert hb is not None
        assert hb.status == "Low"

    def test_status_high_detected(self) -> None:
        text = "WBC\n11200 /uL\nReference\n4000-11000\n"
        tests = extractor.extract(text)
        wbc = next(t for t in tests)
        assert wbc.status == "High"

    def test_inline_format(self) -> None:
        text = "Glucose: 95 mg/dL (70-100)\nCreatinine: 1.2 mg/dL (0.6-1.2)\n"
        tests = extractor.extract(text)
        names = [t.test_name for t in tests]
        assert any("Glucose" in n for n in names)

    def test_no_false_positives_for_headers(self) -> None:
        text = "HAEMATOLOGY\nHemoglobin\n14.5 g/dL\nReference\n13.5-17.5\n"
        tests = extractor.extract(text)
        assert not any(t.test_name.lower() == "haematology" for t in tests)

    def test_empty_text_returns_empty(self) -> None:
        assert extractor.extract("") == []

    def test_reference_range_preserved(self) -> None:
        text = "Hemoglobin\n12.4 g/dL\nReference\n13.5-17.5\n"
        tests = extractor.extract(text)
        hb = tests[0]
        assert hb.reference_range == "13.5-17.5"
