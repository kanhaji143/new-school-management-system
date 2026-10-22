"""AI serializers."""
from rest_framework import serializers

from common.serializers import TenantRelatedField, UserSummarySerializer

from . import models


class AIJobSerializer(serializers.ModelSerializer):
    created_by_detail = UserSummarySerializer(source="created_by", read_only=True)

    class Meta:
        model = models.AIJob
        fields = ("id", "job_type", "status", "input", "output", "error", "created_by_detail", "created_at", "updated_at")
        read_only_fields = ("id", "status", "output", "error", "created_at", "updated_at")


class GeneratedContentSerializer(serializers.ModelSerializer):
    reviewed_by_detail = UserSummarySerializer(source="reviewed_by", read_only=True)
    job = TenantRelatedField(queryset=models.AIJob.all_objects.all(), required=False, allow_null=True)

    class Meta:
        model = models.GeneratedContent
        fields = ("id", "job", "content_type", "title", "body", "status", "reviewed_by_detail", "reviewed_at", "review_note", "created_at", "updated_at")
        read_only_fields = ("id", "reviewed_by", "reviewed_at", "created_at", "updated_at")


class ReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    note = serializers.CharField(required=False, allow_blank=True, default="")
