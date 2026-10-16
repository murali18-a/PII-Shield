"""
PII-Shield — API Redaction & Restoration Endpoint Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for POST /api/v1/redact, POST /api/v1/restore,
GET /api/v1/health, and GET /api/v1/events.
All test data is synthetic.
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestRedactEndpoint:
    """Test the /api/v1/redact endpoint (now working, no longer 501)."""

    def test_redact_returns_200(self):
        response = client.post(
            "/api/v1/redact",
            json={"text": "My name is John and my SSN is 123-45-6789."},
        )
        assert response.status_code == 200

    def test_redact_sanitizes_ssn(self):
        response = client.post(
            "/api/v1/redact",
            json={"text": "SSN: 123-45-6789"},
        )
        data = response.json()
        assert "123-45-6789" not in data["sanitized_text"]
        assert data["stats"]["total_entities"] > 0

    def test_redact_validates_empty_text(self):
        response = client.post("/api/v1/redact", json={"text": ""})
        assert response.status_code == 422

    def test_redact_validates_missing_text(self):
        response = client.post("/api/v1/redact", json={})
        assert response.status_code == 422

    def test_redact_accepts_policy_profile(self):
        response = client.post(
            "/api/v1/redact",
            json={"text": "Email: test@example.com", "policy_profile": "default"},
        )
        assert response.status_code == 200


class TestRestoreEndpoint:
    """Test the /api/v1/restore endpoint (now working)."""

    def test_restore_round_trip(self):
        """Redact then restore should recover original text."""
        original = "My SSN is 123-45-6789."
        # Step 1: Redact
        redact_resp = client.post("/api/v1/redact", json={"text": original})
        assert redact_resp.status_code == 200
        redact_data = redact_resp.json()
        session_id = redact_data["session_id"]
        sanitized = redact_data["sanitized_text"]
        assert "123-45-6789" not in sanitized

        # Step 2: Restore
        restore_resp = client.post(
            "/api/v1/restore",
            json={"text": sanitized, "session_id": session_id},
        )
        assert restore_resp.status_code == 200
        restore_data = restore_resp.json()
        assert restore_data["restored_text"] == original
        assert restore_data["placeholders_restored"] > 0

    def test_restore_invalid_session_returns_404(self):
        response = client.post(
            "/api/v1/restore",
            json={"text": "[PERSON_1]", "session_id": "nonexistent-session-id"},
        )
        assert response.status_code == 404

    def test_restore_validates_empty_text(self):
        response = client.post(
            "/api/v1/restore",
            json={"text": "", "session_id": "test"},
        )
        assert response.status_code == 422

    def test_restore_validates_missing_session_id(self):
        response = client.post("/api/v1/restore", json={"text": "Hello!"})
        assert response.status_code == 422

    def test_restore_consumes_session(self):
        """Session should be deleted after restoration (one-time use)."""
        original = "SSN: 123-45-6789"
        redact_resp = client.post("/api/v1/redact", json={"text": original})
        session_id = redact_resp.json()["session_id"]
        sanitized = redact_resp.json()["sanitized_text"]

        # First restore should succeed
        resp1 = client.post(
            "/api/v1/restore",
            json={"text": sanitized, "session_id": session_id},
        )
        assert resp1.status_code == 200

        # Second restore should fail (session consumed)
        resp2 = client.post(
            "/api/v1/restore",
            json={"text": sanitized, "session_id": session_id},
        )
        assert resp2.status_code == 404


class TestHealthEndpoint:
    """Test the /api/v1/health and /health endpoints."""

    def test_v1_health_returns_200(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "spacy_model" in data
        assert "presidio_loaded" in data

    def test_root_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestEventsEndpoint:
    """Test the /api/v1/events endpoint."""

    def test_events_returns_200(self):
        response = client.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total_events" in data

    def test_events_after_sanitize(self):
        """After a sanitize request, an audit event should be recorded."""
        # Trigger a sanitize with PII
        client.post("/api/v1/sanitize", json={"text": "SSN: 123-45-6789"})
        response = client.get("/api/v1/events")
        data = response.json()
        assert data["total_events"] > 0
        # Check that the event contains entity types but no PII
        event = data["events"][0]
        assert "entity_types" in event
        assert "entity_count" in event
        event_str = str(event)
        assert "123-45-6789" not in event_str  # No PII in audit logs

    def test_events_pagination(self):
        response = client.get("/api/v1/events?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
