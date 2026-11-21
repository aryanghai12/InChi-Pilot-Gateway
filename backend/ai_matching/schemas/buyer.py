"""
Buyer Requirement Schemas.

Defines BuyerRequirementInput, MandatoryCriteriaInput, and PreferenceCriteriaInput schemas.
Mandatory criteria and preferences are structurally separate (MVP_FEATURES M5-AC1).

Field names follow the demand schema owned by Vishal (C6) in
database/apps/demand/models.py (RequirementEligibilityCriterion,
RequirementPreference, RequirementEvidenceCriterion, BuyerRequirementVersion).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2–3. Contract is PROPOSED (docs/ai/MATCHING_CONTRACT.md).

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-04 (mandatory eligibility criteria and unknown handling).
# criterion_key / operator / value are carried as data exactly as stored; the
# engine does not define which keys or operators exist. Their evaluation
# semantics are Week 4 work and need Gate 2 approval.
# PENDING DECISION: D-05 (preference weights) — weight_key is a reference only;
# no weight values travel in the requirement.
"""

from pydantic import Field

from ai_matching.core.constants import MAX_CRITERIA_PER_REQUIREMENT
from ai_matching.schemas.common import (
    BoundedJsonObject,
    Code,
    ContractModel,
    Identifier,
    LongText,
    PositiveDecimal,
    ShortText,
)


class MandatoryCriteriaInput(ContractModel):
    """One mandatory (hard-gate) criterion. Mirrors RequirementEligibilityCriterion."""

    criterion_key: Identifier
    operator: Identifier
    value: BoundedJsonObject = Field(default_factory=dict)
    unknown_policy: Code = ""


class PreferenceCriteriaInput(ContractModel):
    """One weighted preference. Mirrors RequirementPreference."""

    preference_key: Identifier
    value: BoundedJsonObject = Field(default_factory=dict)
    weight_key: Code = ""


class EvidenceCriterionInput(ContractModel):
    """Required or preferred evidence. Mirrors RequirementEvidenceCriterion."""

    evidence_type: Identifier
    classification: Code = Field(description="'mandatory' or 'preferred' as stored by C6.")


class BuyerRequirementInput(ContractModel):
    """A specific, immutable version of a buyer requirement."""

    requirement_id: Identifier
    requirement_version: int = Field(ge=1)
    title: ShortText = ""
    product_category: Code = ""
    specification_text: LongText = ""
    target_market: Code = ""

    quantity_value: PositiveDecimal | None = None
    quantity_unit: Code = ""
    target_price_min: PositiveDecimal | None = None
    target_price_max: PositiveDecimal | None = None
    currency_code: Code = ""
    price_basis: Code = ""
    delivery_country: Code = ""
    required_lead_time_value: int | None = Field(default=None, gt=0)
    required_lead_time_unit: Code = ""

    mandatory_criteria: list[MandatoryCriteriaInput] = Field(
        default_factory=list, max_length=MAX_CRITERIA_PER_REQUIREMENT
    )
    preference_criteria: list[PreferenceCriteriaInput] = Field(
        default_factory=list, max_length=MAX_CRITERIA_PER_REQUIREMENT
    )
    evidence_criteria: list[EvidenceCriterionInput] = Field(
        default_factory=list, max_length=MAX_CRITERIA_PER_REQUIREMENT
    )
