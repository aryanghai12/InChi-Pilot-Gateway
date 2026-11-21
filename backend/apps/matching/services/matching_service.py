"""
Matching Service Orchestrator.

Coordinates the matching workflow between candidate selection, the AI matching
engine, and result handling:

    requirement (ready) + candidate products
      -> request_builder (requirement adapter + versioned request)
      -> supplier_selector (candidate payloads)
      -> AIEngineClient.match()  (FastAPI engine)
      -> MatchRunOutcome (completed with a validated response, or failed with no results)
      -> result_handler.persist_outcome() when a persister is supplied

run_matching() never raises for engine-side failures: unreachable engine,
timeout, engine error envelope or contract-violating response all become a
FAILED outcome with no results, which the caller stores as a failed run
(MVP_FEATURES M6-AC5). It DOES raise InvalidMatchingPayloadError for caller
errors — requirement not ready (M5-AC2), no criteria version — which are not runs.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Implemented.

NOTE ON ARCHITECTURE & DECISIONS:
# Candidates come from the caller (Vishal's candidate query, C6). The DRF view that
# calls this service, its permissions (policy "match_run") and serializers belong
# to Abhishek (C5). MATCHING_CRITERIA_VERSION names the active scoring
# configuration (ai_matching/criteria/<version>.json).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from apps.matching.exceptions.matching_exceptions import (
    InvalidMatchingPayloadError,
    MatchingEngineError,
    MatchingEngineResponseError,
)
from apps.matching.integrations.ai_engine_client import AIEngineClient
from apps.matching.schemas.matching_response import MatchingResponsePayload
from apps.matching.services import result_handler
from apps.matching.services.request_builder import (
    build_matching_request,
    requirement_payload_from_model,
)
from apps.matching.services.supplier_selector import build_candidate_payloads

logger = logging.getLogger(__name__)

READY_FOR_MATCHING = "ready_for_matching"


@dataclass(frozen=True)
class MatchRunOutcome:
    """Result of one matching attempt. `response` is None exactly when status is 'failed'."""

    status: str
    requirement_id: str
    requirement_version: int
    criteria_version: str
    correlation_id: str
    actor_id: str | None
    started_at: datetime
    finished_at: datetime
    candidates_submitted: int
    response: MatchingResponsePayload | None = None
    error_code: str = ""
    error_message: str = ""
    engine_error_code: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status == "completed"


def _check_ready(requirement) -> None:
    if requirement.requirement_status != READY_FOR_MATCHING:
        raise InvalidMatchingPayloadError("The requirement is not marked ready for matching (M5-AC2).")
    is_ready, reasons = requirement.evaluate_readiness()
    if not is_ready:
        raise InvalidMatchingPayloadError("The requirement has unresolved matching blockers: " + " ".join(reasons))


def run_matching(
    requirement,
    products: Iterable,
    *,
    actor=None,
    criteria_version: str | None = None,
    correlation_id: str = "",
    client: AIEngineClient | None = None,
    readiness_by_supplier: dict[str, str] | None = None,
    persister: result_handler.MatchRunPersister | None = None,
) -> MatchRunOutcome:
    """Run matching for one ready requirement against the supplied candidate products."""
    _check_ready(requirement)
    version = (criteria_version or os.environ.get("MATCHING_CRITERIA_VERSION", "")).strip()
    if not version:
        raise InvalidMatchingPayloadError("No criteria version: set MATCHING_CRITERIA_VERSION or pass one.")

    requirement_payload = requirement_payload_from_model(requirement)
    candidates = build_candidate_payloads(products, readiness_by_supplier)
    request = build_matching_request(requirement_payload, candidates, version, correlation_id)

    started = timezone.now()
    base = {
        "requirement_id": requirement_payload.requirement_id,
        "requirement_version": requirement_payload.requirement_version,
        "criteria_version": version,
        "correlation_id": correlation_id,
        "actor_id": str(actor.id) if getattr(actor, "id", None) else None,
        "started_at": started,
        "candidates_submitted": len(candidates),
    }
    try:
        engine = client or AIEngineClient.from_environment()
        response = engine.match(request)
        outcome = MatchRunOutcome(status="completed", finished_at=timezone.now(), response=response, **base)
    except MatchingEngineError as exc:
        logger.warning("match_run_failed code=%s correlation_id=%s", exc.code, correlation_id or "-")
        outcome = MatchRunOutcome(
            status="failed",
            finished_at=timezone.now(),
            error_code=exc.code,
            error_message=exc.message,
            engine_error_code=exc.engine_code if isinstance(exc, MatchingEngineResponseError) else "",
            **base,
        )

    if persister is not None:
        result_handler.persist_outcome(outcome, persister, actor=actor)
    return outcome
