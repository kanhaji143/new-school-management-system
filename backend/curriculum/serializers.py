"""Curriculum serializers."""
from rest_framework import serializers

from common.serializers import TenantRelatedField, UserSummarySerializer
from academics.models import AcademicYear, Section, Subject, Term
from people.models import Teacher
from timetable.models import TimetableEntry

from . import models


class SubjectMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "code", "name")


class SectionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("id", "name")


class AcademicYearMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ("id", "name")


class TermMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ("id", "name")


class TeacherMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Teacher
        fields = ("id", "employee_id", "full_name")


# ---------------------------------------------------------------- syllabus
class SyllabusSerializer(serializers.ModelSerializer):
    subject_detail = SubjectMiniSerializer(source="subject", read_only=True)
    section_detail = SectionMiniSerializer(source="section", read_only=True)
    academic_year_detail = AcademicYearMiniSerializer(source="academic_year", read_only=True)
    term_detail = TermMiniSerializer(source="term", read_only=True)
    chapter_count = serializers.IntegerField(source="chapters.count", read_only=True)
    subject = TenantRelatedField(queryset=Subject.all_objects.all())
    section = TenantRelatedField(queryset=Section.all_objects.all(), required=False, allow_null=True)
    academic_year = TenantRelatedField(queryset=AcademicYear.all_objects.all())
    term = TenantRelatedField(queryset=Term.all_objects.all(), required=False, allow_null=True)

    class Meta:
        model = models.Syllabus
        fields = (
            "id", "title", "subject", "subject_detail", "section", "section_detail",
            "course", "academic_year", "academic_year_detail", "term", "term_detail",
            "chapter_count", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


# ---------------------------------------------------------------- chapter
class ChapterSerializer(serializers.ModelSerializer):
    lesson_plan_count = serializers.IntegerField(source="lesson_plans.count", read_only=True)
    completion_status = serializers.SerializerMethodField()

    class Meta:
        model = models.Chapter
        fields = (
            "id", "syllabus", "title", "order_index", "planned_hours",
            "lesson_plan_count", "completion_status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_completion_status(self, obj):
        completion = getattr(obj, "completion", None)
        if completion is None:
            return "PLANNED"
        return completion.status


class ChapterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Chapter
        fields = ("title", "order_index", "planned_hours")


# ---------------------------------------------------------------- lesson plan
class LessonPlanSerializer(serializers.ModelSerializer):
    created_by_detail = UserSummarySerializer(source="created_by", read_only=True)
    chapter = TenantRelatedField(queryset=models.Chapter.all_objects.all(), required=False)

    class Meta:
        model = models.LessonPlan
        fields = (
            "id", "chapter", "title", "objectives", "content", "duration_minutes",
            "resources", "created_by", "created_by_detail", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


# ---------------------------------------------------------------- session log
class ClassSessionLogSerializer(serializers.ModelSerializer):
    subject_detail = SubjectMiniSerializer(source="subject", read_only=True)
    section_detail = SectionMiniSerializer(source="section", read_only=True)
    chapter_detail = serializers.SerializerMethodField()
    teacher_detail = TeacherMiniSerializer(source="teacher", read_only=True)
    subject = TenantRelatedField(queryset=Subject.all_objects.all())
    section = TenantRelatedField(queryset=Section.all_objects.all(), required=False, allow_null=True)
    chapter = TenantRelatedField(queryset=models.Chapter.all_objects.all(), required=False, allow_null=True)
    teacher = TenantRelatedField(queryset=Teacher.all_objects.all(), required=False, allow_null=True)
    entry = TenantRelatedField(queryset=TimetableEntry.all_objects.all(), required=False, allow_null=True)

    class Meta:
        model = models.ClassSessionLog
        fields = (
            "id", "entry", "subject", "subject_detail", "section", "section_detail",
            "chapter", "chapter_detail", "topic", "date", "status", "teacher",
            "teacher_detail", "notes", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_chapter_detail(self, obj):
        if obj.chapter is None:
            return None
        return {"id": obj.chapter.id, "title": obj.chapter.title}


# ---------------------------------------------------------------- completion
class LessonCompletionSerializer(serializers.ModelSerializer):
    verified_by_detail = UserSummarySerializer(source="verified_by", read_only=True)

    class Meta:
        model = models.LessonCompletion
        fields = ("id", "chapter", "completed_date", "status", "verified_by_detail")
        read_only_fields = ("id", "verified_by")


class CompleteChapterSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=models.LessonCompletion.Status.choices, default=models.LessonCompletion.Status.COMPLETED
    )
    completed_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
