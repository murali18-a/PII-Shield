# PII-Shield — Windows Setup Guide

> Step-by-step instructions for running PII-Shield on Windows 10/11.

---

## Prerequisites

| Software | Version | Check |
|----------|---------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Git | Any | `git --version` |
| Google Chrome | Latest | chrome://version |

---

## 1. Clone the Repository

```powershell
git clone https://github.com/murali18-a/PII-Shield.git
cd PII-Shield
```

## 2. Create and Activate Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> **Note:** If you get a script execution policy error, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## 3. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

## 4. Download the spaCy NLP Model

```powershell
python -m spacy download en_core_web_sm
```

> For better NER accuracy (larger download), use `en_core_web_lg` instead
> and set `SPACY_MODEL=en_core_web_lg` in your `.env` file.

## 5. Configure Environment

```powershell
copy .env.example .env
# Edit .env if needed — defaults work for local development
```

## 6. Run Tests

```powershell
pytest
```

Expected: **102 tests pass** (unit + integration + edge cases).

## 7. Start All Services

### Option A: Startup Script

```powershell
.\start.ps1
```

This starts both the backend and dashboard, waits for health check,
and provides Ctrl+C shutdown.

### Option B: Manual Start

Terminal 1 — Backend:
```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal 2 — Dashboard:
```powershell
cd dashboard
npm install
npx vite
```

## 8. Load the Chrome Extension

1. Open `chrome://extensions/` in Google Chrome
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select the `extension/` folder from the project
5. The PII-Shield icon appears in your toolbar

## 9. Verify Everything Works

1. **Backend**: Visit http://127.0.0.1:8000/health — should return `{"status": "healthy"}`
2. **API docs**: Visit http://127.0.0.1:8000/docs — interactive Swagger UI
3. **Dashboard**: Visit http://localhost:5173 — admin dashboard
4. **Extension popup**: Click the PII-Shield icon — should show "Engine ready"
5. **Demo page**: Click "Open Demo Page" in the popup — full workflow test

## 10. Run the Detection Evaluation

```powershell
$env:PYTHONUTF8=1
python -m tests.test_evaluation
```

This reports precision, recall, and F1 score against the synthetic test set.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'backend'` | Run from the project root, not inside `backend/` |
| Presidio not loaded (regex-only mode) | Run `python -m spacy download en_core_web_sm` |
| Extension shows "Backend offline" | Start the backend first (`uvicorn backend.main:app`) |
| Port 8000 in use | Change `PORT` in `.env` or stop the conflicting process |
| PowerShell script blocked | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Unicode errors in evaluation output | Set `$env:PYTHONUTF8=1` before running |

---

## Directory Structure After Setup

```
PII-Shield/
├── .env                  ← Your local config (gitignored)
├── .venv/                ← Python virtual environment (gitignored)
├── backend/              ← FastAPI application
├── dashboard/            ← Admin dashboard (Vite)
│   └── node_modules/     ← Node dependencies (gitignored)
├── extension/            ← Chrome Extension
├── tests/                ← pytest test suite
├── data/                 ← Synthetic test data
├── docs/                 ← API contracts, threat model
├── start.ps1             ← Startup script
├── requirements.txt      ← Python dependencies
└── pyproject.toml        ← Project config
```
