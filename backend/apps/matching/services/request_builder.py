"""
Matching Request Builder.

Assembles and validates the MatchingRequestPayload sent to the FastAPI engine
from a buyer requirement and the candidate payloads prepared by
supplier_selector.py. Validation here is a fast pre-flight check; the engine's
Pydantic schemas remain the authority on the contract.

requirement_payload_from_model() adapts the backend BuyerRequirement model
(apps.demand, owned by Abhishek/Vishal) READ-ONLY. Its criteria are free JSON
lists; the adapter maps each entry without inventing rules:

* {"criterion_key", "operator", "value"} entries are passed through as
  structured criteria (comparison vocabulary, docs/ai/MATCHING_CONTRACT.md §6).
* Anything else — e.g. the frontend's {"id", "name", "type"} free-text entries —
  becomes a "manual_review" criterion. The engine never passes it: candidates are
  reported as insufficient data until a reviewer checks the criterion (M6-AC2).
* Free-text preferences become unscored preferences (no operator, no weight).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Implemented.

NOTE ON ARCHITECTURE & DECISIONS:
# The requirement must be matching-ready (M5-AC2). matching_service.py checks it
# defensively; the API layer (Abhishek, C5) remains the primary gate.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from apps.matching.exceptions.matching_exceptions import InvalidMatchingPayloadError
from apps.matching.schemas.matching_request import (
    BuyerRequirementPayload,
    EvidenceCriterionPayload,
    MandatoryCriteriaPayload,
    MatchingRequestPayload,
    PreferenceCriteriaPayload,
    SupplierCandidatePayload,
)

# Must equal the engine constants (checked by test_contract.py).
MAX_CANDIDATES_PER_REQUEST = 1000
MAX_LONG_TEXT_LENGTH = 5000
MANUAL_REVIEW_OPERATOR = "manual_review"
# Free-text criteria are display-only; capped so they stay within the engine's
# MAX_CRITERION_VALUE_CHARS bound (ai_matching/core/constants.py).
MAX_FREE_TEXT_CHARS = 500


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


# ---------------------------------------------------------------------------
# Adapter: apps.demand.models.BuyerRequirement -> BuyerRequirementPayload
# ---------------------------------------------------------------------------


def _entry_text(entry: Any) -> str:
    """Display text of a free-text entry, capped (the engine only shows the first 200 characters)."""
    if isinstance(entry, dict):
        for key in ("name", "text", "description", "document_name", "label"):
            if isinstance(entry.get(key), str) and entry[key].strip():
                return entry[key].strip()[:MAX_FREE_TEXT_CHARS]
        return ""
    return str(entry).strip()[:MAX_FREE_TEXT_CHARS] if entry is not None else ""


def _mandatory_criteria(entries: Any) -> tuple[MandatoryCriteriaPayload, ...]:
    result = []
    for i, entry in enumerate(entries or []):
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("criterion_key"), str)
            and isinstance(entry.get("operator"), str)
            and isinstance(entry.get("value"), dict)
        ):
            result.append(MandatoryCriteriaPayload(
                criterion_key=entry["criterion_key"],
                operator=entry["operator"],
                value=entry["value"],
                unknown_policy=str(entry.get("unknown_policy", "")),
            ))
        else:
            result.append(MandatoryCriteriaPayload(
                criterion_key=f"manual_review_{i + 1}",
                operator=MANUAL_REVIEW_OPERATOR,
                value={"text": _entry_text(entry)},
            ))
    return tuple(result)


def _preferences(entries: Any) -> tuple[PreferenceCriteriaPayload, ...]:
    result = []
    for i, entry in enumerate(entries or []):
        if isinstance(entry, dict) and isinstance(entry.get("preference_key"), str) and isinstance(entry.get("value"), dict):
            result.append(PreferenceCriteriaPayload(
                preference_key=entry["preference_key"],
                value=entry["value"],
                weight_key=str(entry.get("weight_key", "")),
            ))
        else:
            # Free text: carried for transparency, never scored.
            result.append(PreferenceCriteriaPayload(preference_key=f"free_text_{i + 1}", value={"text": _entry_text(entry)}))
    return tuple(result)


def _evidence(entries: Any) -> tuple[EvidenceCriterionPayload, ...]:
    result = []
    for entry in entries or []:
        if isinstance(entry, dict):
            evidence_type = entry.get("evidence_type") or entry.get("document_type") or entry.get("document_name")
            if "classification" in entry:
                classification = str(entry["classification"])
            else:
                classification = "preferred" if entry.get("is_mandatory") is False else "mandatory"
        else:
            evidence_type, classification = entry, "mandatory"
        if isinstance(evidence_type, str) and evidence_type.strip():
            result.append(EvidenceCriterionPayload(evidence_type=evidence_type.strip(), classification=classification))
    return tuple(result)


def requirement_payload_from_model(requirement) -> BuyerRequirementPayload:
    """Map a BuyerRequirement instance (read-only) to the engine payload."""
    specification = requirement.product_specifications or ""
    if len(specification) > MAX_LONG_TEXT_LENGTH:
        raise InvalidMatchingPayloadError(
            f"Product specifications exceed {MAX_LONG_TEXT_LENGTH} characters and cannot be matched."
        )
    return BuyerRequirementPayload(
        requirement_id=str(requirement.id),
        requirement_version=int(requirement.version),
        title=requirement.requirement_title or "",
        product_category=requirement.product_category or "",
        specification_text=specification,
        target_market=requirement.target_market or "",
        quantity_value=requirement.quantity_value,
        quantity_unit=requirement.quantity_unit or "",
        target_price_min=requirement.target_price_min,
        target_price_max=requirement.target_price_max,
        currency_code=requirement.currency_code or "",
        price_basis=requirement.price_basis or "",
        # delivery_location is free text (port/city); no country is derived from it.
        delivery_country="",
        required_lead_time_value=requirement.required_lead_time_value,
        required_lead_time_unit=requirement.required_lead_time_unit or "",
        mandatory_criteria=_mandatory_criteria(requirement.mandatory_criteria),
        preference_criteria=_preferences(requirement.preferred_criteria),
        evidence_criteria=_evidence(requirement.required_evidence),
    )
