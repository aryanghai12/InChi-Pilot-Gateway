"""
Candidate Ranking Service (Pipeline Stage 6).

Sorts eligible candidates by score and applies deterministic tie-breaking logic
(ARCHITECTURE.md §6.2):

    hybrid_score DESC -> rule_score DESC -> supplier_id ASC -> candidate_id ASC

candidate_id is the final tie-breaker because one supplier can offer several
products. Only ELIGIBLE candidates are ever passed here (M6-AC1); there is no
minimum-score threshold, so every eligible candidate is ranked and none is
promoted to fill the list (M6-AC4).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Implemented.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RankedItem(Generic[T]):
    rank: int
    item: T


def rank_candidates(
    items: Sequence[T],
    *,
    hybrid_score,
    rule_score,
    supplier_id,
    candidate_id,
) -> list[RankedItem[T]]:
    """
    Rank items with the deterministic ordering above. The accessors are callables
    returning each field, so this works on any internal structure.
    A missing rule score (rule component not applicable) sorts as equal for all.
    """

    def key(item: T):
        rule = rule_score(item)
        return (-hybrid_score(item), -(rule if rule is not None else 0.0), supplier_id(item), candidate_id(item))

    return [RankedItem(rank=index + 1, item=item) for index, item in enumerate(sorted(items, key=key))]
