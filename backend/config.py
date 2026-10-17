"""
PII-Shield — Application Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Loads configuration from environment variables / .env file via pydantic-settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings with safe defaults."""

    # ── Server ───────────────────────────────────
    VERSION: str = "0.2.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "info"

    # ── CORS ─────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,null,chrome-extension://*"

    # ── Presidio / spaCy ─────────────────────────
    SPACY_MODEL: str = "en_core_web_sm"
    PRESIDIO_SCORE_THRESHOLD: float = 0.5

    # ── Input limits ─────────────────────────────
    MAX_INPUT_LENGTH: int = 50_000  # Max characters in a single request
    MAX_BATCH_SIZE: int = 10  # Max texts in a batch request (future)

    # ── Session ──────────────────────────────────
    SESSION_TTL_SECONDS: int = 3600

    # ── Audit ────────────────────────────────────
    AUDIT_DB_URL: str = "sqlite:///./audit.db"
    MAX_AUDIT_EVENTS: int = 10_000  # Max in-memory events before rotation

    # ── Policy ───────────────────────────────────
    DEFAULT_POLICY_PROFILE: str = "default"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
