"""
PII-Shield — Detector Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for the detection orchestrator and regex patterns.
All test data is synthetic.
"""

from backend.engine.regex_patterns import scan_with_regex, RegexMatch
from backend.engine.detector import Detector, DetectedEntity


class TestRegexPatterns:
    """Test individual regex pattern detection."""

    def test_detects_ssn(self):
        text = "My SSN is 123-45-6789."
        matches = scan_with_regex(text)
        ssn_matches = [m for m in matches if m.entity_type == "US_SSN"]
        assert len(ssn_matches) == 1
        assert ssn_matches[0].matched_text == "123-45-6789"
        assert ssn_matches[0].score == 1.0

    def test_detects_email(self):
        text = "Contact me at test.user@example.com for details."
        matches = scan_with_regex(text)
        email_matches = [m for m in matches if m.entity_type == "EMAIL_ADDRESS"]
        assert len(email_matches) == 1
        assert email_matches[0].matched_text == "test.user@example.com"

    def test_detects_credit_card_with_luhn(self):
        """Credit cards must pass Luhn validation."""
        text = "Card number: 4111-1111-1111-1111"
        matches = scan_with_regex(text)
        cc_matches = [m for m in matches if m.entity_type == "CREDIT_CARD"]
        assert len(cc_matches) == 1

    def test_rejects_invalid_credit_card(self):
        """A number matching the format but failing Luhn should be excluded."""
        text = "Card number: 4111-1111-1111-1112"
        matches = scan_with_regex(text)
        cc_matches = [m for m in matches if m.entity_type == "CREDIT_CARD"]
        assert len(cc_matches) == 0

    def test_detects_phone_number(self):
        text = "Call me at (555) 123-4567."
        matches = scan_with_regex(text)
        phone_matches = [m for m in matches if m.entity_type == "PHONE_NUMBER"]
        assert len(phone_matches) >= 1

    def test_detects_ip_address(self):
        text = "Server IP: 192.168.1.100"
        matches = scan_with_regex(text)
        ip_matches = [m for m in matches if m.entity_type == "IP_ADDRESS"]
        assert len(ip_matches) == 1
        assert ip_matches[0].matched_text == "192.168.1.100"

    def test_detects_aws_key(self):
        text = "Access key: AKIAIOSFODNN7EXAMPLE"
        matches = scan_with_regex(text)
        aws_matches = [m for m in matches if m.entity_type == "AWS_ACCESS_KEY"]
        assert len(aws_matches) == 1

    def test_detects_aadhaar(self, sample_text_aadhaar_pan):
        matches = scan_with_regex(sample_text_aadhaar_pan)
        aadhaar_matches = [m for m in matches if m.entity_type == "AADHAAR"]
        assert len(aadhaar_matches) >= 1

    def test_detects_pan(self, sample_text_aadhaar_pan):
        matches = scan_with_regex(sample_text_aadhaar_pan)
        pan_matches = [m for m in matches if m.entity_type == "PAN"]
        assert len(pan_matches) == 1
        assert pan_matches[0].matched_text == "ABCPD1234E"

    def test_detects_api_key(self):
        text = 'api_key: "synth_key_abc123def456ghi789jkl012mno"'
        matches = scan_with_regex(text)
        key_matches = [m for m in matches if m.entity_type == "API_KEY"]
        assert len(key_matches) >= 1

    def test_detects_password(self):
        text = 'password = "SuperSecret123!@#"'
        matches = scan_with_regex(text)
        pwd_matches = [m for m in matches if m.entity_type == "PASSWORD"]
        assert len(pwd_matches) >= 1

    def test_no_false_positives_clean_text(self, sample_text_clean):
        matches = scan_with_regex(sample_text_clean)
        # Clean text should have minimal or no high-confidence matches
        high_confidence = [m for m in matches if m.score >= 0.9]
        assert len(high_confidence) == 0

    def test_multiple_entities_in_one_text(self, sample_text_with_pii):
        matches = scan_with_regex(sample_text_with_pii)
        entity_types = {m.entity_type for m in matches}
        # Should detect at least SSN, email, phone, credit card
        assert "US_SSN" in entity_types
        assert "EMAIL_ADDRESS" in entity_types
        assert "PHONE_NUMBER" in entity_types
        assert "CREDIT_CARD" in entity_types

    def test_matches_sorted_by_position(self, sample_text_with_pii):
        matches = scan_with_regex(sample_text_with_pii)
        positions = [m.start for m in matches]
        assert positions == sorted(positions)


class TestDetector:
    """Test the detection orchestrator (regex only, Presidio not loaded)."""

    def test_detect_returns_entities(self, sample_text_with_pii):
        detector = Detector()  # No Presidio
        entities = detector.detect(sample_text_with_pii)
        assert len(entities) > 0
        assert all(isinstance(e, DetectedEntity) for e in entities)

    def test_detect_clean_text_minimal(self, sample_text_clean):
        detector = Detector()
        entities = detector.detect(sample_text_clean)
        high_confidence = [e for e in entities if e.score >= 0.9]
        assert len(high_confidence) == 0

    def test_detect_sources_are_regex(self, sample_text_with_pii):
        detector = Detector()
        entities = detector.detect(sample_text_with_pii)
        # Without Presidio, all sources should be "regex"
        assert all(e.source == "regex" for e in entities)

    def test_detect_empty_text(self):
        detector = Detector()
        entities = detector.detect("")
        assert entities == []

    def test_deduplicate_overlapping_spans(self):
        """Verify that overlapping detections are deduplicated."""
        detector = Detector()
        entities = [
            DetectedEntity("TYPE_A", 0, 10, 0.8, "0123456789", "regex"),
            DetectedEntity("TYPE_B", 5, 15, 0.9, "56789abcde", "presidio"),
        ]
        result = detector._deduplicate(entities)
        # TYPE_B has higher score, should win
        assert len(result) == 1
        assert result[0].entity_type == "TYPE_B"
