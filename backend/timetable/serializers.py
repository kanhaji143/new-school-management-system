"""Timetable API serializers."""
from rest_framework import serializers

from common.serializers import TenantRelatedField, UserSummarySerializer

from .models import (
    PeriodTemplate,
    Timetable,
    TimetableChangeRequest,
    TimetableEntry,
)


class PeriodTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodTemplate
        fields = ("id", "name", "day", "start_time", "end_time",
                  "order_index", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end = attrs.get("end_time") or getattr(self.instance, "end_time", None)
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_time": "End time must be after the start time."}
            )
        return attrs


class TeacherSummarySerializer(serializers.ModelSerializer):
    """Small teacher payload used inside timetable entries."""

    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        from people.models import Teacher  # local import avoids a circular app import

        model = Teacher
        fields = ("id", "employee_id", "full_name", "department")


class SubjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        from academics.models import Subject  # local import keeps the migration graph clean

        model = Subject
        fields = ("id", "name", "code")


class SectionSummarySerializer(serializers.ModelSerializer):
    school_class_name = serializers.CharField(
        source="school_class_class_times.name", read_only=True
    )

    class Meta:
        from academics.models import Section  # local import

        model = Section
        fields = ("id", "name")


class CourseSummarySerializer(serializers.ModelSerializer):
    class Meta:
        from academics.models import Course  # local import

        model = Course
        fields = ("id", "code", "name")


class TimetableEntrySummarySerializer(serializers.ModelSerializer):
    """Compact entry used inside the weekly grid response."""

    period_name = serializers.CharField(source="period.name", read_only=True)
    period_start = serializers.CharField(source="period.start_time", read_only=True)
    period_end = serializers.CharField(source="period.end_time", read_only=True)
    subject = SubjectSummarySerializer(read_only=True)
    teacher = TeacherSummarySerializer(read_only=True)

    class Meta:
        model = TimetableEntry
        fields = (
            "id", "day", "period", "period_name", "period_start", "period_end",
            "subject", "teacher", "room", "status",
        )


class TimetableEntrySerializer(serializers.ModelSerializer):
    period_detail = PeriodTemplateSerializer(source="period", read_only=True)
    subject_detail = serializers.SerializerMethodField()
    teacher_detail = serializers.SerializerMethodField()
    timetable_label = serializers.CharField(source="timetable.__str__", read_only=True)

    class Meta:
        model = TimetableEntry
        fields = (
            "id", "timetable", "timetable_label", "day", "period", "period_detail",
            "subject", "subject_detail", "teacher", "teacher_detail",
            "room", "status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_subject_detail(self, obj):
        return {"id": obj.subject_id, "name": obj.subject.name, "code": obj.subject.code}

    def get_teacher_detail(self, obj):
        if not obj.teacher:
            return None
        return {
            "id": obj.teacher_id,
            "employee_id": obj.teacher.employee_id,
            "full_name": obj.teacher.user.full_name,
        }


class TimetableWriteSerializer(serializers.ModelSerializer):
    """Create a draft timetable (version is derived automatically)."""

    class Meta:
        model = Timetable
        fields = ("id", "section", "course", "academic_year", "term")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if not attrs.get("section") and not attrs.get("course"):
            raise serializers.ValidationError(
                {"section": "Provide a section (school) or a course (college)."}
            )
        return attrs

    def create(self, validated_data):
        from . import services

        return services.create_draft(validated_data)


class TimetableSerializer(serializers.ModelSerializer):
    section_detail = serializers.SerializerMethodField()
    course_detail = serializers.SerializerMethodField()
    academic_year_detail = serializers.SerializerMethodField()
    entry_count = serializers.SerializerMethodField()
    published_by_detail = UserSummarySerializer(source="published_by", read_only=True)

    class Meta:
        model = Timetable
        fields = (
            "id", "section", "section_detail", "course", "course_detail",
            "academic_year", "academic_year_detail",
            "term", "version", "status", "entry_count",
            "published_at", "published_by_detail", "created_at", "updated_at",
        )
        read_only_fields = ("id", "version", "status", "published_at",
                            "created_at", "updated_at")

    def get_section_detail(self, obj):
        if not obj.section:
            return None
        return {
            "id": obj.section.id,
            "name": obj.section.name,
            "school_class": obj.section.school_class.name,
        }

    def get_course_detail(self, obj):
        if not obj.course:
            return None
        return {"id": obj.course_id, "code": obj.course.code, "name": obj.course.name}

    def get_academic_year_detail(self, obj):
        return {"id": obj.academic_year_id, "name": obj.academic_year.name}

    def get_entry_count(self, obj):
        return obj.entries.exclude(status=TimetableEntry.Status.CANCELLED).count()


class TimetableChangeRequestSerializer(serializers.ModelSerializer):
    entry_detail = TimetableEntrySerializer(source="entry", read_only=True)
    requested_by_detail = UserSummarySerializer(source="requested_by", read_only=True)
    reviewed_by_detail = UserSummarySerializer(source="approved_by", read_only=True)
    proposed_teacher_detail = serializers.SerializerMethodField()

    class Meta:
        model = TimetableChangeRequest
        fields = (
            "id", "entry", "entry_detail",
            "proposed_teacher", "proposed_teacher_detail",
            "proposed_room", "reason", "status", "requested_by_detail",
            "reviewed_by_detail", "approved_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "status", "approved_at", "created_at", "updated_at")

    def get_proposed_teacher_detail(self, obj):
        if not obj.proposed_teacher:
            return None
        return {"id": obj.proposed_teacher_id,
                "full_name": obj.proposed_teacher.user.full_name}


class ChangeRequestWriteSerializer(serializers.ModelSerializer):
    """Payload for proposing a change to a published entry."""

    class Meta:
        model = TimetableChangeRequest
        fields = ("entry", "proposed_teacher", "proposed_room", "reason")
