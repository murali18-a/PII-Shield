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
    validator: str | None = None  # Optional validator function name


def _luhn_check(number_str: str) -> bool:
    """
    Validate a credit card number using the Luhn algorithm.
    Returns True if the number passes the check.
    """
    digits = [int(d) for d in number_str if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _aadhaar_check(number_str: str) -> bool:
    """
    Basic validation for Aadhaar-format identifiers.
    Aadhaar numbers are 12 digits, cannot start with 0 or 1.
    Uses Verhoeff algorithm in production — here we do format check only.
    """
    digits = re.sub(r"[\s-]", "", number_str)
    if len(digits) != 12:
        return False
    if digits[0] in ("0", "1"):
        return False
    return True


def _pan_check(pan_str: str) -> bool:
    """
    Validate Indian PAN format: AAAAA9999A.
    - First 5 chars: uppercase letters
    - Next 4: digits
    - Last 1: uppercase letter
    - 4th character indicates holder type (C, P, H, F, A, T, B, L, J, G)
    """
    pan = pan_str.strip().upper()
    if len(pan) != 10:
        return False
    valid_4th = set("CPHFATBLJG")
    return (
        pan[:3].isalpha()
        and pan[3] in valid_4th
        and pan[4].isalpha()
        and pan[5:9].isdigit()
        and pan[9].isalpha()
    )


# Map of validator names to functions
VALIDATORS = {
    "luhn": _luhn_check,
    "aadhaar": _aadhaar_check,
    "pan": _pan_check,
}


# ── Pattern Definitions ─────────────────────────────

REGEX_PATTERNS: list[RegexPattern] = [
    # US Social Security Number: 123-45-6789
    RegexPattern(
        entity_type="US_SSN",
        pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        score=1.0,
    ),
    # Credit card (Visa, MC, Amex, Discover) with Luhn validation
    RegexPattern(
        entity_type="CREDIT_CARD",
        pattern=re.compile(
            r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
        ),
        score=0.95,
        validator="luhn",
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
    # Indian phone numbers: +91 or 0 prefix, 10 digits
    RegexPattern(
        entity_type="PHONE_NUMBER",
        pattern=re.compile(r"(?:\+91[-.\s]?|0)?[6-9]\d{4}[-.\s]?\d{5}\b"),
        score=0.85,
    ),
    # Aadhaar-format identifier: 12 digits, optionally separated by spaces/hyphens
    RegexPattern(
        entity_type="AADHAAR",
        pattern=re.compile(r"\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b"),
        score=0.90,
        validator="aadhaar",
    ),
    # Indian PAN format: AAAAA9999A
    RegexPattern(
        entity_type="PAN",
        pattern=re.compile(r"\b[A-Z]{3}[CPHFATBLJG][A-Z]\d{4}[A-Z]\b"),
        score=0.95,
        validator="pan",
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
    # Generic API key patterns (common formats: hex, base64-like, 20+ chars)
    RegexPattern(
        entity_type="API_KEY",
        pattern=re.compile(
            r"(?i)(?:api[_-]?key|apikey|access[_-]?token|secret[_-]?key|auth[_-]?token)"
            r"[\s]*[:=][\s]*['\"]?([A-Za-z0-9_\-]{20,})['\"]?"
        ),
        score=0.85,
    ),
    # Password patterns in config/code: password = "...", passwd: "..."
    RegexPattern(
        entity_type="PASSWORD",
        pattern=re.compile(
            r"(?i)(?:password|passwd|pwd|secret)[\s]*[:=][\s]*['\"]([^'\"]{4,})['\"]"
        ),
        score=0.90,
    ),
    # JWT token (three base64url segments separated by dots)
    RegexPattern(
        entity_type="JWT_TOKEN",
        pattern=re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
        score=0.95,
    ),
    # US Passport Number (9 digits) — low confidence, context-dependent
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

    Patterns with validators will have their matches validated;
    failed validation reduces the score to zero (excluded).

    Args:
        text: The input text to scan.

    Returns:
        A list of RegexMatch objects sorted by start position.
    """
    matches: list[RegexMatch] = []
    for pat in REGEX_PATTERNS:
        for m in pat.pattern.finditer(text):
            matched_text = m.group()

            # For patterns with capture groups (API_KEY, PASSWORD),
            # use the captured group for matched_text but keep full span
            if m.lastindex and m.lastindex >= 1:
                # Use the full match span for position tracking
                pass

            # Run validator if configured
            if pat.validator and pat.validator in VALIDATORS:
                if not VALIDATORS[pat.validator](matched_text):
                    continue  # Skip invalid matches

            matches.append(
                RegexMatch(
                    entity_type=pat.entity_type,
                    start=m.start(),
                    end=m.end(),
                    score=pat.score,
                    matched_text=matched_text,
                )
            )
    # Sort by start position for consistent processing
    matches.sort(key=lambda x: x.start)
    return matches
