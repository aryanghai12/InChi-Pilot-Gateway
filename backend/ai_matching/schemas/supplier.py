"""
Supplier Candidate Schemas.

Defines SupplierCandidateInput (one product together with its supplier, per
MVP_FEATURES M6 "the candidate is a product together with its supplier") and
EvidenceInput (evidence metadata only, D-10).

Field names follow backend/apps/registry/models.py so the Django request
builder can map them one-to-one.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2–3. Contract is PROPOSED (docs/ai/MATCHING_CONTRACT.md).

NOTE ON ARCHITECTURE & DECISIONS:
# Product has no structured certifications field yet; certifications can only be
# inferred from evidence metadata (document_type). Raised with Vishal (C6).
# readiness_status is optional until the M4 readiness module exists.
"""

from typing import Annotated

from pydantic import Field

from ai_matching.core.constants import MAX_EVIDENCE_ITEMS_PER_CANDIDATE
from ai_matching.schemas.common import (
    Code,
    ContractModel,
    Identifier,
    LongText,
    PositiveDecimal,
    ShortText,
)


class EvidenceInput(ContractModel):
    """Evidence metadata attached to a supplier or product. "Provided" is not "verified" (M2-AC5)."""

    document_type: Code
    presence_status: Code = ""
    review_status: Code = ""
    expiry_date: str | None = Field(default=None, max_length=10, description="ISO date YYYY-MM-DD")


class SupplierCandidateInput(ContractModel):
    """A matching candidate: one product with its supplier's attributes."""

    candidate_id: Identifier = Field(description="Product ID (UUID string).")
    supplier_id: Identifier
    supplier_name: ShortText = ""
    supplier_country: Code = Field(default="", description="Supplier country of registration.")
    supplier_record_status: Code = ""
    supplier_industry_description: LongText = ""
    readiness_status: Code | None = Field(default=None, description="Reviewed readiness outcome; None if unknown.")

    product_name: ShortText
    product_category: Code = ""
    description: LongText = ""
    specifications: LongText = ""
    origin: Code = ""

    moq_value: PositiveDecimal | None = None
    moq_unit: Code = ""
    price_min: PositiveDecimal | None = None
    price_max: PositiveDecimal | None = None
    currency: Code = ""
    price_basis: Code = ""
    capacity_quantity: PositiveDecimal | None = None
    capacity_unit: Code = ""
    capacity_period: Code = ""
    lead_time_value: Annotated[int, Field(gt=0)] | None = None
    lead_time_unit: Code = ""

    evidence: list[EvidenceInput] = Field(default_factory=list, max_length=MAX_EVIDENCE_ITEMS_PER_CANDIDATE)
