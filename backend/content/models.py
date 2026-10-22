"""Notes, classwork and homework."""
from django.db import models

from common.models import TenantModel


class ContentItem(TenantModel):
    class ContentType(models.TextChoices):
        NOTE = "NOTE", "Note"
        CLASSWORK = "CLASSWORK", "Classwork"
        HOMEWORK = "HOMEWORK", "Homework"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    content_type = models.CharField(max_length=12, choices=ContentType.choices)
    subject = models.ForeignKey(
        "academics.Subject", null=True, blank=True, on_delete=models.SET_NULL, related_name="content_items"
    )
    section = models.ForeignKey(
        "academics.Section", null=True, blank=True, on_delete=models.CASCADE, related_name="content_items"
    )
    course = models.ForeignKey(
        "academics.Course", null=True, blank=True, on_delete=models.CASCADE, related_name="content_items"
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear", null=True, blank=True, on_delete=models.SET_NULL, related_name="content_items"
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="created_content"
    )

    class Meta:
        indexes = [models.Index(fields=["institution", "content_type", "status"])]

    def __str__(self):
        return self.title


class ContentAttachment(TenantModel):
    content = models.ForeignKey(ContentItem, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="content/attachments/")
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
