"""Coordinator command center: dashboard widgets and tasks."""
from django.db import models

from common.models import TenantModel


class CommandCenterWidget(TenantModel):
    key = models.CharField(max_length=60)
    label = models.CharField(max_length=120)
    config = models.JSONField(default=dict, blank=True)
    order_index = models.PositiveIntegerField(default=0)
    visible_roles = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("institution", "key")
        ordering = ["order_index"]

    def __str__(self):
        return self.label


class CoordinatorTask(TenantModel):
    class TaskType(models.TextChoices):
        SUBSTITUTION = "SUBSTITUTION", "Substitution"
        TIMETABLE_CHANGE = "TIMETABLE_CHANGE", "Timetable change"
        ATTENDANCE_FIX = "ATTENDANCE_FIX", "Attendance correction"
        MARKS_FIX = "MARKS_FIX", "Marks correction"
        AI_REVIEW = "AI_REVIEW", "AI content review"
        GENERAL = "GENERAL", "General"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        DONE = "DONE", "Done"

    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.GENERAL)
    title = models.CharField(max_length=255)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=14, choices=Status.choices, default=Status.OPEN)
    assignee = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_tasks"
    )
    created_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        indexes = [models.Index(fields=["institution", "status"])]
