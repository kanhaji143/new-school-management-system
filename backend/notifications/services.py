"""Notifications services: enqueue + retry."""
from django.utils import timezone

from . import models


def enqueue(institution_id, event, channel, recipient, subject="", body="", payload=None, template=None):
    """Create an outbox row. Returns the Notification or None if no active template."""
    if template is None:
        template = models.NotificationTemplate.all_objects.filter(
            institution_id=institution_id, event=event, channel=channel, is_active=True
        ).first()
    if template is None and not body:
        return None

    notification = models.Notification.all_objects.create(
        institution_id=institution_id,
        recipient=recipient,
        template=template,
        channel=channel,
        subject=subject or (template.subject if template else ""),
        body=body or (template.body if template else ""),
        payload=payload or {},
        status=models.Notification.Status.PENDING,
    )
    return notification


def retry(notification, provider="manual"):
    if notification.status not in (models.Notification.Status.FAILED, models.Notification.Status.PENDING):
        return notification
    notification.status = models.Notification.Status.PENDING
    notification.attempts += 1
    notification.save(update_fields=["status", "attempts", "updated_at"])
    models.NotificationDeliveryLog.all_objects.create(
        institution_id=notification.institution_id,
        notification=notification,
        provider=provider,
        attempt=notification.attempts,
        status=models.Notification.Status.PENDING,
        provider_response="queued for retry",
    )
    return notification


def mark_sent(notification, provider="manual", response=""):
    notification.status = models.Notification.Status.SENT
    notification.sent_at = timezone.now()
    notification.attempts += 1
    notification.save(update_fields=["status", "sent_at", "attempts", "updated_at"])
    models.NotificationDeliveryLog.all_objects.create(
        institution_id=notification.institution_id,
        notification=notification,
        provider=provider,
        attempt=notification.attempts,
        status=models.Notification.Status.SENT,
        provider_response=response,
    )
    return notification


def mark_failed(notification, provider="manual", error=""):
    notification.status = models.Notification.Status.FAILED
    notification.attempts += 1
    notification.save(update_fields=["status", "attempts", "updated_at"])
    models.NotificationDeliveryLog.all_objects.create(
        institution_id=notification.institution_id,
        notification=notification,
        provider=provider,
        attempt=notification.attempts,
        status=models.Notification.Status.FAILED,
        error=error,
    )
    return notification
