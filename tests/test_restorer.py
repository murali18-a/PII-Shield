"""
PII-Shield — Restorer Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for the placeholder restoration engine.
All test data is synthetic.
"""

from backend.engine.restorer import Restorer, RestorationResult


class TestRestorer:
    """Test placeholder-to-original restoration."""

    def test_restore_single_placeholder(self):
        restorer = Restorer()
        mapping = {"[PERSON_1]": "Jane Doe"}
        text = "Hello, [PERSON_1]!"
        result = restorer.restore(text, mapping)

        assert isinstance(result, RestorationResult)
        assert result.restored_text == "Hello, Jane Doe!"
        assert result.placeholders_restored == 1

    def test_restore_multiple_placeholders(self):
        restorer = Restorer()
        mapping = {
            "[PERSON_1]": "Jane Doe",
            "[US_SSN_1]": "123-45-6789",
            "[EMAIL_ADDRESS_1]": "jane@example.com",
        }
        text = "[PERSON_1]'s SSN is [US_SSN_1]. Email: [EMAIL_ADDRESS_1]."
        result = restorer.restore(text, mapping)

        assert "Jane Doe" in result.restored_text
        assert "123-45-6789" in result.restored_text
        assert "jane@example.com" in result.restored_text
        assert result.placeholders_restored == 3

    def test_restore_repeated_placeholder(self):
        """Same placeholder appearing multiple times in response."""
        restorer = Restorer()
        mapping = {"[PERSON_1]": "Jane Doe"}
        text = "[PERSON_1] said hello. Later, [PERSON_1] left."
        result = restorer.restore(text, mapping)

        assert result.restored_text == "Jane Doe said hello. Later, Jane Doe left."
        assert result.placeholders_restored == 2

    def test_restore_empty_mapping(self):
        restorer = Restorer()
        text = "No placeholders here."
        result = restorer.restore(text, {})

        assert result.restored_text == text
        assert result.placeholders_restored == 0

    def test_restore_missing_placeholder_in_text(self):
        """Mapping has entries but none appear in the text."""
        restorer = Restorer()
        mapping = {"[PERSON_1]": "Jane Doe"}
        text = "No matching placeholders."
        result = restorer.restore(text, mapping)

        assert result.restored_text == text
        assert result.placeholders_restored == 0

    def test_full_round_trip(self, sample_text_with_pii):
        """Full pipeline: detect → redact → restore should recover original text."""
        from backend.engine.detector import Detector
        from backend.engine.redactor import Redactor

        detector = Detector()
        redactor = Redactor()
        restorer = Restorer()

        # Detect
        entities = detector.detect(sample_text_with_pii)

        # Redact
        redaction = redactor.redact(sample_text_with_pii, entities)
        assert redaction.sanitized_text != sample_text_with_pii

        # Restore
        restoration = restorer.restore(redaction.sanitized_text, redaction.mapping)
        assert restoration.restored_text == sample_text_with_pii
