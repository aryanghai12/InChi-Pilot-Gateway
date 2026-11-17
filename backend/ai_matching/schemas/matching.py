"""
Matching API Schemas.

Defines MatchRequest, the body of POST /match sent by the Django matching
integration layer (backend/apps/matching/services/request_builder.py).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2. Contract is PROPOSED (docs/ai/MATCHING_CONTRACT.md).
"""

from typing import Literal

from pydantic import Field, model_validator

from ai_matching.core.constants import CONTRACT_VERSION, MAX_CANDIDATES_PER_REQUEST
from ai_matching.schemas.buyer import BuyerRequirementInput
from ai_matching.schemas.common import Code, ContractModel, Identifier
from ai_matching.schemas.supplier import SupplierCandidateInput


class MatchRequest(ContractModel):
    """A complete, self-contained matching request. The engine never reads the database."""

    contract_version: Literal[CONTRACT_VERSION]  # type: ignore[valid-type]
    correlation_id: Code = ""
    criteria_version: Identifier = Field(
        description="Version of the matching configuration the criteria come from (M6-AC6)."
    )
    requirement: BuyerRequirementInput
    candidates: list[SupplierCandidateInput] = Field(max_length=MAX_CANDIDATES_PER_REQUEST)

    @model_validator(mode="after")
    def _candidate_ids_unique(self) -> "MatchRequest":
        seen: set[str] = set()
        for candidate in self.candidates:
            if candidate.candidate_id in seen:
                raise ValueError("candidate_id values must be unique within a request.")
            seen.add(candidate.candidate_id)
        return self
