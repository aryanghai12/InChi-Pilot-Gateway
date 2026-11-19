"""
Mandatory Eligibility Evaluation Service (Pipeline Stage 2).

Evaluates mandatory criteria against supplier capabilities.
Hard-gate rule: any supplier failing ANY mandatory criterion is excluded from final ranking.
Unknown or missing criteria must not pass by default.

The engine defines no criteria of its own. Every criterion comes from the buyer
requirement as data: (criterion_key, operator, value). This module only knows
HOW to compare a candidate field with a value — the generic comparison
vocabulary below (docs/ai/MATCHING_CONTRACT.md §6). WHICH criteria apply is a
business decision (D-04) recorded in the requirement.

Outcome rules (MVP_FEATURES M6-AC1, M6-AC2):
* candidate value unknown            -> insufficient_data (never pass)
* units / currency differ             -> insufficient_data (no conversion, BUY-D05/D07)
* required evidence not recorded      -> insufficient_data ("provided" is not proof of absence)
* free-text criterion (manual_review) -> insufficient_data (a reviewer must check it)
* comparison false                    -> fail
* any fail -> candidate EXCLUDED; else any insufficient -> INSUFFICIENT_DATA; else ELIGIBLE.

A structurally invalid criterion (unknown key, unsupported operator, bad value)
fails the whole run with a validation error instead of being guessed.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Implemented (comparison vocabulary is PROPOSED, contract §6).

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-04 (mandatory eligibility criteria and unknown handling).
# The `unknown_policy` stored with a criterion is carried but not used to turn
# unknown into a pass or an exclusion: M6-AC2 requires "insufficient data".
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from ai_matching.core.constants import (
    MANUAL_REVIEW_OPERATOR,
    CriterionOutcome,
    EligibilityOutcome,
)
from ai_matching.core.exceptions import InvalidRequestError
from ai_matching.services.preprocessing import (
    normalise_capacity_period,
    normalise_category,
    normalise_country,
    normalise_currency,
    normalise_evidence_type,
    normalise_lead_time_unit,
    normalise_quantity_unit,
    normalise_text,
)

# ---------------------------------------------------------------------------
# Comparison vocabulary (PROPOSED — contract §6)
# ---------------------------------------------------------------------------

CODE, MEASURED, MONEY, EVIDENCE = "code", "measured", "money", "evidence"

OPERATORS: dict[str, frozenset[str]] = {
    CODE: frozenset({"equals", "not_equals", "in"}),
    MEASURED: frozenset({"equals", "lte", "gte"}),
    MONEY: frozenset({"equals", "lte", "gte"}),
    EVIDENCE: frozenset({"includes_all"}),
}


@dataclass(frozen=True)
class FieldSpec:
    """How a criterion key maps onto normalised candidate values (preprocessing output)."""

    kind: str
    value_key: str
    unit_key: str | None = None
    period_key: str | None = None
    normalise: Callable[[str], str | None] | None = None


def _code_of(normaliser) -> Callable[[str], str | None]:
    return lambda raw: normaliser(raw).code


def _lower(raw: str) -> str | None:
    return normalise_text(raw).lower() or None


FIELD_REGISTRY: dict[str, FieldSpec] = {
    "product_category": FieldSpec(CODE, "product_category", normalise=_code_of(normalise_category)),
    "origin_country": FieldSpec(CODE, "origin_country", normalise=_code_of(normalise_country)),
    "supplier_country": FieldSpec(CODE, "supplier_country", normalise=_code_of(normalise_country)),
    "supplier_record_status": FieldSpec(CODE, "supplier_record_status", normalise=_lower),
    "moq": FieldSpec(MEASURED, "moq_value", unit_key="moq_unit"),
    "capacity": FieldSpec(MEASURED, "capacity_quantity", unit_key="capacity_unit", period_key="capacity_period"),
    "lead_time": FieldSpec(MEASURED, "lead_time_value", unit_key="lead_time_unit"),
    "price_min": FieldSpec(MONEY, "price_min", unit_key="currency"),
    "price_max": FieldSpec(MONEY, "price_max", unit_key="currency"),
    "evidence": FieldSpec(EVIDENCE, "evidence_types", normalise=lambda raw: normalise_evidence_type(raw) or None),
}

_UNIT_NORMALISERS: dict[str, Callable[[str], str | None]] = {
    "moq": _code_of(normalise_quantity_unit),
    "capacity": _code_of(normalise_quantity_unit),
    "lead_time": _code_of(normalise_lead_time_unit),
    "price_min": _code_of(normalise_currency),
    "price_max": _code_of(normalise_currency),
}


@dataclass(frozen=True)
class ParsedCriterion:
    """A validated criterion ready for evaluation."""

    criterion_key: str
    operator: str
    field: FieldSpec | None  # None for manual_review
    target: Any = None  # str | tuple[str, ...] | Decimal
    unit: str | None = None
    period: str | None = None
    description: str = ""


@dataclass(frozen=True)
class CriterionEvaluation:
    criterion_key: str
    operator: str
    outcome: CriterionOutcome
    detail: str


# ---------------------------------------------------------------------------
# Parsing / validation
# ---------------------------------------------------------------------------


def _invalid(path: str, message: str) -> InvalidRequestError:
    return InvalidRequestError("A matching criterion is invalid.", field_errors={path: [message]})


def _decimal(raw: Any, path: str) -> Decimal:
    if isinstance(raw, bool) or raw is None:
        raise _invalid(path, "A numeric 'value' is required.")
    try:
        value = Decimal(str(raw))
    except InvalidOperation as exc:
        raise _invalid(path, "'value' must be a number.") from exc
    if not value.is_finite():
        raise _invalid(path, "'value' must be finite.")
    return value


def parse_criterion(criterion_key: str, operator: str, value: dict[str, Any], path: str) -> ParsedCriterion:
    """Validate one criterion against the comparison vocabulary. Raises InvalidRequestError."""
    if operator == MANUAL_REVIEW_OPERATOR:
        text = normalise_text(str(value.get("text", "")))[:200]
        return ParsedCriterion(criterion_key, operator, None, description=text)

    field = FIELD_REGISTRY.get(criterion_key)
    if field is None:
        raise _invalid(path, f"Unsupported criterion key '{criterion_key}'.")
    if operator not in OPERATORS[field.kind]:
        raise _invalid(path, f"Operator '{operator}' is not supported for '{criterion_key}'.")
    if not isinstance(value, dict) or "value" not in value:
        raise _invalid(path, "Criterion value must be an object with a 'value' entry.")

    raw = value["value"]
    if field.kind in (MEASURED, MONEY):
        unit_raw = value.get("currency" if field.kind == MONEY else "unit", "")
        unit = _UNIT_NORMALISERS[criterion_key](str(unit_raw)) if unit_raw else None
        if unit is None:
            label = "currency" if field.kind == MONEY else "unit"
            raise _invalid(path, f"A recognised '{label}' is required for '{criterion_key}'.")
        period = None
        if field.period_key and value.get("period"):
            period = normalise_capacity_period(str(value["period"])).code
            if period is None:
                raise _invalid(path, "Unrecognised capacity 'period'.")
        return ParsedCriterion(criterion_key, operator, field, _decimal(raw, path), unit, period)

    raw_items = raw if isinstance(raw, list) else [raw]
    if operator in ("equals", "not_equals") and isinstance(raw, list):
        raise _invalid(path, f"Operator '{operator}' expects a single value.")
    if not raw_items or not all(isinstance(item, str) and item.strip() for item in raw_items):
        raise _invalid(path, "'value' must be a non-empty string or list of strings.")
    normalised = tuple(field.normalise(item) for item in raw_items)
    if any(item is None for item in normalised):
        raise _invalid(path, f"'value' contains an unrecognised code for '{criterion_key}'.")
    target = normalised if operator in ("in", "includes_all") else normalised[0]
    return ParsedCriterion(criterion_key, operator, field, target)


def parse_mandatory_criteria(criteria: Sequence, required_evidence: Sequence[str]) -> tuple[ParsedCriterion, ...]:
    """Parse the requirement's mandatory criteria plus its mandatory evidence (one combined check)."""
    parsed = [
        parse_criterion(c.criterion_key, c.operator, c.value, f"requirement.mandatory_criteria.{i}")
        for i, c in enumerate(criteria)
    ]
    keys = [p.criterion_key for p in parsed]
    if len(keys) != len(set(keys)):
        raise _invalid("requirement.mandatory_criteria", "criterion_key values must be unique.")
    if required_evidence:
        parsed.append(
            ParsedCriterion("required_evidence", "includes_all", FIELD_REGISTRY["evidence"], tuple(required_evidence))
        )
    return tuple(parsed)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _fmt(value: Any) -> str:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, tuple):
        return ", ".join(value)
    return str(value)


