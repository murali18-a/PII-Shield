"""
PII-Shield — Sanitize Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
POST /api/v1/sanitize — Detect PII and return sanitised text with placeholders.

This is the primary endpoint for the Chrome extension:
  1. Detect PII via regex + Presidio
  2. Apply policy decisions (REDACT / WARN / BLOCK)
  3. Replace detected PII with typed placeholders
  4. Store the mapping in-memory for later restoration
  5. Return the sanitised text, session_id, and metadata
"""

import time

from fastapi import APIRouter, HTTPException

from backend.api.schemas import (
    SanitizeRequest,
    SanitizeResponse,
    DetectionItem,
)
from backend.engine.detector import Detector
from backend.engine.redactor import Redactor
from backend.policy.rules import PolicyEngine, Action

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


@router.post("/sanitize", response_model=SanitizeResponse)
async def sanitize_text(request: SanitizeRequest):
    """
    Detect PII in the submitted text and return a sanitised version
    with deterministic typed placeholders (e.g. [PERSON_1], [EMAIL_ADDRESS_1]).

    The placeholder-to-original mapping is stored only in-memory,
    keyed by the returned session_id. The mapping is NEVER logged or
    included in the response.

    If the policy decision is BLOCK, a 422 is returned and no
    sanitised text is produced.
    """
    start_time = time.perf_counter()

    detector = _get_detector()
    entities = detector.detect(request.text)

    # Evaluate policy decisions
    decisions = _policy_engine.evaluate(request.policy_profile, entities)

    # Check for BLOCK action
    block_decisions = [d for d in decisions if d.action == Action.BLOCK]
    if block_decisions:
        blocked_types = [d.entity.entity_type for d in block_decisions]
        raise HTTPException(
            status_code=422,
            detail={
                "error": "request_blocked",
                "message": (
                    f"Request blocked by '{request.policy_profile}' policy. "
                    f"Blocked entity types: {blocked_types}"
                ),
                "blocked_types": blocked_types,
            },
        )

    # Separate entities to redact vs warn
    redact_entities = [d.entity for d in decisions if d.action == Action.REDACT]
    warn_entities = [d.entity for d in decisions if d.action == Action.WARN]

    # Perform redaction on REDACT entities only
    result = _redactor.redact(request.text, redact_entities)

    # Store mapping in session store
    from backend.main import session_store, audit_logger

    session_id = session_store.create(result.mapping) if result.mapping else "no-pii-detected"

    # Log audit event (privacy-safe: no raw text, no mapping)
    all_entity_types = [d.entity.entity_type for d in decisions]
    if decisions:
        overall_action = "REDACT" if redact_entities else "WARN"
        audit_logger.log_redaction(
            entity_types=all_entity_types,
            entity_count=len(decisions),
            policy_profile=request.policy_profile,
            action=overall_action,
        )

    # Build detection items for response
    detection_items: list[DetectionItem] = []

    # Add redacted entities with their placeholders
    decision_map = {(d.entity.start, d.entity.end): d for d in decisions}
    for info in result.placeholders:
        key = (info.original_start, info.original_end)
        d = decision_map.get(key)
        detection_items.append(DetectionItem(
            entity_type=info.entity_type,
            placeholder=info.placeholder,
            start=info.original_start,
            end=info.original_end,
            score=info.score,
            source=info.source,
            action="REDACT",
            reason=d.reason if d else "Redacted by policy",
        ))

    # Add warned entities (not redacted, but flagged)
    for entity in warn_entities:
        key = (entity.start, entity.end)
        d = decision_map.get(key)
        detection_items.append(DetectionItem(
            entity_type=entity.entity_type,
            placeholder="",  # Not redacted
            start=entity.start,
            end=entity.end,
            score=entity.score,
            source=entity.source,
            action="WARN",
            reason=d.reason if d else "Flagged for review",
        ))

    categories = sorted(set(d.entity.entity_type for d in decisions))

    # Determine overall action
    actions = {d.action for d in decisions}
    if Action.REDACT in actions:
        overall = "REDACT"
    elif Action.WARN in actions:
        overall = "WARN"
    else:
        overall = "PASS"

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return SanitizeResponse(
        sanitized_text=result.sanitized_text,
        session_id=session_id,
        detections=detection_items,
        categories_found=categories,
        overall_action=overall,
        total_detections=len(detection_items),
        processing_time_ms=elapsed_ms,
    )
