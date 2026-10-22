"""Substitution routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("substitution-requests", views.SubstitutionRequestViewSet, basename="substitution-request")

urlpatterns = router.urls
