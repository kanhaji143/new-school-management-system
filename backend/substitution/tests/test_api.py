"""Substitution API tests: request -> recommend -> assign -> handover -> outcome."""
import pytest

from academics.models import AcademicYear, GradeLevel, SchoolClass, Section, Subject
from conftest import make_user
from people import services as people_services
from timetable.models import PeriodTemplate, Timetable, TimetableEntry

pytestmark = pytest.mark.django_db


@pytest.fixture
def section(institution):
    grade = GradeLevel.objects.create(institution=institution, name="Grade 10")
    school_class = SchoolClass.objects.create(
        institution=institution, grade_level=grade, name="Grade 10"
    )
    return Section.objects.create(
        institution=institution, school_class=school_class, name="A"
    )


@pytest.fixture
def academic_year(institution):
    return AcademicYear.objects.create(
        institution=institution, name="2026-2027",
        start_date="2026-06-01", end_date="2027-03-31", is_active=True,
    )


@pytest.fixture
def teachers(institution):
    return [
        people_services.create_teacher(institution.id, "absent@test.school", employee_id="E1", department="Math"),
        people_services.create_teacher(institution.id, "sub@test.school", employee_id="E2", department="Math"),
    ]


@pytest.fixture
def subject(institution):
    return Subject.objects.create(institution=institution, code="MATH", name="Mathematics")


@pytest.fixture
def published_entry(institution, section, academic_year, teachers, subject):
    period = PeriodTemplate.objects.create(
        institution=institution, name="Period 1", day=1,
        start_time="09:00", end_time="09:45", order_index=1,
    )
    timetable = Timetable.objects.create(
        institution=institution, section=section, academic_year=academic_year,
        version=1, status=Timetable.Status.PUBLISHED,
    )
    from academics.models import ClassSubject

    ClassSubject.objects.create(
        institution=institution, subject=subject, section=section,
        teacher=teachers[1], academic_year=academic_year,
    )
    return TimetableEntry.objects.create(
        institution=institution, timetable=timetable, day=1, period=period,
        subject=subject, teacher=teachers[0], room="101",
    )


def _create_request(api_client, entry, absent_teacher, date="2026-10-26"):
    response = api_client.post(
        "/api/substitution-requests/",
        {
            "absent_teacher": absent_teacher.id,
            "entry": entry.id,
            "date": date,
            "reason": "Sick",
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    return response.data["data"]


def test_create_request(api_client, published_entry, teachers):
    data = _create_request(api_client, published_entry, teachers[0])
    assert data["status"] == "OPEN"
    assert data["absent_teacher"] == teachers[0].id


def test_recommendations_generated_and_ranked(api_client, published_entry, teachers):
    request = _create_request(api_client, published_entry, teachers[0])
    response = api_client.get(f"/api/substitution-requests/{request['id']}/recommendations/")
    assert response.status_code == 200, response.data
    recs = response.data["data"]
    assert len(recs) >= 1
    # substitute teacher should be ranked first (subject match)
    assert recs[0]["teacher"] == teachers[1].id
    # persisted
    detail = api_client.get(f"/api/substitution-requests/{request['id']}/")
    assert detail.data["data"]["status"] == "PROPOSED"


def test_assign_substitute(api_client, published_entry, teachers):
    request = _create_request(api_client, published_entry, teachers[0])
    api_client.get(f"/api/substitution-requests/{request['id']}/recommendations/")
    response = api_client.post(
        f"/api/substitution-requests/{request['id']}/assign/",
        {"recommendation": 1} if False else {"substitute_teacher": teachers[1].id},
        format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["status"] == "APPROVED"
    assert response.data["data"]["substitute_teacher"] == teachers[1].id

    detail = api_client.get(f"/api/substitution-requests/{request['id']}/")
    assert detail.data["data"]["status"] == "APPROVED"


def test_handover_and_outcome(api_client, published_entry, teachers):
    request = _create_request(api_client, published_entry, teachers[0])
    api_client.post(
        f"/api/substitution-requests/{request['id']}/assign/",
        {"substitute_teacher": teachers[1].id},
        format="json",
    )
    ho = api_client.post(
        f"/api/substitution-requests/{request['id']}/handover/",
        {"notes": "Cover chapter 3"},
        format="json",
    )
    assert ho.status_code == 200, ho.data
    assert ho.data["data"]["notes"] == "Cover chapter 3"

    outcome = api_client.post(
        f"/api/substitution-requests/{request['id']}/outcome/",
        {"status": "COMPLETED", "notes": "Done"},
        format="json",
    )
    assert outcome.status_code == 200, outcome.data
    assert outcome.data["data"]["status"] == "COMPLETED"

    detail = api_client.get(f"/api/substitution-requests/{request['id']}/")
    assert detail.data["data"]["status"] == "COMPLETED"
    assert detail.data["data"]["assignment"]["status"] == "COMPLETED"


def test_non_coordinator_forbidden(api_client, published_entry, teachers, institution):
    # create a teacher user client manually
    from rest_framework.test import APIClient

    teacher_user = make_user(institution, "teacherx@test.school", "TEACHER")
    client = APIClient()
    client.force_authenticate(user=teacher_user)
    request = _create_request(api_client, published_entry, teachers[0])
    api_client.get(f"/api/substitution-requests/{request['id']}/recommendations/")
    response = client.post(
        f"/api/substitution-requests/{request['id']}/assign/",
        {"substitute_teacher": teachers[1].id},
        format="json",
    )
    assert response.status_code == 403


def test_signal_auto_creates_request_on_absence(api_client, published_entry, teachers):
    from attendance.models import TeacherAttendance
    from datetime import date

    # Monday 2026-10-26 (weekday 0 -> day 1)
    response = api_client.post(
        "/api/teacher-attendance/bulk/",
        {"date": "2026-10-26", "records": [{"teacher": teachers[0].id, "status": "ABSENT"}]},
        format="json",
    )
    assert response.status_code == 200
    from substitution.models import SubstitutionRequest

    qs = SubstitutionRequest.objects.filter(absent_teacher=teachers[0], date="2026-10-26")
    assert qs.count() == 1
    assert qs.first().entry_id == published_entry.id


def test_tenant_isolation(api_client, published_entry, teachers, other_institution):
    from people import services as people_services

    foreign_teacher = people_services.create_teacher(other_institution.id, "foreign@other.school", employee_id="FX")
    response = api_client.post(
        "/api/substitution-requests/",
        {
            "absent_teacher": foreign_teacher.id,
            "entry": published_entry.id,
            "date": "2026-10-26",
        },
        format="json",
    )
    assert response.status_code == 400
