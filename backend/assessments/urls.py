"""Assessments routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("question-banks", views.QuestionBankViewSet, basename="question-bank")
router.register("questions", views.QuestionViewSet, basename="question")
router.register("grade-scales", views.GradeScaleViewSet, basename="grade-scale")
router.register("assessments", views.AssessmentViewSet, basename="assessment")
router.register("assessment-questions", views.AssessmentQuestionViewSet, basename="assessment-question")
router.register("student-assessments", views.StudentAssessmentViewSet, basename="student-assessment")
router.register("question-imports", views.QuestionImportViewSet, basename="question-import")

urlpatterns = router.urls
