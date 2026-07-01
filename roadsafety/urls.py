"""URL Configuration for roadsafety project."""
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/dashboard/", permanent=False)),
    # Single include — Django's LocaleMiddleware handles /sw/ prefix automatically
    # when Accept-Language or session says so. URLs work both /dashboard/ AND /sw/dashboard/
    path("", include("accidents.urls")),
]

# i18n_patterns adds /<lang>/ prefix to URLs when Language-Cookie is set
urlpatterns += i18n_patterns(
    path("", include("accidents.urls")),
    prefix_default_language=False,
)
