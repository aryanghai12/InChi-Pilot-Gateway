"""
Matching API Endpoints.

Defines POST /match for dispatching a buyer requirement version and its
candidate pool to the matching pipeline. The route is thin: validation is done
by the MatchRequest schema, work by services/matching_pipeline.py, and error
mapping by the exception handlers in main.py.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 implementation. Until D-04 is approved every call ends with a
503 "stage_not_available" error envelope; no results are produced.
"""

from fastapi import APIRouter, Depends

from ai_matching.api.dependencies import correlation_id_dependency
from ai_matching.schemas.matching import MatchRequest
from ai_matching.schemas.result import MatchResponse
from ai_matching.services.matching_pipeline import run_pipeline

router = APIRouter(tags=["matching"])


@router.post("/match", response_model=MatchResponse)
def match(request: MatchRequest, correlation_id: str = Depends(correlation_id_dependency)) -> MatchResponse:
    if not request.correlation_id:
        request = request.model_copy(update={"correlation_id": correlation_id})
    return run_pipeline(request)
