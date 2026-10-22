"""
Cross-cutting abstract models.

Every tenant-scoped business model should inherit `TenantModel`, which:

* adds a mandatory `institution` foreign key,
* exposes a manager that automatically filters by the *current* institution,
* makes cross-tenant reads architecturally impossible for non-super-admins.

The current institution is stored in a `ContextVar` (see `common.middleware`).
"""
from contextvars import ContextVar
from typing import Optional

from django.conf import settings
from django.db import models

# Set by InstitutionMiddleware on every request.
current_institution_var: ContextVar[Optional[int]] = ContextVar(
    "current_institution", default=None
)


def get_current_institution_id() -> Optional[int]:
    return current_institution_var.get()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Default manager hides soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])


class TenantManager(models.Manager):
    """Filters by the current institution for non-super-admins."""

    def get_queryset(self):
        qs = super().get_queryset()
        institution_id = get_current_institution_id()
        if institution_id is not None:
            return qs.filter(institution_id=institution_id)
        return qs


class TenantModel(TimeStampedModel):
    institution = models.ForeignKey(
        "tenancy.Institution",
        on_delete=models.CASCADE,
        related_name="+",
        db_index=True,
    )

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True


class AuditMixin(models.Model):
    """Adds actor tracking to a model."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True
