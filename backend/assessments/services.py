"""Assessments services: bulk marks, grading, results."""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from common.audit import log_action
from people.models import Student

from . import models


class AssessmentError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


@transaction.atomic
def assign_students(assessment, students):
    """Create pending assignment rows for selected students, idempotently."""
    students = list(students)
    if not students:
        raise AssessmentError("Select at least one student.")
    if any(student.institution_id != assessment.institution_id for student in students):
        raise AssessmentError("Students must belong to this institution.")
    if assessment.section_id and any(student.section_id != assessment.section_id for student in students):
        raise AssessmentError("Only students in this assessment's section can be assigned.")

    created = unchanged = 0
    for student in students:
        _row, was_created = models.StudentAssessment.all_objects.get_or_create(
            institution_id=assessment.institution_id,
            assessment=assessment,
            student=student,
            defaults={"status": models.StudentAssessment.Status.PENDING},
        )
        created += int(was_created)
        unchanged += int(not was_created)
    return {"created": created, "already_assigned": unchanged, "total": len(students)}


@transaction.atomic
def submit_student_answers(assignment, student_user, answers):
    if assignment.student.user_id != student_user.id:
        raise AssessmentError("You can only submit answers for your own assignment.")
    if assignment.status != models.StudentAssessment.Status.PENDING:
        raise AssessmentError("This assessment is no longer accepting submissions.")
    allowed_question_ids = set(
        assignment.assessment.questions.values_list("question_id", flat=True)
    )
    try:
        submitted_question_ids = {int(question_id) for question_id in answers}
    except (TypeError, ValueError) as exc:
        raise AssessmentError("Answer keys must be question IDs.") from exc
    if submitted_question_ids - allowed_question_ids:
        raise AssessmentError("Answers include a question that is not part of this assessment.")
    links = assignment.assessment.questions.select_related("question").all()
    auto_marks = Decimal("0")
    has_manual_questions = False
    for link in links:
        question = link.question
        if question.question_type in (
            models.Question.QuestionType.MCQ,
            models.Question.QuestionType.TRUE_FALSE,
        ):
            submitted = str(answers.get(str(question.id), "")).strip().lower()
            correct = str(question.correct_answer).strip().lower()
            if submitted and submitted == correct:
                auto_marks += Decimal(link.marks_override or question.marks)
        else:
            has_manual_questions = True

    assignment.answers = answers
    assignment.obtained_marks = auto_marks
    if has_manual_questions:
        assignment.status = models.StudentAssessment.Status.SUBMITTED
        assignment.remarks = "Objective questions auto-graded; descriptive answers await teacher review."
    else:
        assignment.status = models.StudentAssessment.Status.GRADED
        assignment.grade = _grade_for_marks(
            assignment.institution_id, auto_marks, assignment.assessment.total_marks
        )
        assignment.remarks = "Auto-graded objective assessment."
    assignment.submitted_at = timezone.now()
    assignment.save(update_fields=[
        "answers", "obtained_marks", "grade", "remarks", "status", "submitted_at", "updated_at"
    ])
    return assignment


def _grade_for_marks(institution_id, marks, total_marks):
    if marks is None:
        return ""
    scales = models.GradeScale.all_objects.filter(institution_id=institution_id)
    for scale in scales:
        if scale.min_mark <= marks <= scale.max_mark:
            return scale.grade
    # Fallback: percentage-based letter grade if no scale matches.
    if total_marks:
        pct = (Decimal(marks) / Decimal(total_marks)) * 100
        if pct >= 90:
            return "A+"
        if pct >= 80:
            return "A"
        if pct >= 70:
            return "B"
        if pct >= 60:
            return "C"
        if pct >= 50:
            return "D"
        return "F"
    return ""


