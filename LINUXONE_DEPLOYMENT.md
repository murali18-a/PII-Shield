# PII-Shield — LinuxONE / IBM Z Deployment Guide

> IBM Z Datathon 2026 — "AI Secured: Innovation Without Exposure"

---

## IBM Z Relevance

PII-Shield is designed as a **local-first privacy guardrail**. The architecture
separates two concerns:

1. **Client-side prompt sanitization** — runs in the browser extension,
   communicating with a local FastAPI backend on the user's machine.
2. **Enterprise policy and audit services** — the FastAPI backend can
   optionally be deployed as a centralized service for organizational
   policy enforcement and audit aggregation.

### Why LinuxONE?

IBM LinuxONE (s390x) is purpose-built for workloads requiring:

- **Data privacy at scale**: Hardware-accelerated encryption (CPACF),
  secure key management, and tamper-resistant execution environments.
- **High availability**: 99.999% uptime SLA, ideal for always-on
  privacy policy enforcement.
- **Regulatory compliance**: Certified for PCI DSS, HIPAA, GDPR workloads
  where PII handling must be auditable and controlled.

**Intended deployment**: The PII-Shield backend (FastAPI + detection engine)
runs on LinuxONE as a centralized enterprise privacy gateway. Individual
users run the Chrome extension, which sends prompts to the LinuxONE-hosted
backend instead of `127.0.0.1`. The backend sanitizes text before it
reaches any external LLM, with enterprise-grade audit logging.

---

## Deployment Architecture

```
┌─────────────────────────┐     ┌─────────────────────────────────┐
│ User's Workstation      │     │ IBM LinuxONE (s390x)            │
│                         │     │                                 │
│  Chrome Extension ──────────► │  PII-Shield Backend             │
│  (prompt interception)  │HTTPS│  ├── FastAPI + uvicorn          │
│                         │     │  ├── Detection Engine           │
│                         │     │  ├── Policy Engine              │
│                         │     │  ├── Audit Logger               │
│                         │     │  └── Admin Dashboard            │
└─────────────────────────┘     │                                 │
                                │  Security:                      │
                                │  ├── TLS termination            │
                                │  ├── Authentication (required)  │
                                │  ├── CPACF encryption           │
                                │  └── Audit to persistent DB     │
                                └─────────────────────────────────┘
```

---

## Prerequisites

- Access to an IBM LinuxONE / IBM Z system (s390x architecture)
- Linux distribution: Ubuntu 22.04+, RHEL 9+, or SLES 15+ for s390x
- Python 3.11+ (available in system repos or via pyenv)
- Git

---

## Deployment Steps

### 1. Prepare the System

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git

# RHEL/Fedora
sudo dnf install -y python3 python3-pip git
```

### 2. Clone and Set Up

```bash
git clone https://github.com/murali18-a/PII-Shield.git
cd PII-Shield
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Configure for Network Access

When deploying as a shared service, the backend must bind to a network
interface (not just loopback) and require authentication:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=warning
ALLOWED_ORIGINS=https://your-org-domain.com
```

> **IMPORTANT**: When binding to `0.0.0.0`, you MUST add:
> - TLS termination (nginx/caddy reverse proxy or uvicorn with `--ssl-*`)
> - Authentication middleware
> - Rate limiting
> - Persistent audit storage
>
> These are NOT yet implemented in the current codebase.

### 4. Run with Production Server

```bash
# Development / testing
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Production (with multiple workers)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Verify

```bash
curl http://localhost:8000/health
# {"status":"healthy","version":"0.2.0","presidio_loaded":true,...}

curl -X POST http://localhost:8000/api/v1/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "My SSN is 123-45-6789"}'
# {"sanitized_text":"My SSN is [US_SSN_1]",...}
```

### 6. Run Tests

```bash
pytest tests/ -v
```

---

## Docker Deployment (Optional)

A Dockerfile is provided for containerized deployment:

```dockerfile
# Dockerfile — place in project root
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

COPY backend/ backend/
COPY data/ data/

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t pii-shield .
docker run -p 8000:8000 pii-shield
```

> **Note on s390x**: The base `python:3.11-slim` image supports
> `linux/s390x` via multi-arch builds. spaCy and Presidio have
> pre-built wheels for s390x on Python 3.11+.

---

## What Has Been Verified

| Item | Status |
|------|--------|
| Backend runs on Windows (x86_64) | ✅ Tested, 102 tests pass |
| Backend runs on Linux (x86_64) | ✅ Expected (standard Python stack) |
| Backend runs on Linux (s390x / LinuxONE) | ⬜ Not yet tested — no access |
| Docker build on s390x | ⬜ Not yet tested |
| TLS / Authentication | ⬜ Not implemented |
| Persistent audit storage | ⬜ Schema exists, write path not wired |
| Multi-worker deployment | ⬜ Requires shared session store (Redis) |

---

## What Remains Unverified

1. **No LinuxONE access** was available during development. The deployment
   configuration is prepared and tested locally, but actual s390x
   execution has not been confirmed.
2. **No fabricated benchmarks or screenshots** — this document does not
   claim successful remote deployment.
3. **spaCy/Presidio s390x compatibility**: These packages publish
   `manylinux` wheels that include s390x support on Python 3.11+,
   but we have not verified this firsthand.

---

## Future Work for Enterprise Deployment

1. **Authentication**: Add OAuth2/JWT middleware for multi-user access
2. **TLS**: Configure HTTPS via reverse proxy or uvicorn SSL
3. **Persistent audit**: Wire SQLAlchemy models to a real database
4. **Shared sessions**: Replace in-memory SessionStore with Redis
   for multi-worker deployments
5. **CPACF integration**: Leverage LinuxONE hardware encryption for
   session data at rest
6. **Rate limiting**: Add per-client request throttling
7. **Monitoring**: Prometheus metrics endpoint for operational visibility
