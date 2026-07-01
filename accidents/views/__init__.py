"""
Views package — split by concern for maintainability.

All public views are re-exported here so ``from . import views`` continues
to work in urls.py and tests.
"""
from accidents.decorators import _rate_log  # noqa: F401 — kept for test backward compat

from .public import (               # noqa: F401
    dashboard,
    offline_page,
    api_docs,
    api_export_csv,
    api_recommendations,
    _build_recommendation_engine_context,
    _rule_based_recommendations,
    _ai_recommendations,
)
from .authority_views import (      # noqa: F401
    authority,
    api_authority_filter,
    api_authority_export_csv,
)
from .reports import (              # noqa: F401
    report_form,
    api_accidents,
    api_accidents_create,
)
from .stats import (                # noqa: F401
    api_stats_severity,
    api_stats_vehicles,
    api_stats_monthly,
    api_stats_hourly,
    api_stats_junctions,
    api_stats_summary,
    api_heatmap,
    api_vehicles,
    api_severity,
    api_monthly,
    api_hourly,
    api_junctions,
    api_summary,
)
from .telegram import (            # noqa: F401
    api_telegram_webhook,
)
from .pdf import (                 # noqa: F401
    api_monthly_report,
)
