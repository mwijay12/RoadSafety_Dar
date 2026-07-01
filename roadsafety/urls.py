"""URL Configuration for roadsafety project."""
import json
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import path, include
from django.views.generic import RedirectView


def pwa_manifest(_request):
    """Serve the PWA manifest.json with correct Content-Type."""
    with open("accidents/static/manifest.json") as f:
        return JsonResponse(json.load(f))


def pwa_sw(_request):
    """Serve the service worker. Must be at root scope for PWA."""
    with open("accidents/static/sw.js") as f:
        return HttpResponse(f.read(), content_type="application/javascript")


def offline_page(_request):
    return render(_request, "accidents/offline.html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/dashboard/", permanent=False)),
    # PWA endpoints (v1.2) — must be at root for proper PWA scope
    path("manifest.json", pwa_manifest, name="pwa_manifest"),
    path("sw.js", pwa_sw, name="pwa_sw"),
    path("offline/", offline_page, name="offline"),
    # Single include — Django's LocaleMiddleware handles /sw/ prefix automatically
    # when Accept-Language or session says so. URLs work both /dashboard/ AND /sw/dashboard/
    path("", include("accidents.urls")),
]

# i18n_patterns adds /<lang>/ prefix to URLs when Language-Cookie is set
urlpatterns += i18n_patterns(
    path("", include("accidents.urls")),
    prefix_default_language=False,
)
