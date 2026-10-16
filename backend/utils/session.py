"""
PII-Shield — Session Store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In-memory session store for placeholder-to-original mappings.

SECURITY INVARIANT:
- Mappings exist ONLY in memory — never written to disk, database, or logs.
- Each session is identified by a cryptographically random UUID.
- Sessions auto-expire after a configurable TTL.
- No external system can query or enumerate active sessions.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Session:
    """A single session holding placeholder mappings."""

    session_id: str
    mapping: dict[str, str]  # placeholder → original value
    created_at: float = field(default_factory=time.time)

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if this session has exceeded its TTL."""
        return (time.time() - self.created_at) > ttl_seconds


class SessionStore:
    """
    Thread-safe in-memory session store with TTL-based expiry.

    Usage:
        store = SessionStore(ttl_seconds=3600)
        sid = store.create({"<PERSON_1>": "John Smith"})
        mapping = store.get(sid)
        store.delete(sid)
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def create(self, mapping: dict[str, str]) -> str:
        """
        Create a new session with the given placeholder mapping.

        Args:
            mapping: Dict of placeholder → original value.

        Returns:
            A new cryptographically random session ID.
        """
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id, mapping=mapping)

        with self._lock:
            self._cleanup_expired()
            self._sessions[session_id] = session

        return session_id

    def get(self, session_id: str) -> dict[str, str] | None:
        """
        Retrieve the mapping for a session.

        Args:
            session_id: The session ID to look up.

        Returns:
            The placeholder mapping, or None if not found or expired.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.is_expired(self.ttl_seconds):
                del self._sessions[session_id]
                return None
            return session.mapping

    def delete(self, session_id: str) -> bool:
        """
        Delete a session (e.g. after restoration).

        Returns:
            True if the session existed and was deleted.
        """
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def _cleanup_expired(self) -> None:
        """Remove all expired sessions. Called internally under lock."""
        expired = [
            sid
            for sid, session in self._sessions.items()
            if session.is_expired(self.ttl_seconds)
        ]
        for sid in expired:
            del self._sessions[sid]

    @property
    def active_count(self) -> int:
        """Number of active (non-expired) sessions."""
        with self._lock:
            self._cleanup_expired()
            return len(self._sessions)
