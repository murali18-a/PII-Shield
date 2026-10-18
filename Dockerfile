FROM python:3.11-slim

LABEL maintainer="PII-Shield Contributors"
LABEL description="Local-first privacy guardrail for LLM interactions"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Copy application code
COPY backend/ backend/
COPY data/ data/
COPY pyproject.toml .

# Non-root user for security
RUN useradd --create-home --no-log-init appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
