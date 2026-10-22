"""Shared viewset base classes."""
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from common.middleware import resolve_institution
from common.permissions import IsAuthenticatedInInstitution, IsAdmin, IsCoordinator


class InstitutionAwareMixin:
    """Resolve the current institution *after* DRF authentication.

    Django middleware runs before DRF authenticates the request, so for JWT
    protected endpoints `request.institution` is not known yet when the
    middleware executes. This mixin re-resolves it once the user is available
    and re-binds the tenant ContextVar used by `TenantModel.objects`.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        resolve_institution(self.request, self.request.user)


class TenantModelViewSet(InstitutionAwareMixin, viewsets.ModelViewSet):
    """Base viewset for tenant-scoped resources.

    * every queryset is filtered to the requesting institution,
    * writes require an elevated role (COORDINATOR / SCHOOL_ADMIN by default),
    * reads require an authenticated member of the institution,
    * the institution is injected into the serializer context so that related
      fields can be validated against the same tenant.
    """

    permission_classes = [IsAuthenticatedInInstitution]

    write_permission_class = IsCoordinator
    write_actions = ("create", "update", "partial_update", "destroy")

    def get_permissions(self):
        if self.action in self.write_actions:
            return [self.write_permission_class()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        institution_id = getattr(self.request, "institution_id", None)
        if institution_id is None:
            # Platform superusers without an institution may read across tenants.
            if self.request.user and self.request.user.is_superuser:
                return queryset
            raise PermissionDenied("No institution context for this request.")
        return queryset.filter(institution_id=institution_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["institution_id"] = getattr(self.request, "institution_id", None)
        return context

    def perform_create(self, serializer):
        model = getattr(getattr(serializer, "Meta", None), "model", None)
        if model is not None and hasattr(model, "institution"):
            serializer.save(institution_id=self.request.institution_id)
        else:
            serializer.save()


class AdminTenantModelViewSet(TenantModelViewSet):
    """Variant restricted to administrators for write operations."""

    write_permission_class = IsAdmin
