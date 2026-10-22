"""Curriculum: syllabus → chapters → lesson plans → session logs → completion."""
from django.db import models

from common.models import TenantModel


class Syllabus(TenantModel):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey("academics.Subject", on_delete=models.PROTECT)
    section = models.ForeignKey(
        "academics.Section", null=True, blank=True, on_delete=models.CASCADE, related_name="syllabi"
    )
    course = models.ForeignKey(
        "academics.Course", null=True, blank=True, on_delete=models.CASCADE, related_name="syllabi"
    )
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.PROTECT)
    term = models.ForeignKey("academics.Term", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("institution", "subject", "section", "course", "academic_year", "term")

    def __str__(self):
        return self.title


class Chapter(TenantModel):
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)
    order_index = models.PositiveIntegerField(default=0)
    planned_hours = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order_index"]
        unique_together = ("syllabus", "order_index")

    def __str__(self):
        return self.title


class LessonPlan(TenantModel):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lesson_plans")
    title = models.CharField(max_length=200)
    objectives = models.TextField(blank=True)
    content = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=40)
    resources = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    def __str__(self):
        return self.title


class ClassSessionLog(TenantModel):
    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        PARTIAL = "PARTIAL", "Partial"
        SKIPPED = "SKIPPED", "Skipped"

    entry = models.ForeignKey(
        "timetable.TimetableEntry", null=True, blank=True, on_delete=models.SET_NULL, related_name="session_logs"
    )
    subject = models.ForeignKey("academics.Subject", on_delete=models.PROTECT)
    section = models.ForeignKey(
        "academics.Section", null=True, blank=True, on_delete=models.CASCADE, related_name="session_logs"
    )
    chapter = models.ForeignKey(
        Chapter, null=True, blank=True, on_delete=models.SET_NULL, related_name="session_logs"
    )
    topic = models.CharField(max_length=255)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    teacher = models.ForeignKey(
        "people.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="session_logs"
    )
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["institution", "date"])]


class LessonCompletion(TenantModel):
    """Explicit, human-verified completion. Never auto-set from elapsed time."""

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"

    chapter = models.OneToOneField(
        Chapter, on_delete=models.CASCADE, related_name="completion"
    )
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PLANNED)
    verified_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    def __str__(self):
        return f"{self.chapter} — {self.status}"
