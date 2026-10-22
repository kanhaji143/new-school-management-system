"""Shared serializer helpers used across apps."""
from rest_framework import serializers


class TenantRelatedField(serializers.PrimaryKeyRelatedField):
    """A primary-key field restricted to the current institution.

    Django's `ForeignKey` validation is skipped by DRF when the related object
    belongs to another tenant, which would break institution isolation. This
    field re-applies the tenant filter at validation time using the
    `institution_id` value placed in the serializer context by the viewset.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        institution_id = self.context.get("institution_id")
        if institution_id is not None and hasattr(queryset.model, "institution"):
            queryset = queryset.filter(institution_id=institution_id)
        return queryset


class UserSummarySerializer(serializers.Serializer):
    """Compact representation of a user, used inside nested payloads."""

    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
