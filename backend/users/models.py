"""Users, roles and invitations."""
import secrets

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from common.models import TimeStampedModel
from tenancy.models import Institution


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Institution-scoped user. Superusers may have no institution (platform operators)."""

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def roles(self):
        # `UserRole.user` declares related_name="user_roles" (see below).
        return Role.objects.filter(user_roles__user=self).distinct()

    def has_any_role(self, *role_names):
        if self.is_superuser:
            return True
        return self.roles().filter(name__in=role_names).exists()


class Role(TimeStampedModel):
    """A named set of permissions within an institution."""

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="roles", null=True, blank=True
    )
    name = models.CharField(max_length=50)
    permissions = models.JSONField(default=list, help_text="List of permission strings")
    is_system = models.BooleanField(default=False, help_text="Built-in, not deletable")

    class Meta:
        unique_together = ("institution", "name")

    def __str__(self):
        return f"{self.name} ({self.institution})"


class UserRole(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    academic_year = models.ForeignKey(
        "academics.AcademicYear", null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = ("user", "role")


class Invitation(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        EXPIRED = "EXPIRED", "Expired"

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    invited_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    def __str__(self):
        return f"{self.email} → {self.role}"
