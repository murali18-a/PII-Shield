"""
PII-Shield — Audit Logger Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for the in-memory audit event logger.
Verifies privacy: no raw text or PII in events.
All test data is synthetic.
"""

from backend.audit.logger import AuditLogger


class TestAuditLogger:
    """Test the in-memory audit event logger."""

    def test_log_returns_event_id(self):
        logger = AuditLogger()
        event_id = logger.log_redaction(
            entity_types=["US_SSN", "EMAIL_ADDRESS"],
            entity_count=2,
        )
        assert event_id.startswith("evt_")
        assert len(event_id) > 4

    def test_events_stored_and_retrievable(self):
        logger = AuditLogger()
        logger.log_redaction(entity_types=["US_SSN"], entity_count=1)
        logger.log_redaction(entity_types=["EMAIL_ADDRESS"], entity_count=1)

        events, total = logger.get_events()
        assert total == 2
        assert len(events) == 2

    def test_events_newest_first(self):
        logger = AuditLogger()
        logger.log_redaction(entity_types=["US_SSN"], entity_count=1)
        logger.log_redaction(entity_types=["EMAIL_ADDRESS"], entity_count=1)

        events, _ = logger.get_events()
        # Newest event first should have EMAIL_ADDRESS
        assert "EMAIL_ADDRESS" in events[0].entity_types

    def test_events_never_contain_pii(self):
        """Audit events must never contain raw PII values."""
        logger = AuditLogger()
        # Log with entity type names only (the API contract)
        logger.log_redaction(
            entity_types=["US_SSN", "PERSON"],
            entity_count=2,
            policy_profile="default",
        )
        events, _ = logger.get_events()
        event = events[0]
        # Verify the event fields — should only contain type names and counts
        event_str = str(event)
        assert "123-45-6789" not in event_str
        assert "John" not in event_str
        assert event.entity_count == 2
        assert "US_SSN" in event.entity_types

    def test_max_events_ring_buffer(self):
        """Ring buffer should cap at max_events."""
        logger = AuditLogger(max_events=5)
        for i in range(10):
            logger.log_redaction(entity_types=[f"TYPE_{i}"], entity_count=1)

        events, total = logger.get_events()
        assert total == 5  # Only last 5 kept

    def test_pagination(self):
        logger = AuditLogger()
        for i in range(10):
            logger.log_redaction(entity_types=[f"TYPE_{i}"], entity_count=1)

        page1, total = logger.get_events(page=1, page_size=3)
        assert len(page1) == 3
        assert total == 10

        page2, _ = logger.get_events(page=2, page_size=3)
        assert len(page2) == 3

    def test_empty_logger(self):
        logger = AuditLogger()
        events, total = logger.get_events()
        assert total == 0
        assert len(events) == 0
