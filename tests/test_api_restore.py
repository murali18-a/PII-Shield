"""
PII-Shield — API Restoration Endpoint Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for POST /api/v1/restore.
Uses FastAPI TestClient (httpx).
All test data is synthetic.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestRestoreEndpoint:
    """Test the /api/v1/restore endpoint."""

    def test_restore_returns_501_not_implemented(self):
        """Stub endpoint should return 501 until Phase 1."""
        response = client.post(
            "/api/v1/restore",
            json={
                "text": "Hello <PERSON_1>!",
                "session_id": "test-session-id",
            },
        )
        assert response.status_code == 501

    def test_restore_validates_empty_text(self):
        """Empty text should fail Pydantic validation."""
        response = client.post(
            "/api/v1/restore",
            json={"text": "", "session_id": "test"},
        )
        assert response.status_code == 422

    def test_restore_validates_missing_session_id(self):
        """Missing session_id should fail validation."""
        response = client.post(
            "/api/v1/restore",
            json={"text": "Hello!"},
        )
        assert response.status_code == 422


class TestHealthEndpoint:
    """Test the /api/v1/health endpoint."""

    def test_health_returns_200(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "spacy_model" in data

    def test_health_reports_presidio_not_loaded(self):
        """Before Phase 1, Presidio should report as not loaded."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["presidio_loaded"] is False
