"""
Timetable services: conflict detection, publishing and change approval.

Rules enforced here (brief requirements #5 and #6):

* a published timetable may not be edited directly - changes go through an
  approved `TimetableChangeRequest`,
* publishing is blocked while unresolved HARD conflicts exist,
* a teacher / section / room cannot be booked twice in the same day + period
  across published timetables.

See `docs/07-timetable-conflict.md` for the design.
"""
from django.db import transaction
from django.utils import timezone

from people.models import Teacher

from .models import (
    Timetable,
    TimetableChangeRequest,
    TimetableConflict,
    TimetableEntry,
)


class BusinessRuleError(Exception):
    """Raised when a timetable rule would be violated."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


# --------------------------------------------------------------------------- lookups
def _excluding(exclude_timetable_ids, exclude_entry_id):
    def apply(qs):
        if exclude_timetable_ids:
            qs = qs.exclude(timetable_id__in=list(exclude_timetable_ids))
        if exclude_entry_id is not None:
            qs = qs.exclude(pk=exclude_entry_id)
        return qs
    return apply


def _find_booked_teacher(institution_id, teacher_id, day, period_id,
                         exclude_timetable_ids=(), exclude_entry_id=None):
    """Where is this teacher already teaching at day/period?"""
    return _excluding(exclude_timetable_ids, exclude_entry_id)(
        TimetableEntry.all_objects.filter(
            institution_id=institution_id,
            teacher_id=teacher_id, day=day, period_id=period_id,
            timetable__status=Timetable.Status.PUBLISHED,
        ).exclude(status=TimetableEntry.Status.CANCELLED)
        .select_related("timetable", "subject")
    ).first()


def _find_booked_room(institution_id, room, day, period_id,
                      exclude_timetable_ids=(), exclude_entry_id=None):
    room = (room or "").strip()
    return _excluding(exclude_timetable_ids, exclude_entry_id)(
        TimetableEntry.all_objects.filter(
            institution_id=institution_id,
            room__iexact=room, day=day, period_id=period_id,
            timetable__status=Timetable.Status.PUBLISHED,
        ).exclude(status=TimetableEntry.Status.CANCELLED)
        .select_related("timetable")
    ).first()


def _find_booked_section(institution_id, section_id, day, period_id,
                         exclude_timetable_ids=(), exclude_entry_id=None):
    """Where is this section already taught at day/period?"""
    return _excluding(exclude_timetable_ids, exclude_entry_id)(
        TimetableEntry.all_objects.filter(
            institution_id=institution_id,
            timetable__section_id=section_id, day=day, period_id=period_id,
            timetable__status=Timetable.Status.PUBLISHED,
        ).exclude(status=TimetableEntry.Status.CANCELLED)
        .select_related("timetable")
    ).first()


def _superseded_published(timetable):
    """
    Published timetables of the *same* section/course scope that publishing this
    one would archive. They are excluded from conflict detection because the new
    version legitimately replaces them.
    """
    qs = Timetable.all_objects.filter(
        institution_id=timetable.institution_id,
        status=Timetable.Status.PUBLISHED,
        academic_year_id=timetable.academic_year_id,
    ).exclude(pk=timetable.pk)
    if timetable.term_id is not None:
        qs = qs.filter(term_id=timetable.term_id)
    if timetable.section_id is not None:
        qs = qs.filter(section_id=timetable.section_id)
    elif timetable.course_id is not None:
        qs = qs.filter(course_id=timetable.course_id)
    return qs


def _weekly_periods(teacher_id, institution_id, statuses=None):
    qs = TimetableEntry.all_objects.filter(
        institution_id=institution_id, teacher_id=teacher_id,
    ).exclude(status=TimetableEntry.Status.CANCELLED)
    if statuses is not None:
        qs = qs.filter(status__in=statuses)
    return qs.count()


# ----------------------------------------------------------------- conflict detection
@transaction.atomic
def detect_conflicts(timetable, persist=True):
    """
    Scan `timetable` and return its `TimetableConflict` objects.

    Hard conflicts (block publishing):
      * TEACHER_DOUBLE_BOOKED - teacher already teaching in a published timetable
      * ROOM_DOUBLE_BOOKED    - room already occupied in a published timetable
      * CLASS_DOUBLE_BOOKED   - the section already has another published timetable
                                active at that time

    Soft conflicts (warnings only):
      * TEACHER_OVERLOAD      - exceeds the teacher's weekly period cap
      * SUBJECT_FREQUENCY     - a subject repeats in one day for one section
    """
    institution_id = timetable.institution_id
    peer_timetable_ids = list(_superseded_published(timetable).values_list("id", flat=True))

    entries = list(
        TimetableEntry.all_objects.filter(timetable=timetable)
        .select_related("timetable", "teacher", "period", "subject")
    )

    conflicts = []
    teacher_period_counts = {}
    subject_day_counts = {}

    for entry in entries:
        if entry.status == TimetableEntry.Status.CANCELLED:
            continue

        if entry.teacher:
            clash = _find_booked_teacher(
                institution_id, entry.teacher_id, entry.day, entry.period_id,
                exclude_timetable_ids=peer_timetable_ids, exclude_entry_id=entry.id,
            )
            if clash:
                conflicts.append(TimetableConflict(
                    institution_id=institution_id,
                    timetable=timetable,
                    conflict_type=TimetableConflict.ConflictType.TEACHER_DOUBLE_BOOKED,
                    severity=TimetableConflict.Severity.HARD,
                    description=(
                        f"{entry.teacher.user.full_name} is already teaching "
                        f"{clash.subject.name} in {clash.timetable} at this time."
                    ),
                    entry_a=entry, entry_b=clash,
                ))

            teacher_period_counts.setdefault(entry.teacher_id, 0)
            teacher_period_counts[entry.teacher_id] += 1

        if entry.room:
            clash = _find_booked_room(
                institution_id, entry.room, entry.day, entry.period_id,
                exclude_timetable_ids=peer_timetable_ids, exclude_entry_id=entry.id,
            )
            if clash:
                conflicts.append(TimetableConflict(
                    institution_id=institution_id,
                    timetable=timetable,
                    conflict_type=TimetableConflict.ConflictType.ROOM_DOUBLE_BOOKED,
                    severity=TimetableConflict.Severity.HARD,
                    description=(
                        f"Room {entry.room} is already used by {clash.timetable} "
                        f"at this time."
                    ),
                    entry_a=entry, entry_b=clash,
                ))

        if entry.timetable.section_id is not None:
            clash = _find_booked_section(
                institution_id, entry.timetable.section_id, entry.day, entry.period_id,
                exclude_timetable_ids=peer_timetable_ids, exclude_entry_id=entry.id,
            )
            if clash and clash.timetable_id != timetable.id:
                conflicts.append(TimetableConflict(
                    institution_id=institution_id,
                    timetable=timetable,
                    conflict_type=TimetableConflict.ConflictType.CLASS_DOUBLE_BOOKED,
                    severity=TimetableConflict.Severity.HARD,
                    description=(
                        f"This section already has {clash.timetable} scheduled "
                        f"at this time."
                    ),
                    entry_a=entry, entry_b=clash,
                ))

        subject_day_key = (entry.subject_id, entry.day)
        subject_day_counts[subject_day_key] = subject_day_counts.get(subject_day_key, 0) + 1

    # Soft: per-teacher weekly overload.
    for teacher_id, count in teacher_period_counts.items():
        from people.models import Teacher as TeacherModel

        teacher = TeacherModel.all_objects.filter(id=teacher_id).first()
        if teacher and count > (teacher.max_periods_per_week or 30):
            conflicts.append(TimetableConflict(
                institution_id=institution_id,
                timetable=timetable,
                conflict_type=TimetableConflict.ConflictType.TEACHER_OVERLOAD,
                severity=TimetableConflict.Severity.SOFT,
                description=(
                    f"{teacher.user.full_name} has {count} periods/week which exceeds "
                    f"the cap of {teacher.max_periods_per_week}."
                ),
            ))

    # Soft: same subject more than once a day for a section.
    for (subject_id, day), count in subject_day_counts.items():
        if count > 1:
            duplicate = next(e for e in entries if e.subject_id == subject_id and e.day == day)
            conflicts.append(TimetableConflict(
                institution_id=institution_id,
                timetable=timetable,
                conflict_type=TimetableConflict.ConflictType.SUBJECT_FREQUENCY,
                severity=TimetableConflict.Severity.SOFT,
                description=(
                    f"{duplicate.subject.name} appears {count} times on "
                    f"{duplicate.get_day_display()}."
                ),
                entry_a=duplicate,
            ))

    if persist:
        TimetableConflict.all_objects.filter(timetable=timetable, is_resolved=False).delete()
        for conflict in conflicts:
            conflict.save()

    return conflicts


def hard_conflicts(timetable):
    return [c for c in detect_conflicts(timetable, persist=False)
            if c.severity == TimetableConflict.Severity.HARD]


def soft_conflicts(timetable):
    return [c for c in detect_conflicts(timetable, persist=False)
            if c.severity == TimetableConflict.Severity.SOFT]


# ------------------------------------------------------------------------ publishing
@transaction.atomic
def publish(timetable, published_by):
    """Publish a draft timetable; refuses when unresolved HARD conflicts exist."""
    unresolved = [c for c in detect_conflicts(timetable, persist=True)
                  if c.severity == TimetableConflict.Severity.HARD]
    if unresolved:
        raise BusinessRuleError(
            f"{len(unresolved)} hard conflict(s) must be resolved before publishing."
        )

    timetable.status = Timetable.Status.PUBLISHED
    timetable.published_at = timezone.now()
    timetable.published_by = published_by
    timetable.save(update_fields=["status", "published_at", "published_by", "updated_at"])

    # Archive older published versions of the same schedule.
    qs = Timetable.all_objects.filter(
        institution_id=timetable.institution_id,
        status=Timetable.Status.PUBLISHED,
        academic_year_id=timetable.academic_year_id,
    ).exclude(pk=timetable.pk)
    if timetable.section_id is not None:
        qs = qs.filter(section_id=timetable.section_id)
    elif timetable.course_id is not None:
        qs = qs.filter(course_id=timetable.course_id)
    if timetable.term_id is not None:
        qs = qs.filter(term_id=timetable.term_id)
    qs.update(status=Timetable.Status.ARCHIVED)

    return timetable


# --------------------------------------------------------------- change-request flow
@transaction.atomic
def create_change_request(entry, requested_by, *, reason,
                          proposed_teacher=None, proposed_room=None):
    """
    Propose an edit to a published entry. Published timetables cannot be
    modified directly (brief requirement #6), everything goes through here.
    """
    if entry.timetable.status != Timetable.Status.PUBLISHED:
        raise BusinessRuleError("Only published timetable entries can be changed.")

    if proposed_teacher is None and (proposed_room or "").strip() == (entry.room or ""):
        raise BusinessRuleError("Nothing to change - propose a teacher or a room.")

    if proposed_teacher:
        clash = _find_booked_teacher(
            entry.institution_id, proposed_teacher.id, entry.day, entry.period_id,
            exclude_entry_id=entry.id,
        )
        if clash:
            raise BusinessRuleError(
                f"{proposed_teacher.user.full_name} is already teaching "
                f"{clash.subject.name} at that time ({clash.timetable})."
            )

    return TimetableChangeRequest.objects.create(
        institution_id=entry.institution_id,
        entry=entry,
        proposed_teacher=proposed_teacher,
        proposed_room=(proposed_room or "").strip(),
        reason=reason,
        requested_by=requested_by,
        status=TimetableChangeRequest.Status.PENDING,
    )


@transaction.atomic
def approve_change_request(change_request, approver):
    """Apply the requested change to the published timetable."""
    if change_request.status != TimetableChangeRequest.Status.PENDING:
        raise BusinessRuleError(
            f"This change request is already {change_request.status.lower()}."
        )

    entry = change_request.entry
    if change_request.proposed_teacher:
        clash = _find_booked_teacher(
            entry.institution_id, change_request.proposed_teacher_id,
            entry.day, entry.period_id, exclude_entry_id=entry.id,
        )
        if clash:
            raise BusinessRuleError(
                f"{change_request.proposed_teacher.user.full_name} is now busy at "
                f"that time ({clash.timetable}). Reject the request instead."
            )

    if change_request.proposed_teacher:
        entry.teacher = change_request.proposed_teacher
        entry.status = TimetableEntry.Status.SUBSTITUTED
    if change_request.proposed_room:
        entry.room = change_request.proposed_room
    entry.save(update_fields=["teacher", "room", "status", "updated_at"])

    change_request.status = TimetableChangeRequest.Status.APPROVED
    change_request.approved_by = approver
    change_request.approved_at = timezone.now()
    change_request.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return change_request


@transaction.atomic
def reject_change_request(change_request, approver, reason):
    if change_request.status != TimetableChangeRequest.Status.PENDING:
        raise BusinessRuleError(
            f"This change request is already {change_request.status.lower()}."
        )
    change_request.status = TimetableChangeRequest.Status.REJECTED
    change_request.approved_by = approver  # reviewed by
    change_request.approved_at = timezone.now()
    change_request.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return change_request


# --------------------------------------------------------------------- entry helpers
@transaction.atomic
def create_draft(validated_data):
    """Create the next version of a draft timetable for the given scope."""
    institution_id = validated_data["institution_id"]
    academic_year = validated_data.get("academic_year")

    scope_q = Timetable.all_objects.filter(
        institution_id=institution_id,
        academic_year=academic_year,
    )
    if validated_data.get("section_id") is not None:
        scope_q = scope_q.filter(section_id=validated_data["section_id"])
    elif validated_data.get("course_id") is not None:
        scope_q = scope_q.filter(course_id=validated_data["course_id"])
    if validated_data.get("term_id") is not None:
        scope_q = scope_q.filter(term_id=validated_data["term_id"])

    latest = scope_q.order_by("-version").first()
    version = (latest.version + 1) if latest else 1

    return Timetable.objects.create(
        version=version, status=Timetable.Status.DRAFT, **validated_data
    )


def cancel_entry(entry):
    """Cancel a draft entry. Published entries must go through change requests."""
    if entry.timetable.status == Timetable.Status.PUBLISHED:
        raise BusinessRuleError(
            "Published timetables cannot be edited directly - raise a change request."
        )
    entry.status = TimetableEntry.Status.CANCELLED
    entry.save(update_fields=["status", "updated_at"])
    return entry
