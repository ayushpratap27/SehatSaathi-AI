"""
End-to-end upload + extraction + parse workflow integration tests.
"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch


class TestFullReportWorkflow:
    """Test the complete upload → extract → parse pipeline."""

    def test_health_check_returns_healthy(self, client) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_readiness_probe(self, client) -> None:
        r = client.get("/api/v1/ready")
        # Either ready or DB not yet configured — both are valid in test context
        assert r.status_code in (200, 503)

    def test_upload_extract_parse_pipeline(self, client, valid_pdf_bytes) -> None:
        """Full pipeline: upload → extract text → parse structured JSON."""
        # Step 1: extract text
        r = client.post(
            "/api/v1/report/extract",
            files={"file": ("report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")},
        )
        assert r.status_code == 200
        extracted = r.json()
        assert "text"   in extracted
        assert "pages"  in extracted
        assert extracted["characters"] > 0

        # Step 2: parse (uses extracted text via text form field)
        r2 = client.post(
            "/api/v1/report/parse",
            data={"text": extracted["text"]},
        )
        assert r2.status_code == 200
        parsed = r2.json()
        assert "patient" in parsed
        assert "tests"   in parsed
        assert "diagnosis" in parsed

    def test_analysis_pipeline(self, client, valid_pdf_bytes) -> None:
        """Parse then analyze pipeline."""
        r = client.post(
            "/api/v1/report/parse",
            data={"text": "Patient: John Doe\nAge: 45\nHemoglobin\n12.4 g/dL\nReference\n13.5-17.5"},
        )
        assert r.status_code == 200
        parsed = r.json()

        r2 = client.post("/api/v1/analysis/analyze", json=parsed)
        assert r2.status_code == 200
        analysis = r2.json()
        assert "risk_level"    in analysis
        assert "analysis"      in analysis
        assert "disclaimer"    in analysis
        assert "recommendations" in analysis

    def test_authenticated_report_upload(self, client, valid_pdf_bytes) -> None:
        """Upload via authenticated /reports/upload endpoint."""
        import uuid
        u = uuid.uuid4().hex[:8]
        reg = client.post("/api/v1/auth/register", json={
            "email": f"wftest-{u}@example.com",
            "username": f"wftest{u}",
            "password": "WfTest123!",
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        upload = client.post(
            "/api/v1/reports/upload",
            files={"file": ("report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")},
            headers=headers,
        )
        assert upload.status_code == 201
        data = upload.json()
        assert data["original_filename"] == "report.pdf"
        assert data["status"] == "pending"
        report_id = data["id"]

        # List reports
        listed = client.get("/api/v1/reports", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["total"] >= 1

        # Get single report
        got = client.get(f"/api/v1/reports/{report_id}", headers=headers)
        assert got.status_code == 200

        # Cannot access another user's report (wrong user)
        reg2 = client.post("/api/v1/auth/register", json={
            "email": f"other-{u}@example.com",
            "username": f"other{u}",
            "password": "Other123!",
        })
        token2 = reg2.json()["access_token"]
        forbidden = client.get(f"/api/v1/reports/{report_id}", headers={"Authorization": f"Bearer {token2}"})
        assert forbidden.status_code == 404  # ownership check returns 404

    def test_rag_chat_requires_index(self, client) -> None:
        """RAG chat returns 404 when no index exists for the document."""
        r = client.post("/api/v1/rag/chat", json={
            "question": "What is my Hb?",
            "document_id": "nonexistent-doc-id",
        })
        assert r.status_code == 404
