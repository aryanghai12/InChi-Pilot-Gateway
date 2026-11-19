"""
Matching Response Payload Schemas.

Represents data payloads received by Django from the FastAPI matching engine:
MatchingResponsePayload, RankedSupplierPayload, EligibilityResultPayload,
ScoreBreakdownPayload and MatchWarningPayload.

from_dict() validates the response against the contract before anything is
handed to the result handler. A response that does not satisfy the contract
raises InvalidMatchingPayloadError, so it can never be persisted as a result.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Contract 0.2.0-proposed (docs/ai/MATCHING_CONTRACT.md). A real
successful response requires an approved scoring configuration (D-04, D-05).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.matching.exceptions.matching_exceptions import InvalidMatchingPayloadError
from apps.matching.schemas.matching_request import CONTRACT_VERSION

ELIGIBILITY_OUTCOMES = {"eligible", "excluded", "insufficient_data"}
CRITERION_OUTCOMES = {"pass", "fail", "insufficient_data"}
PREFERENCE_OUTCOMES = {"satisfied", "not_satisfied", "insufficient_data", "not_scored"}
CONFIGURATION_STATUSES = {"approved", "unapproved"}


def _require(data: Any, key: str, kind: type | tuple[type, ...], where: str) -> Any:
    if not isinstance(data, dict) or key not in data:
        raise InvalidMatchingPayloadError(f"Engine response is missing '{where}.{key}'.")
    value = data[key]
    # bool is a subclass of int; reject it wherever a number is expected.
    if not isinstance(value, kind) or (isinstance(value, bool) and kind is not bool):
        raise InvalidMatchingPayloadError(f"Engine response field '{where}.{key}' has the wrong type.")
    return value


def _unit_interval(data: dict, key: str, where: str) -> float:
    value = float(_require(data, key, (int, float), where))
    if not 0.0 <= value <= 1.0:
        raise InvalidMatchingPayloadError(f"Engine response field '{where}.{key}' is outside [0, 1].")
    return value


def _optional_unit_interval(data: dict, key: str, where: str) -> float | None:
    if not isinstance(data, dict) or data.get(key) is None:
        return None
    return _unit_interval(data, key, where)


@dataclass(frozen=True)
class EligibilityResultPayload:
    criterion_key: str
    outcome: str
    detail: str
    operator: str = ""

    @classmethod
    def from_dict(cls, data: Any, where: str) -> EligibilityResultPayload:
        outcome = _require(data, "outcome", str, where)
        if outcome not in CRITERION_OUTCOMES:
            raise InvalidMatchingPayloadError(f"Unknown criterion outcome at '{where}'.")
        return cls(_require(data, "criterion_key", str, where), outcome, str(data.get("detail", "")),
                   str(data.get("operator", "")))


@dataclass(frozen=True)
class ScoreContributionPayload:
    preference_key: str
    weight_key: str
    weight: float | None
    outcome: str
    contribution: float
    detail: str

    @classmethod
    def from_dict(cls, data: Any, where: str) -> ScoreContributionPayload:
        outcome = _require(data, "outcome", str, where)
        if outcome not in PREFERENCE_OUTCOMES:
            raise InvalidMatchingPayloadError(f"Unknown preference outcome at '{where}'.")
        weight = data.get("weight")
        return cls(
            preference_key=_require(data, "preference_key", str, where),
            weight_key=str(data.get("weight_key", "")),
            weight=float(weight) if weight is not None else None,
            outcome=outcome,
            contribution=_unit_interval(data, "contribution", where),
            detail=str(data.get("detail", "")),
        )


@dataclass(frozen=True)
class ScoreBreakdownPayload:
    rule_score: float | None
    semantic_cosine: float
    semantic_score: float
    hybrid_score: float
    rule_weight: float
    semantic_weight: float
    contributions: tuple[ScoreContributionPayload, ...]

    @classmethod
    def from_dict(cls, data: Any, where: str) -> ScoreBreakdownPayload:
        cosine = float(_require(data, "semantic_cosine", (int, float), where))
        if not -1.0 <= cosine <= 1.0:
            raise InvalidMatchingPayloadError(f"Engine response field '{where}.semantic_cosine' is outside [-1, 1].")
        return cls(
            rule_score=_optional_unit_interval(data, "rule_score", where),
            semantic_cosine=cosine,
            semantic_score=_unit_interval(data, "semantic_score", where),
            hybrid_score=_unit_interval(data, "hybrid_score", where),
            rule_weight=_unit_interval(data, "rule_weight", where),
            semantic_weight=_unit_interval(data, "semantic_weight", where),
            contributions=tuple(
                ScoreContributionPayload.from_dict(item, f"{where}.contributions[{i}]")
                for i, item in enumerate(data.get("contributions", []))
            ),
        )


@dataclass(frozen=True)
class MatchWarningPayload:
    flag: str
    field: str
    message: str


@dataclass(frozen=True)
class RankedSupplierPayload:
    candidate_id: str
    supplier_id: str
    eligibility: str
    rank: int | None
    criteria: tuple[EligibilityResultPayload, ...]
    scores: ScoreBreakdownPayload | None
    explanation: tuple[str, ...]
    warnings: tuple[MatchWarningPayload, ...]
    readiness_status: str | None

    @classmethod
    def from_dict(cls, data: Any, where: str) -> RankedSupplierPayload:
        eligibility = _require(data, "eligibility", str, where)
        if eligibility not in ELIGIBILITY_OUTCOMES:
            raise InvalidMatchingPayloadError(f"Unknown eligibility outcome at '{where}'.")
        scores_raw = data.get("scores")
        return cls(
            candidate_id=_require(data, "candidate_id", str, where),
            supplier_id=_require(data, "supplier_id", str, where),
            eligibility=eligibility,
            rank=data.get("rank"),
            criteria=tuple(
                EligibilityResultPayload.from_dict(item, f"{where}.criteria[{i}]")
                for i, item in enumerate(data.get("criteria", []))
            ),
            scores=ScoreBreakdownPayload.from_dict(scores_raw, f"{where}.scores") if scores_raw else None,
            explanation=tuple(str(line) for line in data.get("explanation", [])),
            warnings=tuple(
                MatchWarningPayload(str(w.get("flag", "")), str(w.get("field", "")), str(w.get("message", "")))
                for w in data.get("warnings", [])
                if isinstance(w, dict)
            ),
            readiness_status=data.get("readiness_status"),
        )


@dataclass(frozen=True)
class MatchingResponsePayload:
    contract_version: str
    status: str
    mode: str
    requirement_id: str
    requirement_version: int
    criteria_version: str
    configuration_status: str
    embedding_model_id: str
    embedding_text_template_version: str
    ranked: tuple[RankedSupplierPayload, ...]
    excluded: tuple[RankedSupplierPayload, ...]
    insufficient_data: tuple[RankedSupplierPayload, ...]
    run_warnings: tuple[str, ...]
    metrics: dict[str, int]

    @classmethod
    def from_dict(cls, data: Any) -> MatchingResponsePayload:
        if _require(data, "contract_version", str, "response") != CONTRACT_VERSION:
            raise InvalidMatchingPayloadError("Engine response uses an unsupported contract version.")
        if _require(data, "status", str, "response") != "completed":
            raise InvalidMatchingPayloadError("A successful engine response must have status 'completed'.")

        def _list(key: str, expected: str) -> tuple[RankedSupplierPayload, ...]:
            items = tuple(
                RankedSupplierPayload.from_dict(item, f"{key}[{i}]")
                for i, item in enumerate(_require(data, key, list, "response"))
            )
            if any(item.eligibility != expected for item in items):
                raise InvalidMatchingPayloadError(f"'{key}' contains a candidate with the wrong eligibility.")
            return items

        ranked = _list("ranked", "eligible")
        # M6-AC1: only eligible candidates may carry a rank and scores.
        if any(item.rank is None or item.scores is None for item in ranked):
            raise InvalidMatchingPayloadError("Every ranked candidate must have a rank and scores.")
        excluded = _list("excluded", "excluded")
        insufficient = _list("insufficient_data", "insufficient_data")
        if any(item.rank is not None or item.scores is not None for item in excluded + insufficient):
            raise InvalidMatchingPayloadError("Ineligible candidates must not be ranked or scored (M6-AC1, M6-AC4).")
        if [item.rank for item in ranked] != list(range(1, len(ranked) + 1)):
            raise InvalidMatchingPayloadError("Ranks must be consecutive from 1 in list order.")
        configuration_status = _require(data, "configuration_status", str, "response")
        if configuration_status not in CONFIGURATION_STATUSES:
            raise InvalidMatchingPayloadError("Unknown configuration status in engine response.")

        return cls(
            contract_version=data["contract_version"],
            status=data["status"],
            mode=_require(data, "mode", str, "response"),
            requirement_id=_require(data, "requirement_id", str, "response"),
            requirement_version=_require(data, "requirement_version", int, "response"),
            criteria_version=_require(data, "criteria_version", str, "response"),
            configuration_status=configuration_status,
            embedding_model_id=_require(data, "embedding_model_id", str, "response"),
            embedding_text_template_version=_require(data, "embedding_text_template_version", str, "response"),
            ranked=ranked,
            excluded=excluded,
            insufficient_data=insufficient,
            run_warnings=tuple(str(w) for w in data.get("run_warnings", [])),
            metrics=dict(_require(data, "metrics", dict, "response")),
        )


@dataclass(frozen=True)
class EngineErrorPayload:
    """The error envelope the engine returns on any non-2xx response."""

    code: str
    message: str
    field_errors: dict[str, list[str]]
    correlation_id: str

    @classmethod
    def from_dict(cls, data: Any) -> EngineErrorPayload:
        if not isinstance(data, dict):
            return cls("matching_engine_error", "The matching engine returned an unreadable error.", {}, "")
        field_errors = data.get("field_errors") if isinstance(data.get("field_errors"), dict) else {}
        return cls(
            code=str(data.get("code", "matching_engine_error")),
            message=str(data.get("message", "The matching engine returned an error.")),
            field_errors=field_errors,
            correlation_id=str(data.get("correlation_id", "")),
        )
