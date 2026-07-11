"""
Unit tests for ai/ner/diagnosis_extractor.py
"""

from __future__ import annotations

from ai.ner.diagnosis_extractor import DiagnosisExtractor

extractor = DiagnosisExtractor()


class TestDiagnosisExtractor:
    def test_extracts_from_diagnosis_section(self) -> None:
        text = "Diagnosis\nIron Deficiency Anemia\n"
        results = extractor.extract(text)
        assert any("Iron Deficiency Anemia" in d for d in results)

    def test_extracts_from_inline_label(self) -> None:
        text = "Diagnosis: Type 2 Diabetes Mellitus\n"
        results = extractor.extract(text)
        assert any("Diabetes" in d for d in results)

    def test_extracts_from_impression_section(self) -> None:
        text = "Impression\nHypothyroidism\n"
        results = extractor.extract(text)
        assert any("Hypothyroidism" in d for d in results)

    def test_extracts_clinical_diagnosis(self) -> None:
        text = "Clinical Diagnosis: Hypertension Stage II\n"
        results = extractor.extract(text)
        assert any("Hypertension" in d for d in results)

    def test_fallback_keyword_detection(self) -> None:
        # No section headers — uses keyword fallback
        text = "Patient presented with symptoms of Iron Deficiency Anemia."
        results = extractor.extract(text)
        assert any("Anemia" in d for d in results)

    def test_empty_text_returns_empty(self) -> None:
        assert extractor.extract("") == []

    def test_deduplicates(self) -> None:
        text = (
            "Diagnosis\n"
            "Iron Deficiency Anemia\n"
            "Iron Deficiency Anemia\n"
        )
        results = extractor.extract(text)
        count = sum(1 for d in results if "Iron Deficiency Anemia" in d)
        assert count == 1

    def test_does_not_include_lab_result_lines(self) -> None:
        text = (
            "Hemoglobin: 12.4 g/dL (reference 13.5-17.5)\n"
            "Diagnosis\nIron Deficiency Anemia\n"
        )
        results = extractor.extract(text)
        assert not any("g/dL" in d for d in results)
