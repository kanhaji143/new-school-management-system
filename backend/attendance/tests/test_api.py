"""Attendance API tests: bulk marking, corrections, leave workflow."""
from datetime import timedelta

import pytest
from django.utils import timezone

from academics.models import AcademicYear, GradeLevel, SchoolClass, Section, Subject
from audit.models import AuditLog
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
def students(institution, section):
    return [
        people_services.create_student(
            institution.id,
            f"student{i}@test.school",
            first_name=f"Student{i}",
            roll_number=f"R{i}",
            admission_number=f"ADM{i}",
            section=section,
        )
        for i in range(1, 4)
    ]


@pytest.fixture
def teacher(institution):
    return people_services.create_teacher(
        institution.id, "staff@test.school", employee_id="E1"
    )


@pytest.fixture
def academic_year(institution):
    return AcademicYear.objects.create(
        institution=institution,
        name="2026-2027",
        start_date="2026-06-01",
        end_date="2027-03-31",
        is_active=True,
    )


@pytest.fixture
def timetable_entry(institution, section, academic_year, teacher):
    subject = Subject.objects.create(
        institution=institution, code="MATH", name="Mathematics"
    )
    period = PeriodTemplate.objects.create(
        institution=institution,
        name="Period 1",
        day=1,
        start_time="09:00",
        end_time="09:45",
        order_index=1,
    )
    timetable = Timetable.objects.create(
        institution=institution,
        section=section,
        academic_year=academic_year,
        version=1,
        status=Timetable.Status.PUBLISHED,
    )
    return TimetableEntry.objects.create(
        institution=institution,
        timetable=timetable,
        day=1,
        period=period,
        subject=subject,
        teacher=teacher,
        room="101",
    )


