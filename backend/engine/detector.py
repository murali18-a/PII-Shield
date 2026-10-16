"""
PII-Shield — Detection Orchestrator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Orchestrates regex-based and Presidio NER-based detection,
merges results, and deduplicates overlapping spans.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.engine.regex_patterns import RegexMatch, scan_with_regex
from backend.engine.presidio_wrapper import PresidioWrapper, PresidioMatch


@dataclass(frozen=True)
class DetectedEntity:
    """Unified detection result from any source."""

    entity_type: str
    start: int
    end: int
    score: float
    matched_text: str
    source: str  # "regex" or "presidio"


class Detector:
    """
    Orchestrates PII detection using a two-pass approach:
      1. Regex patterns (high-precision structured identifiers)
      2. Presidio NER (named entities: persons, locations, orgs)

    Results are merged and overlapping spans are deduplicated,
    preferring higher-confidence detections.
    """

    def __init__(self, presidio: PresidioWrapper | None = None):
        self.presidio = presidio

    def detect(self, text: str) -> list[DetectedEntity]:
        """
        Run all detection passes and return a deduplicated, sorted list of entities.

        Args:
            text: The raw input text to scan.

        Returns:
            List of DetectedEntity objects sorted by start position.
        """
        entities: list[DetectedEntity] = []

        # ── Pass 1: Regex patterns ──────────────────
        regex_matches = scan_with_regex(text)
        for m in regex_matches:
            entities.append(
                DetectedEntity(
                    entity_type=m.entity_type,
                    start=m.start,
                    end=m.end,
                    score=m.score,
                    matched_text=m.matched_text,
                    source="regex",
                )
            )

        # ── Pass 2: Presidio NER ────────────────────
        if self.presidio and self.presidio.is_loaded:
            presidio_matches = self.presidio.analyze(text)
            for m in presidio_matches:
                entities.append(
                    DetectedEntity(
                        entity_type=m.entity_type,
                        start=m.start,
                        end=m.end,
                        score=m.score,
                        matched_text=m.matched_text,
                        source="presidio",
                    )
                )

        # ── Merge & deduplicate ─────────────────────
        entities = self._deduplicate(entities)
        return entities

    @staticmethod
    def _deduplicate(entities: list[DetectedEntity]) -> list[DetectedEntity]:
        """
        Remove overlapping detections, keeping the one with the highest score.
        When scores are equal, prefer regex (more precise for structured data).
        """
        if not entities:
            return []

        # Sort by start position, then by score descending
        sorted_entities = sorted(entities, key=lambda e: (e.start, -e.score))
        result: list[DetectedEntity] = [sorted_entities[0]]

        for current in sorted_entities[1:]:
            prev = result[-1]
            # Check overlap: current starts before previous ends
            if current.start < prev.end:
                # Keep the one with the higher score
                if current.score > prev.score:
                    result[-1] = current
                # If equal score, prefer regex source
                elif current.score == prev.score and current.source == "regex":
                    result[-1] = current
                # Otherwise keep prev (already in result)
            else:
                result.append(current)

        return result
