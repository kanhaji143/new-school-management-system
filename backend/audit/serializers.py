"""Audit and operations serializers."""
from rest_framework import serializers

from common.serializers import UserSummarySerializer

from . import models


class AuditLogSerializer(serializers.ModelSerializer):
    actor_detail = UserSummarySerializer(source="actor", read_only=True)

    class Meta:
        model = models.AuditLog
        fields = (
            "id", "actor_detail", "action", "model", "object_id", "object_repr",
            "before", "after", "ip_address", "user_agent", "created_at",
        )
        read_only_fields = fields


class BackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Backup
        fields = (
            "id", "kind", "size_bytes", "status", "checksum",
            "restore_tested_at", "restore_test_passed", "created_at",
        )
        read_only_fields = fields


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SystemSetting
        fields = ("id", "key", "value", "description", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_key(self, value):
        return value.strip()
