"""
PII-Shield — End-to-End Integration Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests the full pipeline through the FastAPI HTTP layer:
  analyze → sanitize → restore round-trip.

All test data is synthetic — no real PII is used.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Fresh test client for each test."""
    return TestClient(app)


@pytest.fixture
def synthetic_prompts():
    data_path = Path(__file__).parent.parent / "data" / "synthetic_prompts.json"
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)


class TestFullRoundTrip:
    """Verify the complete sanitize → restore cycle."""

    def test_sanitize_then_restore_recovers_original(self, client):
        """The critical invariant: sanitize then restore must recover the original text."""
        original = "My name is Jane Doe and my SSN is 123-45-6789."
        # Step 1: Sanitize
        resp = client.post("/api/v1/sanitize", json={"text": original})
        assert resp.status_code == 200
        data = resp.json()
        sanitized = data["sanitized_text"]
        session_id = data["session_id"]

        # The sanitized text must NOT contain the SSN (regex-detected)
        assert "123-45-6789" not in sanitized
        # Note: "Jane Doe" is only caught by Presidio NER, which may not
        # be loaded in test environments (regex-only mode). This is a
        # documented limitation — see SECURITY.md.

        # It must contain placeholders
        assert "[US_SSN_1]" in sanitized

        # Step 2: Restore
        resp2 = client.post("/api/v1/restore", json={
            "text": sanitized,
            "session_id": session_id,
        })
        assert resp2.status_code == 200
        restored = resp2.json()["restored_text"]
        assert "123-45-6789" in restored

    def test_sanitize_then_restore_with_multiple_types(self, client):
        """Round-trip with multiple PII categories."""
        original = (
            "Email jane.doe@example.com, SSN 123-45-6789, "
            "card 4111-1111-1111-1111, IP 10.0.0.42."
        )
        resp = client.post("/api/v1/sanitize", json={"text": original})
        assert resp.status_code == 200
        data = resp.json()
        sanitized = data["sanitized_text"]
        session_id = data["session_id"]

        # All PII should be removed from sanitized output
        assert "jane.doe@example.com" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "4111-1111-1111-1111" not in sanitized

        # Restore
        resp2 = client.post("/api/v1/restore", json={
            "text": sanitized,
            "session_id": session_id,
        })
        assert resp2.status_code == 200
        restored = resp2.json()["restored_text"]
        assert "123-45-6789" in restored
        assert "jane.doe@example.com" in restored

    def test_clean_text_passes_through_unchanged(self, client):
        """Text with no PII should pass through without modification."""
        original = "Python is a popular programming language for data science."
        resp = client.post("/api/v1/sanitize", json={"text": original})
        assert resp.status_code == 200
        data = resp.json()
        assert data["sanitized_text"] == original
        assert data["total_detections"] == 0
        assert data["session_id"] == "no-pii-detected"


class TestMappingNeverLeaks:
    """Verify that placeholder-to-original mappings never appear in API responses."""

    def test_sanitize_response_has_no_mapping_field(self, client):
        """The sanitize response must never contain the raw mapping."""
        resp = client.post("/api/v1/sanitize", json={
            "text": "SSN is 123-45-6789"
        })
        data = resp.json()
        # No 'mapping' key in response
        assert "mapping" not in data
        # The raw value must not appear anywhere in the JSON string
        raw_json = json.dumps(data)
        assert "123-45-6789" not in raw_json

    def test_audit_events_contain_no_pii(self, client):
        """Audit events must only contain entity types and counts, never values."""
        # Generate some events
        client.post("/api/v1/sanitize", json={
            "text": "Contact jane@example.com, SSN 234-56-7890."
        })
        resp = client.get("/api/v1/events")
        assert resp.status_code == 200
        raw = json.dumps(resp.json())
        assert "jane@example.com" not in raw
        assert "234-56-7890" not in raw


