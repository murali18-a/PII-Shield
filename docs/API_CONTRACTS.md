# PII-Shield — API Contracts

> Version: 0.1.0 | Last Updated: 2026-10-16

---

## Base URL

```
http://127.0.0.1:8000/api/v1
```

## Authentication

None required. The backend runs locally and binds to `127.0.0.1` only.

---

## Endpoints

### 1. `POST /redact`

Detect and redact PII from user text.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | `string` | ✅ | Raw text to scan (1–50,000 chars) |
| `policy_profile` | `string` | ❌ | Policy profile name (default: `"default"`) |

```json
{
  "text": "My name is John Smith and my SSN is 123-45-6789.",
  "policy_profile": "default"
}
```

**Response (200):**

| Field | Type | Description |
|---|---|---|
| `sanitized_text` | `string` | Text with PII replaced by placeholders |
| `session_id` | `string` | UUID for retrieving the mapping later |
| `detections` | `array` | List of detected entities |
| `detections[].entity_type` | `string` | Entity type (e.g., `PERSON`, `US_SSN`) |
| `detections[].placeholder` | `string` | Placeholder token (e.g., `<PERSON_1>`) |
| `detections[].start` | `integer` | Start offset in original text |
| `detections[].end` | `integer` | End offset in original text |
| `detections[].score` | `float` | Confidence score (0.0–1.0) |
| `detections[].source` | `string` | Detection method: `regex` or `presidio` |
| `stats.total_entities` | `integer` | Total entities detected |
| `stats.processing_time_ms` | `float` | Processing time in milliseconds |

```json
{
  "sanitized_text": "My name is <PERSON_1> and my SSN is <US_SSN_1>.",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "detections": [
    {
      "entity_type": "PERSON",
      "placeholder": "<PERSON_1>",
      "start": 11,
      "end": 21,
      "score": 0.95,
      "source": "presidio"
    },
    {
      "entity_type": "US_SSN",
      "placeholder": "<US_SSN_1>",
      "start": 35,
      "end": 46,
      "score": 1.0,
      "source": "regex"
    }
  ],
  "stats": {
    "total_entities": 2,
    "processing_time_ms": 42.5
  }
}
```

**Error Responses:**

| Status | Condition |
|---|---|
| `422` | Validation error (empty text, text too long) |
| `501` | Engine not yet implemented (Phase 0 stub) |
| `500` | Internal server error |

---

### 2. `POST /restore`

Restore placeholders in LLM response text to original values.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | `string` | ✅ | Text containing placeholders (1–100,000 chars) |
| `session_id` | `string` | ✅ | Session ID from redact response |

```json
{
  "text": "Sure, <PERSON_1>! Your SSN <US_SSN_1> is valid.",
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

**Error Responses:**

| Status | Condition |
|---|---|
| `404` | Session not found or expired |
| `422` | Validation error |
| `501` | Engine not yet implemented (Phase 0 stub) |

---

### 3. `GET /health`

Service health and readiness check.

**Response (200):**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "presidio_loaded": true,
  "spacy_model": "en_core_web_lg"
}
```

---

### 4. `GET /audit/stats`

Aggregate redaction statistics. **No PII is ever returned.**

**Response (200):**

```json
{
  "total_requests": 1024,
  "total_entities_redacted": 3891,
  "entities_by_type": {
    "PERSON": 1200,
    "EMAIL_ADDRESS": 890,
    "US_SSN": 401
  },
  "requests_last_24h": 87
}
```

---

### 5. `GET /audit/events`

Paginated audit events. **No PII is ever returned.**

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `page` | `integer` | `1` | Page number |
| `page_size` | `integer` | `20` | Items per page |

**Response (200):**

```json
{
  "events": [
    {
      "id": "evt_abc123def456",
      "timestamp": "2026-10-16T22:30:00Z",
      "entity_types": ["PERSON", "EMAIL_ADDRESS"],
      "entity_count": 3,
      "policy_profile": "default",
      "action": "redacted"
    }
  ],
  "page": 1,
  "total_pages": 10
}
```

---

## CORS Configuration

| Setting | Value |
|---|---|
| Allowed Origins | `chrome-extension://<ID>`, `http://localhost:5173` |
| Allowed Methods | All (`*`) |
| Allowed Headers | All (`*`) |
| Credentials | `true` |

Configure via `ALLOWED_ORIGINS` in `.env`.
