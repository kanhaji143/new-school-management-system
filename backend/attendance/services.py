"""Attendance services: bulk marking, audited corrections, leave workflow.

Design notes
------------
* Marking is an *upsert*: re-submitting the same roster only rewrites rows whose
  values actually changed, and every change is written to the audit log
  ("CORRECT") so attendance edits stay traceable (brief requirement #9).
* All queries are scoped explicitly by ``institution_id`` because services are
  also called outside a request (management commands, tests, tasks).
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from common.audit import instance_to_dict, log_action
from people.models import Student

from . import models


class AttendanceError(Exception):
    """Domain error surfaced to the API as a 400 response."""

    def __init__(self, message):
        self.message = message
        super().__init__(message)


CREATED = "created"
CORRECTED = "corrected"
UNCHANGED = "unchanged"


# ------------------------------------------------------------------ helpers
def _snapshot(instance, fields):
    return instance_to_dict(instance, fields=list(fields))


def _upsert(model, lookup, defaults, actor, audit_fields):
    """Create or correct one attendance row.

    Returns ``(instance, outcome)`` where outcome is CREATED / CORRECTED /
    UNCHANGED. Corrections are written to the audit log.
    """
    existing = model.all_objects.filter(**lookup).first()

    if existing is None:
        return model.all_objects.create(**lookup, **defaults), CREATED

    changed = any(
        getattr(existing, field) != value
        for field, value in defaults.items()
        if field in audit_fields
    )
    if not changed:
        return existing, UNCHANGED

    before = _snapshot(existing, audit_fields)
    for field, value in defaults.items():
        setattr(existing, field, value)
    existing.save(update_fields=[*defaults.keys(), "updated_at"])

    log_action(
        actor,
        "CORRECT",
        existing,
        before=before,
        after=_snapshot(existing, audit_fields),
        institution_id=lookup["institution_id"],
    )
    return existing, CORRECTED


def _tally(outcomes):
    return {
        CREATED: sum(1 for outcome in outcomes if outcome == CREATED),
        CORRECTED: sum(1 for outcome in outcomes if outcome == CORRECTED),
        UNCHANGED: sum(1 for outcome in outcomes if outcome == UNCHANGED),
    }


# ------------------------------------------------------------ student (daily)
def mark_daily_attendance(institution_id, date, records, marked_by=None):
    """Upsert a daily roster for ``date``.

    ``records`` is an iterable of ``{student, status, remark}`` mappings.
    """
    records = list(records)
    if not records:
        raise AttendanceError("No attendance records were provided.")

    outcomes = []
    with transaction.atomic():
        for record in records:
            student = record["student"]
            if student.institution_id != institution_id:
                raise AttendanceError("Student does not belong to this institution.")

            _, outcome = _upsert(
                models.StudentAttendance,
                {
                    "institution_id": institution_id,
                    "student": student,
                    "date": date,
                },
                defaults={
                    "status": record.get("status", models.StudentAttendance.Status.PRESENT),
                    "remark": record.get("remark", "") or "",
                    "marked_by": marked_by,
                },
                actor=marked_by,
                audit_fields=("status", "remark"),
            )
            outcomes.append(outcome)

    return _tally(outcomes)


def daily_summary(institution_id, date, section_id=None, course_id=None, student_id=None):
    """Counts for a date, optionally limited to one section."""
    records = models.StudentAttendance.all_objects.filter(
        institution_id=institution_id, date=date
    )
    students = Student.all_objects.filter(
        institution_id=institution_id, status=Student.Status.ACTIVE
    )
    if section_id is not None:
        records = records.filter(student__section_id=section_id)
        students = students.filter(section_id=section_id)
    if course_id is not None:
        records = records.filter(student__course_id=course_id)
        students = students.filter(course_id=course_id)
    if student_id is not None:
        records = records.filter(student_id=student_id)
        students = students.filter(id=student_id)

    counts = {status: 0 for status in models.StudentAttendance.Status.values}
    for row in records.values("status"):
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    enrolled = students.count()
    marked = sum(counts.values())
    present = counts.get(models.StudentAttendance.Status.PRESENT, 0)

    return {
        "date": date,
        "section": section_id,
        "course": course_id,
        "enrolled": enrolled,
        "marked": marked,
        "unmarked": max(enrolled - marked, 0),
        "counts": counts,
        "attendanceRate": round((present / marked) * 100, 1) if marked else 0.0,
    }


# ----------------------------------------------------------- student (period)
def mark_period_attendance(institution_id, date, entry, records, marked_by=None):
    """Upsert per-period attendance for one timetable entry."""
    if entry.institution_id != institution_id:
        raise AttendanceError("Timetable entry does not belong to this institution.")

    records = list(records)
    if not records:
        raise AttendanceError("No attendance records were provided.")

    outcomes = []
    with transaction.atomic():
        for record in records:
            student = record["student"]
            if student.institution_id != institution_id:
                raise AttendanceError("Student does not belong to this institution.")

            _, outcome = _upsert(
                models.PeriodAttendance,
                {
                    "institution_id": institution_id,
                    "student": student,
                    "entry": entry,
                    "date": date,
                },
                defaults={
                    "status": record.get("status", models.PeriodAttendance.Status.PRESENT),
                    "marked_by": marked_by,
                },
                actor=marked_by,
                audit_fields=("status",),
            )
            outcomes.append(outcome)

    return _tally(outcomes)


# -------------------------------------------------------------------- teacher
def mark_teacher_attendance(institution_id, date, records, marked_by=None):
    """Upsert daily staff attendance."""
    records = list(records)
    if not records:
        raise AttendanceError("No attendance records were provided.")

    outcomes = []
    with transaction.atomic():
        for record in records:
            teacher = record["teacher"]
            if teacher.institution_id != institution_id:
                raise AttendanceError("Teacher does not belong to this institution.")

            _, outcome = _upsert(
                models.TeacherAttendance,
                {
                    "institution_id": institution_id,
                    "teacher": teacher,
                    "date": date,
                },
                defaults={
                    "status": record.get("status", models.TeacherAttendance.Status.PRESENT),
                    "check_in": record.get("check_in"),
                    "check_out": record.get("check_out"),
                    "marked_by": marked_by,
                },
                actor=marked_by,
                audit_fields=("status", "check_in", "check_out"),
            )
            outcomes.append(outcome)

    return _tally(outcomes)


# --------------------------------------------------------------------- leave
def _validate_leave_dates(start_date, end_date):
    if end_date < start_date:
        raise AttendanceError("End date cannot be before the start date.")


@transaction.atomic
def approve_leave(leave_request, approver=None):
    """Approve a pending request and record the absence for each working day."""
    if leave_request.status != models.LeaveRequest.Status.PENDING:
        raise AttendanceError("Only pending leave requests can be approved.")
    _validate_leave_dates(leave_request.start_date, leave_request.end_date)

    leave_request.status = models.LeaveRequest.Status.APPROVED
    leave_request.approved_by = approver
    leave_request.approved_at = timezone.now()
    leave_request.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    # Staff attendance: fill any day that has no record yet as ABSENT.
    day = leave_request.start_date
    while day <= leave_request.end_date:
        models.TeacherAttendance.all_objects.get_or_create(
            institution_id=leave_request.institution_id,
            teacher=leave_request.teacher,
            date=day,
            defaults={
                "status": models.TeacherAttendance.Status.ABSENT,
                "marked_by": approver,
            },
        )
        day += timedelta(days=1)

    log_action(
        approver,
        "UPDATE",
        leave_request,
        before={"status": models.LeaveRequest.Status.PENDING},
        after={"status": leave_request.status},
        institution_id=leave_request.institution_id,
    )
    return leave_request


@transaction.atomic
def reject_leave(leave_request, approver=None, reason=""):
    if leave_request.status != models.LeaveRequest.Status.PENDING:
        raise AttendanceError("Only pending leave requests can be rejected.")

    leave_request.status = models.LeaveRequest.Status.REJECTED
    leave_request.approved_by = approver
    leave_request.approved_at = timezone.now()
    if reason:
        leave_request.reason = f"{leave_request.reason}\n\nRejected: {reason}".strip()
    leave_request.save(
        update_fields=["status", "approved_by", "approved_at", "reason", "updated_at"]
    )
    log_action(
        approver,
        "UPDATE",
        leave_request,
        before={"status": models.LeaveRequest.Status.PENDING},
        after={"status": leave_request.status, "reason": reason},
        institution_id=leave_request.institution_id,
    )
    return leave_request
