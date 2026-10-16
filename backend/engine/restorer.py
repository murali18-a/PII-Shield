"""
PII-Shield — Restorer
~~~~~~~~~~~~~~~~~~~~~~
Reverses placeholder substitutions in LLM response text
using the session's placeholder mapping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class RestorationResult:
    """Output of the restoration process."""

    restored_text: str
    placeholders_restored: int


# Matches placeholders like [PERSON_1], [US_SSN_2], [EMAIL_ADDRESS_1]
_PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9_]*_\d+\]")


class Restorer:
    """
    Restores placeholders in LLM response text to their original values.

    The mapping must be provided from the session store — it is never
    persisted to disk or logged.
    """

    def restore(self, text: str, mapping: dict[str, str]) -> RestorationResult:
        """
        Replace all placeholders in text with their original values.

        Args:
            text: Text containing placeholders (e.g. from LLM response).
            mapping: Dict of placeholder → original value.

        Returns:
            RestorationResult with restored text and count.
        """
        if not mapping:
            return RestorationResult(restored_text=text, placeholders_restored=0)

        restored = text
        count = 0

        for placeholder, original in mapping.items():
            occurrences = restored.count(placeholder)
            if occurrences > 0:
                restored = restored.replace(placeholder, original)
                count += occurrences

        return RestorationResult(
            restored_text=restored,
            placeholders_restored=count,
        )
