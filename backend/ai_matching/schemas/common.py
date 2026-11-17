"""
Shared Schema Base and Field Types.

Common Pydantic configuration for every contract model: unknown fields are
rejected (so contract drift fails loudly) and models are immutable.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 foundation. Contract is PROPOSED (docs/ai/MATCHING_CONTRACT.md).
"""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ai_matching.core.constants import (
    MAX_CODE_LENGTH,
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
