"""Users, roles and invitations API views."""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdmin, IsAuthenticatedInInstitution
from common.views import AdminTenantModelViewSet, InstitutionAwareMixin
from tenancy.models import Institution, InstitutionSettings
from .models import Invitation, Role, User, UserRole
from .serializers import (
    InvitationSerializer,
    RegisterSerializer,
    RoleSerializer,
    UserSerializer,
)

DEFAULT_ROLES = ["SCHOOL_ADMIN", "COORDINATOR", "TEACHER", "ACCOUNTANT", "PARENT", "STUDENT"]


class RegisterView(APIView):
    """Create an institution + first admin account."""

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        institution = Institution.objects.create(
            name=data["institution_name"],
            slug=data["institution_name"].lower().replace(" ", "-"),
            type=data["institution_type"],
            is_active=True,
        )
        InstitutionSettings.objects.create(institution=institution)

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            institution=institution,
            is_staff=True,
        )

        admin_role = Role.objects.create(
            institution=institution, name="SCHOOL_ADMIN", is_system=True,
            permissions=["*"],
        )
        UserRole.objects.create(user=user, role=admin_role)
        for name in DEFAULT_ROLES:
            Role.objects.get_or_create(institution=institution, name=name)

        return Response(
            {"success": True, "message": "Institution created", "data": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class MeView(InstitutionAwareMixin, APIView):
    permission_classes = [IsAuthenticatedInInstitution]

    def get(self, request):
        return Response({"success": True, "data": UserSerializer(request.user).data})

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


class UserViewSet(AdminTenantModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        return Response({"success": True})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response({"success": True})


class RoleViewSet(AdminTenantModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class InvitationViewSet(AdminTenantModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer

    def perform_create(self, serializer):
        serializer.save(
            institution_id=self.request.institution_id,
            invited_by=self.request.user,
            expires_at=timezone.now() + timedelta(days=7),
        )

    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        invitation = self.get_object()
        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.save(update_fields=["expires_at", "updated_at"])
        # TODO: enqueue notification via notifications app.
        return Response({"success": True, "message": "Invitation resent"})
