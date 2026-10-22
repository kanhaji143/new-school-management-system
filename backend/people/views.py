"""People API views (students, teachers, guardians)."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from common.views import TenantModelViewSet

from . import models, serializers, services


class CreateWithUserViewSet(TenantModelViewSet):
    """Viewset whose `create` payload also provisions the login account.

    The write serializer is a plain `Serializer` (it has no model), so the
    response is rendered through the matching read serializer.
    """

    create_serializer_class = None
    read_serializer_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return self.create_serializer_class
        return self.read_serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        data = self.read_serializer_class(
            instance, context=self.get_serializer_context()
        ).data
        return Response(
            {"success": True, "data": data}, status=status.HTTP_201_CREATED
        )


class StudentViewSet(CreateWithUserViewSet):
    queryset = models.Student.objects.all()
    create_serializer_class = serializers.StudentCreateSerializer
    read_serializer_class = serializers.StudentSerializer
    filterset_fields = ("status", "section", "course")
    search_fields = (
        "roll_number", "admission_number",
        "user__first_name", "user__last_name", "user__email",
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.has_any_role("STUDENT"):
            queryset = queryset.filter(user=self.request.user)
        return queryset

    @action(detail=True, methods=["get"])
    def guardians(self, request, pk=None):
        """Guardians linked to this student."""
        student = self.get_object()
        links = models.StudentGuardian.all_objects.filter(student=student)
        serializer = serializers.StudentGuardianSerializer(
            links, many=True, context=self.get_serializer_context()
        )
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["post"])
    def link_guardian(self, request, pk=None):
        """Attach a guardian to this student."""
        student = self.get_object()
        guardian = models.Guardian.all_objects.filter(
            institution_id=request.institution_id,
            id=request.data.get("guardian"),
        ).first()
        if guardian is None:
            return Response(
                {"success": False, "message": "Guardian not found in this institution."},
                status=status.HTTP_404_NOT_FOUND,
            )
        link = services.link_guardian(
            student, guardian,
            is_primary=bool(request.data.get("is_primary", False)),
            is_emergency_contact=bool(request.data.get("is_emergency_contact", False)),
        )
        data = serializers.StudentGuardianSerializer(
            link, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def unlink_guardian(self, request, pk=None):
        """Remove a guardian's access to this student."""
        student = self.get_object()
        guardian = models.Guardian.all_objects.filter(
            institution_id=request.institution_id,
            id=request.data.get("guardian"),
        ).first()
        if guardian is None:
            return Response(
                {"success": False, "message": "Guardian not found in this institution."},
                status=status.HTTP_404_NOT_FOUND,
            )
        services.unlink_guardian(student, guardian)
        return Response({"success": True, "message": "Guardian unlinked."})


class TeacherViewSet(CreateWithUserViewSet):
    queryset = models.Teacher.objects.all()
    create_serializer_class = serializers.TeacherCreateSerializer
    read_serializer_class = serializers.TeacherSerializer
    filterset_fields = ("status", "department")
    search_fields = (
        "employee_id", "department",
        "user__first_name", "user__last_name", "user__email",
    )

    @action(detail=True, methods=["get"])
    def class_subjects(self, request, pk=None):
        """Subjects this teacher is assigned to."""
        teacher = self.get_object()
        from academics.models import ClassSubject
        from academics.serializers import ClassSubjectSerializer

        class_subjects = ClassSubject.all_objects.filter(
            institution_id=request.institution_id, teacher=teacher
        ).select_related("subject", "section", "course")
        data = ClassSubjectSerializer(
            class_subjects, many=True, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "data": data})


class GuardianViewSet(CreateWithUserViewSet):
    queryset = models.Guardian.objects.all()
    create_serializer_class = serializers.GuardianCreateSerializer
    read_serializer_class = serializers.GuardianSerializer
    filterset_fields = ("relation",)
    search_fields = (
        "user__first_name", "user__last_name", "user__email",
    )

    @action(detail=True, methods=["get"])
    def students(self, request, pk=None):
        """Students this guardian is linked to."""
        guardian = self.get_object()
        links = models.StudentGuardian.all_objects.filter(guardian=guardian)
        serializer = serializers.StudentGuardianSerializer(
            links, many=True, context=self.get_serializer_context()
        )
        return Response({"success": True, "data": serializer.data})


class StudentGuardianViewSet(TenantModelViewSet):
    queryset = models.StudentGuardian.objects.all()
    serializer_class = serializers.StudentGuardianSerializer
    filterset_fields = ("student", "guardian", "is_primary")
    search_fields = ()

    def perform_create(self, serializer):
        student = serializer.validated_data["student"]
        guardian = serializer.validated_data["guardian"]
        link = services.link_guardian(
            student, guardian,
            is_primary=serializer.validated_data.get("is_primary", False),
            is_emergency_contact=serializer.validated_data.get("is_emergency_contact", False),
        )
        # `serializer.save()` is bypassed: the service already created the row.
        serializer.instance = link
