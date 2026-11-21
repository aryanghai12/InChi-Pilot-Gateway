"""
Versioned Scoring Configuration Loader.

Loads the hybrid-scoring configuration named by a request's `criteria_version`
from `ai_matching/criteria/<version>.json`. Weights, the semantic-score mapping
and the approval record live ONLY in these reviewed, versioned files — never in
code (MVP_FEATURES §5 "Rules, weights and question sets … change only through
versioned configuration, after BNCS approval and a reviewed PR").

A configuration is usable only when:
* its status is "approved" — or the operator explicitly sets
  MATCHING_ALLOW_UNAPPROVED_CONFIG=true for non-production demos, in which case
  every response is labelled configuration_status="unapproved";
* rule and semantic weights are present, non-negative and sum to 1;
* a semantic-score mapping is chosen.

Otherwise the run fails explicitly with stage_not_available (M6-AC5).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 3 implementation.

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-05 (weights and semantic weight) and D-04 (criteria).
# The committed v0-UNAPPROVED.json deliberately contains NO weights.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationError

from ai_matching.core.config import EngineSettings
from ai_matching.core.constants import ConfigurationStatus
from ai_matching.core.exceptions import ConfigurationError, StageNotAvailableError
from ai_matching.schemas.common import Code, ContractModel

_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
_WEIGHT_SUM_TOLERANCE = 1e-9

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
SemanticScoreMapping = Literal["clamp_negative_to_zero", "linear_rescale"]


class HybridWeights(ContractModel):
    rule: NonNegativeFloat | None = None
    semantic: NonNegativeFloat | None = None


class ScoringConfiguration(ContractModel):
    """One versioned scoring configuration file."""

    version: Code
    status: ConfigurationStatus
    approved_by: Code = ""
    approved_at: Code = ""
    decision_refs: list[Code] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)
    hybrid_weights: HybridWeights = Field(default_factory=HybridWeights)
    preference_weights: dict[Code, NonNegativeFloat] = Field(default_factory=dict)
    semantic_score_mapping: SemanticScoreMapping | None = None


def _config_path(criteria_dir: Path, version: str) -> Path:
    if not _VERSION_PATTERN.match(version):
        raise ConfigurationError("criteria_version contains unsupported characters.")
    path = (criteria_dir / f"{version}.json").resolve()
    if path.parent != criteria_dir.resolve():  # defence against path traversal
        raise ConfigurationError("criteria_version must name a file in the criteria directory.")
    return path


def load_scoring_config(version: str, settings: EngineSettings) -> ScoringConfiguration:
    """Load and validate a configuration file. Raises if missing or malformed."""
    path = _config_path(settings.criteria_dir, version)
    if not path.is_file():
        raise StageNotAvailableError(
            stage="scoring", reason=f"no scoring configuration exists for criteria_version '{version}'."
        )
    try:
        config = ScoringConfiguration.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ConfigurationError(f"Scoring configuration '{version}' is malformed.") from exc
    if config.version != version:
        raise ConfigurationError(f"Scoring configuration file '{version}' declares a different version.")
    return config


def require_usable(config: ScoringConfiguration, settings: EngineSettings) -> ScoringConfiguration:
    """Refuse configurations that are unapproved (unless allowed) or incomplete."""
    if config.status != ConfigurationStatus.APPROVED and not settings.allow_unapproved_config:
        raise StageNotAvailableError(
            stage="scoring",
            reason=f"scoring configuration '{config.version}' is not approved (D-04, D-05).",
        )
    weights = config.hybrid_weights
    if weights.rule is None or weights.semantic is None:
        raise StageNotAvailableError(
            stage="scoring", reason=f"scoring configuration '{config.version}' has no hybrid weights (D-05)."
        )
    if not math.isclose(weights.rule + weights.semantic, 1.0, abs_tol=_WEIGHT_SUM_TOLERANCE):
        raise ConfigurationError(f"Hybrid weights in '{config.version}' must sum to 1.")
    if config.semantic_score_mapping is None:
        raise StageNotAvailableError(
            stage="scoring",
            reason=f"scoring configuration '{config.version}' has no semantic score mapping (D-05).",
        )
    return config
