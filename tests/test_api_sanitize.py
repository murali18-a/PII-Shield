"""
PII-Shield — API Sanitize Endpoint Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for POST /api/v1/sanitize.
Uses FastAPI TestClient (httpx).
All test data is synthetic.
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestSanitizeEndpoint:
    """Test the /api/v1/sanitize endpoint."""

    def test_sanitize_detects_and_redacts_pii(self):
        """SSN and email should be redacted in the sanitized text."""
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "My SSN is 123-45-6789 and email is test@example.com."},
        )
        assert response.status_code == 200
        data = response.json()
        assert "123-45-6789" not in data["sanitized_text"]
        assert "test@example.com" not in data["sanitized_text"]
        assert "[US_SSN_1]" in data["sanitized_text"]
        assert data["total_detections"] > 0
        assert data["session_id"] != ""

    def test_sanitize_no_pii(self):
        """Clean text should pass through unchanged."""
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "Python is a popular programming language."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sanitized_text"] == "Python is a popular programming language."
        assert data["total_detections"] == 0

    def test_sanitize_multiple_pii_categories(self):
        """Multiple PII types in one prompt should all be detected."""
        text = (
            "Hi, I'm Jane Doe. Email: jane@example.com, "
            "SSN: 123-45-6789, Phone: (555) 123-4567."
        )
        response = client.post("/api/v1/sanitize", json={"text": text})
        assert response.status_code == 200
        data = response.json()
        categories = data["categories_found"]
        assert "US_SSN" in categories
        assert "EMAIL_ADDRESS" in categories

    def test_sanitize_returns_session_id(self):
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "SSN: 123-45-6789"},
        )
        data = response.json()
        assert data["session_id"] != "no-pii-detected"
        assert len(data["session_id"]) > 0

    def test_sanitize_response_does_not_contain_mapping(self):
        """The response must NEVER contain the placeholder-to-original mapping."""
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "My name is John Smith and SSN is 123-45-6789."},
        )
        data = response.json()
        response_str = str(data)
        # The original values must not appear anywhere in the response
        assert "123-45-6789" not in response_str

    def test_sanitize_validates_empty_text(self):
        response = client.post("/api/v1/sanitize", json={"text": ""})
        assert response.status_code == 422

    def test_sanitize_validates_missing_text(self):
        response = client.post("/api/v1/sanitize", json={})
        assert response.status_code == 422

    def test_sanitize_oversized_input(self):
        """Input exceeding max_length should be rejected."""
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "x" * 50_001},
        )
        assert response.status_code == 422

    def test_sanitize_with_strict_profile(self):
        """Strict profile should block SSN."""
        response = client.post(
            "/api/v1/sanitize",
            json={
                "text": "SSN: 123-45-6789",
                "policy_profile": "strict",
            },
        )
        # Strict blocks SSN, so should get 422
        assert response.status_code == 422
        data = response.json()
        assert "blocked" in str(data["detail"]).lower()

    def test_sanitize_has_disclaimer(self):
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "SSN: 123-45-6789"},
        )
        data = response.json()
        assert "disclaimer" in data
        assert "best-effort" in data["disclaimer"].lower() or "not" in data["disclaimer"].lower()

    def test_sanitize_processing_time_present(self):
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "SSN: 123-45-6789"},
        )
        data = response.json()
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] >= 0

    def test_sanitize_aadhaar(self):
        """Aadhaar-format identifiers should be detected and redacted."""
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "Aadhaar: 2345 6789 0123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "2345 6789 0123" not in data["sanitized_text"]

    def test_sanitize_pan(self):
        """PAN-format identifiers should be detected and redacted."""
        response = client.post(
            "/api/v1/sanitize",
            json={"text": "PAN: ABCPD1234E"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "ABCPD1234E" not in data["sanitized_text"]
