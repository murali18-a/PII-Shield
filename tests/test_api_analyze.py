"""
PII-Shield — API Analyze Endpoint Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for POST /api/v1/analyze.
All test data is synthetic.
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestAnalyzeEndpoint:
    """Test the /api/v1/analyze endpoint."""

    def test_analyze_returns_detections(self):
        response = client.post(
            "/api/v1/analyze",
            json={"text": "My SSN is 123-45-6789 and email is test@example.com."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_detections"] > 0
        assert "US_SSN" in data["categories_found"]

    def test_analyze_clean_text(self):
        response = client.post(
            "/api/v1/analyze",
            json={"text": "Python is a great programming language for data analysis."},
        )
        assert response.status_code == 200
        data = response.json()
        # Clean text might have zero or very few low-confidence detections
        assert data["total_detections"] == 0 or data["overall_action"] in ("PASS", "WARN")

    def test_analyze_returns_action_per_detection(self):
        response = client.post(
            "/api/v1/analyze",
            json={"text": "SSN: 123-45-6789"},
        )
        data = response.json()
        for det in data["detections"]:
            assert det["action"] in ("REDACT", "WARN", "BLOCK")
            assert det["reason"] != ""

    def test_analyze_has_disclaimer(self):
        response = client.post(
            "/api/v1/analyze",
            json={"text": "SSN: 123-45-6789"},
        )
        data = response.json()
        assert "disclaimer" in data

    def test_analyze_validates_empty_text(self):
        response = client.post("/api/v1/analyze", json={"text": ""})
        assert response.status_code == 422

    def test_analyze_overall_action_block_in_strict(self):
        response = client.post(
            "/api/v1/analyze",
            json={
                "text": "SSN: 123-45-6789",
                "policy_profile": "strict",
            },
        )
        data = response.json()
        assert data["overall_action"] == "BLOCK"
