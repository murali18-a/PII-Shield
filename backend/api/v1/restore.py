"""
PII-Shield — Restore Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
POST /api/v1/restore — Restore placeholders in LLM response text.
"""

from fastapi import APIRouter, HTTPException

from backend.api.schemas import RestoreRequest, RestoreResponse
from backend.engine.restorer import Restorer

router = APIRouter()

_restorer = Restorer()


@router.post("/restore", response_model=RestoreResponse)
async def restore_text(request: RestoreRequest):
    """
    Replace placeholders in the LLM's response with original values
    using the in-memory mapping identified by session_id.

    The mapping is consumed/expired after restoration.
    """
    from backend.main import session_store

    # Look up session
    mapping = session_store.get(request.session_id)
    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Session not found or expired. "
                "Sessions expire after the configured TTL or after restoration."
            ),
        )

    # Perform restoration
    result = _restorer.restore(request.text, mapping)

    # Delete session after successful restoration (one-time use)
    session_store.delete(request.session_id)

    return RestoreResponse(
        restored_text=result.restored_text,
        placeholders_restored=result.placeholders_restored,
    )
