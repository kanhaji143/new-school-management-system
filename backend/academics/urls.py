"""Academics routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("academic-years", views.AcademicYearViewSet, basename="academic-year")
router.register("terms", views.TermViewSet, basename="term")
router.register("grade-levels", views.GradeLevelViewSet, basename="grade-level")
router.register("classes", views.SchoolClassViewSet, basename="school-class")
router.register("sections", views.SectionViewSet, basename="section")
router.register("courses", views.CourseViewSet, basename="course")
router.register("subjects", views.SubjectViewSet, basename="subject")
router.register("class-subjects", views.ClassSubjectViewSet, basename="class-subject")
router.register("enrollments", views.EnrollmentViewSet, basename="enrollment")

urlpatterns = router.urls
