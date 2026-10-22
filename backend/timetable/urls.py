"""Timetable routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("period-templates", views.PeriodTemplateViewSet, basename="period-template")
router.register("timetables", views.TimetableViewSet, basename="timetable")
router.register("timetable-entries", views.TimetableEntryViewSet, basename="timetable-entry")
router.register(
    "timetable-change-requests", views.TimetableChangeRequestViewSet,
    basename="timetable-change-request",
)

urlpatterns = router.urls
