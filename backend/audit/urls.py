"""Audit routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("audit-logs", views.AuditLogViewSet, basename="audit-log")
router.register("backups", views.BackupViewSet, basename="backup")
router.register("system-settings", views.SystemSettingViewSet, basename="system-setting")

urlpatterns = router.urls
