"""
PII-Shield — Test Fixtures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shared pytest fixtures for the test suite.
All test data is synthetic — no real PII is ever used.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def synthetic_prompts() -> list[dict]:
    """Load synthetic test prompts from data/synthetic_prompts.json."""
    data_path = Path(__file__).parent.parent / "data" / "synthetic_prompts.json"
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_text_with_pii() -> str:
    """A single synthetic text containing multiple PII types."""
    return (
        "Hello, my name is Jane Doe and my email is jane.doe@example.com. "
        "My SSN is 123-45-6789 and my phone number is (555) 123-4567. "
        "I live at 123 Main Street, Springfield. "
        "My credit card number is 4111-1111-1111-1111."
    )


@pytest.fixture
def sample_text_clean() -> str:
    """A synthetic text with no PII."""
    return (
        "The weather today is sunny with a high of 75 degrees. "
        "Python is a popular programming language used in data science."
    )


@pytest.fixture
def sample_text_aadhaar_pan() -> str:
    """Synthetic text with Indian identity formats."""
    return (
        "My Aadhaar number is 2345 6789 0123 and "
        "my PAN is ABCPD1234E. Please process my application."
    )


@pytest.fixture
def sample_text_secrets() -> str:
    """Synthetic text with API keys and passwords."""
    return (
        'config = {"api_key": "synth_key_abc123def456ghi789jkl012mno", '
        'password: "SuperSecret123!@#"}'
    )


@pytest.fixture
def sample_text_repeated() -> str:
    """Synthetic text where the same PII value appears multiple times."""
    return (
        "Contact jane.doe@example.com for the report. "
        "If jane.doe@example.com is unavailable, try another address."
    )
