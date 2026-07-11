"""
Integration tests for the JSON builder and POST /api/v1/report/parse.
"""

from __future__ import annotations

import io

from ai.ner.json_builder import build_report

# ------------------------------------------------------------------ #
# Shared sample text (Phase 3 spec example)
# ------------------------------------------------------------------ #

SAMPLE_REPORT = """
Patient Name: John Doe
Age: 45 Years
Gender: Male
Hospital: ABC Hospital

Hemoglobin
12.4 g/dL
Reference
13.5-17.5

WBC
11200 /uL
Reference
4000-11000

Diagnosis
Iron Deficiency Anemia

Medicine
Tab. Ferrous Sulfate 150mg OD
"""


class TestJSONBuilder:
    def test_build_report_returns_parsed_report(self) -> None:
        from app.schemas.report import ParsedReport
        report = build_report(SAMPLE_REPORT)
        assert isinstance(report, ParsedReport)

    def test_patient_extracted(self) -> None:
        report = build_report(SAMPLE_REPORT)
        assert report.patient.name == "John Doe"
        assert report.patient.age == 45
        assert report.patient.gender == "Male"

    def test_hospital_extracted(self) -> None:
        report = build_report(SAMPLE_REPORT)
        assert report.hospital.name is not None
        assert "ABC" in (report.hospital.name or "")

    def test_tests_extracted(self) -> None:
        report = build_report(SAMPLE_REPORT)
        assert len(report.tests) >= 2
        names = [t.test_name for t in report.tests]
        assert any("Hemoglobin" in n for n in names)
        assert any("WBC" in n for n in names)

    def test_hb_status_low(self) -> None:
        report = build_report(SAMPLE_REPORT)
        hb = next((t for t in report.tests if "Hemoglobin" in t.test_name), None)
        assert hb is not None
        assert hb.status == "Low"

    def test_wbc_status_high(self) -> None:
        report = build_report(SAMPLE_REPORT)
        wbc = next((t for t in report.tests if "WBC" in t.test_name), None)
        assert wbc is not None
        assert wbc.status == "High"

    def test_diagnosis_extracted(self) -> None:
        report = build_report(SAMPLE_REPORT)
        assert len(report.diagnosis) >= 1
        assert any("Anemia" in d for d in report.diagnosis)

    def test_medicine_extracted(self) -> None:
        report = build_report(SAMPLE_REPORT)
        assert len(report.medicines) >= 1
        assert any("Ferrous" in m.name for m in report.medicines)

    def test_medicine_dosage_and_frequency(self) -> None:
        report = build_report(SAMPLE_REPORT)
        ferrous = next((m for m in report.medicines if "Ferrous" in m.name), None)
        assert ferrous is not None
        assert ferrous.dosage == "150mg"
        assert ferrous.frequency == "Once daily"


class TestParseEndpoint:
    def test_parse_with_text_input(self, client) -> None:
        r = client.post("/api/v1/report/parse", data={"text": SAMPLE_REPORT})
        assert r.status_code == 200
        data = r.json()
        assert "patient" in data
        assert "tests" in data
        assert "diagnosis" in data
        assert "medicines" in data

    def test_parse_with_pdf_file(self, client, valid_pdf_bytes) -> None:
        r = client.post(
            "/api/v1/report/parse",
            files={"file": ("report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")},
        )
        assert r.status_code == 200

    def test_parse_returns_structured_json(self, client) -> None:
        r = client.post("/api/v1/report/parse", data={"text": SAMPLE_REPORT})
        data = r.json()
        # Patient fields
        assert "name" in data["patient"]
        assert "age" in data["patient"]
        # Test object shape
        if data["tests"]:
            t = data["tests"][0]
            assert "test_name" in t
            assert "value" in t
            assert "status" in t

    def test_parse_no_input_returns_400(self, client) -> None:
        r = client.post("/api/v1/report/parse")
        assert r.status_code == 400

    def test_parse_unsupported_file_returns_415(self, client) -> None:
        r = client.post(
            "/api/v1/report/parse",
            files={"file": ("notes.txt", io.BytesIO(b"some text"), "text/plain")},
        )
        assert r.status_code == 415
