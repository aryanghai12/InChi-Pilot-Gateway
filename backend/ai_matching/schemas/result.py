"""
Matching Result and Scoring Schemas.

Defines CriterionResult (EligibilityDetail), ScoreContribution, ScoreBreakdown,
MatchWarning, SupplierRankResult, PipelineMetrics and MatchResponse — the body
returned by a successful POST /match. Failures never use this model; they
return the error envelope instead, so no partial results can be stored (M6-AC5).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Contract 0.2.0-proposed (docs/ai/MATCHING_CONTRACT.md).

NOTE ON ARCHITECTURE & DECISIONS:
# Scores are decision support, never certainty (MVP_FEATURES §2). How they are
# weighted comes from the versioned scoring configuration (D-05).
"""

from typing import Annotated, Literal

from pydantic import Field

from ai_matching.core.constants import (
    CONTRACT_VERSION,
    ConfigurationStatus,
    CriterionOutcome,
    EligibilityOutcome,
    MatchingMode,
    PreferenceOutcome,
    QualityFlag,
    RunStatus,
)
from ai_matching.schemas.common import Code, ContractModel, Identifier, ShortText

UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]
Cosine = Annotated[float, Field(ge=-1.0, le=1.0)]


class CriterionResult(ContractModel):
    """Outcome of one mandatory criterion for one candidate (EligibilityDetail)."""

    criterion_key: Identifier
    operator: Code = ""
    outcome: CriterionOutcome
    detail: ShortText = ""


class ScoreContribution(ContractModel):
    """One preference: its approved weight, outcome and share of the rule score."""

    preference_key: Identifier
    weight_key: Code = ""
    weight: float | None = Field(default=None, ge=0.0)
    outcome: PreferenceOutcome
    contribution: UnitInterval = 0.0
    detail: ShortText = ""


class ScoreBreakdown(ContractModel):
    """Score components for an eligible candidate (M6-AC3)."""

    rule_score: UnitInterval | None = Field(description="None when no preference could be scored.")
    semantic_cosine: Cosine = Field(description="Raw cosine similarity of the embedding texts.")
    semantic_score: UnitInterval = Field(description="Semantic signal; labelled as such in the UI.")
    hybrid_score: UnitInterval
    rule_weight: UnitInterval
    semantic_weight: UnitInterval
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
    configuration_status: ConfigurationStatus
    embedding_model_id: Code = Field(description="Model ID used, per M6-AC6.")
    embedding_text_template_version: Code
    ranked: list[SupplierRankResult] = Field(default_factory=list)
    excluded: list[SupplierRankResult] = Field(default_factory=list)
    insufficient_data: list[SupplierRankResult] = Field(default_factory=list)
    run_warnings: list[ShortText] = Field(default_factory=list)
    metrics: PipelineMetrics
