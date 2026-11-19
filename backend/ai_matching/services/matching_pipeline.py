"""
Matching Pipeline Orchestrator.

Engine-side stages (ARCHITECTURE.md §6.2; Django performs data collection and
persistence around them):

1. Data preparation & normalisation ...... implemented (services/preprocessing.py)
2. Mandatory eligibility (hard gates) .... PENDING D-04 / Gate 2 (Week 4)
3. Semantic matching (embeddings) ........ PENDING D-11 (Week 5)
4. Cosine similarity ..................... implemented as a utility (services/similarity.py)
5. Hybrid scoring ........................ PENDING D-05 (Week 4/5)
6. Ranking ............................... PENDING (Week 5)
7. Explainability ........................ PENDING (Week 5)
8. Structured response ................... contract defined (schemas/result.py)

run_pipeline() executes the implemented stages and then raises
StageNotAvailableError at the first stage that has no approved rules or model.
It never returns partial results (MVP_FEATURES M6-AC5).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 3. Stages 2–7 intentionally not implemented.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_matching.core.exceptions import StageNotAvailableError
from ai_matching.core.logging import get_logger, log_stage
from ai_matching.schemas.matching import MatchRequest
from ai_matching.schemas.result import MatchResponse
from ai_matching.services.preprocessing import (
    PreparedCandidate,
    PreparedRequirement,
    prepare_candidate,
    prepare_requirement,
)

logger = get_logger("pipeline")


@dataclass(frozen=True)
class PreparedInputs:
    """Output of Stage 1, the input to every later stage."""

    correlation_id: str
    criteria_version: str
    requirement: PreparedRequirement
    candidates: tuple[PreparedCandidate, ...]


def prepare_inputs(request: MatchRequest) -> PreparedInputs:
    """Stage 1: normalise the requirement and every candidate, collecting quality issues."""
    prepared = PreparedInputs(
        correlation_id=request.correlation_id,
        criteria_version=request.criteria_version,
        requirement=prepare_requirement(request.requirement),
        candidates=tuple(prepare_candidate(candidate) for candidate in request.candidates),
    )
    log_stage(
        logger,
        "preprocessing",
        request.correlation_id,
        candidates=len(prepared.candidates),
        quality_issues=sum(len(c.quality_issues) for c in prepared.candidates),
    )
    return prepared


def run_pipeline(request: MatchRequest) -> MatchResponse:
    """Run the matching pipeline. Raises StageNotAvailableError until Stage 2 is approved."""
    prepare_inputs(request)
    log_stage(logger, "eligibility_unavailable", request.correlation_id)
    raise StageNotAvailableError(
        stage="eligibility",
        reason="mandatory eligibility criteria are pending BNCS approval (D-04, Gate 2).",
    )
