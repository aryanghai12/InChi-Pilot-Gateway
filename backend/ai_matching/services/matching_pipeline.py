"""
Matching Pipeline Orchestrator.

Engine-side stages (ARCHITECTURE.md §6.2; Django performs data collection and
persistence around them):

0. Pre-flight: scoring configuration usable (approved, weights present) and an
   embedding provider configured — otherwise fail before any work.
1. Data preparation & normalisation ...... services/preprocessing.py
2. Mandatory eligibility (hard gates) .... services/eligibility.py
3. Semantic matching (embeddings) ........ services/semantic_matcher.py + providers/
4. Cosine similarity ..................... services/similarity.py
5. Hybrid scoring ........................ services/hybrid_scorer.py
6. Ranking ............................... services/ranking.py
7. Explainability ........................ services/explainability.py
8. Structured response ................... schemas/result.py

Guarantees:
* Eligibility runs before semantics; only ELIGIBLE candidates are embedded,
  scored or ranked, so similarity can never override a mandatory failure (M6-AC1).
* Unknown mandatory data is never a pass (M6-AC2).
* Semantic matching is mandatory: no provider, or any embedding/similarity
  failure, fails the whole run. There is no rules-only fallback (M6-AC5).
* Either a complete MatchResponse is returned or an exception is raised;
  partial results are never returned.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Implemented.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_matching.core.config import EngineSettings
from ai_matching.core.constants import (
    CONTRACT_VERSION,
    EMBEDDING_TEXT_TEMPLATE_VERSION,
    ConfigurationStatus,
    EligibilityOutcome,
    MatchingMode,
    RunStatus,
)
from ai_matching.core.exceptions import StageNotAvailableError
from ai_matching.core.logging import get_logger, log_stage
from ai_matching.core.scoring_config import load_scoring_config, require_usable
from ai_matching.providers.base import EmbeddingProvider
from ai_matching.schemas.matching import MatchRequest
from ai_matching.schemas.result import (
    CriterionResult,
    MatchResponse,
    MatchWarning,
    PipelineMetrics,
    ScoreBreakdown,
    ScoreContribution,
    SupplierRankResult,
)
from ai_matching.services.eligibility import (
    CriterionEvaluation,
    evaluate_candidate,
    parse_mandatory_criteria,
)
from ai_matching.services.explainability import explain_ineligible, explain_ranked
from ai_matching.services.hybrid_scorer import (
    HybridScore,
    parse_preferences,
    score_candidate,
)
from ai_matching.services.preprocessing import (
    PreparedCandidate,
    PreparedRequirement,
    QualityIssue,
    prepare_candidate,
    prepare_requirement,
)
from ai_matching.services.ranking import rank_candidates
from ai_matching.services.semantic_matcher import compute_semantic_similarities

logger = get_logger("pipeline")

UNAPPROVED_CONFIG_WARNING = (
    "UNAPPROVED scoring configuration: results are for non-production demonstration only (D-04, D-05)."
)


@dataclass(frozen=True)
class PreparedInputs:
    """Output of Stage 1, the input to every later stage."""

    correlation_id: str
    criteria_version: str
    requirement: PreparedRequirement
    candidates: tuple[PreparedCandidate, ...]


@dataclass(frozen=True)
class _Scored:
    candidate: PreparedCandidate
    evaluations: tuple[CriterionEvaluation, ...]
    score: HybridScore


def prepare_inputs(request: MatchRequest) -> PreparedInputs:
    """Stage 1: normalise the requirement and every candidate, collecting quality issues."""
    prepared = PreparedInputs(
        correlation_id=request.correlation_id,
        criteria_version=request.criteria_version,
        requirement=prepare_requirement(request.requirement),
        candidates=tuple(prepare_candidate(candidate) for candidate in request.candidates),
    )
    log_stage(
        logger,
        "preprocessing",
        request.correlation_id,
        candidates=len(prepared.candidates),
        quality_issues=sum(len(c.quality_issues) for c in prepared.candidates),
    )
    return prepared


def _warnings(issues: tuple[QualityIssue, ...]) -> list[MatchWarning]:
    return [MatchWarning(flag=i.flag, field=i.field, message=i.message[:255]) for i in issues]


def _criteria(evaluations: tuple[CriterionEvaluation, ...]) -> list[CriterionResult]:
    return [
        CriterionResult(criterion_key=e.criterion_key, operator=e.operator, outcome=e.outcome, detail=e.detail)
        for e in evaluations
    ]


def run_pipeline(request: MatchRequest, settings: EngineSettings, provider: EmbeddingProvider) -> MatchResponse:
    """Run the full matching pipeline. Returns a complete response or raises."""
    cid = request.correlation_id

    # Stage 0 — pre-flight. Fail fast, before any computation.
    config = require_usable(load_scoring_config(request.criteria_version, settings), settings)
    if provider.name == "none":
        raise StageNotAvailableError(stage="semantic", reason="no embedding provider is configured (D-11).")

    # Stage 1 — preparation.
    prepared = prepare_inputs(request)

    # Stage 2 — mandatory eligibility (validates every criterion first).
    mandatory = parse_mandatory_criteria(
        request.requirement.mandatory_criteria, prepared.requirement.values["mandatory_evidence"]
    )
    preferences = parse_preferences(request.requirement.preference_criteria, config)

    eligible: list[tuple[PreparedCandidate, tuple[CriterionEvaluation, ...]]] = []
    excluded: list[SupplierRankResult] = []
    insufficient: list[SupplierRankResult] = []
    for candidate in prepared.candidates:
        outcome, evaluations = evaluate_candidate(mandatory, candidate.values)
        if outcome == EligibilityOutcome.ELIGIBLE:
            eligible.append((candidate, evaluations))
            continue
        result = SupplierRankResult(
            candidate_id=candidate.candidate_id,
            supplier_id=candidate.supplier_id,
            eligibility=outcome,
            criteria=_criteria(evaluations),
            explanation=explain_ineligible(outcome, evaluations, candidate.quality_issues),
            warnings=_warnings(candidate.quality_issues),
            readiness_status=candidate.values.get("readiness_status"),
        )
        (excluded if outcome == EligibilityOutcome.EXCLUDED else insufficient).append(result)
    log_stage(logger, "eligibility", cid, eligible=len(eligible), excluded=len(excluded),
              insufficient=len(insufficient))

    # Stages 3–5 — semantic similarity and hybrid scoring, eligible candidates only.
    scored: list[_Scored] = []
    if eligible:
        cosines = compute_semantic_similarities(
            provider, prepared.requirement.embedding.text, [c.embedding.text for c, _ in eligible]
        )
        for (candidate, evaluations), cosine in zip(eligible, cosines, strict=True):
            scored.append(_Scored(candidate, evaluations, score_candidate(preferences, candidate.values, cosine, config)))
        log_stage(logger, "semantic_scoring", cid, scored=len(scored))

    # Stage 6 — ranking.
    ranked_items = rank_candidates(
        scored,
        hybrid_score=lambda s: s.score.hybrid_score,
        rule_score=lambda s: s.score.rule_score,
        supplier_id=lambda s: s.candidate.supplier_id,
        candidate_id=lambda s: s.candidate.candidate_id,
    )

    # Stage 7 — explanations; Stage 8 — response.
    weights = (config.hybrid_weights.rule, config.hybrid_weights.semantic)
    ranked: list[SupplierRankResult] = []
    for item in ranked_items:
        s = item.item
        ranked.append(SupplierRankResult(
            candidate_id=s.candidate.candidate_id,
            supplier_id=s.candidate.supplier_id,
            eligibility=EligibilityOutcome.ELIGIBLE,
            rank=item.rank,
            criteria=_criteria(s.evaluations),
            scores=ScoreBreakdown(
                rule_score=s.score.rule_score,
                semantic_cosine=s.score.semantic_cosine,
                semantic_score=s.score.semantic_score,
                hybrid_score=s.score.hybrid_score,
                rule_weight=weights[0],
                semantic_weight=weights[1],
                contributions=[
                    ScoreContribution(
                        preference_key=p.preference_key, weight_key=p.weight_key, weight=p.weight,
                        outcome=p.outcome, contribution=p.contribution, detail=p.detail[:255],
                    )
                    for p in s.score.preferences
                ],
            ),
            explanation=explain_ranked(item.rank, len(ranked_items), s.evaluations, s.score, weights,
                                       s.candidate.quality_issues),
            warnings=_warnings(s.candidate.quality_issues),
            readiness_status=s.candidate.values.get("readiness_status"),
        ))

    run_warnings = []
    if config.status != ConfigurationStatus.APPROVED:
        run_warnings.append(UNAPPROVED_CONFIG_WARNING)
    if not ranked:
        run_warnings.append("No eligible candidates: nothing has been promoted to fill the list (M6-AC4).")

    log_stage(logger, "completed", cid, ranked=len(ranked))
    return MatchResponse(
        contract_version=CONTRACT_VERSION,
        status=RunStatus.COMPLETED,
        mode=MatchingMode.HYBRID,
        requirement_id=request.requirement.requirement_id,
        requirement_version=request.requirement.requirement_version,
        criteria_version=config.version,
        configuration_status=config.status,
        embedding_model_id=provider.model_id,
        embedding_text_template_version=EMBEDDING_TEXT_TEMPLATE_VERSION,
        ranked=ranked,
        excluded=excluded,
        insufficient_data=insufficient,
        run_warnings=run_warnings,
        metrics=PipelineMetrics(
            candidates_received=len(prepared.candidates),
            candidates_eligible=len(ranked),
            candidates_excluded=len(excluded),
            candidates_insufficient_data=len(insufficient),
        ),
    )
