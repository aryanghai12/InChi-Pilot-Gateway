"""
Integration Tests: matching service orchestration, requirement adapter, result
records and weekly summaries (Component A).

Named test_views.py per the ARCHITECTURE.md §4.1 layout; there are no matching
DRF views yet (they belong to Abhishek, C5), so these tests exercise the
service layer that those views will call. The engine is replaced by a fake
client — no network.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase

from apps.audit.models import AuditEvent
from apps.demand.models import BuyerRequirement, RequirementStatus
from apps.matching.exceptions.matching_exceptions import (
    InvalidMatchingPayloadError,
    MatchingEngineResponseError,
    MatchingEngineTimeoutError,
)
from apps.matching.schemas.matching_response import MatchingResponsePayload
from apps.matching.services import result_handler, weekly_summary
from apps.matching.services.matching_service import run_matching
from apps.matching.services.request_builder import requirement_payload_from_model
from apps.matching.tests.helpers import engine_success_response
from apps.registry.models import Product, Supplier, SupplierStatus


class _FakeClient:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.requests = response, error, []

    def match(self, payload):
        self.requests.append(payload)
        if self.error:
            raise self.error
        return self.response


class _FakePersister:
    def __init__(self):
        self.saved = []

    def save_run(self, record):
        self.saved.append(record)
        return SimpleNamespace(id=uuid.uuid4())


def _ready_requirement(**overrides) -> BuyerRequirement:
    fields = dict(
        buyer_organisation_name="Synthetic Buyer Ltd",
        requirement_title="Synthetic circuit boards",
        target_market="China",
        product_category="Electronic Goods",
        product_specifications="Synthetic two-layer boards.",
        quantity_value=Decimal(500),
        quantity_unit="PIECES",
        delivery_location="Synthetic Port",
        requirement_status=RequirementStatus.READY_FOR_MATCHING,
        mandatory_criteria=[
            {"criterion_key": "origin_country", "operator": "equals", "value": {"value": "IN"}},
            {"id": "m-1", "name": "Synthetic ISO certificate", "type": "mandatory"},
        ],
        preferred_criteria=[{"id": "p-1", "name": "Fast delivery", "type": "preferred"}],
        required_evidence=[{"id": "e-1", "document_name": "QUALITY_CERTIFICATE", "is_mandatory": True}],
    )
    fields.update(overrides)
    return BuyerRequirement.objects.create(**fields)


class RequirementAdapterTests(TestCase):
    def test_structured_criteria_pass_through(self):
        payload = requirement_payload_from_model(_ready_requirement())
        first = payload.mandatory_criteria[0]
        self.assertEqual((first.criterion_key, first.operator, first.value), ("origin_country", "equals", {"value": "IN"}))

    def test_free_text_criterion_becomes_manual_review(self):
        second = requirement_payload_from_model(_ready_requirement()).mandatory_criteria[1]
        self.assertEqual(second.operator, "manual_review")
        self.assertEqual(second.value, {"text": "Synthetic ISO certificate"})

    def test_free_text_preference_is_unscored(self):
        pref = requirement_payload_from_model(_ready_requirement()).preference_criteria[0]
        self.assertEqual(pref.weight_key, "")
        self.assertNotIn("operator", pref.value)

    def test_evidence_and_core_fields(self):
        payload = requirement_payload_from_model(_ready_requirement())
        self.assertEqual(payload.evidence_criteria[0].evidence_type, "QUALITY_CERTIFICATE")
        self.assertEqual(payload.evidence_criteria[0].classification, "mandatory")
        self.assertEqual(payload.specification_text, "Synthetic two-layer boards.")
        self.assertEqual(payload.quantity_value, Decimal("500.00"))
        self.assertEqual(payload.delivery_country, "")  # never derived from free-text location

    def test_oversized_specification_rejected(self):
        with self.assertRaises(InvalidMatchingPayloadError):
            requirement_payload_from_model(_ready_requirement(product_specifications="x" * 5001))

    def test_long_free_text_criterion_is_capped(self):
        """ISSUE-034: free-text criteria stay within the engine's value bound."""
        req = _ready_requirement(mandatory_criteria=[{"id": "m-1", "name": "y" * 3000, "type": "mandatory"}])
        criterion = requirement_payload_from_model(req).mandatory_criteria[0]
        self.assertEqual(len(criterion.value["text"]), 500)


