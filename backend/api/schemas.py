"""
PII-Shield — Pydantic Request / Response Schemas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shared data models for all API endpoints.
"""

from pydantic import BaseModel, Field


# ── Detection result ────────────────────────────────


class DetectionResult(BaseModel):
    """A single detected PII entity."""

    entity_type: str = Field(..., description="Entity type, e.g. PERSON, US_SSN")
    placeholder: str = Field(..., description="Placeholder token, e.g. <PERSON_1>")
    start: int = Field(..., description="Start character offset in original text")
    end: int = Field(..., description="End character offset in original text")
    score: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    source: str = Field(..., description="Detection source: 'regex' or 'presidio'")


# ── Redaction ───────────────────────────────────────


class RedactRequest(BaseModel):
    """Request to redact PII from text."""

    text: str = Field(..., min_length=1, max_length=50_000, description="Raw text to scan")
    policy_profile: str = Field(default="default", description="Policy profile to apply")


class RedactStats(BaseModel):
    """Processing statistics for a redaction request."""

    total_entities: int
    processing_time_ms: float


class RedactResponse(BaseModel):
    """Response containing sanitised text and detection metadata."""

    sanitized_text: str
    session_id: str
    detections: list[DetectionResult]
    stats: RedactStats


# ── Restoration ─────────────────────────────────────


class RestoreRequest(BaseModel):
    """Request to restore placeholders in LLM response."""

    text: str = Field(..., min_length=1, max_length=100_000, description="Text with placeholders")
    session_id: str = Field(..., description="Session ID from the redact response")


class RestoreResponse(BaseModel):
    """Response containing restored text."""

    restored_text: str
    placeholders_restored: int


# ── Audit ───────────────────────────────────────────


class AuditEvent(BaseModel):
    """A single privacy-safe audit event (no PII ever included)."""

    id: str
    timestamp: str
    entity_types: list[str]
    entity_count: int
    policy_profile: str
    action: str = "redacted"


class AuditStatsResponse(BaseModel):
    """Aggregate redaction statistics."""

    total_requests: int
    total_entities_redacted: int
    entities_by_type: dict[str, int]
    requests_last_24h: int


class AuditEventsResponse(BaseModel):
    """Paginated list of audit events."""

    events: list[AuditEvent]
    page: int
    total_pages: int


# ── Health ──────────────────────────────────────────


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    presidio_loaded: bool
    spacy_model: str
