"""
Matching Result and Scoring Schemas.

Defines CriterionResult (EligibilityDetail), ScoreBreakdown, MatchWarning,
SupplierRankResult, PipelineMetrics and MatchResponse — the body returned by a
successful POST /match. Failures never use this model; they return the error
envelope instead, so no partial results can be stored (M6-AC5).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2. Contract is PROPOSED (docs/ai/MATCHING_CONTRACT.md).
The engine cannot produce this response yet: eligibility (D-04), scoring
weights (D-05) and the embedding model (D-11) are pending.

NOTE ON ARCHITECTURE & DECISIONS:
# Score fields are bounded [0, 1] containers only. How they are computed and
# weighted is NOT defined here (D-05). Scores are decision support, never
# certainty (MVP_FEATURES §2).
"""

from typing import Annotated, Literal

from pydantic import Field

from ai_matching.core.constants import (
    CONTRACT_VERSION,
    CriterionOutcome,
    EligibilityOutcome,
    MatchingMode,
    QualityFlag,
    RunStatus,
)
from ai_matching.schemas.common import Code, ContractModel, Identifier, ShortText

UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]


class CriterionResult(ContractModel):
    """Outcome of one mandatory criterion for one candidate (EligibilityDetail)."""

    criterion_key: Identifier
    outcome: CriterionOutcome
    detail: ShortText = ""


class ScoreContribution(ContractModel):
    """Weighted contribution of one preference criterion."""

    preference_key: Identifier
    weight_key: Code = ""
    contribution: float


class ScoreBreakdown(ContractModel):
    """Score components for an eligible candidate (M6-AC3)."""

    rule_score: UnitInterval
    semantic_score: UnitInterval = Field(description="Semantic signal; labelled as such in the UI.")
    hybrid_score: UnitInterval
    contributions: list[ScoreContribution] = Field(default_factory=list)


class MatchWarning(ContractModel):
    """A missing-information or data-quality warning (M6-AC3)."""

    flag: QualityFlag
    field: Code
    message: ShortText


class SupplierRankResult(ContractModel):
    """Per-candidate result. Only eligible candidates carry a rank and scores (M6-AC1)."""

    candidate_id: Identifier
    supplier_id: Identifier
    eligibility: EligibilityOutcome
    rank: int | None = Field(default=None, ge=1)
    criteria: list[CriterionResult] = Field(default_factory=list)
    scores: ScoreBreakdown | None = None
    explanation: list[ShortText] = Field(default_factory=list)
    warnings: list[MatchWarning] = Field(default_factory=list)
    readiness_status: Code | None = None


class PipelineMetrics(ContractModel):
    """Counts only — no payload content."""

    candidates_received: int = Field(ge=0)
    candidates_eligible: int = Field(ge=0)
    candidates_excluded: int = Field(ge=0)
    candidates_insufficient_data: int = Field(ge=0)


class MatchResponse(ContractModel):
    """Successful run. Ranked, excluded and insufficient-data lists are separate (M6-AC4)."""

    contract_version: Literal[CONTRACT_VERSION]  # type: ignore[valid-type]
    status: Literal[RunStatus.COMPLETED]
    mode: MatchingMode
    requirement_id: Identifier
    requirement_version: int = Field(ge=1)
    criteria_version: Identifier
    embedding_model_id: Code = Field(description="Model ID and version used, per M6-AC6.")
    embedding_text_template_version: Code
    ranked: list[SupplierRankResult] = Field(default_factory=list)
    excluded: list[SupplierRankResult] = Field(default_factory=list)
    insufficient_data: list[SupplierRankResult] = Field(default_factory=list)
    metrics: PipelineMetrics
