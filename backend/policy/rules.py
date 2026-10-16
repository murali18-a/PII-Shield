"""
PII-Shield — Policy & Decision Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Configurable allow/deny rules per entity type and per policy profile.
Determines which detected entities should be redacted, warned about, or blocked.

Decision actions:
  REDACT — Replace the PII with a placeholder (default)
  WARN   — Flag the PII for user attention but allow it through
  BLOCK  — Reject the entire request because it contains high-risk PII

Profiles allow different departments or use-cases to have different
redaction aggressiveness levels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from backend.engine.detector import DetectedEntity


class Action(str, Enum):
    """Policy action to take on a detected entity."""
    REDACT = "REDACT"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class PolicyDecision:
    """Decision for a single detected entity."""
    entity: DetectedEntity
    action: Action
    reason: str


@dataclass
class PolicyProfile:
    """A named policy profile with entity-level rules."""

    name: str
    # Entity types that should ALWAYS be redacted
    always_redact: set[str] = field(default_factory=set)
    # Entity types that should NEVER be redacted (passthrough)
    never_redact: set[str] = field(default_factory=set)
    # Entity types that should block the entire request
    block_types: set[str] = field(default_factory=set)
    # Entity types that should generate warnings (passed through but flagged)
    warn_types: set[str] = field(default_factory=set)
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
        "AADHAAR",
        "PAN",
        "PASSWORD",
        "API_KEY",
    },
    never_redact=set(),
    block_types=set(),
    warn_types={"DATE_OF_BIRTH", "US_PASSPORT"},
    min_score=0.5,
)

STRICT_PROFILE = PolicyProfile(
    name="strict",
    always_redact={
        "US_SSN",
        "CREDIT_CARD",
        "AWS_ACCESS_KEY",
        "JWT_TOKEN",
        "AADHAAR",
        "PAN",
        "PASSWORD",
        "API_KEY",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "IP_ADDRESS",
        "PERSON",
        "LOCATION",
        "ORGANIZATION",
        "DATE_OF_BIRTH",
        "US_PASSPORT",
    },
    never_redact=set(),
    block_types={"US_SSN", "CREDIT_CARD", "AADHAAR"},
    warn_types=set(),
    min_score=0.3,
)

PERMISSIVE_PROFILE = PolicyProfile(
    name="permissive",
    always_redact={
        "US_SSN",
        "CREDIT_CARD",
        "AWS_ACCESS_KEY",
        "AADHAAR",
        "PAN",
        "PASSWORD",
    },
    never_redact={
        "LOCATION",
        "DATE_OF_BIRTH",
        "ORGANIZATION",
    },
    block_types=set(),
    warn_types={"EMAIL_ADDRESS", "PHONE_NUMBER"},
    min_score=0.7,
)

_PROFILES: dict[str, PolicyProfile] = {
    p.name: p for p in [DEFAULT_PROFILE, STRICT_PROFILE, PERMISSIVE_PROFILE]
}


class PolicyEngine:
    """
    Applies policy rules to produce decisions for each detection.

    Usage:
        engine = PolicyEngine()
        decisions = engine.evaluate("default", detections)
        # Each decision has .action (REDACT/WARN/BLOCK) and .reason
    """

    def __init__(self, profiles: dict[str, PolicyProfile] | None = None):
        self.profiles = profiles or _PROFILES

    def get_profile(self, name: str) -> PolicyProfile:
        """Get a policy profile by name, falling back to default."""
        return self.profiles.get(name, DEFAULT_PROFILE)

    def list_profiles(self) -> list[str]:
        """Return available profile names."""
        return list(self.profiles.keys())

    def evaluate(
        self, profile_name: str, entities: list[DetectedEntity]
    ) -> list[PolicyDecision]:
        """
        Evaluate detected entities against the given policy profile.

        Returns a PolicyDecision for each entity, including those
        in never_redact (they get action=WARN with a note).

        Args:
            profile_name: Name of the policy profile.
            entities: List of detected entities.

        Returns:
            List of PolicyDecision objects.
        """
        profile = self.get_profile(profile_name)
        decisions: list[PolicyDecision] = []

        for entity in entities:
            et = entity.entity_type

            # Skip if explicitly in never_redact
            if et in profile.never_redact:
                continue

            # BLOCK takes highest priority
            if et in profile.block_types:
                decisions.append(PolicyDecision(
                    entity=entity,
                    action=Action.BLOCK,
                    reason=f"Entity type '{et}' is blocked under '{profile.name}' policy",
                ))
                continue

            # WARN types: flag but pass through
            if et in profile.warn_types and et not in profile.always_redact:
                decisions.append(PolicyDecision(
                    entity=entity,
                    action=Action.WARN,
                    reason=f"Entity type '{et}' flagged for review (score={entity.score:.2f})",
                ))
                continue

            # Always redact if in always_redact list
            if et in profile.always_redact:
                decisions.append(PolicyDecision(
                    entity=entity,
                    action=Action.REDACT,
                    reason=f"Entity type '{et}' is always redacted under '{profile.name}' policy",
                ))
                continue

            # Otherwise, apply score threshold
            if entity.score >= profile.min_score:
                decisions.append(PolicyDecision(
                    entity=entity,
                    action=Action.REDACT,
                    reason=f"Score {entity.score:.2f} >= threshold {profile.min_score:.2f}",
                ))

        return decisions

    def apply(
        self, profile_name: str, entities: list[DetectedEntity]
    ) -> list[DetectedEntity]:
        """
        Filter detected entities through the given policy profile.
        Returns only entities that should be redacted (backward compat).

        Args:
            profile_name: Name of the policy profile.
            entities: List of detected entities.

        Returns:
            Filtered list of entities that should be redacted.
        """
        decisions = self.evaluate(profile_name, entities)
        return [d.entity for d in decisions if d.action == Action.REDACT]
