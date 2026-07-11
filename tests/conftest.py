"""
Shared pytest fixtures for Phase 2 tests.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from main import app


# ------------------------------------------------------------------ #
# API client
# ------------------------------------------------------------------ #

@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI test client (session-scoped — created once per test run)."""
    with TestClient(app) as c:
        yield c


# ------------------------------------------------------------------ #
# Sample file content
# ------------------------------------------------------------------ #

@pytest.fixture(scope="session")
def valid_pdf_bytes() -> bytes:
    """
    Minimal valid digital PDF created with PyMuPDF.
    Contains enough text to be recognised as a non-scanned document.
    """
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        (
            "SehatSaathi-AI Test Report\n"
            "Patient: John Doe\n"
            "Hemoglobin: 14.5 g/dL  (Normal: 13.5–17.5)\n"
            "Glucose: 95 mg/dL  (Normal: 70–100)\n"
            "WBC: 7.2 x10^3/uL  (Normal: 4.5–11.0)\n"
        ),
        fontsize=12,
    )
    data = doc.write()
    doc.close()
    return data


@pytest.fixture(scope="session")
def valid_png_bytes() -> bytes:
    """Minimal 200×100 white PNG image."""
    from PIL import Image

    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(scope="session")
def fake_pdf_bytes() -> bytes:
    """PNG bytes renamed to .pdf — should fail magic-byte validation."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), color=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