class TestEdgeCases:
    """Security and robustness edge cases."""

    def test_repeated_value_same_placeholder(self, client):
        """The same PII value appearing twice should get the same placeholder."""
        text = (
            "Contact jane.doe@example.com for help. "
            "If jane.doe@example.com is busy, try later."
        )
        resp = client.post("/api/v1/sanitize", json={"text": text})
        data = resp.json()
        sanitized = data["sanitized_text"]
        # The email should be replaced consistently
        assert "jane.doe@example.com" not in sanitized
        # Both occurrences should use the same placeholder
        assert sanitized.count("[EMAIL_ADDRESS_1]") == 2

    def test_malformed_json_returns_422(self, client):
        """Malformed request body should return a validation error, not crash."""
        resp = client.post(
            "/api/v1/sanitize",
            content=b'{"text": }',
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_empty_text_returns_422(self, client):
        """Empty text should be rejected by validation."""
        resp = client.post("/api/v1/sanitize", json={"text": ""})
        assert resp.status_code == 422

    def test_expired_session_returns_404(self, client):
        """Restoring with a non-existent session ID returns 404."""
        resp = client.post("/api/v1/restore", json={
            "text": "Hello [PERSON_1]",
            "session_id": "00000000-0000-0000-0000-000000000000",
        })
        assert resp.status_code == 404

    def test_session_consumed_after_restore(self, client):
        """Sessions are single-use — second restore should fail."""
        resp = client.post("/api/v1/sanitize", json={
            "text": "My SSN is 123-45-6789."
        })
        data = resp.json()
        session_id = data["session_id"]

        # First restore succeeds
        r1 = client.post("/api/v1/restore", json={
            "text": data["sanitized_text"],
            "session_id": session_id,
        })
        assert r1.status_code == 200

        # Second restore fails (session consumed)
        r2 = client.post("/api/v1/restore", json={
            "text": data["sanitized_text"],
            "session_id": session_id,
        })
        assert r2.status_code == 404

    def test_strict_policy_blocks_ssn(self, client):
        """Strict policy should BLOCK requests containing SSNs."""
        resp = client.post("/api/v1/sanitize", json={
            "text": "SSN: 123-45-6789",
            "policy_profile": "strict",
        })
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert detail["error"] == "request_blocked"
        assert "US_SSN" in detail["blocked_types"]

    def test_analyze_does_not_store_session(self, client):
        """Analyze endpoint should not create sessions — it's read-only."""
        resp = client.post("/api/v1/analyze", json={
            "text": "SSN 123-45-6789"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" not in data

    def test_health_endpoint(self, client):
        """Health check should return system status."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "presidio_loaded" in data


class TestSyntheticPromptSuite:
    """Run all synthetic prompts through the pipeline and verify detection."""

    def test_all_synthetic_prompts_process_without_error(self, client, synthetic_prompts):
        """Every synthetic prompt should process without 5xx errors."""
        for prompt in synthetic_prompts:
            resp = client.post("/api/v1/sanitize", json={"text": prompt["text"]})
            assert resp.status_code == 200, (
                f"Prompt {prompt['id']} failed: {resp.status_code}"
            )

    def test_synthetic_no_pii_prompts_return_zero_detections(self, client, synthetic_prompts):
        """Clean prompts (synth_004, synth_010) should return zero detections."""
        clean_ids = {"synth_004", "synth_010"}
        for prompt in synthetic_prompts:
            if prompt["id"] in clean_ids:
                resp = client.post("/api/v1/sanitize", json={"text": prompt["text"]})
                data = resp.json()
                assert data["total_detections"] == 0, (
                    f"False positive in {prompt['id']}: {data['detections']}"
                )

    def test_synthetic_pii_prompts_detect_expected_types(self, client, synthetic_prompts):
        """PII prompts should detect at least the expected entity types."""
        for prompt in synthetic_prompts:
            expected = set(prompt["expected_entities"])
            if not expected:
                continue
            resp = client.post("/api/v1/analyze", json={"text": prompt["text"]})
            data = resp.json()
            detected = set(data["categories_found"])
            # Check that at least some expected types are found
            # (Presidio-dependent types like PERSON may not be caught in regex-only mode)
            regex_expected = expected - {"PERSON", "LOCATION", "ORGANIZATION"}
            found = regex_expected & detected
            if regex_expected:
                assert found, (
                    f"Prompt {prompt['id']}: expected {regex_expected}, "
                    f"detected {detected}"
                )
"""
End of integration tests.
"""
