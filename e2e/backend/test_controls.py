"""QA-owned regression against the unchanged Django application (M1/M10)."""
import secrets
import uuid

import pytest
from django.contrib.sessions.models import Session
from django.db import DatabaseError, connection, transaction
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.audit.models import AuditEvent


@pytest.fixture
def account(db):
    password = secrets.token_urlsafe(32)
    user = User.objects.create_user(
        email=f"qa-{uuid.uuid4()}@example.test", password=password,
        role=Role.COMMERCIAL_ANALYST, is_verified=True,
    )
    return user, password


def test_m1_ac3_real_csrf_rejects_anonymous_login(account):
    user, password = account
    client = APIClient(enforce_csrf_checks=True)
    response = client.post("/api/v1/auth/login/", {"email": user.email, "password": password}, format="json")
    assert response.status_code == 403
    assert "application/json" in response["Content-Type"]
    assert response.json()["code"] == "csrf_failed"


def test_m1_ac2_expired_session_denied(account):
    user, _ = account
    client = APIClient()
    client.force_login(user)
    Session.objects.filter(session_key=client.session.session_key).update(expire_date=timezone.now())
    response = client.get("/api/v1/auth/me/")
    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


def test_m1_ac4_deactivation_revokes_next_request(account):
    user, _ = account
    client = APIClient()
    client.force_login(user)
    admin = User.objects.create_user(
        email=f"qa-{uuid.uuid4()}@example.test", password=secrets.token_urlsafe(32),
        role=Role.PLATFORM_ADMIN, is_verified=True,
    )
    administrator = APIClient()
    administrator.force_login(admin)
    response = administrator.post(f"/api/v1/auth/users/{user.pk}/deactivate/", {}, format="json")
    assert response.status_code == 200
    response = client.get("/api/v1/auth/me/")
    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


def test_m1_ac1_login_rotates_existing_session_key(account):
    user, password = account
    client = APIClient(enforce_csrf_checks=True)
    session = client.session
    session["qa_pre_login"] = True
    session.save()
    old_key = session.session_key
    client.get("/api/v1/auth/csrf/")
    response = client.post(
        "/api/v1/auth/login/", {"email": user.email, "password": password}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert response.status_code == 200
    assert client.session.session_key != old_key
    assert not Session.objects.filter(session_key=old_key).exists()


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_m10_ac2_database_trigger_blocks_raw_mutation(account, operation):
    if connection.vendor != "postgresql":
        pytest.skip("Blocked: PostgreSQL required to prove the TD-03 trigger")
    user, _ = account
    event = AuditEvent.objects.create(actor=user, action="qa_control", object_type="qa", object_id="synthetic", outcome="success")
    with pytest.raises(DatabaseError), transaction.atomic():
        with connection.cursor() as cursor:
            if operation == "UPDATE":
                cursor.execute("UPDATE audit_auditevent SET action = %s WHERE id = %s", ["tampered", event.pk])
            else:
                cursor.execute("DELETE FROM audit_auditevent WHERE id = %s", [event.pk])
    event.refresh_from_db()
    assert event.action == "qa_control"
