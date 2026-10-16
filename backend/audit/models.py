"""
PII-Shield — Audit Database Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SQLAlchemy ORM models for privacy-safe audit events.

CRITICAL: These models must NEVER store raw PII, original text,
placeholder mappings, or any data that could identify an individual.
"""

from __future__ import annotations

# TODO [Phase 3]: Implement SQLAlchemy models
#
# from sqlalchemy import Column, Integer, String, DateTime, JSON
# from sqlalchemy.orm import DeclarativeBase
# from datetime import datetime, timezone
#
#
# class Base(DeclarativeBase):
#     pass
#
#
# class AuditEventRecord(Base):
#     """
#     A single audit event. Contains ONLY:
#     - Timestamp
#     - Entity types detected (list of strings)
#     - Count of entities redacted
#     - Policy profile used
#     - Action taken (redacted / restored / blocked)
#
#     Does NOT contain:
#     - Original text
#     - Redacted text
#     - Placeholder mappings
#     - Any raw PII
#     """
#     __tablename__ = "audit_events"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     event_id = Column(String, unique=True, nullable=False)
#     timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
#     entity_types = Column(JSON, nullable=False)  # e.g. ["PERSON", "SSN"]
#     entity_count = Column(Integer, nullable=False)
#     policy_profile = Column(String, nullable=False, default="default")
#     action = Column(String, nullable=False, default="redacted")
