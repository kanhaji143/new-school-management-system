"""Coordinator command-center serializers."""
from rest_framework import serializers

from common.serializers import UserSummarySerializer
from users.models import User

from . import models


class CoordinatorPendingSerializer(serializers.Serializer):
    substitutions = serializers.IntegerField()
    timetable_changes = serializers.IntegerField()
    leave_requests = serializers.IntegerField()
    ai_reviews = serializers.IntegerField()
    grading = serializers.IntegerField()
    tasks = serializers.IntegerField()


class CoordinatorDashboardDataSerializer(serializers.Serializer):
    pending = CoordinatorPendingSerializer()
    total_pending = serializers.IntegerField()
    widgets = serializers.ListField(child=serializers.DictField())


class CoordinatorDashboardSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = CoordinatorDashboardDataSerializer()


class CommandCenterWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CommandCenterWidget
        fields = ("id", "key", "label", "config", "order_index", "visible_roles", "is_active")
        read_only_fields = ("id",)


class CoordinatorTaskSerializer(serializers.ModelSerializer):
    assignee_detail = UserSummarySerializer(source="assignee", read_only=True)
    created_by_detail = UserSummarySerializer(source="created_by", read_only=True)
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = models.CoordinatorTask
        fields = (
            "id", "task_type", "title", "payload", "status", "assignee",
            "assignee_detail", "created_by_detail", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate_assignee(self, user):
        institution_id = self.context.get("institution_id")
        if user and user.institution_id != institution_id:
            raise serializers.ValidationError("Assignee must belong to this institution.")
        return user

    def validate_status(self, value):
        if self.instance and self.instance.status == models.CoordinatorTask.Status.DONE and value != self.instance.status:
            raise serializers.ValidationError("Completed tasks cannot be reopened.")
        return value
