from django.urls import path
from . import views

urlpatterns = [
    # HTML pages
    path("dashboard/", views.dashboard, name="dashboard"),
    path("report/", views.report_form, name="report"),
    path("authority/", views.authority, name="authority"),

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
]
