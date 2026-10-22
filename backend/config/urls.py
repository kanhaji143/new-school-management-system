"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})

api_urlpatterns = [
    path("auth/", include("users.urls_auth")),
    path("", include("tenancy.urls")),
    path("", include("users.urls")),
    path("", include("academics.urls")),
    path("", include("people.urls")),
    path("", include("timetable.urls")),
    path("", include("attendance.urls")),
    path("", include("substitution.urls")),
    path("", include("curriculum.urls")),
    path("", include("content.urls")),
    path("", include("assessments.urls")),
    path("", include("notifications.urls")),
    path("ai/", include("ai.urls")),
    path("", include("coordinator.urls")),
    path("", include("analytics.urls")),
    path("", include("audit.urls")),
]

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/", include(api_urlpatterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
