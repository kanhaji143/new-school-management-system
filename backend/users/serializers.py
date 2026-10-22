"""Users, roles and invitations serializers.

Serializers whitelist fields explicitly to prevent mass assignment (OWASP).
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Invitation, Role, UserRole

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    full_name = serializers.CharField(read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True, allow_null=True)
    institution_phone = serializers.CharField(source="institution.phone", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "full_name",
            "phone", "institution", "institution_name", "institution_phone",
            "roles", "is_active", "created_at",
        )
        read_only_fields = ("id", "institution", "created_at")

    def get_roles(self, obj):
        return list(obj.roles().values_list("name", flat=True))


class RegisterSerializer(serializers.Serializer):
    """Create an institution and its first admin user."""

    institution_name = serializers.CharField(max_length=255)
    institution_type = serializers.ChoiceField(choices=["SCHOOL", "COLLEGE"], default="SCHOOL")
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "permissions", "is_system", "institution")
        read_only_fields = ("id", "institution")


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ("id", "user", "role", "academic_year")
        read_only_fields = ("id",)


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = (
            "id", "email", "role", "status", "expires_at", "token", "created_at"
        )
        read_only_fields = ("id", "status", "token", "created_at")
