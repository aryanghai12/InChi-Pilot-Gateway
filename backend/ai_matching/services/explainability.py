"""
Explainability and Reasoning Generator (Pipeline Stage 7).

Generates transparent, human-readable explanations of match results, criteria
evaluations, score breakdowns, and missing-information warnings.
Python-based explainability: no external LLM required. Every sentence is a
template filled with values the pipeline actually computed, so the explanation
can never claim anything the scores do not show.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Implemented.

NOTE: Human-in-the-loop principle: AI advises, humans decide. Every explanation
ends with a decision-support reminder; scores are never presented as certainty.
"""

from __future__ import annotations

from collections.abc import Sequence

from ai_matching.core.constants import (
    CriterionOutcome,
    EligibilityOutcome,
    PreferenceOutcome,
)
from ai_matching.services.eligibility import CriterionEvaluation
from ai_matching.services.hybrid_scorer import HybridScore
from ai_matching.services.preprocessing import QualityIssue

DECISION_SUPPORT_NOTE = "Decision support only: an authorised reviewer makes the final decision."
_MAX_LINE = 255


def _line(text: str) -> str:
    return text if len(text) <= _MAX_LINE else text[: _MAX_LINE - 1] + "…"


def _criteria_lines(evaluations: Sequence[CriterionEvaluation]) -> list[str]:
    if not evaluations:
        return ["The requirement has no mandatory criteria; no hard filter was applied."]
    passed = sum(1 for e in evaluations if e.outcome == CriterionOutcome.PASS)
    lines = [f"Mandatory criteria: {passed} of {len(evaluations)} passed."]
    for e in evaluations:
        if e.outcome != CriterionOutcome.PASS:
            label = "Failed" if e.outcome == CriterionOutcome.FAIL else "Insufficient data"
            lines.append(_line(f"{label} — {e.criterion_key}: {e.detail}"))
    return lines


def explain_ineligible(
    outcome: EligibilityOutcome,
    evaluations: Sequence[CriterionEvaluation],
    quality_issues: Sequence[QualityIssue],
) -> list[str]:
    if outcome == EligibilityOutcome.EXCLUDED:
        head = "Excluded: failed at least one mandatory criterion. Semantic similarity cannot override this."
    else:
        head = "Not ranked: a mandatory criterion could not be confirmed (unknown is not a pass)."
    lines = [head, *_criteria_lines(evaluations)]
    if quality_issues:
        lines.append(f"{len(quality_issues)} data-quality warning(s) recorded for this candidate.")
    lines.append(DECISION_SUPPORT_NOTE)
    return [_line(line) for line in lines]


def explain_ranked(
    rank: int,
    eligible_total: int,
    evaluations: Sequence[CriterionEvaluation],
    score: HybridScore,
    weights: tuple[float, float],
    quality_issues: Sequence[QualityIssue],
) -> list[str]:
    w_rule, w_semantic = weights
    lines = [f"Ranked {rank} of {eligible_total} eligible candidate(s) by hybrid score {score.hybrid_score:.2f}."]
    lines += _criteria_lines(evaluations)

    if score.rule_score is None:
        lines.append(
            "Rule score not applicable: no preference could be scored with approved weights; "
            "ranking uses the semantic signal only."
        )
    else:
        scored = [p for p in score.preferences if p.outcome != PreferenceOutcome.NOT_SCORED]
        satisfied = sum(1 for p in scored if p.outcome == PreferenceOutcome.SATISFIED)
        lines.append(
            f"Rule score {score.rule_score:.2f} (weight {w_rule:g}): {satisfied} of {len(scored)} "
            "weighted preference(s) satisfied."
        )
        for p in scored:
            if p.outcome == PreferenceOutcome.INSUFFICIENT_DATA:
                lines.append(_line(f"Preference {p.preference_key}: no credit, data unknown — {p.detail}"))
    not_scored = [p.preference_key for p in score.preferences if p.outcome == PreferenceOutcome.NOT_SCORED]
    if not_scored:
        lines.append(_line(f"Not scored (no structured rule or approved weight): {', '.join(not_scored)}."))

    lines.append(
        f"Semantic signal {score.semantic_score:.2f} (cosine {score.semantic_cosine:.2f}, "
        f"weight {w_semantic:g}): text similarity only, not a verified capability."
    )
    if quality_issues:
        fields = sorted({issue.field for issue in quality_issues})
        lines.append(_line(f"Incomplete or uncertain information: {', '.join(fields)}."))
    lines.append(DECISION_SUPPORT_NOTE)
    return [_line(line) for line in lines]
