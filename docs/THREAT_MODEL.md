# PII-Shield — Threat Model

> **IBM Z Datathon 2026 — "AI Secured: Innovation Without Exposure"**
> Version: 0.2.0 | Last Updated: 2026-10-18

---

## 1. Overview

PII-Shield is a local-first privacy guardrail that detects and redacts personally identifiable information (PII) from prompts before they are sent to external LLMs. This threat model documents the security risks, attack surfaces, and mitigations for the system.

### Trust Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│ TRUSTED ZONE (User's Local Machine)                         │
│                                                             │
│  Browser Extension ←→ FastAPI Backend ←→ Detection Engine   │
│                           │                                 │
│                    In-Memory Session Store                   │
│                    (placeholder mappings)                    │
│                           │                                 │
│                    SQLite Audit DB                           │
│                    (entity types/counts only)                │
└──────────────────────────┬──────────────────────────────────┘
                           │ TRUST BOUNDARY
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ UNTRUSTED ZONE (External Network)                           │
│                                                             │
│  External LLM APIs (ChatGPT, Claude, Gemini, etc.)          │
│  (Receive ONLY sanitised text with placeholders)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Threat Catalogue

### T1 — Sensitive Data Sent to External LLM

| Property | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **STRIDE** | Information Disclosure |
| **Description** | Raw PII (names, SSNs, emails, etc.) is transmitted to an external LLM API, where it may be logged, trained on, or accessed by third parties. |
| **Attack Vector** | User submits a prompt containing PII; the extension or backend fails to intercept and redact it. |
| **Mitigation** | All text must pass through the redaction pipeline before leaving the trust boundary. The extension intercepts input submission events. If the backend is unreachable, the extension should BLOCK submission (fail-closed), not send raw text. |
| **Residual Risk** | If the extension is disabled or not installed on a particular browser, text flows directly to the LLM without protection. |

### T2 — Incomplete Redaction (False Negatives)

| Property | Value |
|---|---|
| **Severity** | 🟠 High |
| **STRIDE** | Information Disclosure |
| **Description** | The detection engine fails to identify some PII entities, allowing them to pass through to the external LLM in plaintext. |
| **Attack Vector** | Novel PII formats, misspelled names, obfuscated identifiers (e.g., "one two three-four five-six seven eight nine" for SSN), or entity types not covered by regex/Presidio patterns. |
| **Mitigation** | Layer multiple detection methods (regex for structured data, Presidio NER for named entities). Flag low-confidence detections for user review. Allow users to manually mark sensitive spans. Maintain a living pattern library. |
| **Residual Risk** | No detection system achieves 100% recall. Users should review redaction results before sending. |

### T3 — Over-Redaction (False Positives)

| Property | Value |
|---|---|
| **Severity** | 🟡 Medium |
| **STRIDE** | Denial of Service (usability) |
| **Description** | The detection engine incorrectly flags non-PII text as sensitive, degrading the quality of prompts sent to the LLM. |
| **Attack Vector** | Common words that match patterns (e.g., "123-45-6789" as a product SKU, a character name matching a PERSON entity). |
| **Mitigation** | Configurable confidence thresholds per entity type. User can un-redact specific detections in the extension UI. Policy profiles (permissive/default/strict) allow tuning. |
| **Residual Risk** | Some false positives are inevitable. The user must have final approval. |

### T4 — Placeholder Mapping Leakage

| Property | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **STRIDE** | Information Disclosure |
| **Description** | The mapping from placeholders (e.g., `<PERSON_1>`) to original values (e.g., "John Smith") is leaked via logs, database, disk, or network. |
| **Attack Vector** | A developer accidentally logs the mapping. The session store is persisted to disk. A debug endpoint exposes session data. |
| **Mitigation** | Mapping stored ONLY in an in-memory `SessionStore` with TTL expiry. The audit logger is architecturally prohibited from receiving mapping data — it accepts only entity types and counts. Code review checklist item: "Does this log/persist any mapping data?" No debug endpoints expose session contents. |
| **Residual Risk** | A memory dump or malicious code injection could theoretically extract mappings from RAM. |

### T5 — Audit Log Contains PII

| Property | Value |
|---|---|
| **Severity** | 🟠 High |
| **STRIDE** | Information Disclosure |
| **Description** | The audit logging system inadvertently records raw PII, original text, or placeholder mappings in the SQLite database. |
| **Attack Vector** | A code change passes raw text to the audit logger. An exception handler logs the full request body. |
| **Mitigation** | The `AuditLogger` API accepts ONLY `entity_types: list[str]`, `entity_count: int`, and `policy_profile: str`. It has no parameter for raw text or mappings. Exception handlers strip request bodies before logging. Audit DB schema has no columns that could hold raw text. |
| **Residual Risk** | Framework-level access logs (uvicorn) could log request bodies if misconfigured. Set `access_log=False` in production. |

### T6 — Prompt Injection / Adversarial Evasion

