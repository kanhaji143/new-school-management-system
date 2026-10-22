"""Notifications serializers."""
from rest_framework import serializers

from common.serializers import TenantRelatedField, UserSummarySerializer
from users.models import User

from . import models


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NotificationTemplate
        fields = ("id", "event", "channel", "subject", "body", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class NotificationDeliveryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NotificationDeliveryLog
        fields = ("id", "provider", "attempt", "status", "provider_response", "error", "created_at")
        read_only_fields = ("id", "created_at")


class NotificationSerializer(serializers.ModelSerializer):
    recipient_detail = UserSummarySerializer(source="recipient", read_only=True)
    template_detail = NotificationTemplateSerializer(source="template", read_only=True)
    delivery_logs = NotificationDeliveryLogSerializer(many=True, read_only=True)
    recipient = TenantRelatedField(queryset=User.objects.all())
    template = TenantRelatedField(queryset=models.NotificationTemplate.all_objects.all(), required=False, allow_null=True)

    class Meta:
        model = models.Notification
        fields = (
            "id", "recipient", "recipient_detail", "template", "template_detail", "channel",
            "subject", "body", "payload", "status", "attempts", "sent_at", "delivery_logs",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "status", "attempts", "sent_at", "created_at", "updated_at")


class ProviderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProviderConfig
        fields = ("id", "channel", "provider", "config", "is_active", "priority", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
