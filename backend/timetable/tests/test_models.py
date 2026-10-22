"""Timetable API + conflict-detection tests."""
import pytest

from academics.models import AcademicYear
from conftest import make_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def academic_year(institution):
    return AcademicYear.objects.create(
        institution=institution, name="2026-2027",
        start_date="2026-06-01", end_date="2027-03-31", is_active=True,
    )


@pytest.fixture
def period(institution):
    from timetable.models import PeriodTemplate

    return PeriodTemplate.objects.create(
        institution=institution,
        name="Period 1", day=1, start_time="09:00", end_time="09:45", order_index=1
    )


@pytest.fixture
def subject(institution):
    from academics.models import Subject

    return Subject.objects.create(institution=institution, code="MATH", name="Mathematics")


@pytest.fixture
def section(institution):
    from academics.models import GradeLevel, SchoolClass, Section

    grade = GradeLevel.objects.create(institution=institution, name="Grade 10")
    school_class = SchoolClass.objects.create(
        institution=institution, grade_level=grade, name="Grade 10"
    )
    return Section.objects.create(
        institution=institution, school_class=school_class, name="A"
    )


@pytest.fixture
def teachers(institution):
    from people import services

    return [
        services.create_teacher(institution.id, "t1@test.school", employee_id="E1"),
        services.create_teacher(institution.id, "t2@test.school", employee_id="E2"),
    ]


def _create_timetable(api_client, section, academic_year):
    response = api_client.post(
        "/api/timetables/",
        {"section": section.id, "academic_year": academic_year.id},
        format="json",
    )
    assert response.status_code == 201, response.data
    return response.data["data"]


def _add_entry(api_client, timetable, period, subject, teacher, room="101",
               day=1, timetable_id=None):
    payload = {
        "timetable": timetable_id or timetable["id"],
        "day": day,
        "period": period.id,
        "subject": subject.id,
        "teacher": teacher.id,
        "room": room,
    }
    return api_client.post("/api/timetable-entries/", payload, format="json")


# ------------------------------------------------------------------ draft & publishing
def test_create_draft_assigns_version_one(api_client, section, academic_year):
    data = _create_timetable(api_client, section, academic_year)
    assert data["version"] == 1
    assert data["status"] == "DRAFT"


def test_second_draft_bumps_the_version(api_client, section, academic_year):
    first = _create_timetable(api_client, section, academic_year)
    second = _create_timetable(api_client, section, academic_year)
    assert second["version"] == first["version"] + 1


def test_free_entry_reports_no_conflicts(api_client, section, academic_year,
                                         period, subject, teachers):
    timetable = _create_timetable(api_client, section, academic_year)
    response = _add_entry(api_client, timetable, period, subject, teachers[0])
    assert response.status_code == 201, response.data

    report = api_client.post(f"/api/timetables/{timetable['id']}/validate/", {},
                             format="json").data["data"]
    assert report["totalEntries"] == 1
    assert report["hardCount"] == 0
    assert report["canPublish"] is True


def test_publish_free_timetable_and_archive_previous(api_client, section, academic_year,
                                                     period, subject, teachers):
    blueprint = _create_timetable(api_client, section, academic_year)
    _add_entry(api_client, blueprint, period, subject, teachers[0])
    publish = api_client.post(f"/api/timetables/{blueprint['id']}/publish/", {},
                              format="json")
    assert publish.status_code == 200, publish.data
    assert publish.data["data"]["status"] == "PUBLISHED"

    # A second published version must archive the first one.
    newer = _create_timetable(api_client, section, academic_year)
    assert newer["version"] == 2
    _add_entry(api_client, newer, period, subject, teachers[0])
    second_publish = api_client.post(f"/api/timetables/{newer['id']}/publish/", {},
                                     format="json")
    assert second_publish.status_code == 200

    from timetable.models import Timetable

    blueprint_model = Timetable.all_objects.get(id=blueprint["id"])
    assert blueprint_model.status == Timetable.Status.ARCHIVED


# --------------------------------------------------------------- conflict detection
def test_teacher_double_booked_is_a_hard_conflict(api_client, section, academic_year,
                                                  period, subject, teachers):
    from academics.models import Section as SectionModel

    published = _create_timetable(api_client, section, academic_year)
    _add_entry(api_client, published, period, subject, teachers[0], room="101")
    assert api_client.post(
        f"/api/timetables/{published['id']}/publish/", {}, format="json"
    ).status_code == 200

    # A different section tries to book the same teacher at the same slot.
    other_section = SectionModel.objects.create(
        institution=section.institution, school_class=section.school_class, name="B"
    )
    draft = _create_timetable(api_client, other_section, academic_year)
    clash = _add_entry(api_client, draft, period, subject, teachers[0], room="201")
    assert clash.status_code == 201  # drafts may hold conflicts

    report = api_client.post(f"/api/timetables/{draft['id']}/validate/", {},
                             format="json").data["data"]
    assert report["totalEntries"] == 1
    assert report["hardCount"] == 1
    assert report["canPublish"] is False
    assert report["conflicts"][0]["conflictType"] == "TEACHER_DOUBLE_BOOKED"

    # Publishing must be refused.
    blocked = api_client.post(f"/api/timetables/{draft['id']}/publish/", {}, format="json")
    assert blocked.status_code == 400
    assert "conflict" in blocked.data["message"].lower()


