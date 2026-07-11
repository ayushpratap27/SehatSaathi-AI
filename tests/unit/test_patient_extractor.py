"""
Unit tests for ai/ner/patient_extractor.py
"""

from __future__ import annotations

from ai.ner.patient_extractor import PatientExtractor

extractor = PatientExtractor()


class TestPatientExtractor:
    def test_extracts_name_from_label(self) -> None:
        text = "Patient Name: John Doe\nAge: 45"
        info = extractor.extract(text)
        assert info.name == "John Doe"

    def test_extracts_age_from_label(self) -> None:
        text = "Age: 45 Years\nGender: Male"
        info = extractor.extract(text)
        assert info.age == 45

    def test_extracts_gender_male(self) -> None:
        text = "Gender: Male\n"
        info = extractor.extract(text)
        assert info.gender == "Male"

    def test_extracts_gender_female(self) -> None:
        text = "Sex: Female"
        info = extractor.extract(text)
        assert info.gender == "Female"

    def test_extracts_gender_shorthand(self) -> None:
        text = "Age/Sex: 30/F"
        info = extractor.extract(text)
        assert info.gender == "Female"
        assert info.age == 30

    def test_age_gender_slash_format(self) -> None:
        text = "Patient: Priya Sharma\nAge/Sex: 28/F"
        info = extractor.extract(text)
        assert info.age == 28
        assert info.gender == "Female"

    def test_returns_none_for_missing_fields(self) -> None:
        info = extractor.extract("Random text with no patient info.")
        assert info.name is None
        assert info.age is None
        assert info.gender is None

    def test_rejects_unreasonable_age(self) -> None:
        text = "Age: 200 Years"
        info = extractor.extract(text)
        assert info.age is None

    def test_extracts_patient_id(self) -> None:
        text = "PID: P123456\nPatient: Raj Kumar"
        info = extractor.extract(text)
        assert info.patient_id == "P123456"

    def test_name_does_not_span_newlines(self) -> None:
        text = "Patient Name: John Doe\nAge: 45"
        info = extractor.extract(text)
        assert "\n" not in (info.name or "")
        assert "Age" not in (info.name or "")

    def test_full_sample(self) -> None:
        text = (
            "Patient Name: John Doe\n"
            "Age: 45 Years\n"
            "Gender: Male\n"
            "Hospital: ABC Hospital\n"
        )
        info = extractor.extract(text)
        assert info.name == "John Doe"
        assert info.age == 45
        assert info.gender == "Male"