class MatchingServiceTests(TestCase):
    def setUp(self):
        supplier = Supplier.objects.create(legal_name="Synthetic Supplier", country_of_registration="IN",
                                           supplier_type="manufacturer", record_status=SupplierStatus.COMPLETE)
        self.product = Product.objects.create(supplier=supplier, product_name="Synthetic Board",
                                              product_category="Electronic Goods", origin="India")
        self.requirement = _ready_requirement()

    def test_completed_run(self):
        client = _FakeClient(MatchingResponsePayload.from_dict(engine_success_response()))
        outcome = run_matching(self.requirement, [self.product], criteria_version="test-v1",
                               correlation_id="corr-9", client=client)
        self.assertTrue(outcome.succeeded)
        self.assertEqual(outcome.candidates_submitted, 1)
        sent = client.requests[0]
        self.assertEqual(sent.criteria_version, "test-v1")
        self.assertEqual(sent.requirement.requirement_id, str(self.requirement.id))

    def test_engine_error_becomes_failed_outcome_without_results(self):
        error = MatchingEngineResponseError(503, "stage_not_available", "pending")
        outcome = run_matching(self.requirement, [self.product], criteria_version="v", client=_FakeClient(error=error))
        self.assertEqual(outcome.status, "failed")
        self.assertIsNone(outcome.response)
        self.assertEqual(outcome.engine_error_code, "stage_not_available")

    def test_timeout_becomes_failed_outcome(self):
        outcome = run_matching(self.requirement, [self.product], criteria_version="v",
                               client=_FakeClient(error=MatchingEngineTimeoutError()))
        self.assertEqual(outcome.error_code, "matching_engine_timeout")

    def test_missing_engine_url_becomes_failed_outcome(self):
        with self.settings():
            import os
            saved = os.environ.pop("FASTAPI_MATCHING_URL", None)
            try:
                outcome = run_matching(self.requirement, [self.product], criteria_version="v")
            finally:
                if saved is not None:
                    os.environ["FASTAPI_MATCHING_URL"] = saved
        self.assertEqual(outcome.error_code, "matching_engine_unavailable")

    def test_not_ready_requirement_rejected_before_any_call(self):
        draft = _ready_requirement(requirement_status=RequirementStatus.DRAFT)
        client = _FakeClient()
        with self.assertRaises(InvalidMatchingPayloadError):
            run_matching(draft, [self.product], criteria_version="v", client=client)
        self.assertEqual(client.requests, [])

    def test_requirement_with_blockers_rejected(self):
        blocked = _ready_requirement(quantity_value=None)
        with self.assertRaises(InvalidMatchingPayloadError):
            run_matching(blocked, [self.product], criteria_version="v", client=_FakeClient())

    def test_criteria_version_required(self):
        import os
        saved = os.environ.pop("MATCHING_CRITERIA_VERSION", None)
        try:
            with self.assertRaises(InvalidMatchingPayloadError):
                run_matching(self.requirement, [self.product], client=_FakeClient())
        finally:
            if saved is not None:
                os.environ["MATCHING_CRITERIA_VERSION"] = saved

    def test_persister_receives_record_and_audit_event_written(self):
        persister = _FakePersister()
        client = _FakeClient(MatchingResponsePayload.from_dict(engine_success_response()))
        run_matching(self.requirement, [self.product], criteria_version="v", client=client, persister=persister)
        self.assertEqual(len(persister.saved), 1)
        self.assertEqual(persister.saved[0].status, "completed")
        self.assertTrue(AuditEvent.objects.filter(action="match_run", outcome="success").exists())

    def test_failed_run_persisted_with_no_results_and_failure_audit(self):
        persister = _FakePersister()
        error = MatchingEngineResponseError(503, "stage_not_available", "pending")
        run_matching(self.requirement, [self.product], criteria_version="v",
                     client=_FakeClient(error=error), persister=persister)
        record = persister.saved[0]
        self.assertEqual(record.status, "failed")
        self.assertEqual(record.results, ())
        self.assertTrue(AuditEvent.objects.filter(action="match_run", outcome="failure").exists())


