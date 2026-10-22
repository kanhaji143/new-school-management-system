"""Notifications API tests."""
import pytest

from people import services as people_services
from notifications.models import Notification, NotificationTemplate, ProviderConfig

pytestmark = pytest.mark.django_db


@pytest.fixture
def template(institution):
    return NotificationTemplate.objects.create(
        institution=institution, event="student.absent", channel="EMAIL",
        subject="Absence", body="Ward absent", is_active=True,
    )


def test_create_template_and_list(api_client, institution):
    response = api_client.post(
        "/api/notification-templates/",
        {"event": "teacher.absent", "channel": "SMS", "subject": "s", "body": "b", "is_active": True},
        format="json",
    )
    assert response.status_code == 201, response.data
    listed = api_client.get("/api/notification-templates/")
    assert listed.data["data"]["total"] >= 1


def test_outbox_list_and_logs(api_client, institution, template):
    from users.models import User

    user = User.objects.create_user(email="parent@test.school", password="Pass@12345", institution=institution)
    notif = Notification.objects.create(
        institution=institution, recipient=user, template=template, channel="EMAIL",
        subject="s", body="b", status=Notification.Status.PENDING,
    )
    logs = api_client.get(f"/api/notifications/{notif.id}/logs/")
    assert logs.status_code == 200, logs.data

    retry = api_client.post(f"/api/notifications/{notif.id}/retry/")
    assert retry.status_code == 200, retry.data
    assert retry.data["data"]["status"] == "PENDING"
    assert retry.data["data"]["attempts"] == 1

    listed = api_client.get("/api/notifications/")
    assert listed.data["data"]["total"] >= 1


def test_provider_config(api_client, institution):
    response = api_client.post(
        "/api/provider-configs/",
        {"channel": "EMAIL", "provider": "sendgrid", "config": {"key": "x"}, "is_active": True, "priority": 1},
        format="json",
    )
    assert response.status_code == 201, response.data
