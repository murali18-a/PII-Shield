# PII-Shield — Security

> IBM Z Datathon 2026 — "AI Secured: Innovation Without Exposure"
> Version: 0.2.0

---

## Security Design Principles

1. **Local-first**: All detection and redaction runs on the user's machine.
   No text or PII values are sent to external services by the backend.
2. **Data minimization**: The system processes only what is needed and
   retains nothing beyond the session TTL.
3. **Defense in depth**: Multiple detection engines (regex + NER), policy
   profiles, and input validation layers.
4. **Fail-safe defaults**: Unknown entity types are redacted. Unknown policy
   profiles fall back to `default`. Empty/invalid input is rejected.

---

## Data Classification

| Data | Classification | Storage | Logged? |
|------|---------------|---------|---------|
| Raw user input text | **Sensitive** | In-memory during processing only | Never |
| Placeholder mappings | **Sensitive** | In-memory session store (TTL) | Never |
| Sanitized text | Non-sensitive | Transient (returned to client) | Never |
| Entity types detected | Non-sensitive | In-memory audit ring buffer | Yes |
| Entity counts | Non-sensitive | In-memory audit ring buffer | Yes |
| Timestamps | Non-sensitive | In-memory audit ring buffer | Yes |
| Session IDs | Internal | In-memory only | Never |

---

## Trust Boundaries

The **trust boundary** separates the user's local machine from external
networks. PII-Shield ensures that only sanitized text (with deterministic
placeholders) crosses this boundary.

### What stays local:
- Raw text
- Placeholder → original value mappings
- Session IDs
- Audit event details

### What may leave the machine:
- Sanitized text with placeholders like `[PERSON_1]`, `[US_SSN_1]`
- These contain no recoverable PII

---

## Network Security

| Control | Implementation |
|---------|---------------|
| Loopback binding | Backend binds to `127.0.0.1` only — not reachable from other machines |
| CORS | Allows `*` origins — safe because of loopback binding |
| Extension permissions | `host_permissions` restricted to `http://127.0.0.1:8000/*` |
| CSP | `script-src 'self'; object-src 'self'` — no inline scripts, no external resources |
| TLS | Not used (localhost only); required if ever exposed to network |
| Authentication | None (single-user localhost); required if deployed as shared service |

---

## Input Validation

| Check | Implementation |
|-------|---------------|
| Max text length | Pydantic `max_length=50_000` on all text inputs |
| Min text length | Pydantic `min_length=1` — empty strings rejected |
| JSON schema | Pydantic models validate all request fields |
| Request timeout | Extension uses `AbortSignal.timeout(10000)` |

---

## Session Security

- **UUID4** session IDs: 122 bits of cryptographic entropy
- **TTL expiry**: sessions auto-delete after 1 hour (configurable)
- **Single-use**: mapping deleted after first restoration
- **No enumeration**: no API to list active sessions
- **No persistence**: sessions exist in RAM only — lost on restart

---

## Known Limitations

> **PII-Shield is a hackathon prototype. It has NOT been audited for
> production deployment. Do not rely on it as the sole privacy control.**

### Detection Gaps (False Negatives)

The detection engine **will miss some PII**. Known gaps:

1. **Obfuscated PII**: spelled-out numbers ("one two three"), Unicode
   homoglyphs, zero-width characters, Base64-encoded data
2. **Novel formats**: PII patterns not covered by regex or NER
3. **Context-dependent data**: a 9-digit number may be a passport,
   a zip code, or a product SKU — context is not always sufficient
4. **Non-English text**: NER model (`en_core_web_sm`) is English-only
5. **Multi-message correlation**: PII split across multiple messages
   is not correlated

### Detection Noise (False Positives)

The engine may flag non-PII text:

1. Presidio's NER detects ORGANIZATION and PERSON entities aggressively
2. Low-confidence regex patterns (US_PASSPORT: 0.4 score) match many
   9-digit numbers
3. DATE_OF_BIRTH regex matches ordinary dates

### Architectural Limitations

1. **Fail-open extension**: If the backend is unreachable, the content
   script scaffold does not block LLM submission. Users must use the
   demo page for verified protection.
2. **No rate limiting**: The backend has no request throttling
3. **No encryption at rest**: Session data is unencrypted in RAM
4. **No audit persistence**: Audit events are lost on restart
5. **Single-user model**: No authentication or multi-tenancy

---

## Threat Model Summary

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for the full catalogue.

| Threat | Severity | Status |
|--------|----------|--------|
| T1 — PII sent to external LLM | Critical | Mitigated by redaction pipeline |
| T2 — Incomplete redaction | High | Partially mitigated; documented limitations above |
| T3 — Over-redaction | Medium | Mitigated by policy profiles and confidence thresholds |
| T4 — Mapping leakage | Critical | Mitigated by in-memory-only design |
| T5 — Audit log contains PII | High | Mitigated by API design (no PII parameters) |
| T6 — Adversarial evasion | High | Partially mitigated; documented limitation |
| T7 — Credential leakage in repo | High | Mitigated by .gitignore and synthetic-only data |
| T8 — Extension compromise | Medium | Mitigated by CSP and localhost-only permissions |
| T9 — Local DoS | Low | Partially mitigated by input size limits |
| T10 — Session hijacking | Medium | Mitigated by UUID4 entropy, TTL, single-use |

---

## Verification Commands

```bash
# Run all tests including security edge cases
pytest tests/ -v

# Run integration tests specifically
pytest tests/test_integration.py -v

# Run evaluation (precision/recall)
python -m tests.test_evaluation

# Check for committed secrets (manual)
git log --all --diff-filter=A -- "*.env" "*.pem" "*.key"
git grep -i "password\|secret\|api_key" -- "*.py" "*.js" | grep -v "test_\|synth\|example\|placeholder"
```
