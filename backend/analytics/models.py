"""Analytics snapshots (computed by Celery jobs, read by dashboards/reports)."""
from django.db import models

from common.models import TenantModel


class StudentProgressSnapshot(TenantModel):
    student = models.ForeignKey(
        "people.Student", on_delete=models.CASCADE, related_name="progress_snapshots"
    )
    term = models.ForeignKey("academics.Term", on_delete=models.CASCADE, related_name="progress_snapshots")
    metrics = models.JSONField(default=dict, blank=True)  # attendance %, avg marks, GPA, rank
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("institution", "student", "term")


class TeacherWorkloadSnapshot(TenantModel):
    teacher = models.ForeignKey(
        "people.Teacher", on_delete=models.CASCADE, related_name="workload_snapshots"
    )
    month = models.DateField(help_text="First day of the month")
    periods_taught = models.PositiveIntegerField(default=0)
    substitutions_covered = models.PositiveIntegerField(default=0)
    leave_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    metrics = models.JSONField(default=dict, blank=True)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("institution", "teacher", "month")
