"""
PII-Shield — Pydantic Request / Response Schemas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shared data models for all API endpoints.
"""

from pydantic import BaseModel, Field


# ── Detection result ────────────────────────────────


class DetectionItem(BaseModel):
    """A single detected PII entity."""

    entity_type: str = Field(..., description="Entity type, e.g. PERSON, US_SSN, AADHAAR")
    placeholder: str = Field(..., description="Placeholder token, e.g. [PERSON_1]")
    start: int = Field(..., description="Start character offset in original text")
    end: int = Field(..., description="End character offset in original text")
    score: float = Field(..., ge=0.0, le=1.0, description="Detection confidence (estimate, not guarantee)")
    source: str = Field(..., description="Detection source: 'regex' or 'presidio'")
    action: str = Field(default="REDACT", description="Policy action: REDACT, WARN, or BLOCK")
    reason: str = Field(default="", description="Why this action was taken")


# ── Analyze (detection-only, no redaction) ──────────


class AnalyzeRequest(BaseModel):
    """Request to analyze text for PII without redacting."""

    text: str = Field(..., min_length=1, max_length=50_000, description="Text to scan for PII")
    policy_profile: str = Field(default="default", description="Policy profile to apply")


class AnalyzeResponse(BaseModel):
    """Response listing detected PII categories and actions."""

    detections: list[DetectionItem]
    categories_found: list[str] = Field(default_factory=list, description="Unique entity types detected")
    overall_action: str = Field(default="REDACT", description="Aggregate action: REDACT, WARN, or BLOCK")
    total_detections: int
    processing_time_ms: float
    disclaimer: str = Field(
        default="Detection is best-effort. Confidence scores are estimates and not a guarantee of accuracy.",
    )


# ── Sanitize (detect + redact) ─────────────────────


class SanitizeRequest(BaseModel):
    """Request to detect and redact PII from text."""

    text: str = Field(..., min_length=1, max_length=50_000, description="Raw text to scan and sanitize")
    policy_profile: str = Field(default="default", description="Policy profile to apply")


class SanitizeResponse(BaseModel):
    """Response containing sanitised text and detection metadata."""

    sanitized_text: str
    session_id: str = Field(..., description="Opaque session ID for later restoration")
    detections: list[DetectionItem]
    categories_found: list[str]
    overall_action: str = Field(default="REDACT", description="REDACT, WARN, or BLOCK")
    total_detections: int
    processing_time_ms: float
    disclaimer: str = Field(
        default="Detection is best-effort. Some PII may not be caught.",
    )


# ── Redaction (backward compat alias) ──────────────


class RedactRequest(BaseModel):
    """Request to redact PII from text (backward compat)."""

    text: str = Field(..., min_length=1, max_length=50_000, description="Raw text to scan")
    policy_profile: str = Field(default="default", description="Policy profile to apply")


class RedactStats(BaseModel):
    """Processing statistics for a redaction request."""

    total_entities: int
    processing_time_ms: float


class RedactResponse(BaseModel):
    """Response containing sanitised text and detection metadata (backward compat)."""

    sanitized_text: str
    session_id: str
    detections: list[DetectionItem]
    stats: RedactStats


# ── Restoration ─────────────────────────────────────


class RestoreRequest(BaseModel):
    """Request to restore placeholders in LLM response."""

    text: str = Field(..., min_length=1, max_length=100_000, description="Text with placeholders")
    session_id: str = Field(..., description="Session ID from the sanitize/redact response")


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
    action: str = "REDACT"


class AuditEventsResponse(BaseModel):
    """Paginated list of audit events."""

    events: list[AuditEvent]
    total_events: int
    page: int
    page_size: int


# ── Health ──────────────────────────────────────────


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    presidio_loaded: bool
    spacy_model: str
    active_sessions: int = 0
    note: str = ""
