"""
AI jobs and generated content.

Every piece of AI-generated educational content MUST pass a human review
(`PENDING_REVIEW`) before it can be published (`APPROVED`).
"""
from django.db import models

from common.models import TenantModel


class AIJob(TenantModel):
    class JobType(models.TextChoices):
        QUESTION_GEN = "QUESTION_GEN", "Generate questions"
        MATERIAL_GEN = "MATERIAL_GEN", "Generate learning material"
        SUMMARIZE = "SUMMARIZE", "Summarize content"
        MARKING_ASSIST = "MARKING_ASSIST", "Assess/mark"

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    job_type = models.CharField(max_length=20, choices=JobType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    input = models.JSONField(default=dict, blank=True)
    output = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )


class GeneratedContent(TenantModel):
    class ContentType(models.TextChoices):
        QUESTION = "QUESTION", "Question"
        MATERIAL = "MATERIAL", "Learning material"
        SUMMARY = "SUMMARY", "Summary"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    job = models.ForeignKey(
        AIJob, null=True, blank=True, on_delete=models.SET_NULL, related_name="generated_content"
    )
    content_type = models.CharField(max_length=12, choices=ContentType.choices)
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING_REVIEW)
    reviewed_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    def approve(self, user, note=""):
        from django.utils import timezone

        self.status = self.Status.APPROVED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_note = note
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])

    def reject(self, user, note=""):
        from django.utils import timezone

        self.status = self.Status.REJECTED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_note = note
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])
