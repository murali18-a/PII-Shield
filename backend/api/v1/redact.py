"""
PII-Shield — Redact Endpoint (backward compat)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
POST /api/v1/redact — Detect and redact PII from user text.

This endpoint mirrors /api/v1/sanitize with a simpler response schema
for backward compatibility.
"""

import time

from fastapi import APIRouter

from backend.api.schemas import (
    RedactRequest,
    RedactResponse,
    RedactStats,
    DetectionItem,
)
from backend.engine.detector import Detector
from backend.engine.redactor import Redactor
from backend.policy.rules import PolicyEngine

router = APIRouter()

_detector: Detector | None = None
_redactor = Redactor()
_policy_engine = PolicyEngine()


def _get_detector() -> Detector:
    global _detector
    if _detector is None:
        from backend.main import presidio_wrapper
        _detector = Detector(presidio=presidio_wrapper)
    return _detector


@router.post("/redact", response_model=RedactResponse)
async def redact_text(request: RedactRequest):
    """
    Detect PII in the submitted text and return a sanitised version
    with deterministic placeholders.

    The placeholder-to-original mapping is stored only in-memory,
    keyed by the returned session_id.
    """
    start_time = time.perf_counter()

    detector = _get_detector()
    entities = detector.detect(request.text)

    # Apply policy filter (only REDACT action entities)
    filtered = _policy_engine.apply(request.policy_profile, entities)

    # Redact
    result = _redactor.redact(request.text, filtered)

    # Store mapping
    from backend.main import session_store

    session_id = session_store.create(result.mapping) if result.mapping else "no-pii-detected"

    # Build detection items
    detection_items: list[DetectionItem] = []
    for info in result.placeholders:
        detection_items.append(DetectionItem(
            entity_type=info.entity_type,
            placeholder=info.placeholder,
            start=info.original_start,
            end=info.original_end,
            score=info.score,
            source=info.source,
        ))

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return RedactResponse(
        sanitized_text=result.sanitized_text,
        session_id=session_id,
        detections=detection_items,
        stats=RedactStats(
            total_entities=len(detection_items),
            processing_time_ms=elapsed_ms,
        ),
    )
