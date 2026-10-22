"""Substitution signals: auto-create a request when a teacher is marked absent."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from attendance.models import TeacherAttendance
from people.models import Teacher
from timetable.models import Timetable, TimetableEntry

from .models import SubstitutionRequest


@receiver(post_save, sender=TeacherAttendance)
def create_substitution_request_on_absence(sender, instance, created, **kwargs):
    """When a teacher is marked absent, open a substitution request for each
    of their published timetable entries on that weekday."""
    if instance.status == TeacherAttendance.Status.PRESENT:
        return

    teacher = instance.teacher
    date = instance.date
    weekday = date.weekday() + 1  # PeriodTemplate days are 1..7 (Mon..Sun)

    entries = TimetableEntry.objects.filter(
        teacher=teacher,
        day=weekday,
        timetable__status=Timetable.Status.PUBLISHED,
    ).select_related("timetable")

    for entry in entries:
        SubstitutionRequest.objects.get_or_create(
            institution_id=instance.institution_id,
            entry=entry,
            date=date,
            defaults={
                "absent_teacher": teacher,
                "reason": f"Auto-created: teacher marked {instance.status.lower()}",
                "created_by": instance.marked_by,
            },
        )
