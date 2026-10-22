"""Institution (tenant) and its configuration."""
from django.db import models

from common.models import TimeStampedModel


class Institution(TimeStampedModel):
    class InstitutionType(models.TextChoices):
        SCHOOL = "SCHOOL", "School"
        COLLEGE = "COLLEGE", "College"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True)
    type = models.CharField(
        max_length=10, choices=InstitutionType.choices, default=InstitutionType.SCHOOL
    )
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="institutions/logos/", null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Institution"
        verbose_name_plural = "Institutions"
        ordering = ["name"]

    def __str__(self):
        return self.name


class InstitutionSettings(TimeStampedModel):
    """Feature flags and academic defaults for one institution."""

    institution = models.OneToOneField(
        Institution, on_delete=models.CASCADE, related_name="settings"
    )
    timezone = models.CharField(max_length=60, default="Asia/Kolkata")
    date_format = models.CharField(max_length=30, default="d-m-Y")
    features = models.JSONField(
        default=dict,
        help_text="Feature flags, e.g. {'ai_content': true, 'parent_portal': true}",
    )
    academic_defaults = models.JSONField(default=dict, blank=True)
    notification_defaults = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Settings for {self.institution}"


class InstitutionDomain(TimeStampedModel):
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="domains"
    )
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.domain
