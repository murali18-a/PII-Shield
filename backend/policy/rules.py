"""
PII-Shield — Policy Rules Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Configurable allow/deny rules per entity type and per policy profile.
Determines which detected entities should actually be redacted.

Profiles allow different departments or use-cases to have different
redaction aggressiveness levels.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.engine.detector import DetectedEntity


@dataclass
class PolicyProfile:
    """A named policy profile with entity-level rules."""

    name: str
    # Entity types that should ALWAYS be redacted
    always_redact: set[str] = field(default_factory=set)
    # Entity types that should NEVER be redacted (passthrough)
    never_redact: set[str] = field(default_factory=set)
    # Minimum confidence score to trigger redaction
    min_score: float = 0.5
    # Maximum text length accepted (0 = unlimited)
    max_text_length: int = 50_000


# ── Built-in profiles ───────────────────────────────

DEFAULT_PROFILE = PolicyProfile(
    name="default",
    always_redact={
        "US_SSN",
        "CREDIT_CARD",
        "AWS_ACCESS_KEY",
        "JWT_TOKEN",
    },
    never_redact=set(),
    min_score=0.5,
)

STRICT_PROFILE = PolicyProfile(
    name="strict",
    always_redact={
        "US_SSN",
        "CREDIT_CARD",
        "AWS_ACCESS_KEY",
        "JWT_TOKEN",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "IP_ADDRESS",
        "PERSON",
        "LOCATION",
        "DATE_OF_BIRTH",
        "US_PASSPORT",
    },
    never_redact=set(),
    min_score=0.3,
)

PERMISSIVE_PROFILE = PolicyProfile(
    name="permissive",
    always_redact={
        "US_SSN",
        "CREDIT_CARD",
        "AWS_ACCESS_KEY",
    },
    never_redact={
        "LOCATION",
        "DATE_OF_BIRTH",
    },
    min_score=0.7,
)

_PROFILES: dict[str, PolicyProfile] = {
    p.name: p for p in [DEFAULT_PROFILE, STRICT_PROFILE, PERMISSIVE_PROFILE]
}


class PolicyEngine:
    """
    Applies policy rules to filter detection results.

    Usage:
        engine = PolicyEngine()
        filtered = engine.apply("default", detections)
    """

    def __init__(self, profiles: dict[str, PolicyProfile] | None = None):
        self.profiles = profiles or _PROFILES

    def get_profile(self, name: str) -> PolicyProfile:
        """Get a policy profile by name, falling back to default."""
        return self.profiles.get(name, DEFAULT_PROFILE)

    def apply(
        self, profile_name: str, entities: list[DetectedEntity]
    ) -> list[DetectedEntity]:
        """
        Filter detected entities through the given policy profile.

        Args:
            profile_name: Name of the policy profile.
            entities: List of detected entities.

        Returns:
            Filtered list of entities that should be redacted.
        """
        profile = self.get_profile(profile_name)
        result: list[DetectedEntity] = []

        for entity in entities:
            # Skip if explicitly in never_redact
            if entity.entity_type in profile.never_redact:
                continue

            # Always redact if in always_redact list
            if entity.entity_type in profile.always_redact:
                result.append(entity)
                continue

            # Otherwise, apply score threshold
            if entity.score >= profile.min_score:
                result.append(entity)

        return result
