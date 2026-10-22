"""AI API tests: job -> generated content -> human review gate."""
import pytest

pytestmark = pytest.mark.django_db


def test_job_generates_pending_review_content(api_client):
    response = api_client.post(
        "/api/ai/jobs/",
        {"job_type": "MATERIAL_GEN", "input": {"prompt": "Explain fractions", "title": "Fractions 101", "content_type": "MATERIAL"}},
        format="json",
    )
    assert response.status_code == 201, response.data
    job = response.data["data"]
    assert job["status"] == "SUCCESS"

    listing = api_client.get("/api/ai/generated-content/?status=PENDING_REVIEW")
    assert listing.data["data"]["total"] >= 1
    content_id = listing.data["data"]["items"][0]["id"]
    assert listing.data["data"]["items"][0]["status"] == "PENDING_REVIEW"


def test_human_review_approve_and_reject(api_client):
    api_client.post(
        "/api/ai/jobs/",
        {"job_type": "MATERIAL_GEN", "input": {"prompt": "p", "title": "T", "content_type": "MATERIAL"}},
        format="json",
    )
    listing = api_client.get("/api/ai/generated-content/")
    content_id = listing.data["data"]["items"][0]["id"]

    approved = api_client.post(
        f"/api/ai/generated-content/{content_id}/review/",
        {"decision": "approve", "note": "Looks good"},
        format="json",
    )
    assert approved.status_code == 200, approved.data
    assert approved.data["data"]["status"] == "APPROVED"

    # Re-reviewing is rejected.
    again = api_client.post(
        f"/api/ai/generated-content/{content_id}/review/",
        {"decision": "reject"},
        format="json",
    )
    assert again.status_code == 400


def test_non_coordinator_cannot_review(api_client, institution):
    from conftest import make_user
    from rest_framework.test import APIClient

    api_client.post(
        "/api/ai/jobs/",
        {"job_type": "MATERIAL_GEN", "input": {"prompt": "p", "title": "T2", "content_type": "MATERIAL"}},
        format="json",
    )
    listing = api_client.get("/api/ai/generated-content/")
    content_id = listing.data["data"]["items"][0]["id"]

    teacher_user = make_user(institution, "teacherai@test.school", "TEACHER")
    client = APIClient()
    client.force_authenticate(user=teacher_user)
    response = client.post(
        f"/api/ai/generated-content/{content_id}/review/",
        {"decision": "approve"},
        format="json",
    )
    assert response.status_code == 403
