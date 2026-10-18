<p align="center">
  <h1 align="center">PII-Shield</h1>
  <p align="center">
    <strong>Local-first privacy guardrail for LLM interactions</strong><br/>
    Detect &amp; redact sensitive information before it leaves your machine.
  </p>
  <p align="center">
    <em>IBM Z Datathon 2026 — "AI Secured: Innovation Without Exposure"</em>
  </p>
</p>

---

## What It Does

PII-Shield intercepts prompts you send to external LLMs (ChatGPT, Claude, etc.) and:

1. **Detects** personally identifiable information (PII) using layered regex patterns and Microsoft Presidio NER.
2. **Replaces** each detected entity with a deterministic placeholder (`[PERSON_1]`, `[US_SSN_1]`, ...).
3. **Sends** only the sanitised text to the LLM.
4. **Restores** placeholders in the LLM's response back to original values — entirely on your local machine.

> **Privacy invariant:** Original sensitive values never leave the local trust boundary.

---

## Architecture Overview

```
Browser Extension ──► FastAPI Backend ──► Detection Engine ──► Redaction Engine
       │                     │                                       │
       │                     ▼                                       ▼
       │              Policy Engine                          Placeholder Map
       │              Audit Logger                          (in-memory only)
       │                     │
       ▼                     ▼
  External LLM       Admin Dashboard
 (sanitised only)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full data-flow diagram and component details.

## Supported Entity Types

| Category | Examples |
|---|---|
| **Structured (Regex)** | US SSN, credit card (Luhn-validated), phone, email, IP, AWS key, API key, JWT, password, Aadhaar, PAN |
| **Named Entities (Presidio + spaCy)** | Person names, locations, organisations, dates |

---

## Quick Start

### Prerequisites

- Python 3.11+ (tested with 3.13)
- Node.js 18+ (for Dashboard dev server)
- Google Chrome (for extension)
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/murali18-a/PII-Shield.git
cd PII-Shield

python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure

```bash
copy .env.example .env
```

### 3. Run Everything

```powershell
.\start.ps1
```

Or manually:

```bash
# Terminal 1: Backend
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Dashboard
cd dashboard && npx vite
```

### 4. Load Chrome Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder
4. The PII-Shield icon appears in your toolbar

### 5. Run Tests

```bash
pytest                               # 102 tests
python -m tests.test_evaluation      # Precision/recall report
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/analyze` | Detect PII and return categories (no redaction) |
| `POST` | `/api/v1/sanitize` | Detect, redact, and return sanitized text |
| `POST` | `/api/v1/redact` | Backward-compatible alias for sanitize |
| `POST` | `/api/v1/restore` | Restore placeholders to original values |
| `GET` | `/api/v1/events` | Paginated privacy-safe audit events |
| `GET` | `/api/v1/health` | Health and readiness check |

Full API documentation: [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md) | Interactive docs: http://127.0.0.1:8000/docs

---

## Project Structure

```
PII-Shield/
├── backend/              # FastAPI application
│   ├── api/              # HTTP endpoints & Pydantic schemas
│   ├── engine/           # Detection, redaction, restoration
│   ├── policy/           # Configurable allow/deny rules
│   ├── audit/            # Privacy-safe audit logging
│   └── utils/            # Session management
├── extension/            # Chrome Extension (Manifest V3)
│   ├── popup/            # Extension popup UI
│   ├── demo/             # Full-workflow demo page
│   ├── background/       # Service worker
│   └── content/          # Content script (scaffold)
├── dashboard/            # Admin dashboard (Vite + vanilla JS)
├── tests/                # pytest test suite (102 tests)
├── data/                 # Synthetic test data
├── docs/                 # API contracts, threat model
├── ARCHITECTURE.md       # Data-flow diagram & component details
├── SECURITY.md           # Threat model, limitations, verification
├── TESTING.md            # Test suite guide & evaluation results
├── WINDOWS_SETUP.md      # Step-by-step Windows setup
├── LINUXONE_DEPLOYMENT.md # IBM Z deployment guide
└── start.ps1             # One-command startup script
```

---

## Security & Privacy

- **No raw PII is ever logged** — audit records contain only entity types, counts, and timestamps.
- **Placeholder mappings are in-memory only** — they expire with the session and are never persisted.
- **No external APIs required** — all detection runs locally via Presidio + spaCy.
- **No credentials in source** — `.env` is gitignored; `.env.example` contains only safe defaults.
- **Detection is best-effort** — some PII may be missed. See [SECURITY.md](SECURITY.md) for known limitations.

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) and [SECURITY.md](SECURITY.md) for detailed security analysis.

---

## Development Status

| Component | Status |
|---|---|
| Detection engine (regex + Presidio NER) | ✅ Complete |
| Redaction & restoration pipeline | ✅ Complete |
| Policy engine (3 profiles) | ✅ Complete |
| Audit logging (privacy-safe) | ✅ Complete |
| FastAPI endpoints (6 routes) | ✅ Complete |
| Chrome Extension (popup + demo) | ✅ Complete |
| Admin dashboard | ✅ Complete |
| Integration tests | ✅ Complete (102 tests) |
| Content script DOM interception | ⬜ Scaffold only |
| LinuxONE deployment | ⬜ Prepared, not verified |

---

## Evaluation Results

On a 10-prompt synthetic test set:

| Metric | Value |
|--------|-------|
| **Precision** | 59.26% |
| **Recall** | 88.89% |
| **F1 Score** | 71.11% |

- High recall: catches most structured PII (SSN, email, CC, keys)
- Lower precision: Presidio NER produces protective false positives (PERSON, ORGANIZATION)
- See [TESTING.md](TESTING.md) for full breakdown

---

## Contributing

This project was created for the IBM Z Datathon 2026. Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

[MIT](LICENSE)
