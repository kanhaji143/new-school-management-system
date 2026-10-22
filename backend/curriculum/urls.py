"""Curriculum routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("syllabi", views.SyllabusViewSet, basename="syllabus")
router.register("chapters", views.ChapterViewSet, basename="chapter")
router.register("lesson-plans", views.LessonPlanViewSet, basename="lesson-plan")
router.register("class-session-logs", views.ClassSessionLogViewSet, basename="class-session-log")

urlpatterns = router.urls
