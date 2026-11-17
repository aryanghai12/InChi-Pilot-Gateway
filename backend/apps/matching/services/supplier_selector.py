"""
Candidate Supplier Selection and Payload Preparation Service.

Coordinates candidate data preparation and transforms database records into the
payload format expected by the FastAPI matching engine.

candidate_from_product() maps one registry Product (with its Supplier and
evidence metadata) to a SupplierCandidatePayload, field for field, without
filtering, scoring or guessing. Unknown values stay unknown (M3-AC2).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Week 3 implementation (payload mapping only).

STRICT OWNERSHIP BOUNDARY:
- Vishal Chauhan (C6 — Data and Platform Services Engineer) owns all Django database
  models, migrations, PostgreSQL schemas, pgvector columns, and database-level candidate
  query design and optimization.
- Coordination with Vishal is required for all database-level query logic.
- This module defines NO candidate query. Callers pass products obtained from Vishal's
  candidate query. For efficiency that query should use
  select_related("supplier") and prefetch_related("evidence_items", "supplier__evidence_items").
- No eligibility filtering happens here: mandatory criteria are evaluated by the engine.
"""

from __future__ import annotations

from collections.abc import Iterable

from apps.matching.schemas.matching_request import (
    EvidencePayload,
    SupplierCandidatePayload,
)


def _evidence_payload(item) -> EvidencePayload:
    return EvidencePayload(
        document_type=item.document_type or "",
        presence_status=item.presence_status or "",
        review_status=item.review_status or "",
        expiry_date=item.expiry_date.isoformat() if item.expiry_date else None,
    )


def candidate_from_product(product, readiness_status: str | None = None) -> SupplierCandidatePayload:
    """
    Map a registry Product to the engine candidate payload.

    readiness_status: the reviewed readiness outcome for the supplier, if the
    caller has one. The M4 readiness module does not exist yet, so it defaults
    to None (unknown) rather than any assumed status.
    """
    supplier = product.supplier
    evidence = [*product.evidence_items.all(), *supplier.evidence_items.all()]

    return SupplierCandidatePayload(
        candidate_id=str(product.id),
        supplier_id=str(supplier.id),
        supplier_name=supplier.legal_name or supplier.trade_name or "",
        supplier_country=supplier.country_of_registration or "",
        supplier_record_status=supplier.record_status or "",
        supplier_industry_description=supplier.industry_description or "",
        readiness_status=readiness_status,
        product_name=product.product_name,
        product_category=product.product_category or "",
        description=product.description or "",
        specifications=product.specifications or "",
        origin=product.origin or "",
        moq_value=product.moq_value,
        moq_unit=product.moq_unit or "",
        price_min=product.price_min,
        price_max=product.price_max,
        currency=product.currency or "",
        price_basis=product.price_basis or "",
        capacity_quantity=product.capacity_quantity,
        capacity_unit=product.capacity_unit or "",
        capacity_period=product.capacity_period or "",
        lead_time_value=product.lead_time_value,
        lead_time_unit=product.lead_time_unit or "",
        evidence=tuple(_evidence_payload(item) for item in evidence),
    )


def build_candidate_payloads(
    products: Iterable, readiness_by_supplier: dict[str, str] | None = None
) -> tuple[SupplierCandidatePayload, ...]:
    """Map every product in order. readiness_by_supplier maps supplier ID -> readiness outcome."""
    readiness = readiness_by_supplier or {}
    return tuple(candidate_from_product(p, readiness.get(str(p.supplier_id))) for p in products)
