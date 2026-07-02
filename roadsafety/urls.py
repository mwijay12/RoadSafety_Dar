"""
URL Configuration for the RoadSafety Dar es Salaam project.

This module defines the URL routing for the entire application, including
admin interfaces, public dashboards, API endpoints, PWA assets, and system health checks.
It also integrates Django's internationalization (i18n) patterns.
"""

import json

from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import include, path
from django.views.generic import RedirectView


from django.conf import settings

def pwa_manifest(_request):
    """
    Serve the PWA manifest.json with the correct Content-Type.
    This file defines the Progressive Web App properties like name, icons, and display mode.
    """
    path = settings.BASE_DIR / "accidents" / "static" / "manifest.json"
    with open(path) as f:
        return JsonResponse(json.load(f))


def pwa_sw(_request):
    """
    Serve the service worker (sw.js). It must be at the root scope for proper PWA functionality.
    The service worker enables offline capabilities, caching, and background synchronization.
    """
    path = settings.BASE_DIR / "accidents" / "static" / "sw.js"
    with open(path) as f:
        return HttpResponse(f.read(), content_type="application/javascript")


def offline_page(_request):
    """
    Renders a dedicated offline page for the PWA.
    This page is displayed when the user loses network connectivity.
    """
    return render(_request, "accidents/offline.html")


def healthz(_request):
    """
    Liveness probe endpoint for cloud platforms like Railway/Render.
    Returns a 200 OK status along with version information. This helps
    load balancers and orchestration systems determine application health.
    """
    from roadsafety.version import version_info

    return JsonResponse(
        {
            "service_status": "ok",  # Primary status for load balancers.
            "status": "ok",  # Legacy alias for older health checks.
            "service": "roadsafety-dar",  # Identifier for this service.
            **version_info(),  # Include detailed version information.
        }
    )


def version_endpoint(_request):
    """
    Public API endpoint to retrieve application version information.
    Useful for monitoring and external API consumers to track releases.
    """
    from roadsafety.version import version_info

    return JsonResponse(version_info())


urlpatterns = [
    # Django Admin URL.
    path("admin/", admin.site.urls),
    # django-allauth authentication URLs.
    path("accounts/", include("allauth.urls")),
    # Root URL redirects to the dashboard for user-friendliness.
    path("", RedirectView.as_view(url="/dashboard/", permanent=False)),
    # PWA endpoints (v1.2) — these must be at the root for proper PWA scope.
    path("manifest.json", pwa_manifest, name="pwa_manifest"),
    path("sw.js", pwa_sw, name="pwa_sw"),
    path("offline/", offline_page, name="offline"),
    # System health and version endpoints.
    path("healthz", healthz, name="healthz"),
    path("health/", healthz, name="health"),  # alias for Render default healthcheck
    path("api/version", version_endpoint, name="version"),
    # Include all URLs defined in the 'accidents' app.
    # Django's LocaleMiddleware handles /<lang>/ prefix automatically
    # when Accept-Language or session says so. URLs work both /dashboard/ AND /sw/dashboard/
    path("", include("accidents.urls")),
]

# i18n_patterns adds /<lang>/ prefix to URLs when a Language-Cookie is set.
# This enables multilingual support for the application.
urlpatterns += i18n_patterns(
    path("", include("accidents.urls")),
    prefix_default_language=False,  # Do not prefix default language URLs.
)
