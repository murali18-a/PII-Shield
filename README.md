<p align="center">
  <h1 align="center">🛡️ PII-Shield</h1>
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
2. **Replaces** each detected entity with a deterministic placeholder (`<PERSON_1>`, `<SSN_1>`, …).
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
       │              Audit Logger ──► SQLite               (in-memory only)
       │                     │
       ▼                     ▼
  External LLM        React Dashboard
 (sanitised only)       (optional)
```

## Supported Entity Types

| Category | Examples |
|---|---|
| **Structured (Regex)** | SSN, credit card, phone, email, IP address, AWS key, JWT |
| **Named Entities (Presidio + spaCy)** | Person names, locations, organisations, dates, NRP |

---

## Quick Start

### Prerequisites

- Python 3.11+ (tested with 3.13)
- Node.js 18+ (for Chrome Extension / Dashboard)
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/murali18-a/PII-Shield.git
cd PII-Shield

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg
```

### 2. Configure

```bash
copy .env.example .env
# Edit .env if needed (defaults work for local development)
```

### 3. Run the Backend

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Run Tests

```bash
pytest
```

### 5. Load Chrome Extension (Development)

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder
4. The PII-Shield icon appears in your toolbar

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/redact` | Detect PII and return sanitised text |
| `POST` | `/api/v1/restore` | Restore placeholders to originals |
| `GET` | `/api/v1/audit/stats` | Aggregate redaction statistics |
| `GET` | `/api/v1/audit/events` | Recent audit events (no PII) |
| `GET` | `/api/v1/health` | Health check |

See full API contracts in [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md).

---

## Project Structure

```
PII-Shield/
├── backend/            # FastAPI application
│   ├── api/            # HTTP endpoints & Pydantic schemas
│   ├── engine/         # Detection, redaction, restoration
│   ├── policy/         # Configurable allow/deny rules
│   ├── audit/          # Privacy-safe logging to SQLite
│   └── utils/          # Session management
├── extension/          # Chrome Extension (Manifest V3)
├── dashboard/          # React + Vite admin dashboard (optional)
├── tests/              # pytest test suite
├── data/               # Synthetic test data
└── docs/               # Threat model, API contracts, setup guide
```

---

## Security & Privacy

- **No raw PII is ever logged** — audit records contain only entity types, counts, and timestamps.
- **Placeholder mappings are in-memory only** — they expire with the session and are never persisted.
- **No paid APIs required** — all detection runs locally via Presidio + spaCy.
- **No credentials in source** — `.env` is gitignored; `.env.example` contains only safe defaults.

See the full [Threat Model](docs/THREAT_MODEL.md) for detailed security analysis.

---

## Development Status

| Component | Status |
|---|---|
| Project scaffold & architecture | ✅ Complete |
| Detection engine (regex + Presidio) | 🔲 Phase 1 |
| Redaction & restoration pipeline | 🔲 Phase 1 |
| FastAPI endpoints | 🔲 Phase 2 |
| Chrome Extension | 🔲 Phase 2 |
| Policy engine | 🔲 Phase 3 |
| Audit logging | 🔲 Phase 3 |
| React dashboard | 🔲 Phase 3 (Optional) |

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
