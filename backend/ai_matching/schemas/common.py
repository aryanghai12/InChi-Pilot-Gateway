"""
Shared Schema Base and Field Types.

Common Pydantic configuration for every contract model: unknown fields are
rejected (so contract drift fails loudly) and models are immutable.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 foundation. Contract is PROPOSED (docs/ai/MATCHING_CONTRACT.md).
"""

import json
from decimal import Decimal
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from ai_matching.core.constants import (
    MAX_CODE_LENGTH,
    MAX_CRITERION_VALUE_CHARS,
    MAX_CRITERION_VALUE_DEPTH,
    MAX_LONG_TEXT_LENGTH,
    MAX_SHORT_TEXT_LENGTH,
)


class ContractModel(BaseModel):
    """Base for all request/response contract models."""

    model_config = ConfigDict(extra="forbid", frozen=True)


# Reusable bounded field types (THREAT_MODEL T-DS-01).
Identifier = Annotated[str, Field(min_length=1, max_length=MAX_CODE_LENGTH)]
ShortText = Annotated[str, Field(max_length=MAX_SHORT_TEXT_LENGTH)]
LongText = Annotated[str, Field(max_length=MAX_LONG_TEXT_LENGTH)]
Code = Annotated[str, Field(max_length=MAX_CODE_LENGTH)]

# Optional positive decimal. None means "unknown" and must never be read as zero (M3-AC2).
PositiveDecimal = Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=4)]


def _depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((_depth(v) for v in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_depth(v) for v in value), default=0)
    return 0


def _bounded_json_object(value: dict[str, Any]) -> dict[str, Any]:
    """Reject oversized or deeply nested JSON objects (THREAT_MODEL T-DS-01)."""
    if _depth(value) > MAX_CRITERION_VALUE_DEPTH:
        raise ValueError(f"value must not be nested deeper than {MAX_CRITERION_VALUE_DEPTH} levels.")
    if len(json.dumps(value, default=str)) > MAX_CRITERION_VALUE_CHARS:
        raise ValueError(f"value must not exceed {MAX_CRITERION_VALUE_CHARS} characters when serialised.")
    return value


# A criterion or preference `value` object: free JSON, but bounded.
BoundedJsonObject = Annotated[dict[str, Any], AfterValidator(_bounded_json_object)]
