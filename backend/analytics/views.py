"""Analytics API views (DRF viewsets + permissions)."""
from rest_framework import viewsets

from . import models, serializers


# TODO: implement viewsets. Every queryset must stay institution-scoped
# via TenantModel.objects (see common.models.TenantManager).
