"""Coordinator routes."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("coordinator-tasks", views.CoordinatorTaskViewSet, basename="coordinator-task")
router.register("command-center-widgets", views.CommandCenterWidgetViewSet, basename="command-center-widget")

urlpatterns = [path("coordinator/dashboard/", views.CoordinatorDashboardView.as_view(), name="coordinator-dashboard"), *router.urls]
