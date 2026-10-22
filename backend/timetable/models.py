"""Timetable: period templates, versioned timetables, entries, change requests, conflicts."""
from django.db import models

from common.models import TenantModel


class PeriodTemplate(TenantModel):
    DAY_CHOICES = [(i, day) for i, day in enumerate(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], start=1
    )]

    name = models.CharField(max_length=30)  # Period 1
    day = models.PositiveSmallIntegerField(choices=DAY_CHOICES, default=1)
    start_time = models.TimeField()
    end_time = models.TimeField()
    order_index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["day", "order_index"]

    def __str__(self):
        return f"{self.name} ({self.get_day_display()}) {self.start_time:%H:%M}"


class Timetable(TenantModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    section = models.ForeignKey(
        "academics.Section", null=True, blank=True, on_delete=models.CASCADE, related_name="timetables"
    )
    course = models.ForeignKey(
        "academics.Course", null=True, blank=True, on_delete=models.CASCADE, related_name="timetables"
    )
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.PROTECT)
    term = models.ForeignKey("academics.Term", null=True, blank=True, on_delete=models.SET_NULL)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        unique_together = ("institution", "section", "course", "academic_year", "term", "version")

    def __str__(self):
        target = self.section or self.course
        return f"Timetable {target} v{self.version} ({self.status})"


class TimetableEntry(TenantModel):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CANCELLED = "CANCELLED", "Cancelled"
        SUBSTITUTED = "SUBSTITUTED", "Substituted"

    timetable = models.ForeignKey(
        Timetable, on_delete=models.CASCADE, related_name="entries"
    )
    day = models.PositiveSmallIntegerField(choices=PeriodTemplate.DAY_CHOICES)
    period = models.ForeignKey(PeriodTemplate, on_delete=models.PROTECT, related_name="entries")
    subject = models.ForeignKey("academics.Subject", on_delete=models.PROTECT)
    teacher = models.ForeignKey(
        "people.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="timetable_entries"
    )
    room = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)

    class Meta:
        unique_together = ("timetable", "day", "period")
        indexes = [models.Index(fields=["timetable", "day"])]

    def __str__(self):
        return f"{self.timetable} {self.get_day_display()} {self.period} → {self.subject}"


class TimetableChangeRequest(TenantModel):
    """No change to a published timetable without an approved request."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    entry = models.ForeignKey(
        TimetableEntry, on_delete=models.CASCADE, related_name="change_requests"
    )
    proposed_teacher = models.ForeignKey(
        "people.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    proposed_room = models.CharField(max_length=40, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    approved_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Change request for {self.entry} ({self.status})"


class TimetableConflict(TenantModel):
    class ConflictType(models.TextChoices):
        TEACHER_DOUBLE_BOOKED = "TEACHER_DOUBLE_BOOKED", "Teacher double-booked"
        ROOM_DOUBLE_BOOKED = "ROOM_DOUBLE_BOOKED", "Room double-booked"
        CLASS_DOUBLE_BOOKED = "CLASS_DOUBLE_BOOKED", "Class double-booked"
        TEACHER_UNAVAILABLE = "TEACHER_UNAVAILABLE", "Teacher unavailable"
        TEACHER_OVERLOAD = "TEACHER_OVERLOAD", "Teacher overload"
        CLASS_OVERLOAD = "CLASS_OVERLOAD", "Class overload"
        SUBJECT_FREQUENCY = "SUBJECT_FREQUENCY", "Subject frequency"
        WORKLOAD_IMBALANCE = "WORKLOAD_IMBALANCE", "Workload imbalance"

    class Severity(models.TextChoices):
        HARD = "HARD", "Hard"
        SOFT = "SOFT", "Soft"

    timetable = models.ForeignKey(
        Timetable, on_delete=models.CASCADE, related_name="conflicts"
    )
    conflict_type = models.CharField(max_length=30, choices=ConflictType.choices)
    severity = models.CharField(max_length=5, choices=Severity.choices, default=Severity.HARD)
    description = models.TextField()
    entry_a = models.ForeignKey(
        TimetableEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    entry_b = models.ForeignKey(
        TimetableEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.conflict_type}: {self.description[:60]}"
