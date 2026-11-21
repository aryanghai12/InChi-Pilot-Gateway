"""
Matching Result Handler and Persistence Coordinator.

Handles and coordinates persistence of matching results returned from the
FastAPI engine:

* build_run_record() turns a MatchRunOutcome into persistence-ready records:
  one MatchRunRecord (every M6-AC6 field) and one MatchResultRecord per
  candidate. A failed run carries NO result records (M6-AC5).
* persist_outcome() saves those records through a MatchRunPersister and writes
  the audit event in the SAME transaction.atomic() block (ARCHITECTURE.md §5).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Implemented (records + persistence coordination). Waiting on models.

STRICT OWNERSHIP BOUNDARY:
- Vishal Chauhan (C6 — Data and Platform Services Engineer) owns all Django database
  models, migrations, tables, and persistence schemas.
- Coordinates with existing models once defined; does not independently define models
  or execute database migrations.
- MatchRun / MatchResult models do not exist yet. The concrete MatchRunPersister that
  writes them is Vishal's to provide; this module only defines the hand-off shape.

NOTE: audit.services.record_event (Abhishek, C5) currently logs and swallows its own
exceptions, so an audit failure would not roll this transaction back. Raised with
Abhishek and Ajendra (docs/ai/MATCHING_CONTRACT.md §6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from django.db import transaction

from apps.audit.services import record_event

AUDIT_ACTION = "match_run"


@dataclass(frozen=True)
class MatchResultRecord:
    """One candidate's stored result (MVP_FEATURES §6 MatchResult)."""

    candidate_id: str
    supplier_id: str
    eligibility: str
    rank: int | None
    rule_score: float | None
    semantic_cosine: float | None
    semantic_score: float | None
    hybrid_score: float | None
    criteria: tuple[dict[str, str], ...]
    contributions: tuple[dict[str, Any], ...]
    explanation: tuple[str, ...]
    warnings: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class MatchRunRecord:
    """One stored run (MVP_FEATURES M6-AC6)."""

    status: str
    requirement_id: str
    requirement_version: int
    criteria_version: str
    configuration_status: str | None
    embedding_model_id: str
    mode: str | None
    actor_id: str | None
    correlation_id: str
    started_at: datetime
    finished_at: datetime
    candidates_submitted: int
    candidates_ranked: int
    candidates_excluded: int
    candidates_insufficient_data: int
    error_code: str = ""
    error_message: str = ""
    run_warnings: tuple[str, ...] = ()
    results: tuple[MatchResultRecord, ...] = field(default_factory=tuple)


class MatchRunPersister(Protocol):
    """Implemented by the data layer (Vishal, C6). Must write the run and its results."""

    def save_run(self, record: MatchRunRecord) -> Any:
        """Persist the run and results; return the saved run object (must have an `id`)."""


def _result(item, eligibility: str) -> MatchResultRecord:
    scores = item.scores
    return MatchResultRecord(
        candidate_id=item.candidate_id,
        supplier_id=item.supplier_id,
        eligibility=eligibility,
        rank=item.rank,
        rule_score=scores.rule_score if scores else None,
        semantic_cosine=scores.semantic_cosine if scores else None,
        semantic_score=scores.semantic_score if scores else None,
        hybrid_score=scores.hybrid_score if scores else None,
        criteria=tuple(
            {"criterion_key": c.criterion_key, "operator": c.operator, "outcome": c.outcome, "detail": c.detail}
            for c in item.criteria
        ),
        contributions=tuple(
            {"preference_key": p.preference_key, "weight_key": p.weight_key, "weight": p.weight,
             "outcome": p.outcome, "contribution": p.contribution, "detail": p.detail}
            for p in (scores.contributions if scores else ())
        ),
        explanation=item.explanation,
        warnings=tuple({"flag": w.flag, "field": w.field, "message": w.message} for w in item.warnings),
    )


def build_run_record(outcome) -> MatchRunRecord:
    """Persistence-ready record for a MatchRunOutcome. Failed runs have no results."""
    response = outcome.response
    if response is None:
        return MatchRunRecord(
            status="failed",
            requirement_id=outcome.requirement_id,
            requirement_version=outcome.requirement_version,
            criteria_version=outcome.criteria_version,
            configuration_status=None,
            embedding_model_id="none",
            mode=None,
            actor_id=outcome.actor_id,
            correlation_id=outcome.correlation_id,
            started_at=outcome.started_at,
            finished_at=outcome.finished_at,
            candidates_submitted=outcome.candidates_submitted,
            candidates_ranked=0,
            candidates_excluded=0,
            candidates_insufficient_data=0,
            error_code=outcome.error_code,
            error_message=outcome.error_message,
        )
    results = (
        tuple(_result(i, "eligible") for i in response.ranked)
        + tuple(_result(i, "excluded") for i in response.excluded)
        + tuple(_result(i, "insufficient_data") for i in response.insufficient_data)
    )
    return MatchRunRecord(
        status="completed",
        requirement_id=response.requirement_id,
        requirement_version=response.requirement_version,
        criteria_version=response.criteria_version,
        configuration_status=response.configuration_status,
        embedding_model_id=response.embedding_model_id,
        mode=response.mode,
        actor_id=outcome.actor_id,
        correlation_id=outcome.correlation_id,
        started_at=outcome.started_at,
        finished_at=outcome.finished_at,
        candidates_submitted=outcome.candidates_submitted,
        candidates_ranked=len(response.ranked),
        candidates_excluded=len(response.excluded),
        candidates_insufficient_data=len(response.insufficient_data),
        run_warnings=response.run_warnings,
        results=results,
    )


def persist_outcome(outcome, persister: MatchRunPersister, actor=None) -> Any:
    """Save the run record and its audit event atomically. Returns the saved run object."""
    record = build_run_record(outcome)
    with transaction.atomic():
        saved = persister.save_run(record)
        record_event(
            actor=actor,
            action=AUDIT_ACTION,
            obj=saved,
            outcome="success" if record.status == "completed" else "failure",
            reason="" if record.status == "completed" else record.error_code,
            changes={
                "requirement_id": record.requirement_id,
                "requirement_version": record.requirement_version,
                "criteria_version": record.criteria_version,
                "configuration_status": record.configuration_status,
                "embedding_model_id": record.embedding_model_id,
                "candidates_submitted": record.candidates_submitted,
                "candidates_ranked": record.candidates_ranked,
                "candidates_excluded": record.candidates_excluded,
                "candidates_insufficient_data": record.candidates_insufficient_data,
            },
            correlation_id=record.correlation_id,
        )
    return saved
