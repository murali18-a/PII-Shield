"""
PII-Shield — Presidio Wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Wraps Microsoft Presidio AnalyzerEngine with a spaCy NLP backend
for named-entity-based PII detection (persons, locations, orgs, etc.).

This module handles lazy initialisation of the heavy spaCy model
so it is loaded once at startup, not on every request.
"""

from __future__ import annotations

from dataclasses import dataclass

# TODO [Phase 1]: Uncomment once presidio + spaCy are installed
# from presidio_analyzer import AnalyzerEngine, RecognizerResult
# from presidio_analyzer.nlp_engine import NlpEngineProvider


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
        wrapper = PresidioWrapper(model_name="en_core_web_lg")
        wrapper.load()
        results = wrapper.analyze("John Smith lives in NYC.")
    """

    def __init__(self, model_name: str = "en_core_web_lg", score_threshold: float = 0.5):
        self.model_name = model_name
        self.score_threshold = score_threshold
        self._engine = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        """
        Initialise the Presidio AnalyzerEngine with the configured spaCy model.
        Call this once during application startup.
        """
        if self._loaded:
            return

        # TODO [Phase 1]: Implement actual Presidio initialisation
        # configuration = {
        #     "nlp_engine_name": "spacy",
        #     "models": [{"lang_code": "en", "model_name": self.model_name}],
        # }
        # provider = NlpEngineProvider(nlp_configuration=configuration)
        # nlp_engine = provider.create_engine()
        # self._engine = AnalyzerEngine(nlp_engine=nlp_engine)
        # self._loaded = True
        pass

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
        if not self._loaded:
            return []

        # TODO [Phase 1]: Implement actual analysis
        # results = self._engine.analyze(
        #     text=text,
        #     entities=entities,
        #     language="en",
        #     score_threshold=self.score_threshold,
        # )
        # return [
        #     PresidioMatch(
        #         entity_type=r.entity_type,
        #         start=r.start,
        #         end=r.end,
        #         score=r.score,
        #         matched_text=text[r.start:r.end],
        #     )
        #     for r in sorted(results, key=lambda x: x.start)
        # ]
        return []
