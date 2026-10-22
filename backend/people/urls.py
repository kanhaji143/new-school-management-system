"""People routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("students", views.StudentViewSet, basename="student")
router.register("teachers", views.TeacherViewSet, basename="teacher")
router.register("guardians", views.GuardianViewSet, basename="guardian")
router.register("student-guardians", views.StudentGuardianViewSet, basename="student-guardian")

urlpatterns = router.urls
