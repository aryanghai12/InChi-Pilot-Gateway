"""
Text Preprocessing and Input Sanitization Service (Pipeline Stage 1).

Normalizes text, sanitizes input, and prepares structured text representations
for requirement and capability embeddings:

* normalise_text: Unicode NFKC, control characters removed, whitespace collapsed.
* normalise_* codes: units, currency, country and category aliases mapped to the
  codes already used in the repository. Unknown values stay unknown and are
  flagged; nothing is guessed and no unit conversion is performed.
* quality flags: missing values, missing units and unrecognised codes, used for
  missing-information warnings (M6-AC3). Flags never decide eligibility.
* embedding-ready records: a deterministic text per requirement and candidate,
  plus a SHA-256 source hash (TD-01 "embedding_source_hash").

All functions are pure and deterministic. Rules are documented in
docs/ai/PREPROCESSING.md.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 3 implementation.

NOTE ON ARCHITECTURE & DECISIONS:
# Canonical unit codes mirror backend/apps/registry/models.py (QuantityUnit,
# LeadTimeUnit). Category codes mirror the PROVISIONAL reference values in
# database/apps/demand/management/commands/seed_demo.py (BUY-D04 / D-02 open).
# Unit conversion is NOT performed (BUY-D05: "do not assume conversions").
# Currency conversion is NOT performed (BUY-D07).
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal

from ai_matching.core.constants import EMBEDDING_TEXT_TEMPLATE_VERSION, QualityFlag
from ai_matching.schemas.buyer import BuyerRequirementInput
from ai_matching.schemas.supplier import SupplierCandidateInput

# ---------------------------------------------------------------------------
# Alias tables. Keys are normalised lookup tokens (see _token()).
# ---------------------------------------------------------------------------

# Canonical codes = registry QuantityUnit. Aliases mirror ProductSerializer.
QUANTITY_UNIT_ALIASES: dict[str, str] = {
    "MT": "MT", "TONNE": "MT", "TONNES": "MT", "METRIC_TONNE": "MT", "METRIC_TONNES": "MT",
    "KG": "KG", "KGS": "KG", "KILOGRAM": "KG", "KILOGRAMS": "KG",
    "PIECES": "PIECES", "PIECE": "PIECES", "PCS": "PIECES", "PC": "PIECES",
    "BOXES": "BOXES", "BOX": "BOXES",
    "CONTAINERS": "CONTAINERS", "CONTAINER": "CONTAINERS",
}

# Canonical codes = registry LeadTimeUnit. The demand seed stores "days".
LEAD_TIME_UNIT_ALIASES: dict[str, str] = {
    "DAYS": "DAYS", "DAY": "DAYS", "D": "DAYS",
    "WEEKS": "WEEKS", "WEEK": "WEEKS", "WK": "WEEKS", "WKS": "WEEKS",
    "MONTHS": "MONTHS", "MONTH": "MONTHS",
}

# Canonical codes = registry CapacityPeriod.
CAPACITY_PERIOD_ALIASES: dict[str, str] = {
    "MONTH": "MONTH", "MONTHLY": "MONTH", "PER_MONTH": "MONTH",
    "QUARTER": "QUARTER", "QUARTERLY": "QUARTER", "PER_QUARTER": "QUARTER",
    "YEAR": "YEAR", "YEARLY": "YEAR", "ANNUAL": "YEAR", "PER_YEAR": "YEAR",
}

# ISO 3166-1 alpha-2 for the markets present in repository reference data
# (registry serializer maps India/China; demand seed markets IN, CN, AE).
COUNTRY_ALIASES: dict[str, str] = {
    "IN": "IN", "IND": "IN", "INDIA": "IN",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "AE": "AE", "ARE": "AE", "UAE": "AE", "UNITED_ARAB_EMIRATES": "AE",
}

# PROVISIONAL — mirrors demand ReferenceValue "product_category" (BUY-D04, D-02 open).
CATEGORY_ALIASES: dict[str, str] = {
    "AGRI_FOOD": "AGRI_FOOD", "AGRICULTURE_AND_FOOD": "AGRI_FOOD",
    "TEXTILES": "TEXTILES",
    "ENGINEERING": "ENGINEERING", "ENGINEERING_GOODS": "ENGINEERING",
    "ELECTRONICS": "ELECTRONICS", "ELECTRONIC_GOODS": "ELECTRONICS",
    "CHEMICALS": "CHEMICALS",
    # Seed display name is "Minerals and Metals"; frontend type uses "Minerals & Metals".
    "MINERALS": "MINERALS", "MINERALS_AND_METALS": "MINERALS", "MINERALS_METALS": "MINERALS",
    "MARINE": "MARINE", "MARINE_PRODUCTS": "MARINE",
}

_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_WHITESPACE = re.compile(r"\s+")
_TOKEN_SEPARATORS = re.compile(r"[\s\-/&]+")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QualityIssue:
    """One data-quality observation about a field."""

    flag: QualityFlag
    field: str
    message: str


@dataclass(frozen=True)
class NormalisedCode:
    """Result of normalising a coded value. code is None when unknown or unrecognised."""

    code: str | None
    raw: str


@dataclass(frozen=True)
class EmbeddingRecord:
    """Deterministic text prepared for embedding, with its provenance hash."""

    text: str
    source_hash: str
    template_version: str = EMBEDDING_TEXT_TEMPLATE_VERSION


@dataclass(frozen=True)
class PreparedCandidate:
    """A candidate after Stage 1: normalised values, quality issues, embedding record."""

    candidate_id: str
    supplier_id: str
    values: dict[str, object]
    quality_issues: tuple[QualityIssue, ...]
    embedding: EmbeddingRecord


@dataclass(frozen=True)
class PreparedRequirement:
    """A requirement after Stage 1."""

    requirement_id: str
    requirement_version: int
    values: dict[str, object]
    quality_issues: tuple[QualityIssue, ...]
    embedding: EmbeddingRecord


@dataclass
class _IssueCollector:
    issues: list[QualityIssue] = field(default_factory=list)

    def add(self, flag: QualityFlag, field_name: str, message: str) -> None:
        self.issues.append(QualityIssue(flag=flag, field=field_name, message=message))


# ---------------------------------------------------------------------------
# Text and code normalisation
# ---------------------------------------------------------------------------


def normalise_text(value: str | None) -> str:
    """NFKC-normalise, replace control characters with spaces, collapse whitespace."""
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", value)
    text = "".join(" " if unicodedata.category(ch).startswith("C") else ch for ch in text)
    return _WHITESPACE.sub(" ", text).strip()


def _token(value: str) -> str:
    """Lookup token: NFKC, upper-case, separators collapsed to underscores."""
    text = normalise_text(value).upper()
    return _TOKEN_SEPARATORS.sub("_", text).strip("_")


def _normalise_with_aliases(value: str | None, aliases: dict[str, str]) -> NormalisedCode:
    raw = normalise_text(value)
    if not raw:
        return NormalisedCode(code=None, raw="")
    return NormalisedCode(code=aliases.get(_token(raw)), raw=raw)


def normalise_quantity_unit(value: str | None) -> NormalisedCode:
    return _normalise_with_aliases(value, QUANTITY_UNIT_ALIASES)


def normalise_lead_time_unit(value: str | None) -> NormalisedCode:
    return _normalise_with_aliases(value, LEAD_TIME_UNIT_ALIASES)


def normalise_capacity_period(value: str | None) -> NormalisedCode:
    return _normalise_with_aliases(value, CAPACITY_PERIOD_ALIASES)


def normalise_country(value: str | None) -> NormalisedCode:
    return _normalise_with_aliases(value, COUNTRY_ALIASES)


def normalise_category(value: str | None) -> NormalisedCode:
    return _normalise_with_aliases(value, CATEGORY_ALIASES)


def normalise_currency(value: str | None) -> NormalisedCode:
    """Accept any three-letter alphabetic code (ISO 4217 shape). No conversion."""
    raw = normalise_text(value)
    if not raw:
        return NormalisedCode(code=None, raw="")
    token = raw.upper()
    return NormalisedCode(code=token if _CURRENCY_PATTERN.match(token) else None, raw=raw)


def normalise_evidence_type(value: str | None) -> str:
    """Evidence types are compared as upper-case tokens (e.g. QUALITY_CERTIFICATE)."""
    return _token(value or "")


# ---------------------------------------------------------------------------
# Field-level helpers that record quality issues
# ---------------------------------------------------------------------------


def _coded_field(
    collector: _IssueCollector,
    field_name: str,
    result: NormalisedCode,
    unrecognised_flag: QualityFlag,
    *,
    required_for_quality: bool = True,
) -> str | None:
    if result.code is not None:
        return result.code
    if result.raw:
        collector.add(unrecognised_flag, field_name, f"Value for '{field_name}' is not a recognised code.")
    elif required_for_quality:
        collector.add(QualityFlag.MISSING_VALUE, field_name, f"'{field_name}' is not provided.")
    return None


def _measured_field(
    collector: _IssueCollector,
    value_field: str,
    value: Decimal | int | None,
    unit_field: str,
    unit: NormalisedCode,
) -> tuple[Decimal | int | None, str | None]:
    """A numeric value with a unit. Unknown stays None, never zero (M3-AC2)."""
    if value is None:
        collector.add(QualityFlag.MISSING_VALUE, value_field, f"'{value_field}' is not provided.")
        return None, unit.code
    if unit.code is None:
        flag = QualityFlag.UNRECOGNISED_UNIT if unit.raw else QualityFlag.MISSING_UNIT
        collector.add(flag, unit_field, f"'{value_field}' has no recognised unit.")
    return value, unit.code


def _range_field(
    collector: _IssueCollector, range_name: str, low: Decimal | None, high: Decimal | None
) -> None:
    if low is None and high is None:
        collector.add(QualityFlag.MISSING_VALUE, range_name, f"'{range_name}' is not provided.")
    elif low is None or high is None:
        collector.add(QualityFlag.INCOMPLETE_RANGE, range_name, f"'{range_name}' has only one bound.")


# ---------------------------------------------------------------------------
# Embedding-ready text (template documented in docs/ai/PREPROCESSING.md)
# ---------------------------------------------------------------------------


def _embedding_record(lines: list[tuple[str, str]]) -> EmbeddingRecord:
    text = "\n".join(f"{label}: {value}" for label, value in lines if value)
    digest = hashlib.sha256(f"{EMBEDDING_TEXT_TEMPLATE_VERSION}\n{text}".encode()).hexdigest()
    return EmbeddingRecord(text=text, source_hash=digest)


def build_candidate_embedding_record(candidate: SupplierCandidateInput) -> EmbeddingRecord:
    """Capability text: descriptive fields only. Numbers are handled by rules, not semantics."""
    category = normalise_category(candidate.product_category)
    return _embedding_record(
        [
            ("Product", normalise_text(candidate.product_name)),
            ("Category", category.code or category.raw),
            ("Description", normalise_text(candidate.description)),
            ("Specifications", normalise_text(candidate.specifications)),
            ("Supplier capability", normalise_text(candidate.supplier_industry_description)),
        ]
    )


def build_requirement_embedding_record(requirement: BuyerRequirementInput) -> EmbeddingRecord:
    category = normalise_category(requirement.product_category)
    return _embedding_record(
        [
            ("Requirement", normalise_text(requirement.title)),
            ("Category", category.code or category.raw),
            ("Specification", normalise_text(requirement.specification_text)),
        ]
    )


# ---------------------------------------------------------------------------
# Public Stage 1 entry points
# ---------------------------------------------------------------------------


def prepare_candidate(candidate: SupplierCandidateInput) -> PreparedCandidate:
    collector = _IssueCollector()

    values: dict[str, object] = {
        "product_name": normalise_text(candidate.product_name),
        "supplier_record_status": normalise_text(candidate.supplier_record_status).lower() or None,
        "readiness_status": candidate.readiness_status,
        "product_category": _coded_field(
            collector, "product_category", normalise_category(candidate.product_category),
            QualityFlag.UNRECOGNISED_CATEGORY,
        ),
        "origin_country": _coded_field(
            collector, "origin", normalise_country(candidate.origin), QualityFlag.UNRECOGNISED_COUNTRY
        ),
        "supplier_country": _coded_field(
            collector, "supplier_country", normalise_country(candidate.supplier_country),
            QualityFlag.UNRECOGNISED_COUNTRY,
        ),
    }

    values["moq_value"], values["moq_unit"] = _measured_field(
        collector, "moq_value", candidate.moq_value, "moq_unit", normalise_quantity_unit(candidate.moq_unit)
    )
    values["capacity_quantity"], values["capacity_unit"] = _measured_field(
        collector, "capacity_quantity", candidate.capacity_quantity,
        "capacity_unit", normalise_quantity_unit(candidate.capacity_unit),
    )
    values["capacity_period"] = (
        _coded_field(
            collector, "capacity_period", normalise_capacity_period(candidate.capacity_period),
            QualityFlag.UNRECOGNISED_UNIT,
        )
        if candidate.capacity_quantity is not None
        else None
    )
    values["lead_time_value"], values["lead_time_unit"] = _measured_field(
        collector, "lead_time_value", candidate.lead_time_value,
        "lead_time_unit", normalise_lead_time_unit(candidate.lead_time_unit),
    )

    _range_field(collector, "price_range", candidate.price_min, candidate.price_max)
    values["price_min"] = candidate.price_min
    values["price_max"] = candidate.price_max
    values["currency"] = (
        _coded_field(collector, "currency", normalise_currency(candidate.currency), QualityFlag.UNRECOGNISED_CURRENCY)
        if candidate.price_min is not None or candidate.price_max is not None
        else normalise_currency(candidate.currency).code
    )

    values["evidence_types"] = tuple(
        sorted({normalise_evidence_type(item.document_type) for item in candidate.evidence if item.document_type})
    )

    if not (normalise_text(candidate.description) or normalise_text(candidate.specifications)):
        collector.add(
            QualityFlag.NO_DESCRIPTIVE_TEXT, "description",
            "No description or specifications; the semantic signal will rely on the name only.",
        )

    return PreparedCandidate(
        candidate_id=candidate.candidate_id,
        supplier_id=candidate.supplier_id,
        values=values,
        quality_issues=tuple(collector.issues),
        embedding=build_candidate_embedding_record(candidate),
    )


def prepare_requirement(requirement: BuyerRequirementInput) -> PreparedRequirement:
    collector = _IssueCollector()

    values: dict[str, object] = {
        "title": normalise_text(requirement.title),
        "product_category": _coded_field(
            collector, "product_category", normalise_category(requirement.product_category),
            QualityFlag.UNRECOGNISED_CATEGORY,
        ),
        "target_market": _coded_field(
            collector, "target_market", normalise_country(requirement.target_market),
            QualityFlag.UNRECOGNISED_COUNTRY, required_for_quality=False,
        ),
        "delivery_country": _coded_field(
            collector, "delivery_country", normalise_country(requirement.delivery_country),
            QualityFlag.UNRECOGNISED_COUNTRY, required_for_quality=False,
        ),
    }
    values["quantity_value"], values["quantity_unit"] = _measured_field(
        collector, "quantity_value", requirement.quantity_value,
        "quantity_unit", normalise_quantity_unit(requirement.quantity_unit),
    )
    values["required_lead_time_value"], values["required_lead_time_unit"] = (
        (requirement.required_lead_time_value, normalise_lead_time_unit(requirement.required_lead_time_unit).code)
        if requirement.required_lead_time_value is None
        else _measured_field(
            collector, "required_lead_time_value", requirement.required_lead_time_value,
            "required_lead_time_unit", normalise_lead_time_unit(requirement.required_lead_time_unit),
        )
    )
    values["target_price_min"] = requirement.target_price_min
    values["target_price_max"] = requirement.target_price_max
    values["currency_code"] = normalise_currency(requirement.currency_code).code
    values["mandatory_evidence"] = tuple(
        sorted(
            normalise_evidence_type(item.evidence_type)
            for item in requirement.evidence_criteria
            if item.classification.strip().lower() == "mandatory"
        )
    )
    values["preferred_evidence"] = tuple(
        sorted(
            normalise_evidence_type(item.evidence_type)
            for item in requirement.evidence_criteria
            if item.classification.strip().lower() != "mandatory"
        )
    )

    if not (normalise_text(requirement.title) or normalise_text(requirement.specification_text)):
        collector.add(
            QualityFlag.NO_DESCRIPTIVE_TEXT, "specification_text",
            "No title or specification text; a semantic signal cannot be computed meaningfully.",
        )

    return PreparedRequirement(
        requirement_id=requirement.requirement_id,
        requirement_version=requirement.requirement_version,
        values=values,
        quality_issues=tuple(collector.issues),
        embedding=build_requirement_embedding_record(requirement),
    )
