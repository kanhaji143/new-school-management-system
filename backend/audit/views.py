"""Audit-log, backup and system-setting APIs."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response

from common.permissions import IsAdmin, IsCoordinator
from common.views import InstitutionAwareMixin, TenantModelViewSet

from . import models, serializers, services


class AuditLogViewSet(InstitutionAwareMixin, ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.AuditLogSerializer
    permission_classes = [IsCoordinator]
    filterset_fields = ("action", "model", "actor")
    search_fields = ("object_repr", "object_id", "model")
    ordering_fields = ("created_at", "action")

    def get_queryset(self):
        return models.AuditLog.all_objects.filter(
            institution_id=self.request.institution_id
        ).select_related("actor")


class BackupViewSet(InstitutionAwareMixin, ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.BackupSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ("kind", "status", "restore_test_passed")

    def get_queryset(self):
        # Database snapshots are global, so only platform SUPER_ADMIN can see them.
        if not self.request.user.has_any_role("SUPER_ADMIN"):
            return models.Backup.objects.none()
        return models.Backup.objects.filter(institution__isnull=True).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        if not request.user.has_any_role("SUPER_ADMIN"):
            return Response({"success": False, "message": "Platform SUPER_ADMIN role required."}, status=403)
        try:
            backup = services.create_backup(actor=request.user)
        except services.BackupError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_501_NOT_IMPLEMENTED if "support" in str(exc) else status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {"success": True, "data": self.get_serializer(backup).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="test-restore")
    def test_restore(self, request, pk=None):
        if not request.user.has_any_role("SUPER_ADMIN"):
            return Response({"success": False, "message": "Platform SUPER_ADMIN role required."}, status=403)
        backup = self.get_object()
        passed, message = services.verify_backup(backup)
        return Response(
            {"success": passed, "message": message, "data": self.get_serializer(backup).data},
            status=status.HTTP_200_OK if passed else status.HTTP_400_BAD_REQUEST,
        )


class SystemSettingViewSet(TenantModelViewSet):
    queryset = models.SystemSetting.objects.all()
    serializer_class = serializers.SystemSettingSerializer
    permission_classes = [IsAdmin]
    write_permission_class = IsAdmin
    filterset_fields = ("key",)
    search_fields = ("key", "description")

    def perform_create(self, serializer):
        serializer.save(institution_id=self.request.institution_id)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data}, status=response.status_code)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=response.status_code)
