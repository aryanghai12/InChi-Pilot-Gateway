"""Week 4 API acceptance checks: M4/M5 and v2.2 sections 6-8.

Run against config.settings with pytest-django. Users and records are synthetic;
each test gets a rolled-back database. Current reference codes are compatibility
fixtures, not approval of the three-role/seven-category implementation (D-22/23).
Product failures deliberately remain ordinary failing assertions.
"""

import copy
import secrets
import uuid
from types import SimpleNamespace

import pytest
from apps.accounts.models import Role, User
from apps.audit.models import AuditEvent
from apps.demand.models import BuyerRequirement, ProductCategory
from apps.readiness.models import AssessmentEvidence, ReadinessAssessment
from apps.registry.models import Product, Supplier
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
ASSESSMENTS = "/api/v1/assessments/"
REQUIREMENTS = "/api/v1/requirements/"
MANDATORY = ["CR-01", "CR-02", "CR-04", *[f"CR-{i:02d}" for i in range(6, 19)]]


@pytest.fixture
def records(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    users = {}
    for name, role in (
        ("analyst", Role.COMMERCIAL_ANALYST),
        ("reviewer", Role.REVIEWER),
        ("admin", Role.PLATFORM_ADMIN),
    ):
        users[name] = User.objects.create_user(
            email=f"qa-week4-{uuid.uuid4()}@example.test",
            password=secrets.token_urlsafe(32),
            role=role,
            is_verified=True,
        )
    supplier = Supplier.objects.create(
        legal_name="Synthetic Week 4 Supplier", country_of_registration="IN"
    )
    product = Product.objects.create(
        supplier=supplier,
        product_name="Synthetic Valve",
        product_category="Engineering Goods",
    )
    answers = {key: {"response": "Recorded synthetic response"} for key in MANDATORY}
    answers.update(
        {
            "CR-02": {"response": "MANUFACTURER"},
            "CR-04": {"response": "0123456789"},
            "CR-06": {"response": str(product.pk)},
            "CR-07": {"response": "ENG_COMPONENT"},
            "CR-08": {"response": "Yes"},
            "CR-09": {"response": "100 PIECE per month"},
            "CR-10": {"response": "MOQ 1 PIECE; lead time 10 days"},
            "CR-11": {"response": "10 USD per PIECE FOB"},
            "CR-13": {"response": "None"},
            "CR-14": {"response": "No"},
            "CR-18": {"response": "Confirmed", "is_limitation_declared": True},
        }
    )
    assessment = ReadinessAssessment.objects.create(
        supplier=supplier, answers=answers, created_by=users["analyst"]
    )
    assessment.linked_products.add(product)
    demand = BuyerRequirement.objects.create(
        buyer_organisation_name="Synthetic China Buyer",
        product_category=ProductCategory.ENGINEERING_GOODS,
        product_specifications="Valve; stainless steel; 40 mm",
        quantity_value="100.00",
        quantity_unit="PIECES",
        delivery_location="Shanghai, China",
        mandatory_criteria=[{"name": "40 mm valve", "type": "mandatory"}],
        preferred_criteria=[{"name": "Prior export experience", "type": "preferred"}],
        owner=users["analyst"],
        created_by=users["analyst"],
    )
    demand.refresh_from_db()
    return SimpleNamespace(
        users=users,
        supplier=supplier,
        product=product,
        assessment=assessment,
        demand=demand,
    )


def client_for(records, role="analyst", csrf=False):
    client = APIClient(enforce_csrf_checks=csrf)
    if role != "anonymous":
        client.force_login(records.users[role])
    return client


def event_for(obj, action):
    events = AuditEvent.objects.filter(object_id=str(obj.pk), action=action)
    assert events.count() == 1
    event = events.get()
    assert event.actor_id and event.reason and event.timestamp
    return event


@pytest.mark.parametrize("criterion", MANDATORY)
def test_m4_ac1_each_missing_submission_answer_is_rejected(records, criterion):
    assessment = records.assessment
    assessment.answers.pop(criterion)
    assessment.save()
    response = client_for(records).post(
        f"{ASSESSMENTS}{assessment.pk}/submit/", {}, format="json"
    )
    assert response.status_code == 400
    assert criterion in str(response.json())
    assessment.refresh_from_db()
    assert assessment.workflow_state == "draft" and assessment.version == 1
    assert not AuditEvent.objects.filter(
        object_id=str(assessment.pk), action="submit"
    ).exists()


@pytest.mark.parametrize("response_value", ["", "   ", None])
def test_m4_ac1_blank_required_response_is_rejected(records, response_value):
    assessment = records.assessment
    assessment.answers["CR-01"] = {"response": response_value}
    assessment.save()
    response = client_for(records).post(
        f"{ASSESSMENTS}{assessment.pk}/submit/", {}, format="json"
    )
    assert response.status_code == 400
    assert "CR-01" in str(response.json())


def test_m4_ac1_product_link_required(records):
    records.assessment.linked_products.clear()
    response = client_for(records).post(
        f"{ASSESSMENTS}{records.assessment.pk}/submit/", {}, format="json"
    )
    assert response.status_code == 400
    assert "product" in str(response.json()).lower()


@pytest.mark.parametrize("confirmed", ["No", "Unknown", ""])
def test_m4_ac1_limitation_confirmation_required(records, confirmed):
    assessment = records.assessment
    assessment.answers["CR-18"] = {
        "response": confirmed,
        "is_limitation_declared": False,
    }
    assessment.save()
    response = client_for(records).post(
        f"{ASSESSMENTS}{assessment.pk}/submit/", {}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.parametrize("state", ["draft", "information_required"])
def test_m4_ac2_ac5_ac6_submit_persists_actor_version_and_audit(records, state):
    assessment = records.assessment
    assessment.workflow_state = state
    assessment.save()
    client = client_for(records)
    response = client.post(
        f"{ASSESSMENTS}{assessment.pk}/submit/",
        {"submission_notes": "Synthetic submission"},
        format="json",
    )
    assert response.status_code == 200
    assessment.refresh_from_db()
    assert assessment.workflow_state == "submitted"
    assert assessment.readiness_outcome is None
    assert assessment.submitted_by_id == records.users["analyst"].pk
    assert assessment.version == 2 and assessment.questionnaire_version == "2.2"
    assert (
        client.get(f"{ASSESSMENTS}{assessment.pk}/").json()["submission_notes"]
        == "Synthetic submission"
    )
    event_for(assessment, "submit")


@pytest.mark.parametrize(
    "state", ["submitted", "under_review", "review_complete", "archived"]
)
def test_m4_submit_rejects_invalid_source_states(records, state):
    assessment = records.assessment
    assessment.workflow_state = state
    assessment.save()
    response = client_for(records).post(
        f"{ASSESSMENTS}{assessment.pk}/submit/", {}, format="json"
    )
    assert response.status_code == 400
    assessment.refresh_from_db()
    assert assessment.workflow_state == state and assessment.version == 1


@pytest.mark.parametrize("state", ["draft", "submitted", "review_complete", "archived"])
@pytest.mark.parametrize(
    "action,payload",
    [
        (
            "complete-review",
            {
                "readiness_outcome": "ready_for_matching",
                "reviewer_notes": "Synthetic reason",
            },
        ),
        ("request-information", {"request_notes": "Please clarify capacity"}),
    ],
)
def test_m4_review_actions_require_under_review_state(records, state, action, payload):
    assessment = records.assessment
    assessment.workflow_state = state
    assessment.save()
    response = client_for(records, "reviewer").post(
        f"{ASSESSMENTS}{assessment.pk}/{action}/", payload, format="json"
    )
    assessment.refresh_from_db()
    assert 400 <= response.status_code < 500, (
        f"Invalid {state} -> {action} accepted ({response.status_code})"
    )
    assert assessment.workflow_state == state and assessment.version == 1


@pytest.mark.parametrize(
    "action,payload,expected",
    [
        (
            "complete-review",
            {
                "readiness_outcome": "information_required",
                "reviewer_notes": "Capacity needs clarification",
            },
            "review_complete",
        ),
        (
            "request-information",
            {"request_notes": "Please clarify capacity"},
            "information_required",
        ),
    ],
)
def test_m4_permitted_review_actions_persist(records, action, payload, expected):
    assessment = records.assessment
    assessment.workflow_state = "under_review"
    assessment.submitted_by = records.users["analyst"]
    assessment.save()
    response = client_for(records, "reviewer").post(
        f"{ASSESSMENTS}{assessment.pk}/{action}/", payload, format="json"
    )
    assert response.status_code == 200
    assessment.refresh_from_db()
    assert assessment.workflow_state == expected and assessment.version == 2
    event_for(assessment, "review" if action == "complete-review" else "request_info")


@pytest.mark.parametrize("reason", ["", "   ", None])
@pytest.mark.parametrize(
    "action,reason_field",
    [("complete-review", "reviewer_notes"), ("request-information", "request_notes")],
)
def test_m4_ac3_reason_required(records, reason, action, reason_field):
    assessment = records.assessment
    assessment.workflow_state = "under_review"
    assessment.save()
    payload = {reason_field: reason}
    if action == "complete-review":
        payload["readiness_outcome"] = "ready_for_matching"
    response = client_for(records, "reviewer").post(
        f"{ASSESSMENTS}{assessment.pk}/{action}/", payload, format="json"
    )
    assert response.status_code == 400
    assert reason_field in str(response.json())
    assessment.refresh_from_db()
    assert assessment.workflow_state == "under_review" and assessment.version == 1


def test_m4_ac3_self_review_denied(records):
    assessment = records.assessment
    assessment.workflow_state = "under_review"
    assessment.submitted_by = records.users["reviewer"]
    assessment.save()
    response = client_for(records, "reviewer").post(
        f"{ASSESSMENTS}{assessment.pk}/complete-review/",
        {
            "readiness_outcome": "ready_for_matching",
            "reviewer_notes": "Synthetic reason",
        },
        format="json",
    )
    assert response.status_code == 403
    assessment.refresh_from_db()
    assert assessment.workflow_state == "under_review"


@pytest.mark.parametrize(
    "field,value",
    [
        ("readiness_outcome", "ready_for_matching"),
        ("outcome", "ready_for_matching"),
        ("workflow_state", "review_complete"),
        ("status", "review_complete"),
    ],
)
def test_m4_ac2_ac3_analyst_cannot_bypass_review_with_patch(records, field, value):
    assessment = records.assessment
    response = client_for(records).patch(
        f"{ASSESSMENTS}{assessment.pk}/", {field: value}, format="json"
    )
    assessment.refresh_from_db()
    assert assessment.readiness_outcome is None, (
        f"Unauthorized {field} persisted ({response.status_code})"
    )
    assert assessment.workflow_state == "draft", (
        f"Review bypass through {field} ({response.status_code})"
    )


def test_m4_gate_requires_referenced_evidence_record(records):
    assessment = records.assessment
    assessment.answers["CR-13"] = {
        "response": "Synthetic report",
        "evidence_reference": "missing-report",
        "evidence_condition": "document_received_unverified",
    }
    assessment.save()
    response = client_for(records).post(
        f"{ASSESSMENTS}{assessment.pk}/submit/", {}, format="json"
    )
    assert response.status_code == 400, (
        "Section 6.1: referenced document has no Evidence record"
    )
    assessment.refresh_from_db()
    assert assessment.workflow_state == "draft"


@pytest.mark.parametrize("condition", ["expired", "discrepancy"])
@pytest.mark.skip(
    reason="Blocked: no agreed API field/contract identifies mandatory assessment evidence; free-text fixture labels do not prove applicability (W4-04)"
)
def test_m4_ac07_ac08_unresolved_mandatory_evidence_blocks_ready(records, condition):
    assessment = records.assessment
    assessment.workflow_state = "under_review"
    assessment.answers["CR-13"] = {
        "response": "Required current test report",
        "evidence_reference": "synthetic-report",
        "evidence_condition": condition,
    }
    assessment.answers["CR-14"] = {
        "response": "Yes",
        "notes": "Mandatory report issue remains unresolved",
    }
    assessment.save()
    AssessmentEvidence.objects.create(
        assessment=assessment,
        criterion_id="CR-13",
        document_name="synthetic-report",
        evidence_condition=condition,
    )
    response = client_for(records, "reviewer").post(
        f"{ASSESSMENTS}{assessment.pk}/complete-review/",
        {
            "readiness_outcome": "ready_for_matching",
            "reviewer_notes": "Issue remains unresolved; no exception or resolution",
        },
        format="json",
    )
    assert response.status_code == 400, (
        "Unresolved mandatory evidence accepted as Ready for Matching"
    )
    assessment.refresh_from_db()
    assert assessment.readiness_outcome is None


def test_m4_ac05_evidence_defaults_unverified(records):
    client = client_for(records)
    response = client.post(
        "/api/v1/assessment-evidence/",
        {
            "assessment": str(records.assessment.pk),
            "criterion_id": "CR-13",
            "document_name": "Synthetic report",
        },
        format="json",
    )
    assert response.status_code == 201
    evidence = AssessmentEvidence.objects.get(pk=response.json()["id"])
    assert evidence.evidence_condition == "document_received_unverified"
    assert (
        client.get(f"/api/v1/assessment-evidence/{evidence.pk}/").json()[
            "document_name"
        ]
        == "Synthetic report"
    )
    event_for(evidence, "create")


@pytest.mark.parametrize("condition", ["verified", "approved", "", None])
def test_m4_evidence_rejects_invalid_condition(records, condition):
    response = client_for(records).post(
        "/api/v1/assessment-evidence/",
        {
            "assessment": str(records.assessment.pk),
            "criterion_id": "CR-13",
            "document_name": "Synthetic report",
            "evidence_condition": condition,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "evidence_condition" in response.json()["field_errors"]
    assert not AssessmentEvidence.objects.filter(assessment=records.assessment).exists()


def test_m4_create_requires_supplier(records):
    response = client_for(records).post(ASSESSMENTS, {}, format="json")
    assert response.status_code == 400
    assert "supplier" in response.json()["field_errors"]


@pytest.mark.parametrize("field", ["submitted_by", "reviewer"])
def test_m4_ac5_analyst_cannot_forge_workflow_actors(records, field):
    assessment = records.assessment
    response = client_for(records).patch(
        f"{ASSESSMENTS}{assessment.pk}/",
        {
            field: records.users["reviewer"].pk,
        },
        format="json",
    )
    assessment.refresh_from_db()
    assert getattr(assessment, f"{field}_id") is None, (
        f"Forged {field} accepted ({response.status_code})"
    )


@pytest.mark.parametrize(
    "resource,action",
    [("assessment", "submit"), ("demand", "mark-ready"), ("demand", "close")],
)
def test_m4_m5_anonymous_mutation_denied(records, resource, action):
    obj = getattr(records, resource)
    base = ASSESSMENTS if resource == "assessment" else REQUIREMENTS
    response = APIClient().post(f"{base}{obj.pk}/{action}/", {}, format="json")
    assert response.status_code == 401
    obj.refresh_from_db()
    assert obj.version == 1


@pytest.mark.parametrize("action", ["mark-ready", "close"])
def test_m5_current_policy_reviewer_lifecycle_denied(records, action):
    # Characterizes the current policy; v2.2 Reviewer close permission awaits D-22.
    response = client_for(records, "reviewer").post(
        f"{REQUIREMENTS}{records.demand.pk}/{action}/", {}, format="json"
    )
    assert response.status_code == 403
    records.demand.refresh_from_db()
    assert records.demand.requirement_status == "draft" and records.demand.version == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("buyer_organisation_name", " "),
        ("quantity_value", "0"),
        ("quantity_value", "-0.01"),
        ("quantity_value", "0.001"),
        ("quantity_value", "1000000000000.00"),
        ("target_price_min", "0"),
        ("target_price_max", "-1"),
        ("delivery_window_end", "not-a-date"),
    ],
)
def test_m5_ac2_invalid_patch_is_field_specific_and_atomic(records, field, value):
    demand = records.demand
    original = getattr(demand, field)
    response = client_for(records).patch(
        f"{REQUIREMENTS}{demand.pk}/", {field: value}, format="json"
    )
    assert response.status_code == 400
    assert field in str(response.json())
    demand.refresh_from_db()
    assert getattr(demand, field) == original and demand.version == 1


@pytest.mark.parametrize("quantity", ["0.01", "999999999999.99"])
def test_m5_quantity_valid_decimal_boundaries_persist(records, quantity):
    client = client_for(records)
    response = client.patch(
        f"{REQUIREMENTS}{records.demand.pk}/",
        {"quantity_value": quantity},
        format="json",
    )
    assert response.status_code == 200
    assert (
        client.get(f"{REQUIREMENTS}{records.demand.pk}/").json()["quantity_value"]
        == quantity
    )


@pytest.mark.parametrize(
    "low,high,expected", [("1", "2", 200), ("2", "2", 200), ("3", "2", 400)]
)
def test_m5_price_bounds(records, low, high, expected):
    response = client_for(records).patch(
        f"{REQUIREMENTS}{records.demand.pk}/",
        {"target_price_min": low, "target_price_max": high},
        format="json",
    )
    assert response.status_code == expected
    if expected == 400:
        assert "target_price_max" in str(response.json())


@pytest.mark.parametrize(
    "start,end,expected",
    [
        ("2026-11-20", "2026-11-21", 200),
        ("2026-11-20", "2026-11-20", 200),
        ("2026-11-21", "2026-11-20", 400),
    ],
)
def test_m5_delivery_window_bounds(records, start, end, expected):
    response = client_for(records).patch(
        f"{REQUIREMENTS}{records.demand.pk}/",
        {"delivery_window_start": start, "delivery_window_end": end},
        format="json",
    )
    assert response.status_code == expected


@pytest.mark.parametrize(
    "field",
    [
        "quantity_value",
        "quantity_unit",
        "target_market",
        "delivery_location",
        "product_specifications",
    ],
)
@pytest.mark.parametrize("route", ["action", "patch"])
def test_m5_ac2_ready_gate_cannot_be_bypassed(records, field, route):
    demand = records.demand
    setattr(demand, field, None if field == "quantity_value" else "")
    demand.save()
    client = client_for(records)
    if route == "action":
        response = client.post(
            f"{REQUIREMENTS}{demand.pk}/mark-ready/", {}, format="json"
        )
    else:
        response = client.patch(
            f"{REQUIREMENTS}{demand.pk}/",
            {"requirement_status": "ready_for_matching"},
            format="json",
        )
    assert response.status_code == 400, (
        f"Missing {field} bypassed readiness via {route}"
    )
    demand.refresh_from_db()
    assert demand.requirement_status == "draft" and demand.version == 1


def test_m5_ac1_ac5_create_ready_close_persists_and_audits(records):
    client = client_for(records)
    payload = {
        "buyer_organisation_name": "Synthetic workflow buyer",
        "product_category": "Engineering Goods",
        "product_specifications": "40 mm valve",
        "quantity_value": "100.00",
        "quantity_unit": "PIECES",
        "delivery_location": "Shanghai, China",
        "mandatory_criteria": [{"name": "40 mm", "type": "mandatory"}],
        "preferred_criteria": [{"name": "Export experience", "type": "preferred"}],
    }
    response = client.post(REQUIREMENTS, payload, format="json")
    assert response.status_code == 201
    demand = BuyerRequirement.objects.get(pk=response.json()["id"])
    assert demand.mandatory_criteria != demand.preferred_criteria
    assert demand.owner_id == records.users["analyst"].pk
    event_for(demand, "create")
    for action, state, version in (
        ("mark-ready", "ready_for_matching", 2),
        ("close", "closed", 3),
    ):
        assert (
            client.post(
                f"{REQUIREMENTS}{demand.pk}/{action}/", {}, format="json"
            ).status_code
            == 200
        )
        data = client.get(f"{REQUIREMENTS}{demand.pk}/").json()
        assert data["requirement_status"] == state and data["version"] == version
        event_for(demand, "mark_ready" if action == "mark-ready" else "close")
    assert (
        client.post(
            f"{REQUIREMENTS}{demand.pk}/mark-ready/", {}, format="json"
        ).status_code
        == 400
    )


@pytest.mark.parametrize("resource", ["assessment", "demand"])
def test_m4_m5_stale_patch_returns_409_without_mutation(records, resource):
    obj = getattr(records, resource)
    base = ASSESSMENTS if resource == "assessment" else REQUIREMENTS
    field = "submission_notes" if resource == "assessment" else "requirement_notes"
    client = client_for(records)
    assert (
        client.patch(
            f"{base}{obj.pk}/", {field: "First edit", "version": 1}, format="json"
        ).status_code
        == 200
    )
    response = client.patch(
        f"{base}{obj.pk}/", {field: "Stale edit", "version": 1}, format="json"
    )
    assert response.status_code == 409
    obj.refresh_from_db()
    assert getattr(obj, field) == "First edit" and obj.version == 2


@pytest.mark.parametrize(
    "base", [ASSESSMENTS, REQUIREMENTS, "/api/v1/assessment-evidence/"]
)
def test_m4_m5_anonymous_read_denied(base):
    response = APIClient().get(base)
    assert (
        response.status_code == 401 and response.json()["code"] == "not_authenticated"
    )


@pytest.mark.parametrize("role", ["reviewer", "admin"])
@pytest.mark.parametrize("resource", ["assessment", "demand"])
def test_m4_m5_current_policy_denies_source_edits(records, role, resource):
    # Current policy characterization only: v2.2 admin/contributor matrix is Blocked D-22.
    obj = getattr(records, resource)
    base = ASSESSMENTS if resource == "assessment" else REQUIREMENTS
    field = "submission_notes" if resource == "assessment" else "requirement_notes"
    response = client_for(records, role).patch(
        f"{base}{obj.pk}/", {field: "Unauthorized edit"}, format="json"
    )
    assert response.status_code == 403
    obj.refresh_from_db()
    assert getattr(obj, field) == "" and obj.version == 1


@pytest.mark.parametrize("role", ["analyst", "admin"])
@pytest.mark.parametrize(
    "action,payload",
    [
        (
            "complete-review",
            {
                "readiness_outcome": "ready_for_matching",
                "reviewer_notes": "Synthetic reason",
            },
        ),
        ("request-information", {"request_notes": "Synthetic reason"}),
    ],
)
def test_m4_current_policy_denies_review_actions(records, role, action, payload):
    response = client_for(records, role).post(
        f"{ASSESSMENTS}{records.assessment.pk}/{action}/", payload, format="json"
    )
    assert response.status_code == 403
    records.assessment.refresh_from_db()
    assert records.assessment.workflow_state == "draft"


@pytest.mark.parametrize(
    "resource,action", [("assessment", "submit"), ("demand", "mark-ready")]
)
def test_m4_m5_session_mutations_require_csrf(records, resource, action):
    obj = getattr(records, resource)
    base = ASSESSMENTS if resource == "assessment" else REQUIREMENTS
    response = client_for(records, csrf=True).post(
        f"{base}{obj.pk}/{action}/", {}, format="json"
    )
    assert response.status_code == 403
    obj.refresh_from_db()
    assert obj.version == 1


def test_m4_request_information_resubmit_preserves_reviewer_notes(records):
    assessment = records.assessment
    assessment.workflow_state = "under_review"
    assessment.save()
    response = client_for(records, "reviewer").post(
        f"{ASSESSMENTS}{assessment.pk}/request-information/",
        {"request_notes": "Clarify capacity period"},
        format="json",
    )
    assert response.status_code == 200
    original_answers = copy.deepcopy(assessment.answers)
    assert (
        client_for(records)
        .post(f"{ASSESSMENTS}{assessment.pk}/submit/", {}, format="json")
        .status_code
        == 200
    )
    assessment.refresh_from_db()
    assert assessment.answers == original_answers
    assert assessment.information_request_notes == "Clarify capacity period"
    assert assessment.workflow_state == "submitted" and assessment.version == 3


@pytest.mark.parametrize(
    "reason",
    [
        "AC-06/AC-22 SEC-01/02: Contributor and Viewer roles absent; D-22 migration/contract pending",
        "M4-AC4 AC-10: immutable submission/history API absent; counter increment is not snapshot evidence",
        "M5-AC3 AC-18/21: immutable requirement versions and match-run API absent",
        "M4 v2.2 8.1: assignment/reassessment/archive action contracts absent",
        "M5-AC4 D-23: approved reference/criteria-version API absent",
        "SEC-03: record ownership/access boundary needs an agreed contract; no invented ownership policy",
    ],
)
def test_week4_blocked_contracts(reason):
    pytest.skip("Blocked: " + reason)
