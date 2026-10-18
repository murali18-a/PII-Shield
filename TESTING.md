# PII-Shield — Testing Guide

> Version: 0.2.0

---

## Test Suite Overview

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_detector.py` | 19 | Regex patterns, Presidio wrapper, deduplication |
| `test_redactor.py` | 8 | Placeholder generation, repeated values, no PII leakage |
| `test_restorer.py` | 6 | Round-trip restoration, repeated placeholders |
| `test_policy.py` | 12 | All three profiles, BLOCK/WARN/REDACT, thresholds |
| `test_audit.py` | 7 | Ring buffer, pagination, no-PII invariant |
| `test_api_analyze.py` | 6 | Analysis endpoint, disclaimers, validation |
| `test_api_redact.py` | 10 | Redaction, restoration, health, events endpoints |
| `test_api_sanitize.py` | 13 | Sanitization, sessions, Aadhaar/PAN, strict profile |
| `test_integration.py` | 16 | End-to-end round-trip, mapping leakage, edge cases |
| **Total** | **97+** | |

---

## Running Tests

### All Tests

```bash
# Activate virtual environment first
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/macOS

# Run full suite
pytest

# Verbose output
pytest -v --tb=short

# Specific test file
pytest tests/test_integration.py -v
```

### Integration Tests Only

```bash
pytest tests/test_integration.py -v
```

These test the full pipeline through the HTTP layer:
- Sanitize → Restore round-trip
- Mapping never leaks in responses
- Repeated values get same placeholder
- Malformed input handling
- Session consumption (single-use)
- Policy BLOCK behavior
- Synthetic prompt suite

### Detection Evaluation (Precision/Recall)

```bash
# Windows
$env:PYTHONUTF8=1
python -m tests.test_evaluation

# Linux
python -m tests.test_evaluation
```

This runs all 14 synthetic prompts through the detection engine and reports:
- Per-prompt: expected vs detected entity types
- Aggregate: true/false positives/negatives
- Precision, Recall, F1 score

---

## Test Data

All test data is **synthetic** — no real PII is ever used.

### Synthetic Prompts (`data/synthetic_prompts.json`)

14 crafted prompts covering:

| ID | Description | Entity Types |
|----|-------------|-------------|
| synth_001 | Multiple structured PII | EMAIL, SSN, PHONE |
| synth_002 | Credit card and IP | CREDIT_CARD, IP_ADDRESS |
| synth_003 | AWS access key | AWS_ACCESS_KEY |
| synth_004 | Clean text (no PII) | — |
| synth_005 | Mixed PII + natural language | DATE, EMAIL, PHONE |
| synth_006 | Multiple SSNs | US_SSN |
| synth_007 | JWT token | JWT_TOKEN |
| synth_008 | Cover letter prompt | EMAIL, PHONE |
| synth_009 | Dense PII paragraph | DATE, SSN, PHONE, EMAIL, IP |
| synth_010 | Code review (no PII) | — |
| synth_011 | Indian identity formats | AADHAAR, PAN, EMAIL |
| synth_012 | Password and API key | PASSWORD, API_KEY |
| synth_013 | Repeated email address | EMAIL |
| synth_014 | Mixed credit card and SSN | CREDIT_CARD, US_SSN |

### Test Fixtures (`tests/conftest.py`)

Reusable fixtures for common test scenarios:
- `sample_text_with_pii` — multi-type PII
- `sample_text_clean` — no PII
- `sample_text_aadhaar_pan` — Indian identity formats
- `sample_text_secrets` — API keys, passwords
- `sample_text_repeated` — same email twice

---

## Security-Focused Tests

The integration test suite includes specific security verification:

1. **`test_sanitize_response_has_no_mapping_field`**: Verifies the raw
   mapping dict is never included in API responses
2. **`test_audit_events_contain_no_pii`**: Verifies audit events contain
   only entity types and counts, never PII values
3. **`test_session_consumed_after_restore`**: Verifies sessions are
   single-use
4. **`test_sanitized_output_contains_no_detected_values`** (in
   `test_redactor.py`): Verifies no detected PII appears in output

---

## Evaluation Results

Latest evaluation on the 14-prompt synthetic test set:

```
Engine: Presidio + Regex
Model: en_core_web_sm

Precision: 66.67%
Recall:    92.31%
F1 Score:  77.42%

True positives:  24
False positives: 12
False negatives:  2
True negatives:   1
```

**Analysis:**
- **High recall (92.31%)**: The engine catches most PII. The 2 false
  negatives are DATE_OF_BIRTH entries — Presidio returns these as
  DATE_TIME (a different label). The dates ARE detected, just under
  a different type name.
- **Lower precision (66.67%)**: Presidio's NER aggressively detects
  PERSON and ORGANIZATION entities that weren't in the expected set.
  These are actually *protective false positives* — over-redaction
  that errs on the side of privacy.
- **True negatives**: Both clean prompts are correctly identified
  in regex-only mode; with Presidio, one gets a false ORGANIZATION
  detection.
- **Sample size**: 14 synthetic prompts. Results should not be
  presented as representative of enterprise-scale traffic.

---

## Adding New Tests

Follow these conventions:

1. Place test files in `tests/` with `test_` prefix
2. Use synthetic data only — never real PII
3. Import fixtures from `conftest.py`
4. Use `TestClient(app)` for API-level tests
5. Group related tests in classes prefixed with `Test`
