from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from config.exceptions import api_catchall_404, custom_404_handler

# API-aware 404 handler for production
handler404 = "config.exceptions.custom_404_handler"


def health_check(request):
    """Readiness/health check probe for monitoring & container orchestrators."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "inchi-backend",
            "timestamp": timezone.now().isoformat(),
        }
    )


urlpatterns = [
    # Health check
    path("api/v1/health/", health_check, name="health-check"),

    # OpenAPI Schema & Interactive Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # Django Admin (custom path from settings)
    path(settings.ADMIN_URL_PATH, admin.site.urls),

    # Module APIs
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.registry.urls")),
    path("api/v1/", include("apps.demand.urls")),

    # Catch-all for unmatched API routes (QA-006 / TD-09)
    re_path(r"^api/.*$", api_catchall_404, name="api-catchall-404"),
]
