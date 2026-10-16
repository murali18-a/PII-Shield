"""
PII-Shield — Audit Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
GET /api/v1/audit/stats  — Aggregate redaction statistics.
GET /api/v1/audit/events — Recent audit events (privacy-safe).
"""

from fastapi import APIRouter, HTTPException

from backend.api.schemas import AuditStatsResponse, AuditEventsResponse

router = APIRouter(prefix="/audit")


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats():
    """Return aggregate redaction statistics. No PII is ever included."""
    # TODO [Phase 3]: Query audit database for real stats
    raise HTTPException(
        status_code=501,
        detail="Audit logging not yet implemented. Coming in Phase 3.",
    )


@router.get("/events", response_model=AuditEventsResponse)
async def get_audit_events(page: int = 1, page_size: int = 20):
    """Return paginated audit events. Events contain only entity types and counts."""
    # TODO [Phase 3]: Query audit database for paginated events
    raise HTTPException(
        status_code=501,
        detail="Audit logging not yet implemented. Coming in Phase 3.",
    )
