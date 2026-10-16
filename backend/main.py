"""
PII-Shield — FastAPI Application Entrypoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sets up the ASGI app, CORS middleware, lifespan hooks, and mounts the API router.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # ── Startup ──────────────────────────────────────
    # TODO [Phase 1]: Initialise Presidio AnalyzerEngine + spaCy model
    # TODO [Phase 3]: Initialise audit database connection
    print(f"🛡️  PII-Shield v{settings.VERSION} starting on {settings.HOST}:{settings.PORT}")
    yield
    # ── Shutdown ─────────────────────────────────────
    # TODO [Phase 1]: Clean up session store
    # TODO [Phase 3]: Close audit database connection
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

# ── Routes ──────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")