def _compare(operator: str, actual: Any, target: Any) -> bool:
    if operator == "equals":
        return actual == target
    if operator == "not_equals":
        return actual != target
    if operator == "in":
        return actual in target
    if operator == "lte":
        return actual <= target
    if operator == "gte":
        return actual >= target
    raise ValueError(operator)  # unreachable: operators validated at parse time


def evaluate_criterion(criterion: ParsedCriterion, values: dict[str, Any]) -> CriterionEvaluation:
    key, op = criterion.criterion_key, criterion.operator

    def result(outcome: CriterionOutcome, detail: str) -> CriterionEvaluation:
        return CriterionEvaluation(key, op, outcome, detail[:255])

    if criterion.field is None:
        label = f" ('{criterion.description}')" if criterion.description else ""
        return result(
            CriterionOutcome.INSUFFICIENT_DATA,
            f"Free-text criterion{label} cannot be evaluated automatically; a reviewer must check it.",
        )

    field = criterion.field
    actual = values.get(field.value_key)

    if field.kind == EVIDENCE:
        recorded = set(actual or ())
        missing = [item for item in criterion.target if item not in recorded]
        if not missing:
            return result(CriterionOutcome.PASS, f"Required evidence recorded: {_fmt(criterion.target)}.")
        return result(
            CriterionOutcome.INSUFFICIENT_DATA,
            f"No evidence recorded for: {', '.join(missing)} (not verified, not proof of absence).",
        )

    if actual is None:
        return result(CriterionOutcome.INSUFFICIENT_DATA, f"Candidate value for '{key}' is unknown.")

    if field.kind in (MEASURED, MONEY):
        actual_unit = values.get(field.unit_key)
        if actual_unit is None:
            return result(CriterionOutcome.INSUFFICIENT_DATA, f"Candidate unit for '{key}' is unknown.")
        if actual_unit != criterion.unit:
            return result(
                CriterionOutcome.INSUFFICIENT_DATA,
                f"Units differ ({actual_unit} vs {criterion.unit}); no conversion is applied.",
            )
        if criterion.period is not None and values.get(field.period_key) != criterion.period:
            return result(
                CriterionOutcome.INSUFFICIENT_DATA,
                f"Capacity period differs or is unknown (required {criterion.period}).",
            )
        actual = Decimal(str(actual))

    passed = _compare(op, actual, criterion.target)
    unit = f" {criterion.unit}" if criterion.unit else ""
    detail = f"{key} {op} {_fmt(criterion.target)}{unit}: candidate value {_fmt(actual)}{unit}."
    return result(CriterionOutcome.PASS if passed else CriterionOutcome.FAIL, detail)


def candidate_outcome(evaluations: Iterable[CriterionEvaluation]) -> EligibilityOutcome:
    """Any fail -> excluded; else any insufficient -> insufficient_data; else eligible."""
    outcomes = {e.outcome for e in evaluations}
    if CriterionOutcome.FAIL in outcomes:
        return EligibilityOutcome.EXCLUDED
    if CriterionOutcome.INSUFFICIENT_DATA in outcomes:
        return EligibilityOutcome.INSUFFICIENT_DATA
    return EligibilityOutcome.ELIGIBLE


def evaluate_candidate(
    criteria: Sequence[ParsedCriterion], values: dict[str, Any]
) -> tuple[EligibilityOutcome, tuple[CriterionEvaluation, ...]]:
    evaluations = tuple(evaluate_criterion(c, values) for c in criteria)
    return candidate_outcome(evaluations), evaluations
