"""
PII-Shield — API v1 Router
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Aggregates all v1 endpoint routers and includes the health check.
"""

from fastapi import APIRouter

from backend.api.v1.redact import router as redact_router
from backend.api.v1.restore import router as restore_router
from backend.api.v1.audit import router as audit_router
from backend.api.schemas import HealthResponse
from backend.config import settings

api_router = APIRouter()

# ── Mount sub-routers ───────────────────────────────
api_router.include_router(redact_router, tags=["Redaction"])
api_router.include_router(restore_router, tags=["Restoration"])
api_router.include_router(audit_router, tags=["Audit"])


# ── Health check ────────────────────────────────────
@api_router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Return service health status."""
    # TODO [Phase 1]: Check actual Presidio/spaCy readiness
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        presidio_loaded=False,  # Will be True after Phase 1 integration
        spacy_model=settings.SPACY_MODEL,
    )
