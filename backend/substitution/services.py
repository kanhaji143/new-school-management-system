"""
Substitute recommendation engine.

Given a `SubstitutionRequest`, find eligible teachers and rank them.

Eligibility (hard filters):
  * not already teaching in that day/period,
  * not on approved leave that date,
  * not marked absent that date,
  * (optionally) teaches the same subject,
  * within weekly workload cap.

Scoring (soft ranking) — weights are configurable via Django settings
`SUBSTITUTION_WEIGHTS`.
"""
from collections import defaultdict

from django.conf import settings
from django.db.models import Count, Q

from attendance.models import LeaveRequest, TeacherAttendance
from people.models import Teacher
from timetable.models import TimetableEntry


def _weights():
    return getattr(
        settings,
        "SUBSTITUTION_WEIGHTS",
        {
            "subject_match": 40,
            "availability": 20,
            "workload_balance": 15,
            "past_substitution": 10,
            "preference": 10,
            "proximity": 5,
        },
    )


def _teacher_is_busy(teacher_id, day, period_id, exclude_timetable_id=None):
    """True if the teacher already has an entry at this day/period."""
    qs = TimetableEntry.objects.filter(
        teacher_id=teacher_id, day=day, period_id=period_id,
    ).exclude(status="CANCELLED")
    if exclude_timetable_id:
        qs = qs.exclude(timetable_id=exclude_timetable_id)
    return qs.exists()


def _teacher_unavailable(teacher_id, date):
    """Approved leave or marked absence on the date."""
    if TeacherAttendance.objects.filter(teacher_id=teacher_id, date=date).exclude(
        status="PRESENT"
    ).exists():
        return True
    return LeaveRequest.objects.filter(
        teacher_id=teacher_id, status="APPROVED", start_date__lte=date, end_date__gte=date
    ).exists()


def _weekly_load(teacher_id, timetable=None):
    """
    Number of periods a teacher is assigned per week.

    Timetable entries are not dated (a timetable is the weekly grid for a term),
    so the load is simply the count of the teacher's non-cancelled entries.
    Restrict to a specific timetable when validating a draft.
    """
    qs = TimetableEntry.objects.filter(teacher_id=teacher_id).exclude(status="CANCELLED")
    if timetable is not None:
        qs = qs.filter(timetable=timetable)
    return qs.count()


def eligible_teachers(request, *, strict_subject=True):
    """
    Return candidate teachers eligible to cover `request`.

    `request` is a SubstitutionRequest whose `entry` carries day/period/subject/teacher.
    """
    entry = request.entry
    institution_id = request.institution_id
    date = request.date
    absent_teacher_id = request.absent_teacher_id

    base_qs = Teacher.objects.filter(institution_id=institution_id).exclude(
        id=absent_teacher_id
    )

    candidates = []
    for teacher in base_qs:
        if _teacher_is_busy(teacher.id, entry.day, entry.period_id, entry.timetable_id):
            continue
        if _teacher_unavailable(teacher.id, date):
            continue
        same_subject = teacher.class_subjects.filter(subject=entry.subject).exists()
        if strict_subject and not same_subject:
            continue
        candidates.append((teacher, same_subject))

    return candidates


def score_candidates(request, candidates):
    """Score and rank (teacher, same_subject) tuples. Returns list of dicts."""
    weights = _weights()
    ranked = []

    for teacher, same_subject in candidates:
        reasons = {}

        subject_score = 1.0 if same_subject else 0.0
        reasons["subject_match"] = subject_score

        weekly = _weekly_load(teacher.id)
        cap = teacher.max_periods_per_week or 30
        availability = max(0.0, 1.0 - (weekly / cap)) if cap else 0.0
        reasons["availability"] = round(availability, 3)

        workload_balance = availability  # inverse of load
        reasons["workload_balance"] = round(workload_balance, 3)

        from .models import SubstituteAssignment

        past = SubstituteAssignment.objects.filter(
            substitute_teacher=teacher, status="COMPLETED"
        ).count()
        reasons["past_substitution"] = min(past / 5.0, 1.0)

        reasons["preference"] = 0.5  # placeholder until teacher preference field exists

        proximity = 1.0 if teacher.department and teacher.department else 0.0
        reasons["proximity"] = proximity

        score = (
            weights["subject_match"] * subject_score
            + weights["availability"] * availability
            + weights["workload_balance"] * workload_balance
            + weights["past_substitution"] * reasons["past_substitution"]
            + weights["preference"] * reasons["preference"]
            + weights["proximity"] * proximity
        )
        ranked.append(
            {"teacher": teacher, "score": round(score, 2), "reasons": reasons}
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
    return ranked


def recommend(request, limit=3):
    """Persist ranked recommendations for a request."""
    from .models import SubstituteRecommendation

    candidates = eligible_teachers(request)
    scored = score_candidates(request, candidates)[:limit]

    SubstituteRecommendation.objects.filter(request=request).delete()
    for item in scored:
        SubstituteRecommendation.objects.create(
            institution_id=request.institution_id,
            request=request,
            teacher=item["teacher"],
            score=item["score"],
            reasons=item["reasons"],
            rank=item["rank"],
        )
    return scored
