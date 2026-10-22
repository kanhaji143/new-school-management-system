"""Curriculum API views."""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAuthenticatedInInstitution, IsCoordinator
from common.views import TenantModelViewSet

from . import models, serializers


class CurriculumRuleMixin:
    @staticmethod
    def rule_error(message):
        return Response(
            {"success": False, "message": message, "errors": {"fieldErrors": {}, "formErrors": [message]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data}, status=response.status_code)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data})

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data})

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data})


class SyllabusViewSet(CurriculumRuleMixin, TenantModelViewSet):
    queryset = models.Syllabus.objects.all()
    serializer_class = serializers.SyllabusSerializer
    filterset_fields = ("subject", "section", "academic_year", "term")
    search_fields = ("title",)
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    @action(detail=True, methods=["get", "post"], url_path="chapters")
    def chapters(self, request, pk=None):
        syllabus = self.get_object()
        if request.method == "GET":
            data = serializers.ChapterSerializer(
                syllabus.chapters.all(), many=True, context=self.get_serializer_context()
            ).data
            return Response({"success": True, "data": data})
        payload = serializers.ChapterCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        chapter = models.Chapter.objects.create(
            institution_id=syllabus.institution_id, syllabus=syllabus, **payload.validated_data
        )
        data = serializers.ChapterSerializer(chapter, context=self.get_serializer_context()).data
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)


class ChapterViewSet(CurriculumRuleMixin, TenantModelViewSet):
    queryset = models.Chapter.objects.all()
    serializer_class = serializers.ChapterSerializer
    filterset_fields = ("syllabus",)
    search_fields = ("title",)
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    @action(detail=True, methods=["get", "post"], url_path="lesson-plans")
    def lesson_plans(self, request, pk=None):
        chapter = self.get_object()
        if request.method == "GET":
            data = serializers.LessonPlanSerializer(
                chapter.lesson_plans.all(), many=True, context=self.get_serializer_context()
            ).data
            return Response({"success": True, "data": data})
        payload = serializers.LessonPlanSerializer(data=request.data, context=self.get_serializer_context())
        payload.is_valid(raise_exception=True)
        plan = payload.save(
            institution_id=chapter.institution_id, chapter=chapter,
            created_by=request.user,
        )
        data = serializers.LessonPlanSerializer(plan, context=self.get_serializer_context()).data
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        chapter = self.get_object()
        payload = serializers.CompleteChapterSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        completion, _ = models.LessonCompletion.objects.get_or_create(
            chapter=chapter,
            defaults={
                "institution_id": chapter.institution_id,
                "status": data.get("status", models.LessonCompletion.Status.COMPLETED),
                "completed_date": data.get("completed_date") or timezone.localdate(),
                "verified_by": request.user,
            },
        )
        completion.status = data.get("status", models.LessonCompletion.Status.COMPLETED)
        completion.completed_date = data.get("completed_date") or completion.completed_date or timezone.localdate()
        completion.verified_by = request.user
        completion.save(update_fields=["status", "completed_date", "verified_by", "updated_at"])
        out = serializers.LessonCompletionSerializer(completion, context=self.get_serializer_context()).data
        return Response({"success": True, "message": "Chapter marked complete.", "data": out})


class LessonPlanViewSet(CurriculumRuleMixin, TenantModelViewSet):
    queryset = models.LessonPlan.objects.all()
    serializer_class = serializers.LessonPlanSerializer
    filterset_fields = ("chapter",)
    search_fields = ("title",)
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    def perform_create(self, serializer):
        serializer.save(institution_id=self.request.institution_id, created_by=self.request.user)


class ClassSessionLogViewSet(CurriculumRuleMixin, TenantModelViewSet):
    queryset = models.ClassSessionLog.objects.all()
    serializer_class = serializers.ClassSessionLogSerializer
    filterset_fields = ("subject", "section", "chapter", "teacher", "status")
    search_fields = ("topic",)
    write_permission_class = IsAuthenticatedInInstitution

    def perform_create(self, serializer):
        serializer.save(institution_id=self.request.institution_id)
