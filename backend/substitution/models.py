"""
Substitution workflow:
request → recommendations → assignment (approval) → handover → outcome.
"""
from django.db import models

from common.models import TenantModel


class SubstitutionRequest(TenantModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        PROPOSED = "PROPOSED", "Proposed"
        APPROVED = "APPROVED", "Approved"
        COMPLETED = "COMPLETED", "Completed"
        UNRESOLVED = "UNRESOLVED", "Unresolved"
        CANCELLED = "CANCELLED", "Cancelled"

    absent_teacher = models.ForeignKey(
        "people.Teacher", on_delete=models.CASCADE, related_name="absence_requests"
    )
    entry = models.ForeignKey(
        "timetable.TimetableEntry", on_delete=models.CASCADE, related_name="substitution_requests"
    )
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        unique_together = ("institution", "entry", "date")
        indexes = [models.Index(fields=["institution", "date"])]

    def __str__(self):
        return f"Substitution for {self.absent_teacher} on {self.date}"


class SubstituteRecommendation(TenantModel):
    """A scored, ranked suggestion. Never auto-assigned."""

    request = models.ForeignKey(
        SubstitutionRequest, on_delete=models.CASCADE, related_name="recommendations"
    )
    teacher = models.ForeignKey(
        "people.Teacher", on_delete=models.CASCADE, related_name="substitute_recommendations"
    )
    score = models.FloatField(default=0)
    reasons = models.JSONField(default=dict, blank=True)
    rank = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("request", "teacher")
        ordering = ["rank"]

    def __str__(self):
        return f"#{self.rank} {self.teacher} (score {self.score})"


class SubstituteAssignment(TenantModel):
    class Status(models.TextChoices):
        PROPOSED = "PROPOSED", "Proposed"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    request = models.OneToOneField(
        SubstitutionRequest, on_delete=models.CASCADE, related_name="assignment"
    )
    substitute_teacher = models.ForeignKey(
        "people.Teacher", on_delete=models.CASCADE, related_name="substitute_assignments"
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PROPOSED)
    approved_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.substitute_teacher} → {self.request} ({self.status})"


class HandoverMaterial(TenantModel):
    assignment = models.OneToOneField(
        SubstituteAssignment, on_delete=models.CASCADE, related_name="handover"
    )
    notes = models.TextField(blank=True)
    prepared_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    def __str__(self):
        return f"Handover for {self.assignment}"


class HandoverAttachment(TenantModel):
    material = models.ForeignKey(
        HandoverMaterial, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="substitution/handover/")
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )


class ClassOutcome(TenantModel):
    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        PARTIAL = "PARTIAL", "Partial"
        SKIPPED = "SKIPPED", "Skipped"

    assignment = models.OneToOneField(
        SubstituteAssignment, on_delete=models.CASCADE, related_name="outcome"
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Outcome: {self.status}"
