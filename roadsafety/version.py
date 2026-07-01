"""
Versioning for RoadSafety Dar.

Uses semantic versioning: MAJOR.MINOR.PATCH
  - MAJOR: breaking changes (model migrations, API rewrites)
  - MINOR: new features (PWA, PDF reports, etc.)
  - PATCH: bug fixes, performance improvements

Bump this BEFORE committing changes.
Update CHANGELOG.md with notable changes.
"""
import datetime

# Application version (semver)
VERSION = "1.2.0"
VERSION_NAME = "Mwangaza"  # Swahili: "Light" — appropriate for safety app
RELEASE_DATE = "2026-07-01"
BUILD = "20260701.001"

# Status
STATUS = "stable"  # "alpha" | "beta" | "stable" | "deprecated"
API_VERSION = "v1"  # API compatibility version

# Compatibility
PYTHON_MIN = "3.11"
DJANGO_MIN = "5.0"

# Changelog summary
CHANGELOG = [
    ("1.2.0", "2026-07-01", "Mwangaza", [
        "✨ PDF monthly report generation (reportlab)",
        "✨ Progressive Web App (PWA) with offline support",
        "✨ Telegram bot integration for instant alerts",
        "✨ Real-time auto-refresh dashboard (30s polling)",
        "✨ PostGIS migration script for spatial queries",
        "✨ Bulk CSV import for TPF legacy data",
        "🔧 Severity-weighted heatmap (v1.1 carried over)",
        "🔧 AI-powered recommendations (v1.1 carried over)",
        "🔧 Swahili i18n support (v1.1 carried over)",
    ]),
    ("1.1.0", "2026-06-30", "Taa", [
        "✨ Public CSV export endpoint",
        "✨ AI recommendations (OpenRouter integration)",
        "✨ Swahili (sw) translation file",
        "✨ Fatal cluster detection management command",
        "🔧 Locale middleware for /sw/ URL prefix",
    ]),
    ("1.0.0", "2026-06-29", "Msingi", [
        "🎉 Initial release",
        "✨ Public dashboard with heatmap + 4 charts",
        "✨ Mobile report form with GPS capture",
        "✨ Authority dashboard with recommendations",
        "✨ Django admin with bulk verify action",
        "✨ 8 JSON API endpoints",
        "✨ 80+ seeded accident records (Dar es Salaam)",
        "✨ 20+ named Dar junctions",
    ]),
]


def version_info():
    """Return version info as a dict (for API responses)."""
    return {
        "version": VERSION,
        "version_name": VERSION_NAME,
        "release_date": RELEASE_DATE,
        "build": BUILD,
        "status": STATUS,
        "api_version": API_VERSION,
        "python_min": PYTHON_MIN,
        "django_min": DJANGO_MIN,
    }


def short_version():
    """Return short version string for display."""
    return f"v{VERSION} ({VERSION_NAME})"
