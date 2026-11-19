"""
Synthetic test payload factories (contract test examples, Week 2).

All values are synthetic and clearly fake. Criterion keys and values mirror the
shape of the demand seed data (database/apps/demand/management/commands/seed_demo.py);
they are examples of the data shape, not approved criteria.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
"""

from __future__ import annotations

import copy

from ai_matching.core.constants import CONTRACT_VERSION

_REQUIREMENT = {
    "requirement_id": "00000000-0000-4000-8000-000000000004",
    "requirement_version": 1,
    "title": "Synthetic demand requirement 004",
    "product_category": "ELECTRONICS",
    "specification_text": "Synthetic electronic components for test matching only.",
    "target_market": "IN",
    "quantity_value": "2000",
    "quantity_unit": "KG",
    "target_price_min": "14",
    "target_price_max": "24",
    "currency_code": "USD",
    "price_basis": "PER_KG",
    "delivery_country": "CN",
    "required_lead_time_value": 34,
    "required_lead_time_unit": "days",
    "mandatory_criteria": [
        {
            "criterion_key": "origin_country",
            "operator": "equals",
            "value": {"value": "IN"},
            "unknown_policy": "exclude",
        }
    ],
    "preference_criteria": [
        # Structured preference (comparison vocabulary, contract §6).
        {"preference_key": "lead_time", "value": {"operator": "lte", "value": 45, "unit": "DAYS"},
         "weight_key": "lead_time"},
        # Seed-style unstructured preference: reported as not scored.
        {"preference_key": "shorter_lead_time", "value": {"preferred_max_days": 45}, "weight_key": "lead_time"},
    ],
    "evidence_criteria": [{"evidence_type": "QUALITY_CERTIFICATE", "classification": "mandatory"}],
}

_CANDIDATE = {
    "candidate_id": "11111111-1111-4111-8111-000000000001",
    "supplier_id": "22222222-2222-4222-8222-000000000001",
    "supplier_name": "Synthetic Supplier One",
    "supplier_country": "IN",
    "supplier_record_status": "complete",
    "supplier_industry_description": "Synthetic electronics assembly.",
    "readiness_status": None,
    "product_name": "Synthetic Circuit Board",
    "product_category": "Electronic Goods",
    "description": "Synthetic printed circuit board for testing.",
    "specifications": "Two-layer, synthetic test data.",
    "origin": "India",
    "moq_value": "100",
    "moq_unit": "pieces",
    "price_min": "10",
    "price_max": "20",
    "currency": "usd",
    "price_basis": "PER_PIECE",
    "capacity_quantity": "5000",
    "capacity_unit": "PIECES",
    "capacity_period": "monthly",
    "lead_time_value": 30,
    "lead_time_unit": "Days",
    "evidence": [{"document_type": "quality certificate", "presence_status": "provided", "review_status": "unreviewed"}],
}


def requirement_payload(**overrides) -> dict:
    payload = copy.deepcopy(_REQUIREMENT)
    payload.update(overrides)
    return payload


def candidate_payload(index: int = 1, **overrides) -> dict:
    payload = copy.deepcopy(_CANDIDATE)
    payload["candidate_id"] = f"11111111-1111-4111-8111-{index:012d}"
    payload["supplier_id"] = f"22222222-2222-4222-8222-{index:012d}"
    payload.update(overrides)
    return payload


def match_request_payload(candidates: list[dict] | None = None, **overrides) -> dict:
    payload = {
        "contract_version": CONTRACT_VERSION,
        "correlation_id": "test-correlation-id",
        "criteria_version": "criteria-v1",
        "requirement": requirement_payload(),
        "candidates": candidates if candidates is not None else [candidate_payload(1), candidate_payload(2)],
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Test doubles: scoring configuration, settings and a deterministic embedder.
# Weights below are SYNTHETIC test values, not proposed or approved weights.
# ---------------------------------------------------------------------------

import json
import re
import tempfile
from pathlib import Path

from ai_matching.core.config import EngineSettings
from ai_matching.providers.base import EmbeddingProvider

TEST_CONFIG_VERSION = "test-approved-v1"


def scoring_config(**overrides) -> dict:
    config = {
        "version": TEST_CONFIG_VERSION,
        "status": "approved",
        "approved_by": "synthetic-test",
        "approved_at": "2026-11-19",
        "decision_refs": ["TEST-ONLY"],
        "hybrid_weights": {"rule": 0.5, "semantic": 0.5},
        "preference_weights": {"lead_time": 1.0},
        "semantic_score_mapping": "clamp_negative_to_zero",
    }
    config.update(overrides)
    return config


class CriteriaDir:
    """Context manager: a temporary criteria directory holding the given config files."""

    def __init__(self, *configs: dict):
        self._configs = configs or (scoring_config(),)

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        path = Path(self._tmp.name)
        for config in self._configs:
            (path / f"{config['version']}.json").write_text(json.dumps(config), encoding="utf-8")
        return path

    def __exit__(self, *exc) -> None:
        self._tmp.cleanup()


def settings(criteria_dir: Path, allow_unapproved: bool = False, provider: str = "sentence_transformers") -> EngineSettings:
    return EngineSettings(
        host="127.0.0.1",
        port=8001,
        embedding_provider=provider,
        embedding_model_name="test-double-model" if provider != "none" else None,
        criteria_dir=criteria_dir,
        allow_unapproved_config=allow_unapproved,
    )


class KeywordEmbedder(EmbeddingProvider):
    """Deterministic bag-of-words embedder over a fixed vocabulary. Never a real model."""

    name = "keyword-test-double"
    VOCABULARY = ("circuit", "board", "electronic", "component", "cotton", "textile", "steel", "synthetic")

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = 0

    @property
    def model_id(self) -> str:
        return "keyword-test-double"

    @property
    def dimension(self) -> int:
        return len(self.VOCABULARY) + 1

    def embed(self, texts):
        self.calls += 1
        if self.fail:
            from ai_matching.core.exceptions import EmbeddingGenerationError

            raise EmbeddingGenerationError("Synthetic embedding failure.")
        vectors = []
        for text in texts:
            words = re.findall(r"[a-z]+", text.lower())
            vector = [float(sum(w.startswith(v) for w in words)) for v in self.VOCABULARY]
            vectors.append(vector + [1.0])  # bias term keeps every vector non-zero
        return vectors
