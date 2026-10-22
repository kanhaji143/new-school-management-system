"""Academics API views.

Every queryset is scoped to the requesting institution. Writes require the
COORDINATOR / SCHOOL_ADMIN role; reads require an authenticated member of the
institution.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAuthenticatedInInstitution, IsCoordinator
from common.views import TenantModelViewSet

from . import models, serializers, services


class TenantViewSet(TenantModelViewSet):
    """Academics-specific base (kept as an alias for readability)."""


class AcademicYearViewSet(TenantViewSet):
    queryset = models.AcademicYear.objects.all()
    serializer_class = serializers.AcademicYearSerializer
    filterset_fields = ("is_active",)
    search_fields = ("name",)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Make this year the only active year for the institution."""
        year = services.activate_academic_year(self.get_object())
        return Response(
            {"success": True, "message": f"{year.name} is now the active year.",
             "data": self.get_serializer(year).data}
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        year = services.deactivate_academic_year(self.get_object())
        return Response(
            {"success": True, "message": f"{year.name} deactivated.",
             "data": self.get_serializer(year).data}
        )

    @action(detail=False, methods=["get"])
    def current(self, request):
        """The institution's active academic year (or null)."""
        year = services.get_active_academic_year(request.institution_id)
        data = self.get_serializer(year).data if year else None
        return Response({"success": True, "data": data})


class TermViewSet(TenantViewSet):
    queryset = models.Term.objects.all()
    serializer_class = serializers.TermSerializer
    filterset_fields = ("academic_year", "term_type", "is_active")
    search_fields = ("name",)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        term = services.activate_term(self.get_object())
        return Response(
            {"success": True, "message": f"{term.name} is now the active term.",
             "data": self.get_serializer(term).data}
        )

    @action(detail=False, methods=["get"])
    def current(self, request):
        """The active term of the active (or requested) academic year."""
        year_id = request.query_params.get("academic_year")
        term = services.get_active_term(request.institution_id, year_id)
        data = self.get_serializer(term).data if term else None
        return Response({"success": True, "data": data})


class GradeLevelViewSet(TenantViewSet):
    queryset = models.GradeLevel.objects.all()
    serializer_class = serializers.GradeLevelSerializer
    filterset_fields = ("level_type",)
    search_fields = ("name",)


class SchoolClassViewSet(TenantViewSet):
    queryset = models.SchoolClass.objects.all()
    serializer_class = serializers.SchoolClassSerializer
    filterset_fields = ("grade_level",)
    search_fields = ("name",)


class SectionViewSet(TenantViewSet):
    queryset = models.Section.objects.all()
    serializer_class = serializers.SectionSerializer
    filterset_fields = ("school_class",)
    search_fields = ("name",)

    @action(detail=True, methods=["get"])
    def subjects(self, request, pk=None):
        """Subjects taught to this section."""
        section = self.get_object()
        class_subjects = models.ClassSubject.all_objects.filter(
            institution_id=request.institution_id, section=section
        ).select_related("subject", "teacher")
        serializer = serializers.ClassSubjectSerializer(
            class_subjects, many=True, context=self.get_serializer_context()
        )
        return Response({"success": True, "data": serializer.data})


class CourseViewSet(TenantViewSet):
    queryset = models.Course.objects.all()
    serializer_class = serializers.CourseSerializer
    filterset_fields = ()
    search_fields = ("code", "name")


class SubjectViewSet(TenantViewSet):
    queryset = models.Subject.objects.all()
    serializer_class = serializers.SubjectSerializer
    filterset_fields = ("subject_type",)
    search_fields = ("code", "name")


class ClassSubjectViewSet(TenantViewSet):
    queryset = models.ClassSubject.objects.all()
    serializer_class = serializers.ClassSubjectSerializer
    filterset_fields = ("subject", "section", "course", "teacher", "academic_year", "term")
    search_fields = ("subject__name", "subject__code", "teacher__user__first_name")


class EnrollmentViewSet(TenantViewSet):
    queryset = models.Enrollment.objects.all()
    serializer_class = serializers.EnrollmentSerializer
    filterset_fields = ("student", "section", "course", "academic_year", "term", "status")
    search_fields = ("student__roll_number", "student__user__first_name")

    @action(detail=False, methods=["post"])
    def promote(self, request):
        """Move a set of active enrollments from one year/term to the next."""
        from_year = models.AcademicYear.all_objects.filter(
            institution_id=request.institution_id,
            id=request.data.get("from_academic_year"),
        ).first()
        to_year = models.AcademicYear.all_objects.filter(
            institution_id=request.institution_id,
            id=request.data.get("to_academic_year"),
        ).first()
        if not from_year or not to_year:
            return Response(
                {"success": False,
                 "message": "from_academic_year and to_academic_year are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from_term = None
        to_term = None
        if request.data.get("from_term"):
            from_term = models.Term.all_objects.filter(
                institution_id=request.institution_id,
                id=request.data["from_term"],
            ).first()
        if request.data.get("to_term"):
            to_term = models.Term.all_objects.filter(
                institution_id=request.institution_id,
                id=request.data["to_term"],
            ).first()

        section_map = request.data.get("section_map") or {}
        created = services.promote_students(
            request.institution_id, from_year, to_year,
            from_term=from_term, to_term=to_term, section_map=section_map,
        )
        return Response(
            {"success": True, "message": f"Promoted {len(created)} enrollment(s).",
             "data": {"count": len(created)}}
        )
