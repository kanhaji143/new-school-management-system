"""Curriculum API tests."""
import pytest

from academics.models import AcademicYear, GradeLevel, SchoolClass, Section, Subject
from people import services as people_services
from curriculum.models import Syllabus, Chapter, LessonPlan, ClassSessionLog, LessonCompletion

pytestmark = pytest.mark.django_db


@pytest.fixture
def section(institution):
    grade = GradeLevel.objects.create(institution=institution, name="Grade 10")
    school_class = SchoolClass.objects.create(institution=institution, grade_level=grade, name="Grade 10")
    return Section.objects.create(institution=institution, school_class=school_class, name="A")


@pytest.fixture
def academic_year(institution):
    return AcademicYear.objects.create(
        institution=institution, name="2026-2027",
        start_date="2026-06-01", end_date="2027-03-31", is_active=True,
    )


@pytest.fixture
def subject(institution):
    return Subject.objects.create(institution=institution, code="MATH", name="Mathematics")


@pytest.fixture
def teacher(institution):
    return people_services.create_teacher(institution.id, "t@test.school", employee_id="E1")


def _create_syllabus(api_client, subject, section, academic_year):
    response = api_client.post(
        "/api/syllabi/",
        {
            "title": "Math syllabus",
            "subject": subject.id,
            "section": section.id,
            "academic_year": academic_year.id,
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    return response.data["data"]


def test_create_syllabus(api_client, subject, section, academic_year):
    data = _create_syllabus(api_client, subject, section, academic_year)
    assert data["title"] == "Math syllabus"
    assert data["subject_detail"]["code"] == "MATH"


def test_nested_chapters_and_lesson_plans(api_client, subject, section, academic_year):
    syllabus = _create_syllabus(api_client, subject, section, academic_year)
    ch = api_client.post(
        f"/api/syllabi/{syllabus['id']}/chapters/",
        {"title": "Chapter 1", "order_index": 1, "planned_hours": 4},
        format="json",
    )
    assert ch.status_code == 201, ch.data
    chapter_id = ch.data["data"]["id"]

    # list chapters
    listed = api_client.get(f"/api/syllabi/{syllabus['id']}/chapters/")
    assert listed.data["data"][0]["title"] == "Chapter 1"

    lp = api_client.post(
        f"/api/chapters/{chapter_id}/lesson-plans/",
        {"title": "Lesson 1", "duration_minutes": 45},
        format="json",
    )
    assert lp.status_code == 201, lp.data
    assert lp.data["data"]["title"] == "Lesson 1"

    listed_lp = api_client.get(f"/api/chapters/{chapter_id}/lesson-plans/")
    assert len(listed_lp.data["data"]) == 1


def test_explicit_complete_chapter(api_client, subject, section, academic_year):
    syllabus = _create_syllabus(api_client, subject, section, academic_year)
    ch = api_client.post(
        f"/api/syllabi/{syllabus['id']}/chapters/",
        {"title": "Chapter 1", "order_index": 1},
        format="json",
    )
    chapter_id = ch.data["data"]["id"]

    # before completion -> PLANNED
    detail = api_client.get(f"/api/chapters/{chapter_id}/")
    assert detail.data["data"]["completion_status"] == "PLANNED"

    resp = api_client.post(
        f"/api/chapters/{chapter_id}/complete/",
        {"status": "COMPLETED"},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["data"]["status"] == "COMPLETED"

    detail2 = api_client.get(f"/api/chapters/{chapter_id}/")
    assert detail2.data["data"]["completion_status"] == "COMPLETED"

    # LessonCompletion persisted
    assert LessonCompletion.objects.filter(chapter_id=chapter_id).count() == 1


def test_session_log_create(api_client, subject, section, teacher):
    response = api_client.post(
        "/api/class-session-logs/",
        {
            "subject": subject.id,
            "section": section.id,
            "topic": "Intro to algebra",
            "date": "2026-10-26",
            "status": "COMPLETED",
            "teacher": teacher.id,
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["data"]["topic"] == "Intro to algebra"


def test_tenant_isolation(api_client, subject, section, academic_year, other_institution):
    from academics.models import Subject as S

    foreign_subject = S.objects.create(institution=other_institution, code="PHY", name="Physics")
    response = api_client.post(
        "/api/syllabi/",
        {
            "title": "Foreign syllabus",
            "subject": foreign_subject.id,
            "academic_year": academic_year.id,
        },
        format="json",
    )
    assert response.status_code == 400
