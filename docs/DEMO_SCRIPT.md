# PII-Shield — Demo Script

> 2–3 minute live demonstration for IBM Z Datathon 2026

---

## Pre-Demo Checklist

```powershell
# 1. Start all services (one command)
.\start.ps1

# OR manually:
# Terminal 1: Backend
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Dashboard
cd dashboard && npx vite --host 127.0.0.1
```

2. Load Chrome extension: `chrome://extensions/` → Developer mode → Load unpacked → `extension/`
3. Verify backend: Open http://127.0.0.1:8000/health — should show `"status": "healthy"`
4. Open the extension demo page: Click PII-Shield icon → "Open Demo Page"
5. Open dashboard: http://localhost:5173 in a separate tab

---

## Demo Flow (2.5 minutes)

### Act 1: The Problem (30 seconds)

**Say:**

> "Every day, millions of people paste personal information — names, Social Security numbers, emails, API keys — directly into AI chatbots. That data gets sent to external servers where it may be logged, stored, or used for training.

> A 2024 Cyberhaven study found that 60% of employees have shared sensitive data with AI tools.

> PII-Shield solves this by intercepting prompts *before* they leave your machine."

---

### Act 2: Live Detection (45 seconds)

1. **Load Sample Prompt**: Click "Load Sample" on the demo page.
   The sample contains: name, email, SSN, phone, Aadhaar, PAN.

2. **Analyze**: Click "Analyze Prompt".
   - Point out the highlighted PII in the original text
   - Show the detection cards: entity types, confidence scores, sources
   - **Say:** "Each entity gets a REDACT, WARN, or BLOCK action based on the active policy."

3. **Show Policy Options**: Switch policy to "strict" → click Analyze
   - Show that strict mode BLOCKS the request entirely for SSNs and credit cards
   - **Say:** "In strict mode, the request is blocked before any text leaves the machine."
   - Switch back to "default"

---

### Act 3: Sanitization & Round-Trip (45 seconds)

1. **Sanitize**: Click "Sanitize & Preview"
   - Show the sanitized text: `[US_SSN_1]`, `[EMAIL_ADDRESS_1]`, etc.
   - **Say:** "This is what would be sent to the LLM — deterministic placeholders, no real data."
   - Point out the session ID

2. **Restore**: Scroll to the restore section
   - Click "Restore Placeholders"
   - **Say:** "When the LLM responds with placeholders, we restore the original values locally. The mapping never leaves your machine and is deleted after use."

---

### Act 4: Dashboard & Audit (30 seconds)

1. Switch to the dashboard tab (http://localhost:5173)
2. **Overview tab**: Show total requests processed, entity category breakdown
3. **Audit Events tab**: Show the logged events
4. **Say:** "Audit logs record only entity types and counts — never the actual data. There's no way to reconstruct the original text from the audit trail. This is privacy by design."

---

### Act 5: Architecture & IBM Z (30 seconds)

**Say:**

> "Today, the backend runs locally for individual protection. But the same codebase can deploy on IBM LinuxONE as an enterprise privacy gateway.

> LinuxONE provides hardware-accelerated encryption via CPACF, five-nines availability, and regulatory compliance for PCI DSS, HIPAA, and GDPR workloads.

> Imagine: every employee's AI prompts routed through a centralized PII-Shield on LinuxONE — enterprise-wide policy enforcement, persistent auditing, and data sovereignty, all on tamper-resistant hardware.

> We've prepared the deployment configuration and Docker support. The architecture scales from a developer laptop to an enterprise data center."

---

## Demo Prompts

Use these prompts to showcase different scenarios:

### 1. Clean Text (No PII)
```
The function accepts two parameters: a list of integers and a boolean
flag for verbose output.
```
**Expected**: 0 detections, prompt passes through unchanged.

### 2. Personal Information (Primary Demo)
```
Hi, I'm Jane Doe. My email is jane.doe@example.com, SSN 123-45-6789,
and phone (555) 987-6543. My Aadhaar is 2345 6789 0123 and PAN is ABCPD1234E.
```
**Expected**: 5+ detections (EMAIL, SSN, PHONE, AADHAAR, PAN).

### 3. API Keys & Secrets
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
AWS key: AKIAIOSFODNN7EXAMPLE
```
**Expected**: 2 detections (JWT_TOKEN, AWS_ACCESS_KEY).

### 4. Cover Letter (Real-World Scenario)
```
Write a cover letter for Sarah Johnson (sarah.j@gmail.com, phone
415-555-0198) applying to Acme Corp as a software engineer.
Card: 4111-1111-1111-1111
```
**Expected**: 3+ detections (EMAIL, PHONE, CREDIT_CARD).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Backend not starting | Check `.venv` exists and `requirements.txt` installed |
| Extension not loading | Ensure Developer mode is on, reload extension |
| Dashboard blank | Run `npm install` in `dashboard/` first |
| "Unhealthy" status | Check port 8000 is free: `netstat -an | findstr 8000` |
| PowerShell script blocked | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## Important Notes

- All PII values in this demo are **synthetic** — no real personal information is used
- The extension demo page provides the full workflow; the content script for automatic DOM interception is a scaffold only
- Detection is best-effort — the system achieves 92.31% recall on the synthetic test set but cannot guarantee 100% coverage
