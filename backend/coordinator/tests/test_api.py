"""Coordinator dashboard and task workflow tests."""
import pytest

from conftest import make_user

pytestmark = pytest.mark.django_db


def test_dashboard_counts_and_task_crud(api_client, institution):
    data = api_client.get("/api/coordinator/dashboard/")
    assert data.status_code == 200, data.data
    assert data.data["data"]["total_pending"] >= 0
    assert "ai_reviews" in data.data["data"]["pending"]

    created = api_client.post(
        "/api/coordinator-tasks/",
        {"task_type": "GENERAL", "title": "Review weekly plan", "payload": {"priority": "normal"}},
        format="json",
    )
    assert created.status_code == 201, created.data
    task_id = created.data["data"]["id"]

    completed = api_client.post(f"/api/coordinator-tasks/{task_id}/complete/")
    assert completed.status_code == 200, completed.data
    assert completed.data["data"]["status"] == "DONE"

    again = api_client.post(f"/api/coordinator-tasks/{task_id}/complete/")
    assert again.status_code == 400


def test_widgets_are_tenant_scoped(api_client, institution, other_institution):
    from coordinator.models import CommandCenterWidget

    CommandCenterWidget.objects.create(
        institution=other_institution, key="foreign", label="Foreign widget"
    )
    response = api_client.get("/api/command-center-widgets/")
    assert response.status_code == 200
    assert response.data["data"]["total"] == 0


def test_teacher_cannot_access_command_center(api_client, institution):
    from rest_framework.test import APIClient

    teacher = make_user(institution, "coord-teacher@test.school", "TEACHER")
    client = APIClient()
    client.force_authenticate(user=teacher)
    assert client.get("/api/coordinator/dashboard/").status_code == 403
    assert client.get("/api/coordinator-tasks/").status_code == 403