| Property | Value |
|---|---|
| **Severity** | 🟠 High |
| **STRIDE** | Tampering |
| **Description** | An adversary crafts input specifically designed to evade PII detection (e.g., Unicode homoglyphs, zero-width characters, Base64-encoded PII, or splitting PII across multiple messages). |
| **Attack Vector** | User (or a malicious page script) submits text with obfuscated PII that bypasses regex and NER patterns. |
| **Mitigation** | Normalise Unicode before detection. Strip zero-width characters. Regex patterns handle common separator variations. Presidio's NER handles some name variations. Consider a deny-list of known evasion patterns. |
| **Residual Risk** | Determined adversaries with novel obfuscation techniques may evade detection. This is a known limitation of pattern-based systems. |

### T7 — Credential / Secret Leakage in Repository

| Property | Value |
|---|---|
| **Severity** | 🟠 High |
| **STRIDE** | Information Disclosure |
| **Description** | API keys, passwords, or real PII are committed to the git repository. |
| **Attack Vector** | Developer accidentally commits `.env` file, hardcodes a key, or uses real data in test files. |
| **Mitigation** | `.gitignore` excludes `.env`, `*.db`, and other sensitive files. `.env.example` contains only placeholder values. All test data is explicitly synthetic. Pre-commit hooks (recommended) can scan for secrets. |
| **Residual Risk** | A developer may bypass `.gitignore` with `git add -f`. |

### T8 — Malicious Browser Extension Compromise

| Property | Value |
|---|---|
| **Severity** | 🟡 Medium |
| **STRIDE** | Elevation of Privilege, Information Disclosure |
| **Description** | A compromised or malicious version of the extension exfiltrates user input to an attacker-controlled server instead of (or in addition to) the local backend. |
| **Attack Vector** | Supply-chain attack on extension dependencies, or a trojanised extension update. |
| **Mitigation** | Extension only communicates with `http://127.0.0.1:8000` (localhost). Manifest V3 `host_permissions` restrict network access. Content Security Policy blocks inline scripts and external connections. Extension source is open and auditable. |
| **Residual Risk** | A sufficiently sophisticated attacker could modify the manifest permissions before installation. |

### T9 — Denial of Service on Local Backend

| Property | Value |
|---|---|
| **Severity** | 🟢 Low |
| **Description** | An attacker floods the local FastAPI backend with requests, consuming CPU/memory and degrading responsiveness. |
| **Attack Vector** | Malicious script on a webpage sends thousands of requests to `localhost:8000`. |
| **Mitigation** | Backend binds to `127.0.0.1` only (not externally accessible). Request size limits in Pydantic schemas (`max_length=50_000`). Rate limiting middleware (recommended for Phase 3). |
| **Residual Risk** | Local DoS is primarily a nuisance, not a data exposure risk. |

### T10 — Session Hijacking / Replay

| Property | Value |
|---|---|
| **Severity** | 🟡 Medium |
| **STRIDE** | Spoofing |
| **Description** | An attacker obtains a valid `session_id` and calls `/restore` to retrieve the original PII values from the placeholder mapping. |
| **Attack Vector** | A malicious page script reads the session_id from extension storage and calls the backend directly. |
| **Mitigation** | Session IDs are UUIDv4 (cryptographically random, 122 bits of entropy). Sessions auto-expire after TTL. Backend only listens on localhost. Sessions can be configured to be single-use (delete after first restoration). |
| **Residual Risk** | If the attacker has code execution on the local machine, they already have access to the user's data through other means. |

---

## 3. Data Classification

| Data | Classification | Storage | Logging |
|---|---|---|---|
| Raw user input text | 🔴 Sensitive | In-memory only (during processing) | ❌ Never |
| Placeholder mappings | 🔴 Sensitive | In-memory session store (TTL) | ❌ Never |
| Sanitised text | 🟢 Non-sensitive | Transient (returned to client) | ❌ Not logged |
| Entity types detected | 🟢 Non-sensitive | SQLite audit DB | ✅ Logged |
| Entity counts | 🟢 Non-sensitive | SQLite audit DB | ✅ Logged |
| Timestamps | 🟢 Non-sensitive | SQLite audit DB | ✅ Logged |
| Policy profile name | 🟢 Non-sensitive | SQLite audit DB | ✅ Logged |
| Session IDs | 🟡 Internal | In-memory only | ❌ Never |

---

## 4. Security Checklist

- [ ] All text passes through redaction before external transmission
- [ ] Placeholder mappings exist only in memory
- [ ] Audit logs contain only entity types, counts, and timestamps
- [ ] `.env` is in `.gitignore`
- [ ] No real PII in test data
- [ ] Backend binds to `127.0.0.1` only
- [ ] Extension uses localhost-only `host_permissions`
- [ ] Request size limits enforced via Pydantic validation
- [ ] Sessions auto-expire after TTL
- [ ] Exception handlers do not log request bodies
