"""
PII-Shield — API v1 Router
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Aggregates all v1 endpoint routers and includes the health check.
"""

from fastapi import APIRouter

from backend.api.v1.analyze import router as analyze_router
from backend.api.v1.sanitize import router as sanitize_router
from backend.api.v1.redact import router as redact_router
from backend.api.v1.restore import router as restore_router
from backend.api.v1.audit import router as audit_router
from backend.api.schemas import HealthResponse
from backend.config import settings

api_router = APIRouter()

# ── Mount sub-routers ───────────────────────────────
api_router.include_router(analyze_router, tags=["Analysis"])
api_router.include_router(sanitize_router, tags=["Sanitization"])
api_router.include_router(redact_router, tags=["Redaction"])
api_router.include_router(restore_router, tags=["Restoration"])
api_router.include_router(audit_router, tags=["Audit"])


# ── Health check ────────────────────────────────────
@api_router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Return service health status."""
    from backend.main import presidio_wrapper, session_store

    note = ""
    if not presidio_wrapper.is_loaded:
        note = (
            f"Presidio not loaded — using regex-only fallback. "
            f"Run: python -m spacy download {settings.SPACY_MODEL}"
        )
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        presidio_loaded=presidio_wrapper.is_loaded,
        spacy_model=settings.SPACY_MODEL,
        active_sessions=session_store.active_count,
        note=note,
    )
