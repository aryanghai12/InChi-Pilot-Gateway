"""
Matching Request Payload Schemas.

Represents data payloads dispatched from Django to the FastAPI matching engine:
MatchingRequestPayload, BuyerRequirementPayload, SupplierCandidatePayload,
MandatoryCriteriaPayload, PreferenceCriteriaPayload, EvidenceCriterionPayload
and EvidencePayload.

Plain dataclasses (standard library only) so the Django process needs no extra
dependency. Keys match the engine's Pydantic schemas in backend/ai_matching/schemas/
exactly; apps/matching/tests/test_contract.py checks that the two sides agree.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Week 2–3. Contract is PROPOSED (docs/ai/MATCHING_CONTRACT.md).

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-04 (mandatory eligibility criteria) — criteria are carried
#   as stored data; no criterion keys or operators are defined here.
# PENDING DECISION: D-05 (weights) — only weight keys travel, never weight values.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any

# Must equal ai_matching.core.constants.CONTRACT_VERSION (checked by test_contract.py).
CONTRACT_VERSION = "0.2.0-proposed"


def _jsonable(value: Any) -> Any:
    """Decimals travel as strings so no precision is lost; None stays None (unknown)."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


@dataclass(frozen=True)
class MandatoryCriteriaPayload:
    criterion_key: str
    operator: str
    value: dict[str, Any] = field(default_factory=dict)
    unknown_policy: str = ""


@dataclass(frozen=True)
class PreferenceCriteriaPayload:
    preference_key: str
    value: dict[str, Any] = field(default_factory=dict)
    weight_key: str = ""


@dataclass(frozen=True)
class EvidenceCriterionPayload:
    evidence_type: str
    classification: str


@dataclass(frozen=True)
class BuyerRequirementPayload:
    requirement_id: str
    requirement_version: int
    title: str = ""
    product_category: str = ""
    specification_text: str = ""
    target_market: str = ""
    quantity_value: Decimal | None = None
    quantity_unit: str = ""
    target_price_min: Decimal | None = None
    target_price_max: Decimal | None = None
    currency_code: str = ""
    price_basis: str = ""
    delivery_country: str = ""
    required_lead_time_value: int | None = None
    required_lead_time_unit: str = ""
    mandatory_criteria: tuple[MandatoryCriteriaPayload, ...] = ()
    preference_criteria: tuple[PreferenceCriteriaPayload, ...] = ()
    evidence_criteria: tuple[EvidenceCriterionPayload, ...] = ()


@dataclass(frozen=True)
class EvidencePayload:
    document_type: str
    presence_status: str = ""
    review_status: str = ""
    expiry_date: str | None = None


@dataclass(frozen=True)
class SupplierCandidatePayload:
    candidate_id: str
    supplier_id: str
    product_name: str
    supplier_name: str = ""
    supplier_country: str = ""
    supplier_record_status: str = ""
    supplier_industry_description: str = ""
    readiness_status: str | None = None
    product_category: str = ""
    description: str = ""
    specifications: str = ""
    origin: str = ""
    moq_value: Decimal | None = None
    moq_unit: str = ""
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    currency: str = ""
    price_basis: str = ""
    capacity_quantity: Decimal | None = None
    capacity_unit: str = ""
    capacity_period: str = ""
    lead_time_value: int | None = None
    lead_time_unit: str = ""
    evidence: tuple[EvidencePayload, ...] = ()


@dataclass(frozen=True)
class MatchingRequestPayload:
    criteria_version: str
    requirement: BuyerRequirementPayload
    candidates: tuple[SupplierCandidatePayload, ...]
    correlation_id: str = ""
    contract_version: str = CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable body for POST /match."""
        return _jsonable(asdict(self))
