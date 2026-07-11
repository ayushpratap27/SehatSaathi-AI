"""
API integration tests for POST /api/v1/report/extract

PaddleOCR is mocked to avoid downloading models during CI.
Digital PDF extraction uses the real PyMuPDF pipeline.
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch


class TestExtractEndpoint:
    # ------------------------------------------------------------------ #
    # Digital PDF — real pipeline (no OCR needed)
    # ------------------------------------------------------------------ #

    def test_extract_digital_pdf_returns_200(self, client, valid_pdf_bytes) -> None:
        response = client.post(
            "/api/v1/report/extract",
            files={"file": ("report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 200

    def test_extract_digital_pdf_response_fields(self, client, valid_pdf_bytes) -> None:
        response = client.post(
            "/api/v1/report/extract",
            files={"file": ("report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")},
        )
        data = response.json()
        assert data["filename"] == "report.pdf"
        assert data["pages"] == 1
        assert data["is_scanned"] is False
        assert isinstance(data["text"], str)
        assert data["characters"] > 0
        assert data["words"] > 0
        assert data["extraction_method"] in ("pymupdf", "pdfplumber")

    def test_extract_digital_pdf_text_contains_content(
        self, client, valid_pdf_bytes
    ) -> None:
        response = client.post(
            "/api/v1/report/extract",
            files={"file": ("report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")},
        )
        text = response.json()["text"]
        # The valid_pdf_bytes fixture includes these terms
        assert "Hemoglobin" in text or "Patient" in text

    # ------------------------------------------------------------------ #
    # Scanned PDF — OCR mocked
    # ------------------------------------------------------------------ #

    def test_extract_scanned_pdf_uses_ocr(self, client, tmp_path) -> None:
        """A blank PDF (no text) should trigger the OCR path."""
        import fitz

        doc = fitz.open()
        doc.new_page()  # blank → scanned
        blank_pdf = doc.write()
        doc.close()

        mock_engine = MagicMock()
        mock_engine.extract_from_pdf.return_value = {
            "text": "Mocked OCR output from scanned report",
            "pages": 1,
        }

        with patch(
            "ai.ocr.ocr_engine.OCREngine.get_instance",
            return_value=mock_engine,
        ):
            response = client.post(
                "/api/v1/report/extract",
                files={"file": ("scan.pdf", io.BytesIO(blank_pdf), "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_scanned"] is True
        assert data["extraction_method"] == "paddleocr"
        assert "Mocked OCR output" in data["text"]

    # ------------------------------------------------------------------ #
    # Image file — OCR mocked
    # ------------------------------------------------------------------ #

    def test_extract_image_uses_ocr(self, client, valid_png_bytes) -> None:
        mock_engine = MagicMock()
        mock_engine.extract_from_image_path.return_value = (
            "Blood Glucose: 95 mg/dL  Normal"
        )

        with patch(
            "ai.ocr.ocr_engine.OCREngine.get_instance",
            return_value=mock_engine,
        ):
            response = client.post(
                "/api/v1/report/extract",
                files={"file": ("scan.png", io.BytesIO(valid_png_bytes), "image/png")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["pages"] == 1
        assert data["is_scanned"] is True
        assert data["extraction_method"] == "paddleocr"

    # ------------------------------------------------------------------ #
    # Validation errors
    # ------------------------------------------------------------------ #

    def test_unsupported_file_type_returns_415(self, client) -> None:
        response = client.post(
            "/api/v1/report/extract",
            files={"file": ("notes.txt", io.BytesIO(b"text"), "text/plain")},
        )
        assert response.status_code == 415

    def test_empty_file_returns_400(self, client) -> None:
        response = client.post(
            "/api/v1/report/extract",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert response.status_code == 400
