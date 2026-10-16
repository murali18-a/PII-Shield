"""
PII-Shield — API Redaction Endpoint Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for POST /api/v1/redact.
Uses FastAPI TestClient (httpx).
All test data is synthetic.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestRedactEndpoint:
    """Test the /api/v1/redact endpoint."""

    def test_redact_returns_501_not_implemented(self):
        """Stub endpoint should return 501 until Phase 1."""
        response = client.post(
            "/api/v1/redact",
            json={"text": "My name is John and my SSN is 123-45-6789."},
        )
        assert response.status_code == 501

    def test_redact_validates_empty_text(self):
        """Empty text should fail Pydantic validation."""
        response = client.post(
            "/api/v1/redact",
            json={"text": ""},
        )
        assert response.status_code == 422  # Validation error

    def test_redact_validates_missing_text(self):
        """Missing text field should fail validation."""
        response = client.post(
            "/api/v1/redact",
            json={},
        )
        assert response.status_code == 422

    def test_redact_accepts_policy_profile(self):
        """Request with policy_profile should be accepted (still 501)."""
        response = client.post(
            "/api/v1/redact",
            json={"text": "Test text.", "policy_profile": "strict"},
        )
        assert response.status_code == 501
