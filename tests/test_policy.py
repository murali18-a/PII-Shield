"""
PII-Shield — Policy Engine Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for the decision engine (REDACT, WARN, BLOCK).
All test data is synthetic.
"""

from backend.engine.detector import DetectedEntity
from backend.policy.rules import PolicyEngine, Action, PolicyProfile


class TestPolicyEngine:
    """Test policy decision logic."""

    def test_default_redacts_ssn(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("US_SSN", 0, 11, 1.0, "123-45-6789", "regex"),
        ]
        decisions = engine.evaluate("default", entities)
        assert len(decisions) == 1
        assert decisions[0].action == Action.REDACT

    def test_default_warns_date_of_birth(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("DATE_OF_BIRTH", 0, 10, 0.6, "03/14/1985", "regex"),
        ]
        decisions = engine.evaluate("default", entities)
        assert len(decisions) == 1
        assert decisions[0].action == Action.WARN

    def test_strict_blocks_ssn(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("US_SSN", 0, 11, 1.0, "123-45-6789", "regex"),
        ]
        decisions = engine.evaluate("strict", entities)
        assert len(decisions) == 1
        assert decisions[0].action == Action.BLOCK

    def test_strict_blocks_aadhaar(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("AADHAAR", 0, 14, 0.9, "2345 6789 0123", "regex"),
        ]
        decisions = engine.evaluate("strict", entities)
        assert len(decisions) == 1
        assert decisions[0].action == Action.BLOCK

    def test_permissive_skips_location(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("LOCATION", 0, 8, 0.7, "New York", "presidio"),
        ]
        decisions = engine.evaluate("permissive", entities)
        assert len(decisions) == 0  # LOCATION is in never_redact

    def test_permissive_warns_email(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("EMAIL_ADDRESS", 0, 18, 1.0, "test@example.com", "regex"),
        ]
        decisions = engine.evaluate("permissive", entities)
        assert len(decisions) == 1
        assert decisions[0].action == Action.WARN

    def test_default_redacts_aadhaar(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("AADHAAR", 0, 14, 0.9, "2345 6789 0123", "regex"),
        ]
        decisions = engine.evaluate("default", entities)
        assert len(decisions) == 1
        assert decisions[0].action == Action.REDACT

    def test_default_redacts_pan(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("PAN", 0, 10, 0.95, "ABCPD1234E", "regex"),
        ]
        decisions = engine.evaluate("default", entities)
        assert len(decisions) == 1
        assert decisions[0].action == Action.REDACT

    def test_apply_returns_redact_only(self):
        """apply() backward compat: returns only entities to redact."""
        engine = PolicyEngine()
        entities = [
            DetectedEntity("US_SSN", 0, 11, 1.0, "123-45-6789", "regex"),
            DetectedEntity("DATE_OF_BIRTH", 15, 25, 0.6, "03/14/1985", "regex"),
        ]
        filtered = engine.apply("default", entities)
        # SSN should be redacted, DOB should be warned (not in result)
        assert len(filtered) == 1
        assert filtered[0].entity_type == "US_SSN"

    def test_unknown_profile_falls_back_to_default(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("US_SSN", 0, 11, 1.0, "123-45-6789", "regex"),
        ]
        decisions = engine.evaluate("nonexistent_profile", entities)
        assert len(decisions) == 1
        assert decisions[0].action == Action.REDACT

    def test_decision_has_reason(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("US_SSN", 0, 11, 1.0, "123-45-6789", "regex"),
        ]
        decisions = engine.evaluate("default", entities)
        assert decisions[0].reason != ""
        assert "always redacted" in decisions[0].reason.lower() or "default" in decisions[0].reason.lower()

    def test_low_score_below_threshold_ignored(self):
        engine = PolicyEngine()
        entities = [
            DetectedEntity("PHONE_NUMBER", 0, 14, 0.3, "(555) 123-4567", "regex"),
        ]
        # Default min_score is 0.5, so 0.3 should be ignored
        decisions = engine.evaluate("default", entities)
        assert len(decisions) == 0