# ------------------------------------------------------------------ daily bulk
def test_bulk_mark_creates_daily_rows(api_client, students):
    response = api_client.post(
        "/api/student-attendance/bulk/",
        {
            "date": "2026-10-20",
            "records": [
                {"student": students[0].id, "status": "PRESENT"},
                {"student": students[1].id, "status": "ABSENT", "remark": "Sick"},
                {"student": students[2].id, "status": "LATE"},
            ],
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["created"] == 3
    assert response.data["data"]["corrected"] == 0

    listing = api_client.get("/api/student-attendance/?date=2026-10-20")
    assert listing.status_code == 200
    assert listing.data["data"]["total"] == 3


def test_resubmitting_roster_corrects_and_audits(api_client, students, admin_user):
    payload = {
        "date": "2026-10-20",
        "records": [{"student": students[0].id, "status": "PRESENT"}],
    }
    assert api_client.post(
        "/api/student-attendance/bulk/", payload, format="json"
    ).status_code == 200

    payload["records"][0]["status"] = "ABSENT"
    payload["records"][0]["remark"] = "Called in sick"
    response = api_client.post(
        "/api/student-attendance/bulk/", payload, format="json"
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["corrected"] == 1

    audit = AuditLog.objects.filter(
        action="CORRECT", model="attendance.StudentAttendance"
    ).latest("id")
    assert audit.actor_id == admin_user.id
    assert audit.before["status"] == "PRESENT"
    assert audit.after["status"] == "ABSENT"


def test_unchanged_resubmission_is_noop(api_client, students):
    payload = {
        "date": "2026-10-20",
        "records": [{"student": students[0].id, "status": "PRESENT"}],
    }
    api_client.post("/api/student-attendance/bulk/", payload, format="json")
    response = api_client.post(
        "/api/student-attendance/bulk/", payload, format="json"
    )
    assert response.data["data"]["unchanged"] == 1
    assert AuditLog.objects.filter(action="CORRECT").count() == 0


def test_bulk_rejects_duplicate_students(api_client, students):
    response = api_client.post(
        "/api/student-attendance/bulk/",
        {
            "date": "2026-10-20",
            "records": [
                {"student": students[0].id, "status": "PRESENT"},
                {"student": students[0].id, "status": "ABSENT"},
            ],
        },
        format="json",
    )
    assert response.status_code == 400


def test_bulk_rejects_future_dates(api_client, students):
    tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
    response = api_client.post(
        "/api/student-attendance/bulk/",
        {
            "date": tomorrow,
            "records": [{"student": students[0].id, "status": "PRESENT"}],
        },
        format="json",
    )
    assert response.status_code == 400


def test_summary_counts(api_client, students, section):
    api_client.post(
        "/api/student-attendance/bulk/",
        {
            "date": "2026-10-20",
            "records": [
                {"student": students[0].id, "status": "PRESENT"},
                {"student": students[1].id, "status": "ABSENT"},
            ],
        },
        format="json",
    )
    response = api_client.get(
        f"/api/student-attendance/summary/?date=2026-10-20&section={section.id}"
    )
    assert response.status_code == 200, response.data
    data = response.data["data"]
    assert data["enrolled"] == 3
    assert data["marked"] == 2
    assert data["unmarked"] == 1
    assert data["counts"]["PRESENT"] == 1
    assert data["attendanceRate"] == 50.0


def test_student_roster_exposes_primary_whatsapp_contact(api_client, institution, students):
    guardian = people_services.create_guardian(
        institution.id, "parent-roster@test.school", first_name="Priya", last_name="Parent",
        phone="+91 98765 43210", relation="MOTHER",
    )
    people_services.link_guardian(students[0], guardian, is_primary=True)
    response = api_client.get(f"/api/students/?search={students[0].roll_number}")
    assert response.status_code == 200, response.data
    student = next(row for row in response.data["data"]["items"] if row["id"] == students[0].id)
    assert student["whatsapp_contacts"][0]["name"] == "Priya Parent"
    assert student["whatsapp_contacts"][0]["phone"] == "+91 98765 43210"
    assert student["whatsapp_contacts"][0]["recipient_type"] == "PARENT"


def test_student_dashboard_apis_are_scoped_to_own_profile(api_client, students):
    from rest_framework.test import APIClient

    marked = api_client.post(
        "/api/student-attendance/bulk/",
        {"date": "2026-10-20", "records": [{"student": students[0].id, "status": "ABSENT"}]},
        format="json",
    )
    assert marked.status_code == 200

    student_client = APIClient()
    student_client.force_authenticate(user=students[0].user)
    own_rows = student_client.get("/api/student-attendance/mine/")
    assert own_rows.status_code == 200
    assert own_rows.data["data"]["total"] == 1

    summary = student_client.get("/api/student-attendance/summary/?date=2026-10-20")
    assert summary.status_code == 200
    assert summary.data["data"]["counts"]["ABSENT"] == 1
    assert summary.data["data"]["enrolled"] == 1

    roster = student_client.get("/api/students/?pageSize=200")
    assert roster.status_code == 200
    assert roster.data["data"]["total"] == 1
    assert roster.data["data"]["items"][0]["id"] == students[0].id

    denied = student_client.post(
        "/api/student-attendance/bulk/",
        {"date": "2026-10-20", "records": [{"student": students[0].id, "status": "PRESENT"}]},
        format="json",
    )
    assert denied.status_code == 403


def test_tenant_isolation_rejects_foreign_student(api_client, students, other_institution):
    foreign = people_services.create_student(
        other_institution.id,
        "foreign@other.school",
        roll_number="X1",
        admission_number="ADMX",
    )
    response = api_client.post(
        "/api/student-attendance/bulk/",
        {
            "date": "2026-10-20",
            "records": [{"student": foreign.id, "status": "PRESENT"}],
        },
        format="json",
    )
    assert response.status_code == 400


# ------------------------------------------------------------- period marking
def test_period_bulk_marks_entry(api_client, students, timetable_entry):
    response = api_client.post(
        "/api/period-attendance/bulk/",
        {
            "date": "2026-10-20",
            "entry": timetable_entry.id,
            "records": [
                {"student": students[0].id, "status": "PRESENT"},
                {"student": students[1].id, "status": "ABSENT"},
            ],
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["created"] == 2

    listing = api_client.get(
        f"/api/period-attendance/?entry={timetable_entry.id}&date=2026-10-20"
    )
    assert listing.data["data"]["total"] == 2


# ------------------------------------------------------------------- teachers
def test_teacher_bulk_marking(api_client, teacher):
    response = api_client.post(
        "/api/teacher-attendance/bulk/",
        {
            "date": "2026-10-20",
            "records": [{"teacher": teacher.id, "status": "PRESENT"}],
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["created"] == 1


# ---------------------------------------------------------------------- leave
@pytest.fixture
def leave_type(institution):
    from attendance.models import LeaveType

    return LeaveType.objects.create(
        institution=institution, name="Sick Leave", paid=True, max_days=10
    )


def _leave_payload(teacher, leave_type):
    return {
        "teacher": teacher.id,
        "leave_type": leave_type.id,
        "start_date": "2026-10-19",
        "end_date": "2026-10-20",
        "reason": "Fever",
    }


def test_leave_approval_marks_staff_absent(api_client, teacher, leave_type):
    created = api_client.post(
        "/api/leave-requests/", _leave_payload(teacher, leave_type), format="json"
    )
    assert created.status_code == 201, created.data
    leave_id = created.data["data"]["id"]

    response = api_client.post(f"/api/leave-requests/{leave_id}/approve/")
    assert response.status_code == 200, response.data
    assert response.data["data"]["status"] == "APPROVED"

    from attendance.models import TeacherAttendance

    absences = TeacherAttendance.objects.filter(
        teacher=teacher, status=TeacherAttendance.Status.ABSENT
    )
    assert absences.count() == 2

    # Approving twice is rejected.
    again = api_client.post(f"/api/leave-requests/{leave_id}/approve/")
    assert again.status_code == 400


def test_leave_rejection_keeps_attendance_untouched(api_client, teacher, leave_type):
    created = api_client.post(
        "/api/leave-requests/", _leave_payload(teacher, leave_type), format="json"
    )
    leave_id = created.data["data"]["id"]
    response = api_client.post(
        f"/api/leave-requests/{leave_id}/reject/",
        {"reason": "Exam week"},
        format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["data"]["status"] == "REJECTED"

    from attendance.models import TeacherAttendance

    assert TeacherAttendance.objects.filter(teacher=teacher).count() == 0


def test_teacher_can_file_own_leave_but_cannot_approve(
    teacher_client, teacher_user, leave_type, institution
):
    from people.models import Teacher

    own_profile = Teacher.objects.create(
        institution=institution, user=teacher_user, employee_id="E9"
    )
    payload = {
        "leave_type": leave_type.id,
        "start_date": "2026-10-19",
        "end_date": "2026-10-19",
        "reason": "Personal",
    }
    created = teacher_client.post("/api/leave-requests/", payload, format="json")
    assert created.status_code == 201, created.data
    assert created.data["data"]["teacher"] == own_profile.id
    assert created.data["data"]["status"] == "PENDING"

    leave_id = created.data["data"]["id"]
    assert teacher_client.post(f"/api/leave-requests/{leave_id}/approve/").status_code == 403


def test_leave_end_before_start_is_invalid(api_client, teacher, leave_type):
    payload = _leave_payload(teacher, leave_type)
    payload["start_date"] = "2026-10-21"
    payload["end_date"] = "2026-10-20"
    response = api_client.post("/api/leave-requests/", payload, format="json")
    assert response.status_code == 400
