"""Attendance routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("student-attendance", views.StudentAttendanceViewSet, basename="student-attendance")
router.register("period-attendance", views.PeriodAttendanceViewSet, basename="period-attendance")
router.register("teacher-attendance", views.TeacherAttendanceViewSet, basename="teacher-attendance")
router.register("leave-types", views.LeaveTypeViewSet, basename="leave-type")
router.register("leave-requests", views.LeaveRequestViewSet, basename="leave-request")

urlpatterns = router.urls
