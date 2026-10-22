"""Academics model + API tests."""
import pytest

from academics.models import AcademicYear, GradeLevel, SchoolClass, Section, Subject, Term
from conftest import make_institution, make_user

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------- models
def test_academic_year_string(institution):
    year = AcademicYear.objects.create(
        institution=institution, name="2026-2027",
        start_date="2026-06-01", end_date="2027-03-31",
    )
    assert str(year) == "2026-2027"


def test_only_one_active_academic_year_per_institution(institution):
    first = AcademicYear.objects.create(
        institution=institution, name="2025-2026",
        start_date="2025-06-01", end_date="2026-03-31", is_active=True,
    )
    second = AcademicYear.objects.create(
        institution=institution, name="2026-2027",
        start_date="2026-06-01", end_date="2027-03-31", is_active=True,
    )

    first.refresh_from_db()
    second.refresh_from_db()
    assert second.is_active is True
    assert first.is_active is False, "only one academic year may stay active"


def test_only_one_active_term_per_academic_year(institution):
    year = AcademicYear.objects.create(
        institution=institution, name="2026-2027",
        start_date="2026-06-01", end_date="2027-03-31",
    )
    first = Term.objects.create(
        institution=institution, academic_year=year, name="Term 1",
        start_date="2026-06-01", end_date="2026-10-31", is_active=True,
    )
    second = Term.objects.create(
        institution=institution, academic_year=year, name="Term 2",
        start_date="2026-11-01", end_date="2027-03-31", is_active=True,
    )

    first.refresh_from_db()
    second.refresh_from_db()
    assert second.is_active is True
    assert first.is_active is False


def test_section_unique_together_is_institution_scoped(institution, other_institution):
    grade = GradeLevel.objects.create(institution=institution, name="Grade 10")
    school_class = SchoolClass.objects.create(
        institution=institution, grade_level=grade, name="Grade 10"
    )
    Section.objects.create(institution=institution, school_class=school_class, name="A")

    other_grade = GradeLevel.objects.create(institution=other_institution, name="Grade 10")
    other_class = SchoolClass.objects.create(
        institution=other_institution, grade_level=other_grade, name="Grade 10"
    )
    # Same names in a different institution must not clash.
    Section.objects.create(institution=other_institution, school_class=other_class, name="A")


# -------------------------------------------------------------------------------- API
def test_create_academic_year(api_client, institution):
    response = api_client.post(
        "/api/academic-years/",
        {"name": "2026-2027", "start_date": "2026-06-01", "end_date": "2027-03-31"},
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["name"] == "2026-2027"
    assert AcademicYear.objects.filter(institution=institution).count() == 1


def test_end_date_before_start_date_is_rejected(api_client):
    response = api_client.post(
        "/api/academic-years/",
        {"name": "bad", "start_date": "2026-06-01", "end_date": "2026-05-01"},
        format="json",
    )
    assert response.status_code == 400
    assert "end_date" in response.data["errors"]["fieldErrors"]


def test_activate_endpoint_deactivates_previous_year(api_client, institution):
    first = AcademicYear.objects.create(
        institution=institution, name="2025-2026",
        start_date="2025-06-01", end_date="2026-03-31", is_active=True,
    )
    second = AcademicYear.objects.create(
        institution=institution, name="2026-2027",
        start_date="2026-06-01", end_date="2027-03-31",
    )

    response = api_client.post(f"/api/academic-years/{second.id}/activate/", {}, format="json")
    assert response.status_code == 200

    first.refresh_from_db()
    second.refresh_from_db()
    assert second.is_active is True
    assert first.is_active is False


def test_current_endpoint_returns_active_year(api_client, institution):
    AcademicYear.objects.create(
        institution=institution, name="2026-2027",
        start_date="2026-06-01", end_date="2027-03-31", is_active=True,
    )
    response = api_client.get("/api/academic-years/current/")
    assert response.status_code == 200
    assert response.data["data"]["name"] == "2026-2027"


def test_listing_is_scoped_to_institution(api_client, other_institution):
    AcademicYear.objects.create(
        institution=other_institution, name="Other year",
        start_date="2026-06-01", end_date="2027-03-31",
    )
    response = api_client.get("/api/academic-years/")
    assert response.status_code == 200
    assert response.data["data"]["total"] == 0


def test_teacher_cannot_create_academic_year(teacher_client):
    response = teacher_client.post(
        "/api/academic-years/",
        {"name": "2026-2027", "start_date": "2026-06-01", "end_date": "2027-03-31"},
        format="json",
    )
    assert response.status_code == 403


def test_anonymous_user_is_rejected():
    from rest_framework.test import APIClient

    response = APIClient().get("/api/academic-years/")
    assert response.status_code == 401


def test_subject_crud(api_client, institution):
    response = api_client.post(
        "/api/subjects/", {"code": "MATH", "name": "Mathematics"}, format="json"
    )
    assert response.status_code == 201
    assert Subject.objects.filter(institution=institution, code="MATH").exists()


def test_role_lookup_works(institution):
    """Regression: `User.roles()` must resolve the `user_roles` related name."""
    user = make_user(institution, "roles@test.school", "SCHOOL_ADMIN")
    assert user.has_any_role("SCHOOL_ADMIN") is True
    assert user.has_any_role("TEACHER") is False
    assert [role.name for role in user.roles()] == ["SCHOOL_ADMIN"]
