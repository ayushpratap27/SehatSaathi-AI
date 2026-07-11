"""
API integration tests for POST /api/v1/upload/

Uses FastAPI TestClient with in-memory file fixtures.
PaddleOCR is NOT invoked — these tests only cover upload + validation.
"""

from __future__ import annotations

import io


# ------------------------------------------------------------------ #
# Happy path
# ------------------------------------------------------------------ #

class TestUploadEndpoint:
    def test_upload_valid_pdf_returns_200(self, client, valid_pdf_bytes) -> None:
        response = client.post(
            "/api/v1/upload/",
            files={"file": ("report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original_filename"] == "report.pdf"
        assert data["status"] == "uploaded"
        assert data["file_size"] > 0
        assert data["saved_filename"].endswith(".pdf")

    def test_upload_valid_png_returns_200(self, client, valid_png_bytes) -> None:
        response = client.post(
            "/api/v1/upload/",
            files={"file": ("scan.png", io.BytesIO(valid_png_bytes), "image/png")},
        )
        assert response.status_code == 200
        assert response.json()["saved_filename"].endswith(".png")

    def test_upload_response_has_timestamp(self, client, valid_pdf_bytes) -> None:
        response = client.post(
            "/api/v1/upload/",
            files={"file": ("r.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")},
        )
        assert "upload_timestamp" in response.json()

    # ------------------------------------------------------------------ #
    # Validation errors
    # ------------------------------------------------------------------ #

    def test_unsupported_extension_returns_415(self, client) -> None:
        response = client.post(
            "/api/v1/upload/",
            files={"file": ("report.docx", io.BytesIO(b"data"), "application/octet-stream")},
        )
        assert response.status_code == 415

    def test_empty_file_returns_400(self, client) -> None:
        response = client.post(
            "/api/v1/upload/",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert response.status_code == 400

    def test_corrupted_pdf_magic_bytes_returns_400(self, client, fake_pdf_bytes) -> None:
        """PNG bytes submitted with a .pdf extension should be rejected."""
        response = client.post(
            "/api/v1/upload/",
            files={"file": ("fake.pdf", io.BytesIO(fake_pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 400

    def test_oversized_file_returns_413(self, client) -> None:
        # Generate content just over 20 MB
        big_content = b"%PDF-" + b"x" * (21 * 1024 * 1024)
        response = client.post(
            "/api/v1/upload/",
            files={"file": ("big.pdf", io.BytesIO(big_content), "application/pdf")},
        )
        assert response.status_code == 413