class ResultRecordTests(TestCase):
    def test_completed_record_carries_m6_ac6_fields(self):
        outcome = SimpleNamespace(
            response=MatchingResponsePayload.from_dict(engine_success_response()),
            requirement_id="r", requirement_version=1, criteria_version="criteria-v1", actor_id=None,
            correlation_id="c", started_at=datetime(2026, 11, 19, tzinfo=UTC),
            finished_at=datetime(2026, 11, 19, tzinfo=UTC), candidates_submitted=1,
            error_code="", error_message="",
        )
        record = result_handler.build_run_record(outcome)
        self.assertEqual((record.status, record.criteria_version, record.embedding_model_id, record.mode),
                         ("completed", "criteria-v1", "test-double", "hybrid"))
        self.assertEqual(record.results[0].rank, 1)
        self.assertEqual(record.results[0].contributions[0]["outcome"], "satisfied")


def _record(day: date, status="completed", error_code="", config="approved", ranked=1):
    return SimpleNamespace(
        started_at=datetime(day.year, day.month, day.day, 10, tzinfo=UTC), status=status,
        requirement_id=f"req-{day.isoformat()}", candidates_submitted=3, candidates_ranked=ranked,
        candidates_excluded=1, candidates_insufficient_data=1, configuration_status=config, error_code=error_code,
    )


class WeeklySummaryTests(TestCase):
    def test_programme_week_numbers(self):
        self.assertEqual(weekly_summary.programme_week(date(2026, 10, 26)), 1)
        self.assertEqual(weekly_summary.programme_week(date(2026, 11, 1)), 1)
        self.assertEqual(weekly_summary.programme_week(date(2026, 11, 19)), 4)

    def test_aggregates_runs_by_week_not_by_day(self):
        records = [
            _record(date(2026, 11, 16)),
            _record(date(2026, 11, 18), status="failed", error_code="matching_engine_timeout"),
            _record(date(2026, 11, 20), config="unapproved"),
            _record(date(2026, 11, 24)),
        ]
        weeks = weekly_summary.summarise_weekly(records)
        self.assertEqual([w.week_number for w in weeks], [4, 5])
        week4 = weeks[0]
        self.assertEqual((week4.runs_total, week4.runs_completed, week4.runs_failed), (3, 2, 1))
        self.assertEqual(week4.failure_codes["matching_engine_timeout"], 1)
        self.assertEqual(week4.runs_with_unapproved_config, 1)
        self.assertEqual(week4.candidates_ranked, 2)  # failed runs contribute no results
        self.assertEqual(week4.week_start, date(2026, 11, 16))
        self.assertEqual(week4.week_end, date(2026, 11, 22))

    def test_report_lines(self):
        lines = weekly_summary.summarise_weekly(
            [_record(date(2026, 11, 18), status="failed", error_code="stage_not_available")]
        )[0].to_report_lines()
        self.assertIn("1 match run(s) — 0 completed, 1 failed", lines[0])
        self.assertIn("stage_not_available ×1", lines[2])

    def test_configurable_programme_start(self):
        weeks = weekly_summary.summarise_weekly([_record(date(2026, 11, 18))], programme_start=date(2026, 10, 19))
        self.assertEqual(weeks[0].week_number, 5)

    def test_week_boundary_uses_reporting_timezone(self):
        """ISSUE-035: 20:00 UTC Sunday 22 Nov is already Monday 23 Nov (week 5) in IST."""
        from zoneinfo import ZoneInfo

        record = _record(date(2026, 11, 22))
        record.started_at = datetime(2026, 11, 22, 20, 0, tzinfo=UTC)
        self.assertEqual(weekly_summary.summarise_weekly([record], tz=ZoneInfo("Asia/Kolkata"))[0].week_number, 5)
        self.assertEqual(weekly_summary.summarise_weekly([record], tz=UTC)[0].week_number, 4)

    def test_naive_timestamps_used_as_is(self):
        record = _record(date(2026, 11, 23))
        record.started_at = datetime(2026, 11, 23, 1, 0)
        self.assertEqual(weekly_summary.summarise_weekly([record])[0].week_number, 5)

    def test_empty(self):
        self.assertEqual(weekly_summary.summarise_weekly([]), [])
