"""Attendance API views."""
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAuthenticatedInInstitution, IsCoordinator
from common.views import TenantModelViewSet
from people.models import Student, Teacher

from . import models, serializers, services


class AttendanceRuleMixin:
    """Render domain errors as the standard 400 envelope."""

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response(
            {"success": True, "data": response.data}, status=response.status_code
        )

    @staticmethod
    def rule_error(exc):
        return Response(
            {
                "success": False,
                "message": exc.message,
                "errors": {"fieldErrors": {}, "formErrors": [exc.message]},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _bulk_payload(self):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class StudentAttendanceViewSet(AttendanceRuleMixin, TenantModelViewSet):
    """Daily student attendance: list, mark one, bulk mark, summary."""

    queryset = models.StudentAttendance.objects.all()
    serializer_class = serializers.StudentAttendanceSerializer
    bulk_serializer_class = serializers.DailyAttendanceBulkSerializer
    filterset_fields = ("date", "student", "status", "student__section", "student__course")
    search_fields = (
        "student__roll_number",
        "student__user__first_name",
        "student__user__last_name",
    )
    ordering_fields = ("date", "created_at")

    def get_permissions(self):
        if self.action in ("list", "retrieve", "summary", "mine"):
            return [IsAuthenticatedInInstitution()]
        if self.action == "bulk":
            return [IsCoordinator()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.has_any_role("STUDENT"):
            queryset = queryset.filter(student__user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "bulk":
            return self.bulk_serializer_class
        return self.serializer_class

    @action(detail=False, methods=["post"])
    def bulk(self, request):
        """Mark (or correct) a whole class roster in one request."""
        payload = self._bulk_payload()
        try:
            result = services.mark_daily_attendance(
                request.institution_id,
                payload["date"],
                payload["records"],
                marked_by=request.user,
            )
        except services.AttendanceError as exc:
            return self.rule_error(exc)
        return Response(
            {"success": True, "message": "Attendance saved.", "data": result}
        )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Daily attendance counts for a date (and optional section)."""
        raw_date = request.query_params.get("date")
        date = parse_date(raw_date) if raw_date else timezone.localdate()
        if date is None:
            return Response(
                {"success": False, "message": "Invalid date format (use YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        student_id = None
        if request.user.has_any_role("STUDENT"):
            student = Student.objects.filter(user=request.user).first()
            if student is None:
                return Response({"success": False, "message": "Student profile not found."}, status=404)
            student_id = student.id
            data = services.daily_summary(
                request.institution_id, date, student_id=student_id
            )
            return Response({"success": True, "data": data})

        section = request.query_params.get("section")
        course = request.query_params.get("course")
        if section and course:
            return Response(
                {"success": False, "message": "Choose either a section or a course, not both."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            section_id = int(section) if section else None
            course_id = int(course) if course else None
        except ValueError:
            return Response(
                {"success": False, "message": "Section and course filters must be numeric IDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = services.daily_summary(
            request.institution_id,
            date,
            section_id=section_id,
            course_id=course_id,
        )
        return Response({"success": True, "data": data})

    @action(detail=False, methods=["get"])
    def mine(self, request):
        if not request.user.has_any_role("STUDENT"):
            return Response({"success": False, "message": "Student account required."}, status=403)
        queryset = self.filter_queryset(self.get_queryset()).order_by("-date")
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response({"success": True, "data": serializer.data})


class PeriodAttendanceViewSet(AttendanceRuleMixin, TenantModelViewSet):
    """Per-period attendance tied to a timetable entry."""

    queryset = models.PeriodAttendance.objects.all()
    serializer_class = serializers.PeriodAttendanceSerializer
    bulk_serializer_class = serializers.PeriodAttendanceBulkSerializer
    filterset_fields = ("date", "entry", "student", "status")
    search_fields = ("student__roll_number",)
    ordering_fields = ("date", "created_at")

    def get_serializer_class(self):
        if self.action == "bulk":
            return self.bulk_serializer_class
        return self.serializer_class

    @action(detail=False, methods=["post"])
    def bulk(self, request):
        payload = self._bulk_payload()
        try:
            result = services.mark_period_attendance(
                request.institution_id,
                payload["date"],
                payload["entry"],
                payload["records"],
                marked_by=request.user,
            )
        except services.AttendanceError as exc:
            return self.rule_error(exc)
        return Response(
            {"success": True, "message": "Period attendance saved.", "data": result}
        )


class TeacherAttendanceViewSet(AttendanceRuleMixin, TenantModelViewSet):
    """Daily staff attendance."""

    queryset = models.TeacherAttendance.objects.all()
    serializer_class = serializers.TeacherAttendanceSerializer
    bulk_serializer_class = serializers.TeacherAttendanceBulkSerializer
    filterset_fields = ("date", "teacher", "status")
    search_fields = ("teacher__employee_id", "teacher__user__first_name")
    ordering_fields = ("date", "created_at")

    def get_serializer_class(self):
        if self.action == "bulk":
            return self.bulk_serializer_class
        return self.serializer_class

    @action(detail=False, methods=["post"])
    def bulk(self, request):
        payload = self._bulk_payload()
        try:
            result = services.mark_teacher_attendance(
                request.institution_id,
                payload["date"],
                payload["records"],
                marked_by=request.user,
            )
        except services.AttendanceError as exc:
            return self.rule_error(exc)
        return Response(
            {"success": True, "message": "Staff attendance saved.", "data": result}
        )


class LeaveTypeViewSet(AttendanceRuleMixin, TenantModelViewSet):
    queryset = models.LeaveType.objects.all()
    serializer_class = serializers.LeaveTypeSerializer
    search_fields = ("name",)


class LeaveRequestViewSet(AttendanceRuleMixin, TenantModelViewSet):
    """Teacher leave requests with an approval workflow."""

    queryset = models.LeaveRequest.objects.all()
    serializer_class = serializers.LeaveRequestSerializer
    filterset_fields = ("status", "teacher", "leave_type")
    search_fields = ("teacher__employee_id", "reason")

    def get_permissions(self):
        # Any member may file a leave request; only coordinators may approve,
        # reject or edit one afterwards.
        if self.action in ("list", "retrieve", "create"):
            return [IsAuthenticatedInInstitution()]
        if self.action in ("approve", "reject"):
            return [IsCoordinator()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not user.has_any_role(
            "COORDINATOR", "SCHOOL_ADMIN", "SUPER_ADMIN"
        ):
            # Teachers only see their own requests.
            queryset = queryset.filter(teacher__user=user)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.has_any_role("COORDINATOR", "SCHOOL_ADMIN", "SUPER_ADMIN"):
            serializer.save(institution_id=self.request.institution_id)
            return
        teacher = Teacher.objects.filter(
            institution_id=self.request.institution_id, user=user
        ).first()
        if teacher is None:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only staff members can file a leave request.")
        serializer.save(
            institution_id=self.request.institution_id, teacher=teacher
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        try:
            services.approve_leave(leave_request, approver=request.user)
        except services.AttendanceError as exc:
            return self.rule_error(exc)
        data = self.serializer_class(
            leave_request, context=self.get_serializer_context()
        ).data
        return Response(
            {"success": True, "message": "Leave approved.", "data": data}
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        try:
            services.reject_leave(
                leave_request,
                approver=request.user,
                reason=request.data.get("reason", ""),
            )
        except services.AttendanceError as exc:
            return self.rule_error(exc)
        data = self.serializer_class(
            leave_request, context=self.get_serializer_context()
        ).data
        return Response(
            {"success": True, "message": "Leave rejected.", "data": data}
        )
