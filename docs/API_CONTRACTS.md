# PII-Shield — API Contracts

> Version: 0.2.0 | Last Updated: 2026-10-18

---

## Base URL

```
http://127.0.0.1:8000/api/v1
```

## Authentication

None required. The backend runs locally and binds to `127.0.0.1` only.

---

## Endpoints

### 1. `POST /analyze`

Detect PII in text and return categories, scores, and policy decisions
**without** redacting or storing anything.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | `string` | Yes | Raw text to scan (1–50,000 chars) |
| `policy_profile` | `string` | No | Policy profile name (default: `"default"`) |

```json
{
  "text": "My name is John Smith and my SSN is 123-45-6789.",
  "policy_profile": "default"
}
```

**Response (200):**

```json
{
  "detections": [
    {
      "entity_type": "US_SSN",
      "placeholder": "[US_SSN_0]",
      "start": 38,
      "end": 49,
      "score": 1.0,
      "source": "regex",
      "action": "REDACT",
      "reason": "Entity type 'US_SSN' is always redacted under 'default' policy"
    }
  ],
  "categories_found": ["US_SSN"],
  "overall_action": "REDACT",
  "total_detections": 1,
  "processing_time_ms": 12.5,
  "disclaimer": "Detection is best-effort. Confidence scores are estimates and not a guarantee of accuracy."
}
```

---

### 2. `POST /sanitize`

Detect PII, replace with placeholders, and return sanitized text.
Stores the mapping in-memory for later restoration.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | `string` | Yes | Raw text to scan (1–50,000 chars) |
| `policy_profile` | `string` | No | Policy profile (default: `"default"`) |

**Response (200):**

```json
{
  "sanitized_text": "My name is John Smith and my SSN is [US_SSN_1].",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "detections": [
    {
      "entity_type": "US_SSN",
      "placeholder": "[US_SSN_1]",
      "start": 38,
      "end": 49,
      "score": 1.0,
      "source": "regex",
      "action": "REDACT",
      "reason": "Entity type 'US_SSN' is always redacted under 'default' policy"
    }
  ],
  "categories_found": ["US_SSN"],
  "overall_action": "REDACT",
  "total_detections": 1,
  "processing_time_ms": 15.3,
  "disclaimer": "Detection is best-effort. Some PII may not be caught."
}
```

**Error (422) — Blocked by Policy:**

```json
{
  "detail": {
    "error": "request_blocked",
    "message": "Request blocked by 'strict' policy. Blocked entity types: ['US_SSN']",
    "blocked_types": ["US_SSN"]
  }
}
```

> **Security note:** The placeholder-to-original mapping is NEVER included
> in the response. It exists only in the in-memory session store.

---

### 3. `POST /redact`

Backward-compatible alias for `/sanitize` with a simpler response schema.

**Request/Response:** Same as `/sanitize` but with `stats` instead of
individual fields:

```json
{
  "sanitized_text": "...",
  "session_id": "...",
  "detections": [...],
  "stats": {
    "total_entities": 2,
    "processing_time_ms": 15.3
  }
}
```

---

### 4. `POST /restore`

Restore placeholders in LLM response text to original values.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | `string` | Yes | Text with placeholders (1–100,000 chars) |
| `session_id` | `string` | Yes | Session ID from sanitize/redact response |

```json
{
  "text": "Sure, [PERSON_1]! Your SSN [US_SSN_1] is valid.",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response (200):**

```json
{
  "restored_text": "Sure, John Smith! Your SSN 123-45-6789 is valid.",
  "placeholders_restored": 2
}
```

**Error (404):** Session not found or expired.

> **Note:** Sessions are single-use. After restoration, the session
> is deleted and cannot be used again.

---

### 5. `GET /events`

Paginated, privacy-safe audit events.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `page` | `integer` | `1` | Page number (1-indexed) |
| `page_size` | `integer` | `20` | Events per page (1–100) |

**Response (200):**

```json
{
  "events": [
    {
      "id": "evt_abc123def456",
      "timestamp": "2026-10-18T12:30:00+00:00",
      "entity_types": ["PERSON", "US_SSN"],
      "entity_count": 3,
      "policy_profile": "default",
      "action": "REDACT"
    }
  ],
  "total_events": 42,
  "page": 1,
  "page_size": 20
}
```

> **Security note:** Events contain only entity types and counts.
> No raw text, PII values, or mappings are ever included.

---

### 6. `GET /health`

Service health and readiness check. Available at both `/health` and `/api/v1/health`.

**Response (200):**

```json
{
  "status": "healthy",
  "version": "0.2.0",
  "presidio_loaded": true,
  "spacy_model": "en_core_web_sm",
  "active_sessions": 3,
  "note": ""
}
```

---

## Placeholder Format

Placeholders use **square brackets** with sequential numbering:

```
[ENTITY_TYPE_N]
```

Examples: `[PERSON_1]`, `[US_SSN_1]`, `[EMAIL_ADDRESS_2]`, `[AADHAAR_1]`

Repeated identical values receive the same placeholder.

---

## Policy Profiles

| Profile | Description |
|---------|-------------|
| `default` | Redacts structured PII. Warns on dates/passports. |
| `strict` | Redacts everything. **Blocks** SSN, credit card, Aadhaar. |
| `permissive` | Redacts high-risk only. Warns on email/phone. Skips locations. |

---

## CORS Configuration

| Setting | Value |
|---|---|
| Allowed Origins | `*` (safe because server binds to 127.0.0.1 only) |
| Allowed Methods | All (`*`) |
| Allowed Headers | All (`*`) |
| Credentials | `false` |

---

## Error Responses

All errors follow FastAPI's standard error format:

| Status | Condition |
|---|---|
| `422` | Validation error or request blocked by policy |
| `404` | Session not found or expired |
| `500` | Internal server error |
