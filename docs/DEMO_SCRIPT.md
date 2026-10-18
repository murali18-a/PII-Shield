# PII-Shield — Demo Script

> 2–3 minute live demonstration for IBM Z Datathon 2026

---

## Setup (Before Demo)

1. Start backend: `uvicorn backend.main:app --host 127.0.0.1 --port 8000`
2. Start dashboard: `cd dashboard && npx vite`
3. Load extension in Chrome (chrome://extensions/ → Load unpacked → extension/)
4. Open the demo page: Click PII-Shield icon → "Open Demo Page"

---

## Demo Flow (2.5 minutes)

### Act 1: The Problem (30 seconds)

**Say:** "When we use AI assistants like ChatGPT, we often paste personal
information — names, SSNs, emails, API keys — directly into the prompt.
That data gets sent to external servers where it may be logged, stored,
or used for training. PII-Shield solves this."

### Act 2: Live Detection (45 seconds)

1. **Load Sample Prompt**: Click "Load Sample" on the demo page.
   The sample contains: name, email, SSN, phone, Aadhaar, PAN.

2. **Analyze**: Click "Analyze Prompt".
   - Point out the highlighted PII in the original text
   - Show the detection cards: entity types, confidence scores, sources
   - Note: "Each entity has a REDACT, WARN, or BLOCK action"

3. **Show Policy Options**: Switch policy to "strict" → click Analyze
   - Show that strict mode BLOCKS the request entirely for SSNs
   - Switch back to "default"

### Act 3: Sanitization & Round-Trip (45 seconds)

1. **Sanitize**: Click "Sanitize & Preview"
   - Show the sanitized text: `[US_SSN_1]`, `[EMAIL_ADDRESS_1]`, etc.
   - "This is what gets sent to the LLM — no real data"
   - Point out the session ID

2. **Restore**: Scroll to the restore section
   - Click "Restore Placeholders"
   - "The LLM's response comes back with placeholders, and we restore
     them locally. The mapping never leaves your machine."

### Act 4: Dashboard & Audit (30 seconds)

1. Switch to the dashboard tab (http://localhost:5173)
2. Show: Overview stats, audit events, policy configuration
3. "Audit logs record only entity types and counts — never the actual
   data. This is by design."

### Act 5: Architecture & IBM Z (30 seconds)

**Say:** "The backend runs locally for individual use, but the same
code can be deployed on IBM LinuxONE as an enterprise privacy gateway.
LinuxONE provides hardware encryption, five-nines availability, and
regulatory compliance — ideal for centralized PII protection at scale.
We've prepared the deployment configuration and Docker support."

---

## Demo Prompts

Use these four prompts to showcase different scenarios:

### 1. Clean Text (No PII)
```
The function accepts two parameters: a list of integers and a boolean
flag for verbose output.
```
Expected: 0 detections, prompt passes through unchanged.

### 2. Personal Information
```
Hi, I'm Jane Doe. My email is jane.doe@example.com, SSN 123-45-6789,
and phone (555) 987-6543. My Aadhaar is 2345 6789 0123 and PAN is ABCPD1234E.
```
Expected: 5+ detections (EMAIL, SSN, PHONE, AADHAAR, PAN).

### 3. API Keys & Secrets
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
AWS key: AKIAIOSFODNN7EXAMPLE
```
Expected: 2 detections (JWT_TOKEN, AWS_ACCESS_KEY).

### 4. Mixed — Cover Letter
```
Write a cover letter for Sarah Johnson (sarah.j@gmail.com, phone
415-555-0198) applying to Acme Corp as a software engineer.
Card: 4111-1111-1111-1111
```
Expected: 3+ detections (EMAIL, PHONE, CREDIT_CARD).
