"""
PII-Shield — Audit Logger
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Writes privacy-safe audit events to an in-memory store.

SECURITY INVARIANT: This module must NEVER receive or log:
- Raw input text or prompts
- Original PII values
- Placeholder-to-original mappings
- Session tokens that could be correlated to specific text

It receives ONLY: entity types (strings), counts (integers),
policy profiles (strings), and action labels (strings).
"""

from __future__ import annotations

import uuid
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from dataclasses import dataclass, field


@dataclass
class AuditRecord:
    """A single privacy-safe audit event."""

    event_id: str
    timestamp: str
    entity_types: list[str]
    entity_count: int
    policy_profile: str
    action: str


class AuditLogger:
    """
    Privacy-safe audit event writer with in-memory ring buffer.

    Events are stored in a bounded deque to prevent unbounded memory growth.
    No PII, raw text, or mappings are ever stored.

    Usage:
        logger = AuditLogger(max_events=10_000)
        event_id = logger.log_redaction(
            entity_types=["PERSON", "US_SSN"],
            entity_count=3,
            policy_profile="default",
            action="REDACT",
        )
        events = logger.get_events(page=1, page_size=20)
    """

    def __init__(self, max_events: int = 10_000):
        self._events: deque[AuditRecord] = deque(maxlen=max_events)
        self._lock = Lock()

    def log_redaction(
        self,
        entity_types: list[str],
        entity_count: int,
        policy_profile: str = "default",
        action: str = "REDACT",
    ) -> str:
        """
        Record a redaction event.

        Args:
            entity_types: List of entity type strings detected.
            entity_count: Total number of entities redacted.
            policy_profile: Policy profile that was applied.
            action: Policy action taken (REDACT, WARN, BLOCK).

        Returns:
            The generated event ID.
        """
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        record = AuditRecord(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            entity_types=list(set(entity_types)),  # Deduplicate
            entity_count=entity_count,
            policy_profile=policy_profile,
            action=action,
        )

        with self._lock:
            self._events.append(record)

        return event_id

    def get_events(self, page: int = 1, page_size: int = 20) -> tuple[list[AuditRecord], int]:
        """
        Return paginated audit events (newest first).

        Args:
            page: 1-indexed page number.
            page_size: Number of events per page.

        Returns:
            Tuple of (events_list, total_events_count).
        """
        with self._lock:
            all_events = list(reversed(self._events))  # Newest first
            total = len(all_events)

        start = (page - 1) * page_size
        end = start + page_size
        return all_events[start:end], total

    @property
    def total_events(self) -> int:
        """Total number of stored audit events."""
        with self._lock:
            return len(self._events)
