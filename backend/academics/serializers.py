"""Academics API serializers.

Serializers whitelist fields explicitly to prevent mass assignment (OWASP).
"""
from rest_framework import serializers

from common.serializers import TenantRelatedField

from .models import (
    AcademicYear,
    ClassSubject,
    Course,
    Enrollment,
    GradeLevel,
    SchoolClass,
    Section,
    Subject,
    Term,
)


def _validate_date_range(attrs, instance=None):
    """Ensure `end_date` is not before `start_date` on create and update."""
    start = attrs.get("start_date") or getattr(instance, "start_date", None)
    end = attrs.get("end_date") or getattr(instance, "end_date", None)
    if start and end and end < start:
        raise serializers.ValidationError(
            {"end_date": "End date must be on or after the start date."}
        )
    return attrs


class AcademicYearSerializer(serializers.ModelSerializer):
    term_count = serializers.SerializerMethodField()

    class Meta:
        model = AcademicYear
        fields = (
            "id", "name", "start_date", "end_date", "is_active",
            "term_count", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_term_count(self, obj):
        return obj.terms.count()

    def validate(self, attrs):
        return _validate_date_range(attrs, self.instance)


class TermSerializer(serializers.ModelSerializer):
    academic_year_detail = AcademicYearSerializer(source="academic_year", read_only=True)

    class Meta:
        model = Term
        fields = (
            "id", "academic_year", "academic_year_detail", "name", "term_type",
            "start_date", "end_date", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        return _validate_date_range(attrs, self.instance)

    def validate_academic_year(self, value):
        institution_id = self.context.get("institution_id")
        if institution_id is not None and value.institution_id != institution_id:
            raise serializers.ValidationError("Academic year belongs to another institution.")
        return value


class GradeLevelSerializer(serializers.ModelSerializer):
    class_count = serializers.SerializerMethodField()

    class Meta:
        model = GradeLevel
        fields = ("id", "name", "level_type", "order_index", "class_count",
                  "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_class_count(self, obj):
        return obj.classes.count()


class SchoolClassSerializer(serializers.ModelSerializer):
    grade_level_detail = GradeLevelSerializer(source="grade_level", read_only=True)
    section_count = serializers.SerializerMethodField()

    class Meta:
        model = SchoolClass
        fields = ("id", "grade_level", "grade_level_detail", "name", "capacity",
                  "section_count", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_section_count(self, obj):
        return obj.sections.count()


class SectionSerializer(serializers.ModelSerializer):
    school_class_detail = SchoolClassSerializer(source="school_class", read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ("id", "school_class", "school_class_detail", "name", "capacity",
                  "student_count", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_student_count(self, obj):
        return obj.students.count()


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "code", "name", "credits", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "code", "name", "subject_type", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class ClassSubjectSerializer(serializers.ModelSerializer):
    subject_detail = SubjectSerializer(source="subject", read_only=True)
    section_detail = SectionSerializer(source="section", read_only=True)
    course_detail = CourseSerializer(source="course", read_only=True)
    teacher_detail = serializers.SerializerMethodField()
    academic_year_detail = AcademicYearSerializer(source="academic_year", read_only=True)
    term_detail = TermSerializer(source="term", read_only=True)

    class Meta:
        model = ClassSubject
        fields = (
            "id", "subject", "subject_detail", "section", "section_detail",
            "course", "course_detail", "teacher", "teacher_detail",
            "academic_year", "academic_year_detail", "term", "term_detail",
            "planned_periods_per_week", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_teacher_detail(self, obj):
        if not obj.teacher:
            return None
        return {
            "id": obj.teacher.id,
            "employee_id": obj.teacher.employee_id,
            "full_name": obj.teacher.user.full_name,
        }


class EnrollmentSerializer(serializers.ModelSerializer):
    student_detail = serializers.SerializerMethodField()
    section_detail = SectionSerializer(source="section", read_only=True)
    course_detail = CourseSerializer(source="course", read_only=True)
    academic_year_detail = AcademicYearSerializer(source="academic_year", read_only=True)
    term_detail = TermSerializer(source="term", read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            "id", "student", "student_detail", "section", "section_detail",
            "course", "course_detail", "academic_year", "academic_year_detail",
            "term", "term_detail", "status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_student_detail(self, obj):
        return {
            "id": obj.student.id,
            "roll_number": obj.student.roll_number,
            "full_name": obj.student.user.full_name,
        }
