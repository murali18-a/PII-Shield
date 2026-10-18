# PII-Shield — Final Independent Audit Report

> Auditor: Independent QA/Security Engineer
> Date: 2026-10-18 (updated)
> Repository: murali18-a/PII-Shield (branch: main, commit 90988a2)
> Platform: Windows 10/11, Python 3.13.5, Chrome (extension source-inspected)

---

## 1. Executive Summary

PII-Shield is a **functional prototype** of a local-first privacy guardrail for LLM interactions. The core backend pipeline — detection, redaction, restoration, policy enforcement, and privacy-safe audit logging — is **implemented and working**. The Chrome extension popup and demo page are functional when the backend is running. The content script for automatic DOM interception is a **scaffold only** and is never injected into pages.

**Overall assessment**: The project is a **credible hackathon prototype** with genuine working code, honest documentation of limitations, and a solid test suite. It is **not production-ready** and does not claim to be.

---

## 2. Component Inventory

| Component | Status | Evidence |
|-----------|--------|----------|
| FastAPI backend (6 endpoints) | **IMPLEMENTED** | Source verified, tests pass, live API tested |
| Detection engine (regex, 13 patterns) | **IMPLEMENTED** | Unit tests, evaluation run |
| Detection engine (Presidio NER) | **IMPLEMENTED** | Loads en_core_web_sm, verified in eval |
| Redactor (placeholder generation) | **IMPLEMENTED** | Unit + integration tests |
| Restorer (placeholder reversal) | **IMPLEMENTED** | Round-trip tests pass, live verified |
| Session store (in-memory, TTL) | **IMPLEMENTED** | Code inspected, single-use verified live |
| Policy engine (3 profiles) | **IMPLEMENTED** | 12 unit tests pass, strict BLOCK verified live |
| Audit logger (in-memory ring buffer) | **IMPLEMENTED** | 7 unit tests, privacy verified live |
| Chrome extension popup | **IMPLEMENTED** | Source inspected |
| Chrome extension demo page | **IMPLEMENTED** | Source inspected, full workflow |
| Chrome extension service worker | **IMPLEMENTED** | Source inspected |
| Chrome extension content script | **SCAFFOLD** | Contains TODO markers, never injected |
| Admin dashboard (4 tabs) | **IMPLEMENTED** | Source inspected, Vite dev server tested |
| Dockerfile | **IMPLEMENTED** | Not tested (no Docker run performed) |
| start.ps1 startup script | **IMPLEMENTED** | Tested, npx.cmd fix applied |

---

## 3. Automated Test Results

**Command**: `.venv\Scripts\python.exe -m pytest tests/ -v --tb=short`
**Result**: 102 passed, 0 failed, 0 skipped, 1 warning (1.40s)

### Breakdown by test file

| File | Tests | Status |
|------|-------|--------|
| test_api_analyze.py | 6 | ALL PASS |
| test_api_redact.py | 10 | ALL PASS |
| test_api_sanitize.py | 13 | ALL PASS |
| test_audit.py | 7 | ALL PASS |
| test_detector.py | 19 | ALL PASS |
| test_integration.py | 16 | ALL PASS |
| test_policy.py | 12 | ALL PASS |
| test_redactor.py | 8 | ALL PASS |
| test_restorer.py | 6 | ALL PASS |
| test_evaluation.py | 0 (script, not pytest) | N/A |
| **Total** | **97 pytest functions (102 items)** | **ALL PASS** |

---

## 4. Live API Validation (8 Tests)

Performed against a running backend (`uvicorn backend.main:app --host 127.0.0.1 --port 8000`):

| Test | Method | Result |
|------|--------|--------|
| Health check | `GET /health` | ✅ `"healthy"`, Presidio loaded, v0.2.0 |
| Clean text — zero detections | `POST /sanitize` | ✅ 0 detections |
| PII text — entities redacted | `POST /sanitize` | ✅ 5 detections (EMAIL, ORG, PERSON, PHONE, SSN) |
| No PII leakage in sanitized output | Check output string | ✅ No SSN or email in output |
| Round-trip restore | `POST /restore` | ✅ All 5 placeholders restored correctly |
| Session consumed (single-use) | Second `POST /restore` | ✅ Returns error (404) |
| Audit events — no PII | `GET /events` | ✅ No mapping field, no PII values |
| Strict policy blocks SSN | `POST /sanitize` with strict | ✅ Returns 422 (blocked) |

