"""Notifications routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("notification-templates", views.NotificationTemplateViewSet, basename="notification-template")
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("provider-configs", views.ProviderConfigViewSet, basename="provider-config")

urlpatterns = router.urls