def test_free_teacher_resolves_the_conflict(api_client, section, academic_year,
                                            period, subject, teachers):
    from academics.models import Section as SectionModel

    published = _create_timetable(api_client, section, academic_year)
    _add_entry(api_client, published, period, subject, teachers[0], room="101")
    api_client.post(f"/api/timetables/{published['id']}/publish/", {}, format="json")

    other_section = SectionModel.objects.create(
        institution=section.institution, school_class=section.school_class, name="B"
    )
    draft = _create_timetable(api_client, other_section, academic_year)
    _add_entry(api_client, draft, period, subject, teachers[1], room="201")

    report = api_client.post(f"/api/timetables/{draft['id']}/validate/", {},
                             format="json").data["data"]
    assert report["hardCount"] == 0
    assert report["canPublish"] is True


def test_room_double_booked_is_a_hard_conflict(api_client, section, academic_year,
                                               period, subject, teachers):
    from academics.models import GradeLevel, SchoolClass, Section

    published = _create_timetable(api_client, section, academic_year)
    _add_entry(api_client, published, period, subject, teachers[0])
    api_client.post(f"/api/timetables/{published['id']}/publish/", {}, format="json")

    school_class = section.school_class
    other_section = Section.objects.create(
        institution=section.institution, school_class=school_class, name="B"
    )
    other = _create_timetable(api_client, other_section, academic_year)
    _add_entry(api_client, other, period, subject, teachers[1], room="101")

    report = api_client.post(f"/api/timetables/{other['id']}/validate/", {},
                             format="json").data["data"]
    assert report["conflicts"][0]["conflictType"] == "ROOM_DOUBLE_BOOKED"


def test_teacher_overload_is_a_soft_conflict(api_client, section, academic_year,
                                             period, subject, teachers):
    from timetable.models import TimetableEntry

    teacher = teachers[0]
    period_template = institution_period = period
    days = [1, 2, 3, 4]

    timetable = _create_timetable(api_client, section, academic_year)
    # 4 entries in one week is below a 30-period cap, so keep the cap tight.
    teacher.max_periods_per_week = 2
    teacher.save(update_fields=["max_periods_per_week"])

    for day in days:
        target_period = period_template
        if not target_period:
            continue
        entry = TimetableEntry.objects.create(
            institution=section.institution, timetable_id=timetable["id"],
            day=day, period=target_period, subject=subject, teacher=teacher,
            status=TimetableEntry.Status.SCHEDULED,
        )
        entry.save()

    report = api_client.post(f"/api/timetables/{timetable['id']}/validate/", {},
                             format="json").data["data"]
    soft = [c for c in report["conflicts"] if c["severity"] == "SOFT"]
    assert any(c["conflictType"] == "TEACHER_OVERLOAD" for c in soft)


# ---------------------------------------------------------- published = immutable (req #6)
def test_published_entry_cannot_be_edited_directly(api_client, section, academic_year,
                                                   period, subject, teachers):
    timetable = _create_timetable(api_client, section, academic_year)
    entry_response = _add_entry(api_client, timetable, period, subject, teachers[0])
    entry_id = entry_response.data["data"]["id"]
    api_client.post(f"/api/timetables/{timetable['id']}/publish/", {}, format="json")

    blocked = api_client.patch(
        f"/api/timetable-entries/{entry_id}/", {"room": "999"}, format="json"
    )
    assert blocked.status_code == 400
    assert "change request" in blocked.data["message"].lower() or \
           "published" in blocked.data["message"].lower()


def test_change_request_flow_applies_the_change(api_client, section, academic_year,
                                                period, subject, teachers):
    timetable = _create_timetable(api_client, section, academic_year)
    _add_entry(api_client, timetable, period, subject, teachers[0])
    api_client.post(f"/api/timetables/{timetable['id']}/publish/", {}, format="json")

    # Propose teacher 2 via the service (API payload needs the published entry id).
    from timetable.models import TimetableEntry
    from timetable import services

    entry = TimetableEntry.objects.get(timetable_id=timetable["id"])
    request = services.create_change_request(
        entry, make_user(section.institution, "req@test.school", "TEACHER"),
        reason="Subject teacher on leave",
        proposed_teacher=teachers[1],
    )
    assert request.status == "PENDING"

    approved = api_client.post(
        f"/api/timetable-change-requests/{request.id}/approve/", {}, format="json"
    )
    assert approved.status_code == 200, approved.data
    entry.refresh_from_db()
    assert entry.teacher_id == teachers[1].id
    assert entry.status == "SUBSTITUTED"


def test_change_request_with_busy_teacher_is_blocked(api_client, section, academic_year,
                                                     period, subject, teachers):
    """Proposing a teacher who already teaches another section at that time must fail."""
    from academics.models import Section as SectionModel
    from timetable import services
    from timetable.models import TimetableEntry

    # Section A: teacher 1 at Period 1 Monday.
    first = _create_timetable(api_client, section, academic_year)
    _add_entry(api_client, first, period, subject, teachers[0], room="101")
    assert api_client.post(
        f"/api/timetables/{first['id']}/publish/", {}, format="json"
    ).status_code == 200

    # Section B: teacher 2 at the same slot.
    other_school_class = section.school_class
    other_section = SectionModel.objects.create(
        institution=section.institution, school_class=other_school_class, name="B"
    )
    second = _create_timetable(api_client, other_section, academic_year)
    _add_entry(api_client, second, period, subject, teachers[1], room="102")
    assert api_client.post(
        f"/api/timetables/{second['id']}/publish/", {}, format="json"
    ).status_code == 200

    from users.models import User

    requester = User.objects.get(email="admin@test.school")
    target = TimetableEntry.objects.get(timetable_id=second["id"])

    with pytest.raises(services.BusinessRuleError):
        services.create_change_request(
            target, requester, reason="swap",
            proposed_teacher=teachers[0],
        )
