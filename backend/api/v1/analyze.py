"""
PII-Shield — Analyze Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
POST /api/v1/analyze — Detect PII in text and return categories, scores,
and policy decisions without redacting.
"""

import time

from fastapi import APIRouter, HTTPException

from backend.api.schemas import AnalyzeRequest, AnalyzeResponse, DetectionItem
from backend.engine.detector import Detector
from backend.policy.rules import PolicyEngine, Action

router = APIRouter()

# Lazy-initialised: the actual Presidio reference comes from main.py
_detector: Detector | None = None
_policy_engine = PolicyEngine()


def _get_detector() -> Detector:
    """Get or create the detector, using the global Presidio wrapper."""
    global _detector
    if _detector is None:
        from backend.main import presidio_wrapper
        _detector = Detector(presidio=presidio_wrapper)
    return _detector


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """
    Detect PII in the submitted text and return categories,
    confidence estimates, and policy decisions.

    No redaction or sanitization is performed.
    No text is stored or logged.
    """
    start_time = time.perf_counter()

    detector = _get_detector()
    entities = detector.detect(request.text)

    # Evaluate policy decisions
    decisions = _policy_engine.evaluate(request.policy_profile, entities)

    # Build detection items
    detection_items: list[DetectionItem] = []
    for d in decisions:
        detection_items.append(DetectionItem(
            entity_type=d.entity.entity_type,
            placeholder=f"[{d.entity.entity_type}_0]",  # Preview placeholder
            start=d.entity.start,
            end=d.entity.end,
            score=d.entity.score,
            source=d.entity.source,
            action=d.action.value,
            reason=d.reason,
        ))

    categories = sorted(set(d.entity.entity_type for d in decisions))

    # Determine overall action (BLOCK > REDACT > WARN)
    actions = {d.action for d in decisions}
    if Action.BLOCK in actions:
        overall = "BLOCK"
    elif Action.REDACT in actions:
        overall = "REDACT"
    elif Action.WARN in actions:
        overall = "WARN"
    else:
        overall = "PASS"

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return AnalyzeResponse(
        detections=detection_items,
        categories_found=categories,
        overall_action=overall,
        total_detections=len(detection_items),
        processing_time_ms=elapsed_ms,
    )
