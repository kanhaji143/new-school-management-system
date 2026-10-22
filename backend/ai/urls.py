"""AI routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("jobs", views.AIJobViewSet, basename="ai-job")
router.register("generated-content", views.GeneratedContentViewSet, basename="generated-content")

urlpatterns = router.urls
