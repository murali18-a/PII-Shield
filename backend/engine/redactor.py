"""
PII-Shield — Redactor
~~~~~~~~~~~~~~~~~~~~~~
Generates deterministic placeholders for detected entities and
produces the sanitised text. Returns the placeholder mapping
for later restoration.

Placeholder format: [ENTITY_TYPE_N]  e.g. [PERSON_1], [EMAIL_ADDRESS_1], [AADHAAR_1]
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.engine.detector import DetectedEntity


@dataclass
class RedactionResult:
    """Output of the redaction process."""

    sanitized_text: str
    mapping: dict[str, str]  # placeholder → original value
    placeholders: list[PlaceholderInfo]


@dataclass(frozen=True)
class PlaceholderInfo:
    """Metadata about a single placeholder substitution."""

    entity_type: str
    placeholder: str
    original_start: int
    original_end: int
    score: float
    source: str


class Redactor:
    """
    Replaces detected entities in text with deterministic placeholders.

    The mapping from placeholder to original value is returned as part of
    the RedactionResult and should be stored in the session store (in-memory only).

    Handles:
    - Multiple entities of the same type (numbered sequentially)
    - Repeated identical values (same value gets same placeholder)
    - Overlapping spans (assumed pre-deduplicated by Detector)
    """

    def redact(self, text: str, entities: list[DetectedEntity]) -> RedactionResult:
        """
        Replace all detected entities with placeholders.

        Args:
            text: Original text.
            entities: Detected entities sorted by start position.

        Returns:
            RedactionResult with sanitised text, mapping, and placeholder metadata.
        """
        if not entities:
            return RedactionResult(
                sanitized_text=text,
                mapping={},
                placeholders=[],
            )

        # Track seen values: if the same text appears twice, reuse the placeholder
        value_to_placeholder: dict[tuple[str, str], str] = {}
        # Count occurrences per entity type for numbering
        type_counter: dict[str, int] = {}
        mapping: dict[str, str] = {}
        placeholder_infos: list[PlaceholderInfo] = []

        # Build replacement list (process right-to-left to preserve offsets)
        replacements: list[tuple[int, int, str, PlaceholderInfo]] = []

        for entity in entities:
            et = entity.entity_type
            key = (et, entity.matched_text)

            if key in value_to_placeholder:
                # Reuse placeholder for repeated identical value
                placeholder = value_to_placeholder[key]
            else:
                type_counter[et] = type_counter.get(et, 0) + 1
                placeholder = f"[{et}_{type_counter[et]}]"
                value_to_placeholder[key] = placeholder
                mapping[placeholder] = entity.matched_text

            info = PlaceholderInfo(
                entity_type=et,
                placeholder=placeholder,
                original_start=entity.start,
                original_end=entity.end,
                score=entity.score,
                source=entity.source,
            )
            placeholder_infos.append(info)
            replacements.append((entity.start, entity.end, placeholder, info))

        # Apply replacements right-to-left to preserve character offsets
        sanitized = text
        for start, end, placeholder, _ in reversed(replacements):
            sanitized = sanitized[:start] + placeholder + sanitized[end:]

        return RedactionResult(
            sanitized_text=sanitized,
            mapping=mapping,
            placeholders=placeholder_infos,
        )
