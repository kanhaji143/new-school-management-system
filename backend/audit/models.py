"""Append-only audit log, backups and system settings."""
from django.db import models

from common.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    institution = models.ForeignKey(
        "tenancy.Institution",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        db_index=True,
    )
    actor = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    action = models.CharField(max_length=60)  # CREATE / UPDATE / DELETE / CORRECT
    model = models.CharField(max_length=120, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    # Audit rows are never soft-deleted; use an unscoped manager.
    objects = models.Manager()
    # Alias kept for parity with TenantModel (common.audit writes via all_objects).
    all_objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["institution", "-created_at"])]

    def __str__(self):
        return f"{self.action} {self.model} #{self.object_id}"


class Backup(TimeStampedModel):
    class Kind(models.TextChoices):
        FULL = "FULL", "Full"
        INCREMENTAL = "INCREMENTAL", "Incremental"

    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    institution = models.ForeignKey(
        "tenancy.Institution",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="backups",
    )
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.FULL)
    path = models.CharField(max_length=500)
    size_bytes = models.BigIntegerField(default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    checksum = models.CharField(max_length=128, blank=True)
    restore_tested_at = models.DateTimeField(null=True, blank=True)
    restore_test_passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.kind} backup {self.created_at:%Y-%m-%d %H:%M}"


class SystemSetting(TimeStampedModel):
    institution = models.ForeignKey(
        "tenancy.Institution",
        on_delete=models.CASCADE,
        related_name="system_settings",
        db_index=True,
    )
    key = models.CharField(max_length=120)
    value = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("institution", "key")

    def __str__(self):
        return self.key