@transaction.atomic
def bulk_marks(assessment, records, marked_by=None):
    if assessment.institution_id != assessment.institution_id:
        raise AssessmentError("Assessment does not belong to this institution.")
    if not records:
        raise AssessmentError("No marks records were provided.")

    created = corrected = 0
    for record in records:
        student = record["student"]
        if student.institution_id != assessment.institution_id:
            raise AssessmentError("Student does not belong to this institution.")
        if assessment.section_id and student.section_id != assessment.section_id:
            raise AssessmentError("Student is not in this assessment's section.")

        obtained = record.get("obtained_marks")
        grade = _grade_for_marks(assessment.institution_id, obtained, assessment.total_marks)
        status_value = record.get("status", models.StudentAssessment.Status.GRADED)
        submitted_at = timezone.now() if status_value != models.StudentAssessment.Status.PENDING else None

        existing = models.StudentAssessment.all_objects.filter(
            institution_id=assessment.institution_id, assessment=assessment, student=student
        ).first()

        if existing is None:
            models.StudentAssessment.all_objects.create(
                institution_id=assessment.institution_id,
                assessment=assessment,
                student=student,
                obtained_marks=obtained,
                grade=grade,
                remarks=record.get("remarks", "") or "",
                status=status_value,
                submitted_at=submitted_at,
            )
            created += 1
            continue

        before = {"obtained_marks": str(existing.obtained_marks), "grade": existing.grade, "status": existing.status}
        changed = (
            existing.obtained_marks != obtained
            or existing.grade != grade
            or existing.remarks != (record.get("remarks", "") or "")
            or existing.status != status_value
        )
        if not changed:
            continue
        existing.obtained_marks = obtained
        existing.grade = grade
        existing.remarks = record.get("remarks", "") or ""
        existing.status = status_value
        if submitted_at and not existing.submitted_at:
            existing.submitted_at = submitted_at
        existing.save()
        log_action(
            marked_by, "CORRECT", existing,
            before=before,
            after={"obtained_marks": str(obtained), "grade": grade, "status": status_value},
            institution_id=assessment.institution_id,
        )
        corrected += 1

    return {"created": created, "corrected": corrected, "total": len(records)}


def compute_results(assessment):
    """Return ranked result rows for an assessment."""
    rows = models.StudentAssessment.all_objects.filter(
        institution_id=assessment.institution_id, assessment=assessment
    ).select_related("student__user")

    results = []
    for row in rows:
        obtained = row.obtained_marks
        percentage = None
        if obtained is not None and assessment.total_marks:
            percentage = round((float(obtained) / assessment.total_marks) * 100, 2)
        passed = (
            obtained is not None and float(obtained) >= assessment.pass_marks
        )
        results.append(
            {
                "student": row.student_id,
                "student_detail": {
                    "id": row.student_id,
                    "roll_number": row.student.roll_number,
                    "full_name": row.student.user.full_name,
                },
                "obtained_marks": str(obtained) if obtained is not None else None,
                "total_marks": assessment.total_marks,
                "percentage": percentage,
                "grade": row.grade,
                "passed": passed,
                "status": row.status,
                "remarks": row.remarks,
            }
        )

    results.sort(key=lambda r: (r["obtained_marks"] is None, -(float(r["obtained_marks"]) if r["obtained_marks"] is not None else 0)))
    for index, row in enumerate(results, start=1):
        row["rank"] = index if row["obtained_marks"] is not None else None
    return {
        "assessment": {
            "id": assessment.id,
            "title": assessment.title,
            "total_marks": assessment.total_marks,
            "pass_marks": assessment.pass_marks,
        },
        "results": results,
        "summary": {
            "total": len(results),
            "graded": sum(1 for r in results if r["status"] == models.StudentAssessment.Status.GRADED),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if r["obtained_marks"] is not None and not r["passed"]),
            "average": round(
                sum(float(r["obtained_marks"]) for r in results if r["obtained_marks"] is not None)
                / max(sum(1 for r in results if r["obtained_marks"] is not None), 1),
                2,
            ) if any(r["obtained_marks"] is not None for r in results) else 0.0,
        },
    }
