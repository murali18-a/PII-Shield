# PII-Shield — Presentation Slide Outline

> IBM Z Datathon 2026 — "AI Secured: Innovation Without Exposure"

---

## Slide 1: Title

- **PII-Shield**: Local-First Privacy Guardrail for LLM Interactions
- IBM Z Datathon 2026 — "AI Secured: Innovation Without Exposure"
- Team / Author name

---

## Slide 2: The Problem

- Users paste sensitive data into AI chatbots daily
- PII (names, SSNs, emails, API keys) gets sent to external servers
- External LLMs may log, store, or train on this data
- **60% of employees** have shared sensitive data with AI tools (Cyberhaven, 2024)
- Existing solutions: manual review (slow), enterprise DLP (expensive), or don't use AI (impractical)

---

## Slide 3: Our Solution

- **PII-Shield** — a Chrome extension + local backend
- Intercepts prompts before they leave your machine
- Detects PII using layered engines (regex + NER)
- Replaces PII with deterministic placeholders
- Sends only sanitized text to the LLM
- Restores original values locally when the response arrives
- **Core invariant: sensitive data never crosses the trust boundary**

---

## Slide 4: Architecture

- Data-flow diagram (see ARCHITECTURE.md)
- Trusted Zone: Extension → FastAPI → Detection → Redaction → Session Store
- Trust Boundary
- Untrusted Zone: External LLMs receive sanitized text only
- Admin Dashboard for audit visibility

---

## Slide 5: Detection Engine

- **Pass 1 — Regex**: 13 patterns for structured data
  - SSN, CC (Luhn), email, phone, IP, AWS key, JWT, Aadhaar, PAN, passwords
- **Pass 2 — Presidio NER**: Person, location, organization, date entities
  - Powered by spaCy en_core_web_sm
- **Deduplication**: Overlapping spans resolved by confidence score
- **Policy Engine**: REDACT / WARN / BLOCK per entity type
  - Three profiles: default, strict, permissive

---

## Slide 6: Security Design

- Placeholder mappings: **in-memory only**, TTL expiry, single-use
- Audit logs: **entity types and counts only** — no raw text, no PII values
- Backend: binds to 127.0.0.1 — not network-accessible
- Extension: CSP, localhost-only host permissions
- No credentials in source, all test data synthetic
- **Limitation**: Detection is best-effort, not guaranteed. Users should review.

---

## Slide 7: Evaluation

- 14-prompt synthetic test set
- **Recall: 92.31%** — catches most PII
- **Precision: 66.67%** — protective over-detection (names, orgs)
- **F1: 77.42%**
- 102 automated tests pass (unit + integration + edge cases)
- Security-specific tests: mapping leakage, audit privacy, session consumption
- 8 live API validation tests: all pass
- **Limitation**: Small sample size, not representative of enterprise traffic

---

## Slide 8: IBM Z / LinuxONE Relevance

- **Local mode**: Individual privacy protection (current implementation)
- **Enterprise mode**: Backend deployed on LinuxONE as centralized privacy gateway
- Why LinuxONE?
  - Hardware encryption (CPACF) for session data
  - 99.999% availability for always-on policy enforcement
  - Regulatory compliance (HIPAA, GDPR, PCI DSS)
- Deployment prepared: Dockerfile, network config, deployment guide
- **Honest disclosure**: No LinuxONE access available — deployment not verified on s390x

---

## Slide 9: Live Demo

- Clean text → 0 detections
- Personal info → 5+ detections, sanitized output
- Strict policy → request blocked
- Round-trip: sanitize → (simulated LLM response) → restore
- Dashboard: audit events with no PII visible

---

## Slide 10: What's Implemented vs. Future Work

| Implemented | Scaffold / Future |
|-------------|-------------------|
| Regex + Presidio detection engine | Content script DOM interception |
| Sanitize/restore round-trip API | TLS, authentication |
| Policy engine (3 profiles) | Persistent audit database |
| Chrome extension (popup + demo) | Multi-user / multi-tenant |
| Admin dashboard (4 tabs) | Redis session store for multi-worker |
| 102 automated tests | LinuxONE deployment verification |
| Docker deployment config | Rate limiting middleware |

---

## Slide 11: Key Takeaways

1. **Privacy by design**: Data never leaves the machine
2. **Layered detection**: Regex + NER catches structured and unstructured PII
3. **Policy flexibility**: REDACT / WARN / BLOCK per entity type
4. **Enterprise-ready architecture**: Same code scales from local to LinuxONE
5. **Honest engineering**: Known limitations documented, no fabricated claims
