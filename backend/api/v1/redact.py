"""
PII-Shield — Redact Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
POST /api/v1/redact — Detect and redact PII from user text.
"""

from fastapi import APIRouter, HTTPException

from backend.api.schemas import RedactRequest, RedactResponse

router = APIRouter()


@router.post("/redact", response_model=RedactResponse)
async def redact_text(request: RedactRequest):
    """
    Detect PII in the submitted text and return a sanitised version
    with deterministic placeholders.

    The placeholder-to-original mapping is stored only in-memory,
    keyed by the returned session_id.
    """
    # TODO [Phase 1]: Wire up detection + redaction engine
    # TODO [Phase 2]: Apply policy profile rules
    raise HTTPException(
        status_code=501,
        detail="Redaction engine not yet implemented. Coming in Phase 1.",
    )
