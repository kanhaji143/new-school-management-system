"""Attendance serializers (read payloads + write/bulk validation)."""
from rest_framework import serializers

from common.serializers import TenantRelatedField, UserSummarySerializer
from people.models import Student, Teacher
from timetable.models import TimetableEntry

from . import models


# ------------------------------------------------------------------- summaries
class StudentSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Student
        fields = ("id", "roll_number", "full_name", "email", "section")


class TeacherSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Teacher
        fields = ("id", "employee_id", "full_name", "department")


class SectionSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    school_class = serializers.CharField(source="school_class.name", read_only=True)


# ------------------------------------------------------------ student (daily)
class StudentAttendanceSerializer(serializers.ModelSerializer):
    student_detail = StudentSummarySerializer(source="student", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    marked_by_detail = UserSummarySerializer(source="marked_by", read_only=True)
    student = TenantRelatedField(queryset=Student.all_objects.all())

    class Meta:
        model = models.StudentAttendance
        fields = (
            "id", "student", "student_detail", "date", "status", "status_display",
            "remark", "marked_by_detail", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_date(self, value):
        from django.utils import timezone

        if value > timezone.localdate():
            raise serializers.ValidationError("Attendance cannot be marked for a future date.")
        return value


class StudentAttendanceRecordSerializer(serializers.Serializer):
    student = TenantRelatedField(queryset=Student.all_objects.all())
    status = serializers.ChoiceField(
        choices=models.StudentAttendance.Status.choices,
        default=models.StudentAttendance.Status.PRESENT,
    )
    remark = serializers.CharField(required=False, allow_blank=True, default="")


class DailyAttendanceBulkSerializer(serializers.Serializer):
    date = serializers.DateField()
    records = StudentAttendanceRecordSerializer(many=True)

    def validate_date(self, value):
        from django.utils import timezone

        if value > timezone.localdate():
            raise serializers.ValidationError("Attendance cannot be marked for a future date.")
        return value

    def validate_records(self, value):
        if not value:
            raise serializers.ValidationError("Provide at least one student record.")
        student_ids = [record["student"].id for record in value]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError("Duplicate students in the roster.")
        return value


# ----------------------------------------------------------- student (period)
class PeriodAttendanceSerializer(serializers.ModelSerializer):
    student_detail = StudentSummarySerializer(source="student", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    marked_by_detail = UserSummarySerializer(source="marked_by", read_only=True)
    student = TenantRelatedField(queryset=Student.all_objects.all())
    entry = TenantRelatedField(queryset=TimetableEntry.all_objects.all())

    class Meta:
        model = models.PeriodAttendance
        fields = (
            "id", "student", "student_detail", "entry", "date",
            "status", "status_display", "marked_by_detail", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class PeriodAttendanceRecordSerializer(serializers.Serializer):
    student = TenantRelatedField(queryset=Student.all_objects.all())
    status = serializers.ChoiceField(
        choices=models.PeriodAttendance.Status.choices,
        default=models.PeriodAttendance.Status.PRESENT,
    )


class PeriodAttendanceBulkSerializer(serializers.Serializer):
    date = serializers.DateField()
    entry = TenantRelatedField(queryset=TimetableEntry.all_objects.all())
    records = PeriodAttendanceRecordSerializer(many=True)

    def validate_records(self, value):
        if not value:
            raise serializers.ValidationError("Provide at least one student record.")
        return value


# -------------------------------------------------------------------- teacher
class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_detail = TeacherSummarySerializer(source="teacher", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    marked_by_detail = UserSummarySerializer(source="marked_by", read_only=True)
    teacher = TenantRelatedField(queryset=Teacher.all_objects.all())

    class Meta:
        model = models.TeacherAttendance
        fields = (
            "id", "teacher", "teacher_detail", "date", "status", "status_display",
            "check_in", "check_out", "marked_by_detail", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class TeacherAttendanceRecordSerializer(serializers.Serializer):
    teacher = TenantRelatedField(queryset=Teacher.all_objects.all())
    status = serializers.ChoiceField(
        choices=models.TeacherAttendance.Status.choices,
        default=models.TeacherAttendance.Status.PRESENT,
    )
    check_in = serializers.DateTimeField(required=False, allow_null=True)
    check_out = serializers.DateTimeField(required=False, allow_null=True)


class TeacherAttendanceBulkSerializer(serializers.Serializer):
    date = serializers.DateField()
    records = TeacherAttendanceRecordSerializer(many=True)

    def validate_records(self, value):
        if not value:
            raise serializers.ValidationError("Provide at least one teacher record.")
        teacher_ids = [record["teacher"].id for record in value]
        if len(teacher_ids) != len(set(teacher_ids)):
            raise serializers.ValidationError("Duplicate teachers in the roster.")
        return value


# --------------------------------------------------------------------- leave
class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LeaveType
        fields = ("id", "name", "paid", "max_days", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class LeaveRequestSerializer(serializers.ModelSerializer):
    teacher_detail = TeacherSummarySerializer(source="teacher", read_only=True)
    leave_type_detail = LeaveTypeSerializer(source="leave_type", read_only=True)
    approved_by_detail = UserSummarySerializer(source="approved_by", read_only=True)
    teacher = TenantRelatedField(
        queryset=Teacher.all_objects.all(), required=False
    )
    leave_type = TenantRelatedField(queryset=models.LeaveType.all_objects.all())

    class Meta:
        model = models.LeaveRequest
        fields = (
            "id", "teacher", "teacher_detail", "leave_type", "leave_type_detail",
            "start_date", "end_date", "reason", "status", "approved_by_detail",
            "approved_at", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "status", "approved_at", "created_at", "updated_at",
        )

    def validate(self, attrs):
        start = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end = attrs.get("end_date") or getattr(self.instance, "end_date", None)
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before the start date."}
            )

        if self.instance is None and "teacher" not in attrs:
            request = self.context.get("request")
            user = getattr(request, "user", None)
            if user is not None and user.has_any_role(
                "COORDINATOR", "SCHOOL_ADMIN", "SUPER_ADMIN"
            ):
                raise serializers.ValidationError(
                    {"teacher": "Teacher is required."}
                )
        return attrs
