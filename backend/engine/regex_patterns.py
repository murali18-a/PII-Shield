"""
PII-Shield — Regex Detection Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
High-precision regex patterns for structured PII identifiers and secrets.
Each pattern is defined with a name, compiled regex, and confidence score.

These run BEFORE Presidio NER to catch structured data that NER may miss.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RegexPattern:
    """A named regex pattern with a fixed confidence score."""

    entity_type: str
    pattern: re.Pattern
    score: float = 1.0


# ── Pattern Definitions ─────────────────────────────

REGEX_PATTERNS: list[RegexPattern] = [
    # US Social Security Number: 123-45-6789
    RegexPattern(
        entity_type="US_SSN",
        pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        score=1.0,
    ),
    # Credit card (Visa, MC, Amex, Discover — Luhn not checked here)
    RegexPattern(
        entity_type="CREDIT_CARD",
        pattern=re.compile(r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
        score=0.95,
    ),
    # Email address
    RegexPattern(
        entity_type="EMAIL_ADDRESS",
        pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        score=1.0,
    ),
    # US/international phone numbers
    RegexPattern(
        entity_type="PHONE_NUMBER",
        pattern=re.compile(
            r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        score=0.9,
    ),
    # IPv4 address
    RegexPattern(
        entity_type="IP_ADDRESS",
        pattern=re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
        score=0.9,
    ),
    # AWS Access Key ID (starts with AKIA, 20 chars)
    RegexPattern(
        entity_type="AWS_ACCESS_KEY",
        pattern=re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        score=1.0,
    ),
    # JWT token (three base64url segments separated by dots)
    RegexPattern(
        entity_type="JWT_TOKEN",
        pattern=re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
        score=0.95,
    ),
    # US Passport Number (9 digits)
    RegexPattern(
        entity_type="US_PASSPORT",
        pattern=re.compile(r"\b\d{9}\b"),
        score=0.4,  # Low confidence — many false positives; combine with context
    ),
    # Date of Birth patterns: MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD
    RegexPattern(
        entity_type="DATE_OF_BIRTH",
        pattern=re.compile(
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"
        ),
        score=0.6,  # Medium — dates are common; context matters
    ),
]


@dataclass(frozen=True)
class RegexMatch:
    """Result of a regex pattern match."""

    entity_type: str
    start: int
    end: int
    score: float
    matched_text: str


def scan_with_regex(text: str) -> list[RegexMatch]:
    """
    Scan text against all regex patterns and return matches.

    Args:
        text: The input text to scan.

    Returns:
        A list of RegexMatch objects sorted by start position.
    """
    matches: list[RegexMatch] = []
    for pat in REGEX_PATTERNS:
        for m in pat.pattern.finditer(text):
            matches.append(
                RegexMatch(
                    entity_type=pat.entity_type,
                    start=m.start(),
                    end=m.end(),
                    score=pat.score,
                    matched_text=m.group(),
                )
            )
    # Sort by start position for consistent processing
    matches.sort(key=lambda x: x.start)
    return matches
