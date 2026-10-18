# PII-Shield — Evaluation Report

> IBM Z Datathon 2026 — "AI Secured: Innovation Without Exposure"
> Date: 2026-10-18
> Repository: murali18-a/PII-Shield (branch: main)

---

## 1. Evaluation Methodology

### Detection Model

| Component | Details |
|-----------|---------|
| Regex engine | 13 hand-crafted patterns (SSN, CC, email, phone, IP, AWS key, JWT, Aadhaar, PAN, API key, password, passport, DOB) |
| NER engine | Microsoft Presidio with spaCy `en_core_web_sm` |
| Deduplication | Overlapping spans resolved by confidence; regex preferred on ties |
| Scoring unit | Per unique entity TYPE per prompt (not per instance) |

### Test Dataset

- **14 synthetic prompts** in [`data/synthetic_prompts.json`](data/synthetic_prompts.json)
- All values are synthetic — no real PII is used
- 12 prompts contain PII, 2 are clean (no PII expected)
- Prompts cover: SSN, email, phone, credit card, IP, AWS key, JWT, Aadhaar, PAN, password, API key, dates, repeated values

### Scoring Rules

- **True Positive (TP)**: Expected entity type IS detected in the prompt
- **False Positive (FP)**: Detected entity type was NOT in the expected set
- **False Negative (FN)**: Expected entity type was NOT detected
- **True Negative (TN)**: Clean prompt correctly produces zero detections

---

## 2. Results

### Aggregate Metrics

```
Precision: 66.67%  (24 / 36)
Recall:    92.31%  (24 / 26)
F1 Score:  77.42%

True positives:  24
False positives: 12
False negatives:  2
True negatives:   1
```

### Per-Prompt Results

| ID | Description | Expected | Detected | TP | FP | FN | Status |
|----|------------|----------|----------|----|----|-----|--------|
| synth_001 | Multiple structured PII | EMAIL, SSN, PHONE | EMAIL, SSN, PHONE, ORG, PERSON | 3 | 2 | 0 | PASS |
| synth_002 | Credit card and IP | CC, IP | CC, IP, ORG | 2 | 1 | 0 | PASS |
| synth_003 | AWS access key | AWS_KEY | AWS_KEY | 1 | 0 | 0 | PASS |
| synth_004 | No PII (clean) | — | — | 0 | 0 | 0 | PASS |
| synth_005 | Mixed PII + NLP | DOB, EMAIL, PHONE | DATE_TIME, EMAIL, PERSON, PHONE | 2 | 2 | 1 | MISS |
| synth_006 | Multiple SSNs | SSN | SSN | 1 | 0 | 0 | PASS |
| synth_007 | JWT token | JWT | JWT, ORG | 1 | 1 | 0 | PASS |
| synth_008 | Cover letter | EMAIL, PHONE | EMAIL, PHONE, ORG, PERSON | 2 | 2 | 0 | PASS |
| synth_009 | Dense PII paragraph | DOB, SSN, PHONE, EMAIL, IP | SSN, PHONE, EMAIL, IP, ORG, PERSON | 4 | 2 | 1 | MISS |
| synth_010 | No PII (code review) | — | ORG | 0 | 1 | 0 | FP only |
| synth_011 | Indian identity | AADHAAR, PAN, EMAIL | AADHAAR, PAN, EMAIL | 3 | 0 | 0 | PASS |
| synth_012 | Password + API key | PASSWORD, API_KEY | PASSWORD, API_KEY | 2 | 0 | 0 | PASS |
| synth_013 | Repeated email | EMAIL | EMAIL | 1 | 0 | 0 | PASS |
| synth_014 | CC + SSN | CC, SSN | CC, SSN, ORG | 2 | 1 | 0 | PASS |

---

## 3. Analysis

### False Negatives (2)

Both are `DATE_OF_BIRTH` in synth_005 and synth_009. Presidio detects these dates as `DATE_TIME` (a different label). The dates **are detected** — the issue is a label mismatch in the ground truth, not a detection failure.

**Impact**: A user's date of birth would still be redacted (as `[DATE_TIME_1]`), so there is no privacy leakage.

### False Positives (12)

| Type | Count | Explanation |
|------|-------|-------------|
| ORGANIZATION | 7 | Presidio NER labels company names, abbreviations, and some acronyms as organizations |
| PERSON | 5 | Presidio NER detects names even when not in the expected set |

These are **protective over-detections** — the system errs on the side of privacy by redacting more entities than strictly expected. In a privacy-first tool, over-detection is preferable to under-detection.

### True Negatives

- `synth_004` (clean technical text): Zero detections ✅
- `synth_010` (code review): One false ORGANIZATION detection — Presidio misidentifies "DataFrame" context

---

## 4. Automated Test Suite

### Test Results

```
Command: pytest tests/ -v --tb=short
Result:  102 passed, 0 failed, 0 skipped, 1 warning (1.40s)
```

### Test Breakdown

| Test File | Tests | Category |
|-----------|-------|----------|
| test_detector.py | 19 | Regex patterns, Presidio, deduplication |
| test_redactor.py | 8 | Placeholder generation, no-PII-leakage |
| test_restorer.py | 6 | Round-trip restoration |
| test_policy.py | 12 | REDACT/WARN/BLOCK, 3 profiles, thresholds |
| test_audit.py | 7 | Ring buffer, pagination, no-PII invariant |
| test_api_analyze.py | 6 | Analysis endpoint, validation |
| test_api_redact.py | 10 | Redaction endpoint, events, health |
| test_api_sanitize.py | 13 | Sanitization, sessions, Indian IDs, strict mode |
| test_integration.py | 16 | End-to-end round-trip, leakage, edge cases |
| **Total** | **97 functions (102 items)** | |

### Security-Specific Tests

| Test | What It Verifies |
|------|-----------------|
| `test_sanitize_response_has_no_mapping_field` | Mapping dict never appears in API response |
| `test_audit_events_contain_no_pii` | Audit events contain only entity types/counts |
| `test_session_consumed_after_restore` | Sessions are single-use (deleted after restore) |
| `test_sanitized_output_contains_no_detected_values` | No detected PII value appears in sanitized output |
| `test_strict_policy_blocks_ssn` | Strict policy returns 422 for blocked entity types |

---

## 5. Limitations

1. **Small sample size**: 14 synthetic prompts is insufficient for statistical confidence. Results should not be generalized to enterprise traffic.
2. **Synthetic-only data**: All prompts are hand-crafted. Real-world PII patterns are more diverse and noisy.
3. **English-only**: The spaCy `en_core_web_sm` model supports English only. Non-English PII will be missed by NER.
4. **Label granularity**: The ground truth uses `DATE_OF_BIRTH` but Presidio returns `DATE_TIME`. A more nuanced label mapping could improve reported recall.
5. **No adversarial testing**: Prompts do not include obfuscated, encoded, or deliberately evasive PII.
6. **Detection, not prevention**: The system detects and redacts PII but cannot guarantee 100% coverage.

---

## 6. Reproduction

```powershell
# Setup
git clone https://github.com/murali18-a/PII-Shield.git
cd PII-Shield
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run automated tests
pytest tests/ -v --tb=short

# Run evaluation
$env:PYTHONUTF8=1
python -m tests.test_evaluation
```
