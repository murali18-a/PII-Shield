"""
PII-Shield — Audit Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
GET /api/v1/events — Recent privacy-safe audit events.
"""

from fastapi import APIRouter, Query

from backend.api.schemas import AuditEvent, AuditEventsResponse

router = APIRouter()


@router.get("/events", response_model=AuditEventsResponse, tags=["Audit"])
async def get_audit_events(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Events per page"),
):
    """
    Return paginated, privacy-safe audit events.

    Events contain only entity types, counts, policy profile, and action.
    No raw text, PII values, or mappings are ever included.
    """
    from backend.main import audit_logger

    records, total = audit_logger.get_events(page=page, page_size=page_size)

    events = [
        AuditEvent(
            id=r.event_id,
            timestamp=r.timestamp,
            entity_types=r.entity_types,
            entity_count=r.entity_count,
            policy_profile=r.policy_profile,
            action=r.action,
        )
        for r in records
    ]

    return AuditEventsResponse(
        events=events,
        total_events=total,
        page=page,
        page_size=page_size,
    )
