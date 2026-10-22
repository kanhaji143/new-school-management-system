"""Coordinator dashboard and task APIs."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from common.permissions import IsCoordinator
from common.views import InstitutionAwareMixin, TenantModelViewSet

from . import models, serializers


class CoordinatorResponseMixin:
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


class CoordinatorDashboardView(InstitutionAwareMixin, APIView):
    permission_classes = [IsCoordinator]

    @extend_schema(responses=serializers.CoordinatorDashboardSerializer)
    def get(self, request):
        from ai.models import GeneratedContent
        from assessments.models import Assessment
        from attendance.models import LeaveRequest
        from substitution.models import SubstitutionRequest
        from timetable.models import TimetableChangeRequest

        institution_id = request.institution_id
        pending = {
            "substitutions": SubstitutionRequest.objects.filter(
                institution_id=institution_id,
                status__in=("OPEN", "PROPOSED"),
            ).count(),
            "timetable_changes": TimetableChangeRequest.objects.filter(
                institution_id=institution_id, status="PENDING"
            ).count(),
            "leave_requests": LeaveRequest.objects.filter(
                institution_id=institution_id, status="PENDING"
            ).count(),
            "ai_reviews": GeneratedContent.objects.filter(
                institution_id=institution_id, status="PENDING_REVIEW"
            ).count(),
            "grading": Assessment.objects.filter(
                institution_id=institution_id, status="COMPLETED"
            ).count(),
            "tasks": models.CoordinatorTask.objects.filter(
                institution_id=institution_id, status__in=("OPEN", "IN_PROGRESS")
            ).count(),
        }
        widgets = models.CommandCenterWidget.objects.filter(
            institution_id=institution_id, is_active=True
        )
        return Response(
            {
                "success": True,
                "data": {
                    "pending": pending,
                    "total_pending": sum(pending.values()),
                    "widgets": serializers.CommandCenterWidgetSerializer(widgets, many=True).data,
                },
            }
        )


class CoordinatorTaskViewSet(CoordinatorResponseMixin, TenantModelViewSet):
    queryset = models.CoordinatorTask.objects.select_related("assignee", "created_by")
    serializer_class = serializers.CoordinatorTaskSerializer
    permission_classes = [IsCoordinator]
    filterset_fields = ("task_type", "status", "assignee")
    search_fields = ("title",)
    ordering_fields = ("created_at", "updated_at", "status")

    def perform_create(self, serializer):
        serializer.save(
            institution_id=self.request.institution_id,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        if task.status == models.CoordinatorTask.Status.DONE:
            return Response(
                {"success": False, "message": "Task is already complete."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        task.status = models.CoordinatorTask.Status.DONE
        task.save(update_fields=["status", "updated_at"])
        return Response({"success": True, "data": self.get_serializer(task).data})


class CommandCenterWidgetViewSet(CoordinatorResponseMixin, TenantModelViewSet):
    queryset = models.CommandCenterWidget.objects.all()
    serializer_class = serializers.CommandCenterWidgetSerializer
    permission_classes = [IsCoordinator]
    filterset_fields = ("is_active",)
    ordering_fields = ("order_index", "key")

    def perform_create(self, serializer):
        serializer.save(institution_id=self.request.institution_id)
