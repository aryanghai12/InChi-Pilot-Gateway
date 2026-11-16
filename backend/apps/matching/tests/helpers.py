"""
Synthetic payload helpers for Django matching integration tests.

All values are synthetic. Criterion keys mirror the demand seed data shape only;
they are not approved criteria (D-04).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
"""

from __future__ import annotations

import copy
from decimal import Decimal

from apps.matching.schemas.matching_request import (
    CONTRACT_VERSION,
    BuyerRequirementPayload,
    EvidenceCriterionPayload,
    EvidencePayload,
    MandatoryCriteriaPayload,
    PreferenceCriteriaPayload,
    SupplierCandidatePayload,
)


def requirement(**overrides) -> BuyerRequirementPayload:
    fields = dict(
        requirement_id="00000000-0000-4000-8000-000000000004",
        requirement_version=1,
        title="Synthetic demand requirement 004",
        product_category="ELECTRONICS",
        specification_text="Synthetic electronic components for test matching only.",
        target_market="IN",
        quantity_value=Decimal(2000),
        quantity_unit="KG",
        currency_code="USD",
        delivery_country="CN",
        required_lead_time_value=34,
        required_lead_time_unit="days",
        mandatory_criteria=(MandatoryCriteriaPayload("origin_country", "equals", {"value": "IN"}, "exclude"),),
        preference_criteria=(PreferenceCriteriaPayload("shorter_lead_time", {"preferred_max_days": 45}, "lead_time"),),
        evidence_criteria=(EvidenceCriterionPayload("QUALITY_CERTIFICATE", "mandatory"),),
    )
    fields.update(overrides)
    return BuyerRequirementPayload(**fields)


def candidate(index: int = 1, **overrides) -> SupplierCandidatePayload:
    fields = dict(
        candidate_id=f"11111111-1111-4111-8111-{index:012d}",
        supplier_id=f"22222222-2222-4222-8222-{index:012d}",
        product_name="Synthetic Circuit Board",
        supplier_name="Synthetic Supplier",
        supplier_country="IN",
        supplier_record_status="complete",
        product_category="Electronic Goods",
        description="Synthetic printed circuit board.",
        origin="India",
        moq_value=Decimal("100.00"),
        moq_unit="PIECES",
        price_min=Decimal("10.00"),
        price_max=Decimal("20.00"),
        currency="USD",
        lead_time_value=30,
        lead_time_unit="DAYS",
        evidence=(EvidencePayload("QUALITY_CERTIFICATE", "provided", "unreviewed"),),
    )
    fields.update(overrides)
    return SupplierCandidatePayload(**fields)


_RANKED = {
    "candidate_id": "11111111-1111-4111-8111-000000000001",
    "supplier_id": "22222222-2222-4222-8222-000000000001",
    "eligibility": "eligible",
    "rank": 1,
    "criteria": [{"criterion_key": "origin_country", "outcome": "pass", "detail": ""}],
    "scores": {"rule_score": 0.5, "semantic_score": 0.5, "hybrid_score": 0.5, "contributions": []},
    "explanation": ["Synthetic explanation line."],
    "warnings": [],
    "readiness_status": None,
}


def engine_success_response(**overrides) -> dict:
    """A synthetic, contract-shaped success body. Score values are placeholders, not weights."""
    body = {
        "contract_version": CONTRACT_VERSION,
        "status": "completed",
        "mode": "hybrid",
        "requirement_id": "00000000-0000-4000-8000-000000000004",
        "requirement_version": 1,
        "criteria_version": "criteria-v1",
        "embedding_model_id": "test-double",
        "embedding_text_template_version": "embedding-text-v0",
        "ranked": [copy.deepcopy(_RANKED)],
        "excluded": [],
        "insufficient_data": [],
        "metrics": {
            "candidates_received": 1,
            "candidates_eligible": 1,
            "candidates_excluded": 0,
            "candidates_insufficient_data": 0,
        },
    }
    body.update(overrides)
    return body