---

## 5. Verification of 16 Integration Tests

`test_integration.py` contains 16 test methods across 4 classes using `TestClient(app)` with real singletons — no mocking:

| Class | Tests | What it exercises |
|-------|-------|-------------------|
| TestFullRoundTrip | 3 | Sanitize then restore, multi-type, clean text |
| TestMappingNeverLeaks | 2 | No mapping in response, no PII in audit events |
| TestEdgeCases | 8 | Repeated values, malformed input, empty text, expired session, consumed session, strict BLOCK, analyze no session, health |
| TestSyntheticPromptSuite | 3 | All prompts process, clean prompts zero detections, PII prompts detect expected types |

**VERIFIED: 16 genuine integration tests, no mocking.**

---

## 6. Privacy and Data-Leakage Findings

### F-01: Audit Logger — Privacy by API Design (VERIFIED SECURE)

The `AuditLogger.log_redaction()` method accepts only `entity_types`, `entity_count`, `policy_profile`, and `action`. There is **no parameter** for raw text, PII values, or mappings. Architecturally impossible to pass raw PII to the logger. **VERIFIED by code inspection and live API test.**

### F-02: Session Store — In-Memory Only (VERIFIED SECURE)

- In-memory Python `dict` behind `threading.Lock`
- No disk writes, no database calls, no serialization
- UUID4 session IDs (122 bits entropy)
- TTL-based auto-expiry, single-use deletion
- **VERIFIED by code inspection, test, and live API test.**

### F-03: Sanitize Response — No Mapping Leakage (VERIFIED)

`SanitizeResponse` schema has no `mapping` field. Test explicitly checks `"mapping" not in data`. **VERIFIED by test and live API response inspection.**

### F-04: Content Script Fail-Open Behavior (FINDING — LOW)

`content.js` line 101: `return rawText; // Fail open`

**Mitigating factors**: Content script is **never injected** — no `content_scripts` entry in `manifest.json`. Code path is unreachable.

**Severity**: LOW (unreachable code)

### F-05: CORS Wildcard (FINDING — MEDIUM)

`main.py` uses `allow_origins=["*"]` with `allow_credentials=False`. Any website can make requests to `127.0.0.1:8000`.

**Mitigating factors**: Loopback binding, no credentials, single-user tool. No sensitive data returned unless caller provides it.

**Severity**: MEDIUM for prototype; HIGH if deployed to network.

### F-06: No Rate Limiting (FINDING — LOW)

No request throttling. Localhost DoS is a nuisance, not data exposure.

---

## 7. Security Scan Results

| Check | Result |
|-------|--------|
| `.env` in git history | NOT FOUND (gitignored) |
| `.pem` / `.key` in git history | NOT FOUND |
| `sk_live_` / `sk_test_` patterns | NOT FOUND |
| `AKIA*` patterns | `AKIAIOSFODNN7EXAMPLE` only — AWS docs example key |
| `pip check` (broken dependencies) | No broken requirements |
| Real PII in test data | NOT FOUND — all synthetic |

**Status**: PASS — no real credentials or PII in repository.

---

## 8. Evaluation Metrics Verification

### Reproduced Results (14 synthetic prompts)

| Metric | Value |
|--------|-------|
| Precision | 66.67% |
| Recall | 92.31% |
| F1 Score | 77.42% |
| True positives | 24 |
| False positives | 12 |
| False negatives | 2 |
| True negatives | 1 |

**False negatives**: Both are `DATE_OF_BIRTH` label mismatches — dates ARE detected as `DATE_TIME`.

**False positives**: ORGANIZATION (7) and PERSON (5) — protective over-detection.

