"""Academics domain services.

Business rules that must not be bypassed by direct API calls live here:
  * exactly one active AcademicYear per institution,
  * exactly one active Term per AcademicYear,
  * student promotion between years/terms.
"""
from django.db import transaction

from .models import AcademicYear, Enrollment, Term


def get_active_academic_year(institution_id):
    """Return the institution's active academic year, if any."""
    return (
        AcademicYear.all_objects.filter(institution_id=institution_id, is_active=True)
        .order_by("-start_date")
        .first()
    )


def get_active_term(institution_id, academic_year_id=None):
    """Return the active term for the given (or active) academic year."""
    if academic_year_id is None:
        year = get_active_academic_year(institution_id)
        if year is None:
            return None
        academic_year_id = year.id
    return (
        Term.all_objects.filter(
            academic_year_id=academic_year_id, is_active=True
        ).order_by("start_date")
        .first()
    )


@transaction.atomic
def activate_academic_year(academic_year):
    """Make `academic_year` the only active year for the institution."""
    AcademicYear.all_objects.filter(
        institution_id=academic_year.institution_id, is_active=True
    ).exclude(pk=academic_year.pk).update(is_active=False)

    if not academic_year.is_active:
        academic_year.is_active = True
        academic_year.save(update_fields=["is_active", "updated_at"])
    return academic_year


@transaction.atomic
def deactivate_academic_year(academic_year):
    """Deactivate a year (its terms are deactivated with it)."""
    academic_year.is_active = False
    academic_year.save(update_fields=["is_active", "updated_at"])
    Term.all_objects.filter(
        academic_year_id=academic_year.id, is_active=True
    ).update(is_active=False)
    return academic_year


@transaction.atomic
def activate_term(term):
    """Make `term` the only active term inside its academic year."""
    Term.all_objects.filter(
        academic_year_id=term.academic_year_id, is_active=True
    ).exclude(pk=term.pk).update(is_active=False)

    if not term.is_active:
        term.is_active = True
        term.save(update_fields=["is_active", "updated_at"])
    return term


@transaction.atomic
def promote_students(
    institution_id,
    from_year,
    to_year,
    from_term=None,
    to_term=None,
    section_map=None,
):
    """Carry active enrollments from one year/term into the next.

    `section_map` maps a source section id to a target section id. Students
    without a mapping are carried over with no section (they can be assigned
    later from the Students screen).

    Returns the list of newly created Enrollment objects.
    """
    section_map = section_map or {}

    queryset = Enrollment.all_objects.filter(
        institution_id=institution_id,
        academic_year_id=from_year.id,
        status=Enrollment.Status.ACTIVE,
    )
    if from_term is not None:
        queryset = queryset.filter(term_id=from_term.id)

    created = []
    for enrollment in queryset:
        target_section_id = section_map.get(enrollment.section_id)
        if target_section_id is None and enrollment.section_id:
            # Keep the same section only if it belongs to the target year context.
            target_section_id = enrollment.section_id

        enrollment, _ = Enrollment.all_objects.update_or_create(
            institution_id=institution_id,
            student_id=enrollment.student_id,
            academic_year_id=to_year.id,
            term_id=to_term.id if to_term is not None else None,
            defaults={
                "section_id": target_section_id,
                "course_id": enrollment.course_id,
                "status": Enrollment.Status.ACTIVE,
            },
        )
        created.append(enrollment)

    # Old enrollments become historical records rather than active rows.
    Enrollment.all_objects.filter(
        institution_id=institution_id,
        academic_year_id=from_year.id,
        status=Enrollment.Status.ACTIVE,
    ).exclude(id__in=[e.id for e in created]).update(status=Enrollment.Status.PROMOTED)

    return created
