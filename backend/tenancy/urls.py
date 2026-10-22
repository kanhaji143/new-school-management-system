"""Tenancy routes."""
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
# TODO: router.register('resource', views.ResourceViewSet)

urlpatterns = router.urls
