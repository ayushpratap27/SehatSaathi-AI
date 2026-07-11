"""
Unit tests for ai/ner/medicine_extractor.py
"""

from __future__ import annotations

from ai.ner.medicine_extractor import MedicineExtractor

extractor = MedicineExtractor()


class TestMedicineExtractor:
    def test_extracts_tablet_form(self) -> None:
        text = "Medication\nTab. Amoxicillin 500mg BD x 5 days\n"
        meds = extractor.extract(text)
        assert any("Amoxicillin" in m.name for m in meds)

    def test_extracts_dosage(self) -> None:
        text = "Medication\nTab. Ferrous Sulfate 150mg OD\n"
        meds = extractor.extract(text)
        sulfate = next((m for m in meds if "Ferrous" in m.name), None)
        assert sulfate is not None
        assert sulfate.dosage == "150mg"

    def test_extracts_frequency_od(self) -> None:
        text = "Medicine\nTab. Metformin 500mg OD\n"
        meds = extractor.extract(text)
        met = next((m for m in meds if "Metformin" in m.name), None)
        assert met is not None
        assert met.frequency == "Once daily"

    def test_extracts_frequency_bd(self) -> None:
        text = "Rx\nTab. Amoxicillin 500mg BD\n"
        meds = extractor.extract(text)
        amox = next((m for m in meds if "Amoxicillin" in m.name), None)
        assert amox is not None
        assert amox.frequency == "Twice daily"

    def test_extracts_duration(self) -> None:
        text = "Prescription\nTab. Azithromycin 500mg OD x 3 days\n"
        meds = extractor.extract(text)
        azith = next((m for m in meds if "Azithromycin" in m.name), None)
        assert azith is not None
        assert azith.duration == "3 days"

    def test_empty_text_returns_empty(self) -> None:
        assert extractor.extract("") == []

    def test_deduplicates_medicines(self) -> None:
        text = "Medication\nTab. Metformin 500mg BD\nTab. Metformin 500mg BD\n"
        meds = extractor.extract(text)
        names = [m.name.lower() for m in meds]
        # Should not have duplicates
        assert len(names) == len(set(names))
