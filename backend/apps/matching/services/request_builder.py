"""
Matching Request Builder.

Assembles and validates the MatchingRequestPayload sent to the FastAPI engine
from a buyer requirement version and the candidate payloads prepared by
supplier_selector.py. Validation here is a fast pre-flight check; the engine's
Pydantic schemas remain the authority on the contract.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Week 3 implementation.

NOTE ON ARCHITECTURE & DECISIONS:
# The buyer-requirement models live in database/apps/demand/ (Vishal, C6) and are
# not yet part of the backend project. Until they are merged, callers construct
# BuyerRequirementPayload directly; a model adapter will be added after the merge.
# The requirement must be gated as matching-ready by the API layer (Abhishek, C5;
# M5-AC2) before this builder is called — this module does not decide readiness.
"""

from __future__ import annotations

from collections.abc import Sequence

from apps.matching.exceptions.matching_exceptions import InvalidMatchingPayloadError
from apps.matching.schemas.matching_request import (
    BuyerRequirementPayload,
    MatchingRequestPayload,
    SupplierCandidatePayload,
)

# Must equal ai_matching.core.constants.MAX_CANDIDATES_PER_REQUEST (checked by test_contract.py).
MAX_CANDIDATES_PER_REQUEST = 1000


def build_matching_request(
    requirement: BuyerRequirementPayload,
    candidates: Sequence[SupplierCandidatePayload],
    criteria_version: str,
    correlation_id: str = "",
) -> MatchingRequestPayload:
    """Build a self-contained, versioned matching request (M6-AC6)."""
    if not requirement.requirement_id:
        raise InvalidMatchingPayloadError("Requirement ID is required.")
    if requirement.requirement_version < 1:
        raise InvalidMatchingPayloadError("Requirement version must be 1 or greater.")
    if not criteria_version or not criteria_version.strip():
        raise InvalidMatchingPayloadError("Criteria version is required so the run can be traced.")
    if len(candidates) > MAX_CANDIDATES_PER_REQUEST:
        raise InvalidMatchingPayloadError(
            f"Too many candidates ({len(candidates)}); the engine accepts at most {MAX_CANDIDATES_PER_REQUEST}."
        )
    ids = [candidate.candidate_id for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise InvalidMatchingPayloadError("Candidate IDs must be unique within a request.")

    return MatchingRequestPayload(
        criteria_version=criteria_version.strip(),
        requirement=requirement,
        candidates=tuple(candidates),
        correlation_id=correlation_id or "",
    )
