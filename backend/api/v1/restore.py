"""
PII-Shield — Restore Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
POST /api/v1/restore — Restore placeholders in LLM response text.
"""

from fastapi import APIRouter, HTTPException

from backend.api.schemas import RestoreRequest, RestoreResponse

router = APIRouter()


@router.post("/restore", response_model=RestoreResponse)
async def restore_text(request: RestoreRequest):
    """
    Replace placeholders in the LLM's response with original values
    using the in-memory mapping identified by session_id.

    The mapping is consumed/expired after restoration.
    """
    # TODO [Phase 1]: Wire up restoration engine + session lookup
    raise HTTPException(
        status_code=501,
        detail="Restoration engine not yet implemented. Coming in Phase 1.",
    )
