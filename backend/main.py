"""
PII-Shield — FastAPI Application Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sets up the ASGI app, CORS middleware, lifespan hooks, and mounts the API router.
Initialises the Presidio engine, session store, and audit logger at startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.v1.router import api_router
from backend.api.schemas import HealthResponse
from backend.engine.presidio_wrapper import PresidioWrapper
from backend.utils.session import SessionStore
from backend.audit.logger import AuditLogger


# ── Shared singletons (initialised at startup) ─────
presidio_wrapper = PresidioWrapper(
    model_name=settings.SPACY_MODEL,
    score_threshold=settings.PRESIDIO_SCORE_THRESHOLD,
)
session_store = SessionStore(ttl_seconds=settings.SESSION_TTL_SECONDS)
audit_logger = AuditLogger(max_events=settings.MAX_AUDIT_EVENTS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # ── Startup ──────────────────────────────────────
    print(f"🛡️  PII-Shield v{settings.VERSION} starting on {settings.HOST}:{settings.PORT}")
    presidio_wrapper.load()
    if presidio_wrapper.is_loaded:
        print(f"✅ Presidio loaded with spaCy model '{settings.SPACY_MODEL}'")
    else:
        print(
            f"⚠️  Presidio could not load model '{settings.SPACY_MODEL}'. "
            f"Detection will use regex-only fallback. "
            f"Error: {presidio_wrapper.load_error}"
        )
    yield
    # ── Shutdown ─────────────────────────────────────
    print("🛡️  PII-Shield shutting down")


app = FastAPI(
    title="PII-Shield",
    description="Local-first privacy guardrail — detect and redact PII before it reaches external LLMs.",
    version=settings.VERSION,
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Root health (GET /health) ───────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def root_health():
    """Root-level health check (same as /api/v1/health)."""
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


# ── API v1 Routes ───────────────────────────────────
app.include_router(api_router, prefix="/api/v1")
