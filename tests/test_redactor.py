"""
PII-Shield — Redactor Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for the placeholder generation and redaction engine.
All test data is synthetic.
"""

import re

from backend.engine.detector import DetectedEntity
from backend.engine.redactor import Redactor, RedactionResult


class TestRedactor:
    """Test placeholder generation and text redaction."""

    def test_redact_single_entity(self):
        redactor = Redactor()
        entities = [
            DetectedEntity("US_SSN", 10, 21, 1.0, "123-45-6789", "regex"),
        ]
        text = "My SSN is 123-45-6789 and that's it."
        result = redactor.redact(text, entities)

        assert isinstance(result, RedactionResult)
        assert "[US_SSN_1]" in result.sanitized_text
        assert "123-45-6789" not in result.sanitized_text
        assert result.mapping["[US_SSN_1]"] == "123-45-6789"

    def test_redact_multiple_same_type(self):
        redactor = Redactor()
        entities = [
            DetectedEntity("EMAIL_ADDRESS", 0, 17, 1.0, "alice@example.com", "regex"),
            DetectedEntity("EMAIL_ADDRESS", 21, 36, 1.0, "bob@example.com", "regex"),
        ]
        text = "alice@example.com or bob@example.com for info."
        result = redactor.redact(text, entities)

        assert "[EMAIL_ADDRESS_1]" in result.sanitized_text
        assert "[EMAIL_ADDRESS_2]" in result.sanitized_text
        assert result.mapping["[EMAIL_ADDRESS_1]"] == "alice@example.com"
        assert result.mapping["[EMAIL_ADDRESS_2]"] == "bob@example.com"

    def test_redact_preserves_non_pii_text(self):
        redactor = Redactor()
        entities = [
            DetectedEntity("US_SSN", 5, 16, 1.0, "123-45-6789", "regex"),
        ]
        text = "SSN: 123-45-6789. End."
        result = redactor.redact(text, entities)

        assert result.sanitized_text.startswith("SSN: ")
        assert result.sanitized_text.endswith(". End.")

    def test_redact_empty_entities(self):
        redactor = Redactor()
        text = "No PII here."
        result = redactor.redact(text, [])

        assert result.sanitized_text == text
        assert result.mapping == {}
        assert result.placeholders == []

    def test_redact_mapping_completeness(self, sample_text_with_pii):
        """Every placeholder in the sanitised text should have a mapping entry."""
        from backend.engine.detector import Detector

        detector = Detector()
        entities = detector.detect(sample_text_with_pii)

        redactor = Redactor()
        result = redactor.redact(sample_text_with_pii, entities)

        for info in result.placeholders:
            assert info.placeholder in result.mapping
            assert info.placeholder in result.sanitized_text

    def test_redact_placeholder_format(self):
        """Placeholders should follow [TYPE_N] format."""
        redactor = Redactor()
        entities = [
            DetectedEntity("PERSON", 0, 8, 0.9, "John Doe", "presidio"),
        ]
        result = redactor.redact("John Doe is here.", entities)

        placeholder_re = re.compile(r"\[[A-Z][A-Z0-9_]*_\d+\]")
        for p in result.mapping:
            assert placeholder_re.match(p), f"Placeholder {p} doesn't match [TYPE_N] format"

    def test_redact_repeated_value_reuses_placeholder(self, sample_text_repeated):
        """Same PII value appearing twice should get the same placeholder."""
        from backend.engine.detector import Detector

        detector = Detector()
        entities = detector.detect(sample_text_repeated)

        redactor = Redactor()
        result = redactor.redact(sample_text_repeated, entities)

        email_placeholders = [p for p in result.mapping if "EMAIL" in p]
        # Should only have one unique email placeholder since the value is the same
        assert len(email_placeholders) == 1

    def test_sanitized_output_contains_no_detected_values(self, sample_text_with_pii):
        """Proof that sanitized output does not contain any of the detected values."""
        from backend.engine.detector import Detector

        detector = Detector()
        entities = detector.detect(sample_text_with_pii)
        detected_values = [e.matched_text for e in entities if e.score >= 0.9]

        redactor = Redactor()
        result = redactor.redact(sample_text_with_pii, entities)

        for val in detected_values:
            assert val not in result.sanitized_text, (
                f"Detected value '{val}' still present in sanitized text"
            )
