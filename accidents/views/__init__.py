"""
Views package — split by concern for maintainability.

All public views are re-exported here so ``from . import views`` continues
to work in urls.py and tests.
"""

from accidents.decorators import _rate_log  # noqa: F401 — kept for test backward compat

from .authority_views import (  # noqa: F401
    api_authority_export_csv,
    api_authority_filter,
    authority,
)
from .pdf import (  # noqa: F401
    api_monthly_report,
)
from .public import (  # noqa: F401
    _ai_recommendations,
    _build_recommendation_engine_context,
    _rule_based_recommendations,
    api_docs,
    api_export_csv,
    api_recommendations,
    api_tts,
    dashboard,
    offline_page,
)
from .reports import (  # noqa: F401
    api_accidents,
    api_accidents_create,
    report_form,
)
from .stats import (  # noqa: F401
    api_heatmap,
    api_hourly,
    api_junctions,
    api_monthly,
    api_severity,
    api_stats_hourly,
    api_stats_junctions,
    api_stats_monthly,
    api_stats_severity,
    api_stats_summary,
    api_stats_vehicles,
    api_summary,
    api_vehicles,
)
from .telegram import (  # noqa: F401
    api_telegram_webhook,
)
