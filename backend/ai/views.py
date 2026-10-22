"""AI API views."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAuthenticatedInInstitution, IsCoordinator
from common.views import TenantModelViewSet

from . import models, serializers, services


class AIRuleMixin:
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


class AIJobViewSet(AIRuleMixin, TenantModelViewSet):
    queryset = models.AIJob.objects.all()
    serializer_class = serializers.AIJobSerializer
    filterset_fields = ("job_type", "status")
    write_permission_class = IsAuthenticatedInInstitution

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsAuthenticatedInInstitution()]

    def perform_create(self, serializer):
        job = serializer.save(institution_id=self.request.institution_id, created_by=self.request.user, status=models.AIJob.Status.QUEUED)
        services.run_job(job)


class GeneratedContentViewSet(AIRuleMixin, TenantModelViewSet):
    queryset = models.GeneratedContent.objects.all()
    serializer_class = serializers.GeneratedContentSerializer
    filterset_fields = ("content_type", "status")
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve", "review"):
            # review requires coordinator
            if self.action == "review":
                return [IsCoordinator()]
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        content = self.get_object()
        if content.status not in (models.GeneratedContent.Status.PENDING_REVIEW, models.GeneratedContent.Status.DRAFT):
            return self.rule_error("This content has already been reviewed.")
        payload = serializers.ReviewSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        if data["decision"] == "approve":
            content.approve(request.user, data.get("note", ""))
        else:
            content.reject(request.user, data.get("note", ""))
        out = serializers.GeneratedContentSerializer(content, context=self.get_serializer_context()).data
        return Response({"success": True, "message": f"Content {data['decision']}d.", "data": out})
