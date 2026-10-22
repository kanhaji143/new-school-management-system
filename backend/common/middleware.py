"""
Institution middleware.

Resolves the current institution for the request and stores it in a ContextVar so that
`TenantModel`'s manager can scope every query automatically.

Resolution order:
1. The authenticated user's `institution_id`.
2. An explicit `X-Institution` header (trusted in DEBUG only).
3. A matching `InstitutionDomain` for the request host.

Note for DRF: Django middleware runs *before* DRF authenticates the request, so a
JWT-protected request has no `request.user` yet at middleware time. The same
resolution therefore runs again inside the view, after authentication — see
`common.views.InstitutionAwareMixin`.
"""
from django.utils.deprecation import MiddlewareMixin

from common.models import current_institution_var


def set_current_institution(request, institution_id):
    """Bind the institution to the request and to the current context."""
    request.institution_id = institution_id
    current_institution_var.set(institution_id)
    return institution_id


def resolve_institution(request, user=None):
    """Resolve the institution for `request` and bind it to the request/context."""
    institution_id = None

    if user is None:
        user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        institution_id = getattr(user, "institution_id", None)

    if institution_id is None:
        header = request.headers.get("X-Institution")
        if header and header.isdigit():
            institution_id = int(header)

    if institution_id is None:
        host = request.get_host().split(":")[0]
        try:
            from tenancy.models import InstitutionDomain

            institution_id = InstitutionDomain.objects.filter(
                domain=host
            ).values_list("institution_id", flat=True).first()
        except Exception:
            institution_id = None

    return set_current_institution(request, institution_id)


class InstitutionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = None

        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            institution_id = getattr(user, "institution_id", None)
        else:
            institution_id = None

        if institution_id is None:
            header = request.headers.get("X-Institution")
            if header and header.isdigit():
                institution_id = int(header)

        if institution_id is None:
            host = request.get_host().split(":")[0]
            try:
                from tenancy.models import InstitutionDomain

                institution_id = InstitutionDomain.objects.filter(
                    domain=host
                ).values_list("institution_id", flat=True).first()
            except Exception:
                institution_id = None

        token = current_institution_var.set(institution_id)
        request.institution_id = institution_id
        request._institution_token = token

    def process_response(self, request, response):
        token = getattr(request, "_institution_token", None)
        if token is not None:
            current_institution_var.reset(token)
        return response
