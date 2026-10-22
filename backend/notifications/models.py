"""Templates, outbox, delivery logs and provider configuration."""
from django.db import models

from common.models import TenantModel


class NotificationTemplate(TenantModel):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        PUSH = "PUSH", "Push"

    event = models.CharField(max_length=80)  # e.g. teacher.absent
    channel = models.CharField(max_length=10, choices=Channel.choices)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("institution", "event", "channel")

    def __str__(self):
        return f"{self.event} [{self.channel}]"


class Notification(TenantModel):
    """The outbox row. Sent asynchronously by a Celery task."""

    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        PUSH = "PUSH", "Push"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    recipient = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="notifications"
    )
    template = models.ForeignKey(
        NotificationTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    channel = models.CharField(max_length=10, choices=Channel.choices)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["institution", "status"])]


class NotificationDeliveryLog(TenantModel):
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="delivery_logs"
    )
    provider = models.CharField(max_length=60)
    attempt = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12, choices=Notification.Status.choices)
    provider_response = models.TextField(blank=True)
    error = models.TextField(blank=True)


class ProviderConfig(TenantModel):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    channel = models.CharField(max_length=10, choices=Channel.choices)
    provider = models.CharField(max_length=60)  # twilio / msg91 / sendgrid ...
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["priority"]
