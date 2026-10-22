"""Attendance (student daily + period-wise) and staff attendance + leave."""
from django.db import models

from common.models import TenantModel


class StudentAttendance(TenantModel):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    student = models.ForeignKey(
        "people.Student", on_delete=models.CASCADE, related_name="daily_attendance"
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    remark = models.CharField(max_length=255, blank=True)
    marked_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        unique_together = ("institution", "student", "date")
        indexes = [models.Index(fields=["institution", "date"])]

    def __str__(self):
        return f"{self.student} {self.date} {self.status}"


class PeriodAttendance(TenantModel):
    """Per-period attendance linked to a timetable entry."""

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"

    student = models.ForeignKey(
        "people.Student", on_delete=models.CASCADE, related_name="period_attendance"
    )
    entry = models.ForeignKey(
        "timetable.TimetableEntry", on_delete=models.CASCADE, related_name="attendance"
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    marked_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        unique_together = ("institution", "student", "entry", "date")


class TeacherAttendance(TenantModel):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        HALF_DAY = "HALF_DAY", "Half day"
        ON_DUTY = "ON_DUTY", "On duty"

    teacher = models.ForeignKey(
        "people.Teacher", on_delete=models.CASCADE, related_name="attendance"
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    marked_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        unique_together = ("institution", "teacher", "date")
        indexes = [models.Index(fields=["institution", "date"])]


class LeaveType(TenantModel):
    name = models.CharField(max_length=80)
    paid = models.BooleanField(default=False)
    max_days = models.PositiveIntegerField(default=0, help_text="0 = unlimited")

    def __str__(self):
        return self.name


class LeaveRequest(TenantModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    teacher = models.ForeignKey(
        "people.Teacher", on_delete=models.CASCADE, related_name="leave_requests"
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.teacher} {self.start_date}→{self.end_date} ({self.status})"
