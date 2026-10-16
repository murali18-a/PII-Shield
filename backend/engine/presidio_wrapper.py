"""
PII-Shield — Presidio Wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Wraps Microsoft Presidio AnalyzerEngine with a spaCy NLP backend
for named-entity-based PII detection (persons, locations, orgs, etc.).

This module handles lazy initialisation of the heavy spaCy model
so it is loaded once at startup, not on every request.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("pii_shield.presidio")


@dataclass(frozen=True)
class PresidioMatch:
    """Result of a Presidio NER detection."""

    entity_type: str
    start: int
    end: int
    score: float
    matched_text: str


class PresidioWrapper:
    """
    Singleton wrapper around Presidio AnalyzerEngine.

    Usage:
        wrapper = PresidioWrapper(model_name="en_core_web_sm")
        wrapper.load()
        results = wrapper.analyze("John Smith lives in NYC.")
    """

    def __init__(self, model_name: str = "en_core_web_sm", score_threshold: float = 0.5):
        self.model_name = model_name
        self.score_threshold = score_threshold
        self._engine = None
        self._loaded = False
        self._load_error: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def load(self) -> None:
        """
        Initialise the Presidio AnalyzerEngine with the configured spaCy model.
        Call this once during application startup.

        If loading fails (missing model, incompatible version), the wrapper
        remains functional but returns no results — detection falls back to
        regex-only mode.
        """
        if self._loaded:
            return

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider

            configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": self.model_name}],
            }
            provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = provider.create_engine()
            self._engine = AnalyzerEngine(nlp_engine=nlp_engine)
            self._loaded = True
            logger.info("Presidio AnalyzerEngine loaded with model '%s'", self.model_name)
        except Exception as e:
            self._load_error = str(e)
            logger.warning(
                "Failed to load Presidio with model '%s': %s. "
                "Detection will use regex-only fallback.",
                self.model_name,
                e,
            )

    def analyze(self, text: str, entities: list[str] | None = None) -> list[PresidioMatch]:
        """
        Analyse text for named entities using Presidio.

        Args:
            text: Input text to scan.
            entities: Optional list of entity types to detect.
                      If None, detects all supported types.

        Returns:
            A list of PresidioMatch objects sorted by start position.
        """
        if not self._loaded or self._engine is None:
            return []

        try:
            results = self._engine.analyze(
                text=text,
                entities=entities,
                language="en",
                score_threshold=self.score_threshold,
            )
            return [
                PresidioMatch(
                    entity_type=r.entity_type,
                    start=r.start,
                    end=r.end,
                    score=round(r.score, 4),
                    matched_text=text[r.start : r.end],
                )
                for r in sorted(results, key=lambda x: x.start)
            ]
        except Exception as e:
            logger.error("Presidio analysis failed: %s", e)
            return []
