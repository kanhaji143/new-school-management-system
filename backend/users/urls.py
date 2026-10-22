"""Users / roles / invitations routes."""
from rest_framework.routers import DefaultRouter

from .views import InvitationViewSet, RoleViewSet, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")
router.register("invitations", InvitationViewSet, basename="invitation")

urlpatterns = router.urls
