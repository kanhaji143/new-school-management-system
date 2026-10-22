"""Notifications API views."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAuthenticatedInInstitution, IsCoordinator
from common.views import TenantModelViewSet

from . import models, serializers, services


class NotificationRuleMixin:
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


class NotificationTemplateViewSet(NotificationRuleMixin, TenantModelViewSet):
    queryset = models.NotificationTemplate.objects.all()
    serializer_class = serializers.NotificationTemplateSerializer
    filterset_fields = ("event", "channel", "is_active")
    search_fields = ("event", "subject")
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]


class NotificationViewSet(NotificationRuleMixin, TenantModelViewSet):
    queryset = models.Notification.objects.all()
    serializer_class = serializers.NotificationSerializer
    filterset_fields = ("status", "channel", "recipient")
    search_fields = ("subject", "body")
    # Outbox is read-only except retry.
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "logs"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not user.has_any_role("COORDINATOR", "SCHOOL_ADMIN", "SUPER_ADMIN"):
            queryset = queryset.filter(recipient=user)
        return queryset

    @action(detail=True, methods=["get"], url_path="logs")
    def logs(self, request, pk=None):
        notification = self.get_object()
        data = serializers.NotificationDeliveryLogSerializer(
            notification.delivery_logs.all(), many=True, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "data": data})

    @action(detail=True, methods=["post"], url_path="retry")
    def retry(self, request, pk=None):
        notification = self.get_object()
        services.retry(notification)
        data = self.serializer_class(notification, context=self.get_serializer_context()).data
        return Response({"success": True, "message": "Queued for retry.", "data": data})


class ProviderConfigViewSet(NotificationRuleMixin, TenantModelViewSet):
    queryset = models.ProviderConfig.objects.all()
    serializer_class = serializers.ProviderConfigSerializer
    filterset_fields = ("channel", "provider", "is_active")
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]