**VERIFIED**: Results independently reproduced via `python -m tests.test_evaluation`.

---

## 9. IBM Z / LinuxONE Status

| Check | Status |
|-------|--------|
| LINUXONE_DEPLOYMENT.md exists | YES |
| Dockerfile exists and syntactically correct | YES |
| Docker build executed | **NOT EXECUTED** |
| LinuxONE (s390x) deployment tested | **NOT EXECUTED — no access** |
| TLS configured | **NOT IMPLEMENTED** |
| Authentication configured | **NOT IMPLEMENTED** |
| Persistent audit storage | **NOT IMPLEMENTED** |

Documentation honestly states: "No LinuxONE access was available during development."

**Status**: NOT VERIFIED. Deployment guide and Dockerfile are prepared but untested on any Linux/s390x system.

---

## 10. Feature Status Matrix

| Feature | Status | Evidence |
|---------|--------|----------|
| Regex detection (13 patterns) | **VERIFIED** | 19 tests + evaluation |
| Presidio NER detection | **VERIFIED** | Evaluation output |
| Deduplication of overlapping spans | **VERIFIED** | Dedicated test |
| Placeholder generation [TYPE_N] | **VERIFIED** | Tests + live API |
| Repeated value → same placeholder | **VERIFIED** | Test + live API |
| Sanitized output contains no detected values | **VERIFIED** | Test + live API |
| Session single-use (consumed after restore) | **VERIFIED** | Test + live API |
| Policy REDACT/WARN/BLOCK actions | **VERIFIED** | 12 tests + live API |
| Strict policy BLOCK behavior | **VERIFIED** | Test + live API |
| Audit events contain no PII | **VERIFIED** | Test + live API |
| Extension popup with health check | PARTIALLY VERIFIED | Source inspected |
| Extension demo page workflow | PARTIALLY VERIFIED | Source inspected |
| Content script DOM interception | **NOT IMPLEMENTED** | Scaffold with TODOs |
| Dashboard (4 tabs) | PARTIALLY VERIFIED | Source inspected, Vite serves |
| Docker deployment | **NOT VERIFIED** | Dockerfile present |
| LinuxONE deployment | **NOT VERIFIED** | Guide present, no access |

---

## 11. Remaining Blockers for Demo

| Blocker | Severity | Impact |
|---------|----------|--------|
| Content script never injected | LOW | Demo uses extension demo page — works fine |
| CORS wildcard | LOW | Acceptable for localhost demo |
| Dashboard policy config is read-only | LOW | Shows rules but doesn't allow runtime changes |
| No persistent audit storage | LOW | Events lost on restart — acceptable for demo |

**No critical blockers for a live hackathon demonstration.**

---

## 12. Reproduction Commands

```powershell
# Clone and setup
git clone https://github.com/murali18-a/PII-Shield.git
cd PII-Shield
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
copy .env.example .env

# Run all tests
pytest tests/ -v --tb=short

# Run evaluation
$env:PYTHONUTF8=1
python -m tests.test_evaluation

# Start services
.\start.ps1

# Verify live
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

---

## 13. Audit Summary

| Claim | Status |
|-------|--------|
| 102/102 tests pass | **VERIFIED** |
| 16 integration tests (no mocking) | **VERIFIED** |
| Mapping-leakage prevention | **VERIFIED** (API + live) |
| Audit privacy (no PII in logs) | **VERIFIED** (API + live) |
| 92.31% recall, 77.42% F1 (14 prompts) | **VERIFIED** (reproduced) |
| Live API sanitize/restore round-trip | **VERIFIED** |
| Session single-use enforcement | **VERIFIED** (live) |
| Strict policy blocks SSN | **VERIFIED** (live) |
| Dockerfile exists | **VERIFIED** (not built) |
| LinuxONE deployment | **NOT VERIFIED** (no access) |
| No hardcoded credentials | **VERIFIED** |
| Content script intercepts LLM submissions | **NOT IMPLEMENTED** (scaffold) |
| Extension works as Chrome extension | PARTIALLY VERIFIED (source only) |
