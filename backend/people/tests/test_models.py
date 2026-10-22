"""People model + API tests (students, teachers, guardians)."""
import pytest

from academics.models import Section
from people.models import Guardian, Student, StudentGuardian, Teacher
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def section(institution):
    from academics.models import GradeLevel, SchoolClass

    grade = GradeLevel.objects.create(institution=institution, name="Grade 10")
    school_class = SchoolClass.objects.create(
        institution=institution, grade_level=grade, name="Grade 10"
    )
    return Section.objects.create(
        institution=institution, school_class=school_class, name="A"
    )


# ----------------------------------------------------------------------------- models
def test_create_student_service_assigns_role(institution):
    from people import services

    student = services.create_student(
        institution.id, "student@test.school", first_name="Asha", last_name="Rao",
        roll_number="R-001", admission_number="ADM-001",
    )
    assert student.user.full_name == "Asha Rao"
    assert student.user.has_any_role("STUDENT") is True
    assert Student.objects.filter(institution=institution).count() == 1


def test_create_teacher_service_assigns_role(institution):
    from people import services

    teacher = services.create_teacher(
        institution.id, "teacher2@test.school", employee_id="EMP-1", department="Maths"
    )
    assert teacher.user.has_any_role("TEACHER") is True
    assert teacher.max_periods_per_week == 30


def test_link_guardian_enforces_single_primary(institution):
    from people import services

    student = services.create_student(
        institution.id, "s2@test.school", roll_number="R-002", admission_number="ADM-002"
    )
    father = services.create_guardian(institution.id, "f@test.school", relation="FATHER")
    mother = services.create_guardian(institution.id, "m@test.school", relation="MOTHER")

    services.link_guardian(student, father, is_primary=True)
    services.link_guardian(student, mother, is_primary=True)

    primaries = StudentGuardian.objects.filter(student=student, is_primary=True)
    assert primaries.count() == 1
    assert primaries.first().guardian == mother


def test_link_guardian_rejects_cross_institution(institution, other_institution):
    from people import services

    student = services.create_student(
        institution.id, "s3@test.school", roll_number="R-003", admission_number="ADM-003"
    )
    outsider = services.create_guardian(
        other_institution.id, "x@test.school", relation="GUARDIAN"
    )
    with pytest.raises(ValueError):
        services.link_guardian(student, outsider)


# -------------------------------------------------------------------------------- API
def test_create_student_api(api_client, institution, section):
    response = api_client.post(
        "/api/students/",
        {
            "email": "newstudent@test.school",
            "first_name": "Ravi",
            "last_name": "Kumar",
            "roll_number": "R-100",
            "admission_number": "ADM-100",
            "section": section.id,
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["data"]["roll_number"] == "R-100"
    assert response.data["data"]["user"]["email"] == "newstudent@test.school"

    user = User.objects.get(email="newstudent@test.school")
    assert user.has_any_role("STUDENT") is True
    assert user.institution_id == institution.id


def test_duplicate_email_is_rejected(api_client):
    api_client.post(
        "/api/students/",
        {"email": "dupe@test.school", "roll_number": "R-1", "admission_number": "A-1"},
        format="json",
    )
    response = api_client.post(
        "/api/students/",
        {"email": "dupe@test.school", "roll_number": "R-2", "admission_number": "A-2"},
        format="json",
    )
    assert response.status_code == 400


def test_duplicate_admission_number_is_rejected(api_client):
    api_client.post(
        "/api/students/",
        {"email": "a@test.school", "roll_number": "R-1", "admission_number": "SAME"},
        format="json",
    )
    response = api_client.post(
        "/api/students/",
        {"email": "b@test.school", "roll_number": "R-2", "admission_number": "SAME"},
        format="json",
    )
    assert response.status_code == 400
    assert "admission_number" in response.data["errors"]["fieldErrors"]


def test_student_listing_is_scoped_to_institution(api_client, other_institution):
    from people import services

    services.create_student(
        other_institution.id, "other@test.school",
        roll_number="R-O", admission_number="ADM-O",
    )
    response = api_client.get("/api/students/")
    assert response.status_code == 200
    assert response.data["data"]["total"] == 0


def test_teacher_cannot_create_student(teacher_client):
    response = teacher_client.post(
        "/api/students/",
        {"email": "t@test.school", "roll_number": "R-9", "admission_number": "A-9"},
        format="json",
    )
    assert response.status_code == 403


def test_teacher_can_read_students(teacher_client):
    response = teacher_client.get("/api/students/")
    assert response.status_code == 200


def test_link_guardian_api(api_client, institution):
    from people import services

    student = services.create_student(
        institution.id, "lg@test.school", roll_number="R-LG", admission_number="ADM-LG"
    )
    guardian = services.create_guardian(institution.id, "lgp@test.school", relation="FATHER")

    response = api_client.post(
        f"/api/students/{student.id}/link_guardian/",
        {"guardian": guardian.id, "is_primary": True},
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["data"]["is_primary"] is True


def test_guardian_of_another_institution_cannot_be_linked(api_client, admin_user, other_institution):
    from people import services

    student = services.create_student(
        admin_user.institution_id, "li@test.school",
        roll_number="R-LI", admission_number="ADM-LI",
    )
    outsider = services.create_guardian(
        other_institution.id, "out@test.school", relation="GUARDIAN",
    )
    response = api_client.post(
        f"/api/students/{student.id}/link_guardian/",
        {"guardian": outsider.id},
        format="json",
    )
    assert response.status_code == 404


def test_create_teacher_api(api_client, institution):
    response = api_client.post(
        "/api/teachers/",
        {
            "email": "newteacher@test.school",
            "first_name": "Sunita",
            "employee_id": "EMP-77",
            "department": "Science",
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["data"]["employee_id"] == "EMP-77"
    assert Teacher.objects.filter(institution=institution, employee_id="EMP-77").exists()
