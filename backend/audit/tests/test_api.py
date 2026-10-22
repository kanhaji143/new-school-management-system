"""Audit APIs: tenant isolation, protected settings, verified backups."""
import pytest
from django.test import override_settings
from tempfile import TemporaryDirectory

from conftest import make_user
from common.audit import log_action

pytestmark = pytest.mark.django_db


def test_audit_log_is_tenant_scoped(api_client, institution, other_institution, admin_user):
    log_action(admin_user, "CORRECT", before={"x": 1}, after={"x": 2}, institution_id=institution.id)
    log_action(admin_user, "CORRECT", before={"x": 1}, after={"x": 3}, institution_id=other_institution.id)
    response = api_client.get("/api/audit-logs/?action=CORRECT")
    assert response.status_code == 200, response.data
    assert response.data["data"]["total"] == 1


def test_system_setting_crud_and_admin_only(api_client, institution):
    created = api_client.post(
        "/api/system-settings/",
        {"key": "attendance.grace_minutes", "value": {"minutes": 10}, "description": "Late window"},
        format="json",
    )
    assert created.status_code == 201, created.data
    assert created.data["data"]["key"] == "attendance.grace_minutes"

    from rest_framework.test import APIClient

    teacher = make_user(institution, "audit-teacher@test.school", "TEACHER")
    client = APIClient()
    client.force_authenticate(user=teacher)
    assert client.get("/api/system-settings/").status_code == 403


def test_backup_requires_platform_superadmin(api_client):
    response = api_client.post("/api/backups/", {}, format="json")
    assert response.status_code == 403


def test_superadmin_can_create_and_integrity_test_backup(institution):
    from django.db import connection
    from rest_framework.test import APIClient

    if connection.vendor != "sqlite":
        pytest.skip("In-app backup implementation is SQLite-only; managed PostgreSQL backups are separate.")

    superadmin = make_user(institution, "platform@test.school", "SUPER_ADMIN")
    client = APIClient()
    client.force_authenticate(user=superadmin)

    with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
        created = client.post("/api/backups/", {}, format="json")
        assert created.status_code == 201, created.data
        backup_id = created.data["data"]["id"]
        assert created.data["data"]["checksum"]

        tested = client.post(f"/api/backups/{backup_id}/test-restore/")
        assert tested.status_code == 200, tested.data
        assert tested.data["data"]["restore_test_passed"] is True
