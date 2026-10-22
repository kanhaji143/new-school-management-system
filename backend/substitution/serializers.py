"""Substitution serializers."""
from rest_framework import serializers

from common.serializers import TenantRelatedField, UserSummarySerializer
from people.models import Teacher
from timetable.models import TimetableEntry

from . import models


class TeacherSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Teacher
        fields = ("id", "employee_id", "full_name", "department")


# ---------------------------------------------------------------- requests
class SubstitutionRequestSerializer(serializers.ModelSerializer):
    absent_teacher_detail = TeacherSummarySerializer(source="absent_teacher", read_only=True)
    entry_detail = serializers.SerializerMethodField()
    recommendation_count = serializers.IntegerField(
        source="recommendations.count", read_only=True
    )
    assignment = serializers.SerializerMethodField()

    class Meta:
        model = models.SubstitutionRequest
        fields = (
            "id", "absent_teacher", "absent_teacher_detail", "entry", "entry_detail",
            "date", "reason", "status", "created_by", "recommendation_count",
            "assignment", "created_at", "updated_at",
        )
        read_only_fields = ("id", "status", "created_by", "created_at", "updated_at")

    def get_entry_detail(self, obj):
        entry = obj.entry
        return {
            "id": entry.id,
            "day": entry.day,
            "period": entry.period_id,
            "period_name": getattr(entry.period, "name", None),
            "subject": {"id": entry.subject_id, "name": getattr(entry.subject, "name", None),
                        "code": getattr(entry.subject, "code", None)} if entry.subject_id else None,
            "teacher": {"id": entry.teacher_id, "full_name": getattr(entry.teacher.user, "full_name", None)}
            if entry.teacher_id else None,
            "room": entry.room,
            "timetable": entry.timetable_id,
        }

    def get_assignment(self, obj):
        assignment = getattr(obj, "assignment", None)
        if assignment is None:
            return None
        return SubstituteAssignmentSerializer(assignment, context=self.context).data


class SubstitutionRequestCreateSerializer(serializers.ModelSerializer):
    absent_teacher = TenantRelatedField(queryset=Teacher.all_objects.all())
    entry = TenantRelatedField(queryset=TimetableEntry.all_objects.all())

    class Meta:
        model = models.SubstitutionRequest
        fields = ("id", "absent_teacher", "entry", "date", "reason", "status")
        read_only_fields = ("id", "status")

    def validate_date(self, value):
        from django.utils import timezone

        if value < timezone.localdate():
            raise serializers.ValidationError("Cannot create a substitution request for a past date.")
        return value


# ---------------------------------------------------------------- recommendations
class SubstituteRecommendationSerializer(serializers.ModelSerializer):
    teacher_detail = TeacherSummarySerializer(source="teacher", read_only=True)

    class Meta:
        model = models.SubstituteRecommendation
        fields = ("id", "teacher", "teacher_detail", "score", "reasons", "rank")


# ---------------------------------------------------------------- assignment
class SubstituteAssignmentSerializer(serializers.ModelSerializer):
    substitute_teacher_detail = TeacherSummarySerializer(source="substitute_teacher", read_only=True)
    approved_by_detail = UserSummarySerializer(source="approved_by", read_only=True)
    handover = serializers.SerializerMethodField()
    outcome = serializers.SerializerMethodField()

    class Meta:
        model = models.SubstituteAssignment
        fields = (
            "id", "request", "substitute_teacher", "substitute_teacher_detail",
            "status", "approved_by_detail", "approved_at", "handover", "outcome",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "status", "approved_at", "created_at", "updated_at")

    def get_handover(self, obj):
        handover = getattr(obj, "handover", None)
        if handover is None:
            return None
        return HandoverMaterialSerializer(handover, context=self.context).data

    def get_outcome(self, obj):
        outcome = getattr(obj, "outcome", None)
        if outcome is None:
            return None
        return ClassOutcomeSerializer(outcome, context=self.context).data


# ---------------------------------------------------------------- handover
class HandoverAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HandoverAttachment
        fields = ("id", "file", "filename", "uploaded_by", "created_at")
        read_only_fields = ("id", "uploaded_by", "created_at")


class HandoverMaterialSerializer(serializers.ModelSerializer):
    prepared_by_detail = UserSummarySerializer(source="prepared_by", read_only=True)
    attachments = HandoverAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = models.HandoverMaterial
        fields = ("id", "assignment", "notes", "prepared_by_detail", "attachments",
                  "created_at", "updated_at")
        read_only_fields = ("id", "prepared_by", "created_at", "updated_at")


# ---------------------------------------------------------------- outcome
class ClassOutcomeSerializer(serializers.ModelSerializer):
    recorded_by_detail = UserSummarySerializer(source="recorded_by", read_only=True)

    class Meta:
        model = models.ClassOutcome
        fields = ("id", "assignment", "status", "notes", "recorded_by_detail", "recorded_at")
        read_only_fields = ("id", "recorded_by", "recorded_at")


# ---------------------------------------------------------------- action payloads
class AssignSubstituteSerializer(serializers.Serializer):
    substitute_teacher = TenantRelatedField(queryset=Teacher.all_objects.all(), required=False)
    recommendation = serializers.IntegerField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("substitute_teacher") and not attrs.get("recommendation"):
            raise serializers.ValidationError(
                "Provide either substitute_teacher or recommendation."
            )
        return attrs


class HandoverPayloadSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class OutcomePayloadSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=models.ClassOutcome.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class RecommendPayloadSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, default=3, min_value=1, max_value=10)
    strict_subject = serializers.BooleanField(required=False, default=True)
