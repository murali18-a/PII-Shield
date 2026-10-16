# PII-Shield — Setup Guide

> Step-by-step instructions for setting up the development environment on Windows 10/11.

---

## Prerequisites

| Tool | Minimum Version | Check Command |
|---|---|---|
| Python | 3.11+ | `python --version` |
| pip | 23+ | `pip --version` |
| Node.js | 18+ | `node --version` |
| Git | 2.40+ | `git --version` |
| Chrome | 120+ | `chrome://version` |

---

## 1. Clone the Repository

```powershell
git clone https://github.com/murali18-a/PII-Shield.git
cd PII-Shield
```

---

## 2. Python Backend Setup

### 2.1 Create Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> **Note:** If you get an execution policy error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 2.2 Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2.3 Download spaCy Model

```powershell
python -m spacy download en_core_web_lg
```

This downloads a ~560 MB language model. It may take a few minutes.

### 2.4 Configure Environment

```powershell
copy .env.example .env
```

Edit `.env` if needed. The defaults work for local development.

### 2.5 Run the Backend

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Verify at: http://127.0.0.1:8000/api/v1/health

---

## 3. Run Tests

```powershell
pytest
```

For verbose output with coverage:

```powershell
pytest -v --tb=long
```

---

## 4. Chrome Extension Setup

### 4.1 Load Extension in Developer Mode

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select the `extension/` folder from the project root
5. The PII-Shield icon (🛡️) appears in your toolbar

### 4.2 Verify Connection

1. Click the PII-Shield icon in the toolbar
2. The popup should show **"Backend connected"** if the FastAPI server is running
3. If it shows **"Backend offline"**, start the backend (step 2.5)

---

## 5. Dashboard Setup (Optional — Phase 3)

```powershell
cd dashboard
npm install
npm run dev
```

The dashboard runs at http://localhost:5173.

---

## 6. Project Commands Reference

| Command | Description |
|---|---|
| `uvicorn backend.main:app --reload` | Start backend with hot-reload |
| `pytest` | Run all tests |
| `pytest -v` | Run tests with verbose output |
| `pytest tests/test_detector.py` | Run specific test file |
| `ruff check backend/ tests/` | Lint Python code |
| `ruff format backend/ tests/` | Format Python code |

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'backend'"

Make sure you're running commands from the project root (`PII-Shield/`), not from inside the `backend/` directory.

### "spacy.load() error: Can't find model 'en_core_web_lg'"

Run `python -m spacy download en_core_web_lg` to install the model.

### Extension shows "Backend offline"

1. Ensure the FastAPI backend is running on port 8000
2. Check that no firewall is blocking localhost connections
3. Try accessing http://127.0.0.1:8000/api/v1/health directly in your browser

### PowerShell execution policy error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
