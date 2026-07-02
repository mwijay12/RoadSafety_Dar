from django.urls import path

from . import auth_views, views

urlpatterns = [
    # Auth routes
    path("auth/login/", auth_views.login_page, name="login"),
    path("auth/register/", auth_views.register_view, name="register"),
    path("auth/login/email/", auth_views.email_login, name="email_login"),
    path("auth/login/otp/send/", auth_views.send_login_otp, name="send_login_otp"),
    path("auth/login/otp/verify/", auth_views.verify_login_otp, name="verify_login_otp"),
    path("auth/google/", auth_views.google_oauth_redirect, name="google_oauth"),
    path("auth/callback/", auth_views.auth_callback, name="auth_callback"),
    path("auth/callback/process/", auth_views.process_auth_callback, name="process_auth_callback"),
    path("auth/logout/", auth_views.logout_view, name="logout"),

    # HTML pages
    path("dashboard/", views.dashboard, name="dashboard"),
    path("report/", views.report_form, name="report"),
    path("authority/", views.authority, name="authority"),
    path("offline/", views.offline_page, name="offline"),
    # JSON API (PRD §6)
    path("api/accidents", views.api_accidents, name="api_accidents"),
    path("api/accidents/", views.api_accidents_create, name="api_accidents_create"),
    path("api/stats/severity", views.api_stats_severity, name="api_stats_severity"),
    path("api/stats/vehicles", views.api_stats_vehicles, name="api_stats_vehicles"),
    path("api/stats/monthly", views.api_stats_monthly, name="api_stats_monthly"),
    path("api/stats/hourly", views.api_stats_hourly, name="api_stats_hourly"),
    path("api/stats/junctions", views.api_stats_junctions, name="api_stats_junctions"),
    path("api/stats/summary", views.api_stats_summary, name="api_stats_summary"),
    # Legacy aliases (so old dashboard.html keeps working)
    path("api/heatmap/", views.api_heatmap, name="api_heatmap"),
    path("api/severity/", views.api_severity, name="api_severity"),
    path("api/vehicles/", views.api_vehicles, name="api_vehicles"),
    path("api/monthly/", views.api_monthly, name="api_monthly"),
    path("api/hourly/", views.api_hourly, name="api_hourly"),
    path("api/junctions/", views.api_junctions, name="api_junctions"),
    path("api/summary/", views.api_summary, name="api_summary"),
    # v1.1 new features
    path("api/export.csv", views.api_export_csv, name="api_export_csv"),
    path("api/recommendations/", views.api_recommendations, name="api_recommendations"),
    # v1.2 new features
    path("api/report/monthly.pdf", views.api_monthly_report, name="api_monthly_report"),
    path("api/telegram/webhook/", views.api_telegram_webhook, name="api_telegram_webhook"),
    # v1.3 — Authority dashboard endpoints
    path("api/authority/filter/", views.api_authority_filter, name="api_authority_filter"),
    path(
        "api/authority/export/csv/",
        views.api_authority_export_csv,
        name="api_authority_export_csv",
    ),
    # v1.3 — API docs
    path("api/docs/", views.api_docs, name="api_docs"),
    # v1.4 — TTS Endpoint
    path("api/tts/", views.api_tts, name="api_tts"),

    # Prompt 2 — My Reports & Upvotes
    path("my-reports/", views.my_reports, name="my_reports"),
    path("api/accidents/<int:accident_id>/upvote/", views.api_upvote, name="api_upvote"),

    # Prompt 3 — Editor Queue & Admin Panel
    path("editor/queue/", views.editor_queue, name="editor_queue"),
    path("editor/accidents/<int:accident_id>/", views.editor_accident_detail, name="editor_accident_detail"),
    path("editor/accidents/<int:accident_id>/verify/", views.editor_verify_accident, name="editor_verify_accident"),
    path("editor/accidents/<int:accident_id>/reject/", views.editor_reject_accident, name="editor_reject_accident"),
    path("admin-panel/users/", views.admin_users, name="admin_users"),
    path("admin-panel/users/<int:user_id>/set-role/", views.admin_set_role, name="admin_set_role"),

    # Prompt 4 — Spatial radius query API
    path("api/accidents/near/", views.api_accidents_near, name="api_accidents_near"),

    # Prompt 5 — Hierarchical location picker API
    path("api/locations/", views.api_locations, name="api_locations"),
    path("api/locations/districts/", views.api_locations_districts, name="api_locations_districts"),
    path("api/locations/wards/", views.api_locations_wards, name="api_locations_wards"),
    path("api/locations/hotspots/", views.api_locations_hotspots, name="api_locations_hotspots"),
]

# ===================== /api/v1/ versioned aliases (Prompt 7) =====================
# All existing API endpoints mirrored under /api/v1/ for versioned access.
# Old /api/ paths continue to work indefinitely.
_api_v1_patterns = [
    "api/v1/accidents",
    "api/v1/accidents/",
    "api/v1/stats/severity",
    "api/v1/stats/vehicles",
    "api/v1/stats/monthly",
    "api/v1/stats/hourly",
    "api/v1/stats/junctions",
    "api/v1/stats/summary",
    "api/v1/export.csv",
    "api/v1/recommendations/",
    "api/v1/report/monthly.pdf",
    "api/v1/telegram/webhook/",
    "api/v1/authority/filter/",
    "api/v1/authority/export/csv/",
    "api/v1/tts/",
    "api/v1/locations/",
    "api/v1/locations/districts/",
    "api/v1/locations/wards/",
    "api/v1/locations/hotspots/",
]

# Map each v1 path to its corresponding view by swapping the old path prefix
_view_map = {
    "api/v1/accidents": views.api_accidents,
    "api/v1/accidents/": views.api_accidents_create,
    "api/v1/stats/severity": views.api_stats_severity,
    "api/v1/stats/vehicles": views.api_stats_vehicles,
    "api/v1/stats/monthly": views.api_stats_monthly,
    "api/v1/stats/hourly": views.api_stats_hourly,
    "api/v1/stats/junctions": views.api_stats_junctions,
    "api/v1/stats/summary": views.api_stats_summary,
    "api/v1/export.csv": views.api_export_csv,
    "api/v1/recommendations/": views.api_recommendations,
    "api/v1/report/monthly.pdf": views.api_monthly_report,
    "api/v1/telegram/webhook/": views.api_telegram_webhook,
    "api/v1/authority/filter/": views.api_authority_filter,
    "api/v1/authority/export/csv/": views.api_authority_export_csv,
    "api/v1/tts/": views.api_tts,
    "api/v1/locations/": views.api_locations,
    "api/v1/locations/districts/": views.api_locations_districts,
    "api/v1/locations/wards/": views.api_locations_wards,
    "api/v1/locations/hotspots/": views.api_locations_hotspots,
}

for _path, _view in _view_map.items():
    urlpatterns.append(path(_path, _view))

# Register api_docs under /api/v1/docs/ too
urlpatterns.append(path("api/v1/docs/", views.api_docs))
