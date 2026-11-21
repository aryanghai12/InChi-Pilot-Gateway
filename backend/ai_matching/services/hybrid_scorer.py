"""
Hybrid Scoring Service (Pipeline Stage 5).

Combines rule-based preference score and semantic similarity score using approved weights.
Every weight and the semantic-score mapping come from the versioned scoring
configuration (core/scoring_config.py). Nothing is defaulted in code.

rule_score
    Weighted share of satisfied preferences:
        sum(weight_i * satisfied_i) / sum(weight_i)
    over preferences that are structured (operator + value, like a criterion)
    AND whose weight_key has an approved weight. Unknown candidate data earns no
    credit and is flagged. Preferences that cannot be scored are reported as
    NOT_SCORED and never change the result. If no preference can be scored the
    rule component is "not applicable" (rule_score = None).

semantic_score
    Raw cosine in [-1, 1] mapped to [0, 1] by the configured mapping:
        clamp_negative_to_zero: max(0, cosine)
        linear_rescale:         (cosine + 1) / 2

hybrid_score
    w_rule * rule_score + w_semantic * semantic_score.
    When rule_score is None, hybrid_score = semantic_score. This is
    ranking-equivalent to any constant rule score, because applicability depends
    only on the requirement and configuration — identical for every candidate.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Implemented.

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-05 (weighted preference criteria, weights and semantic weight).
# No threshold or minimum score exists: every eligible candidate is ranked.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ai_matching.core.constants import CriterionOutcome, PreferenceOutcome
from ai_matching.core.scoring_config import ScoringConfiguration
from ai_matching.services.eligibility import (
    ParsedCriterion,
    evaluate_criterion,
    parse_criterion,
)


@dataclass(frozen=True)
class ParsedPreference:
    preference_key: str
    weight_key: str
    weight: float | None
    criterion: ParsedCriterion | None
    not_scored_reason: str = ""


@dataclass(frozen=True)
class PreferenceEvaluation:
    preference_key: str
    weight_key: str
    weight: float | None
    outcome: PreferenceOutcome
    contribution: float
    detail: str


@dataclass(frozen=True)
class HybridScore:
    rule_score: float | None
    semantic_cosine: float
    semantic_score: float
    hybrid_score: float
    preferences: tuple[PreferenceEvaluation, ...]


_OUTCOME_MAP = {
    CriterionOutcome.PASS: PreferenceOutcome.SATISFIED,
    CriterionOutcome.FAIL: PreferenceOutcome.NOT_SATISFIED,
    CriterionOutcome.INSUFFICIENT_DATA: PreferenceOutcome.INSUFFICIENT_DATA,
}


def parse_preferences(preferences: Sequence, config: ScoringConfiguration) -> tuple[ParsedPreference, ...]:
    """
    A preference is scorable when its value carries an 'operator' (same vocabulary
    as mandatory criteria) and its weight_key has an approved weight.
    A structured preference with an invalid operator/value fails the run.
    """
    parsed: list[ParsedPreference] = []
    for i, pref in enumerate(preferences):
        weight = config.preference_weights.get(pref.weight_key) if pref.weight_key else None
        value: dict[str, Any] = pref.value or {}
        operator = value.get("operator")
        if not isinstance(operator, str) or not operator:
            parsed.append(
                ParsedPreference(pref.preference_key, pref.weight_key, weight, None,
                                 "not a structured preference (no operator)")
            )
            continue
        criterion = parse_criterion(
            pref.preference_key, operator, {k: v for k, v in value.items() if k != "operator"},
            f"requirement.preference_criteria.{i}",
        )
        if weight is None:
            parsed.append(ParsedPreference(pref.preference_key, pref.weight_key, None, criterion,
                                           "no approved weight for this weight_key"))
        elif weight == 0:
            parsed.append(ParsedPreference(pref.preference_key, pref.weight_key, 0.0, criterion,
                                           "approved weight is zero"))
        else:
            parsed.append(ParsedPreference(pref.preference_key, pref.weight_key, weight, criterion))
    return tuple(parsed)


def map_semantic_score(cosine: float, mapping: str) -> float:
    if mapping == "clamp_negative_to_zero":
        return max(0.0, min(1.0, cosine))
    if mapping == "linear_rescale":
        return max(0.0, min(1.0, (cosine + 1.0) / 2.0))
    raise ValueError(f"Unknown semantic score mapping '{mapping}'.")  # guarded by scoring_config


def score_candidate(
    preferences: Sequence[ParsedPreference],
    values: dict[str, Any],
    semantic_cosine: float,
    config: ScoringConfiguration,
) -> HybridScore:
    evaluations: list[PreferenceEvaluation] = []
    weighted_sum = 0.0
    total_weight = 0.0

    for pref in preferences:
        if pref.not_scored_reason:
            evaluations.append(PreferenceEvaluation(
                pref.preference_key, pref.weight_key, pref.weight, PreferenceOutcome.NOT_SCORED, 0.0,
                f"Not scored: {pref.not_scored_reason}.",
            ))
            continue
        evaluation = evaluate_criterion(pref.criterion, values)
        outcome = _OUTCOME_MAP[evaluation.outcome]
        credit = pref.weight if outcome == PreferenceOutcome.SATISFIED else 0.0
        weighted_sum += credit
        total_weight += pref.weight
        evaluations.append(PreferenceEvaluation(
            pref.preference_key, pref.weight_key, pref.weight, outcome, credit, evaluation.detail,
        ))

    rule_score = weighted_sum / total_weight if total_weight > 0 else None
    if rule_score is not None:
        # Express each contribution as its share of the rule score.
        evaluations = [
            PreferenceEvaluation(e.preference_key, e.weight_key, e.weight, e.outcome,
                                 e.contribution / total_weight, e.detail)
            for e in evaluations
        ]

    semantic_score = map_semantic_score(semantic_cosine, config.semantic_score_mapping)
    weights = config.hybrid_weights
    if rule_score is None:
        hybrid = semantic_score
    else:
        hybrid = weights.rule * rule_score + weights.semantic * semantic_score

    return HybridScore(
        rule_score=rule_score,
        semantic_cosine=max(-1.0, min(1.0, semantic_cosine)),
        semantic_score=semantic_score,
        hybrid_score=max(0.0, min(1.0, hybrid)),
        preferences=tuple(evaluations),
    )
