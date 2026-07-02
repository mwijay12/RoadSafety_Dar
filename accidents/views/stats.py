"""
Statistics API endpoints — all read-only, no auth required.
"""

import logging
from collections import Counter, defaultdict

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from ..models import visible_accidents, visible_junctions
from accidents.services.spatial import junction_severity_scores, accidents_in_bbox

logger = logging.getLogger(__name__)


@require_GET
def api_stats_severity(_request):
    qs = visible_accidents().values("severity").annotate(c=Count("id"))
    return JsonResponse({r["severity"]: r["c"] for r in qs}, safe=False)


@require_GET
def api_stats_vehicles(_request):
    """Explode vehicle_types list into per-type counts."""
    counter = Counter()
    for vt in visible_accidents().values_list("vehicle_types", flat=True):
        for v in vt or []:
            counter[v] += 1
    return JsonResponse(dict(counter), safe=False)


@require_GET
def api_stats_monthly(_request):
    qs = (
        visible_accidents()
        .annotate(month=TruncMonth("occurred_at"))
        .values("month")
        .annotate(c=Count("id"))
        .order_by("month")
    )
    data = [{"month": r["month"].strftime("%Y-%m"), "count": r["c"]} for r in qs]
    return JsonResponse(data, safe=False)


@require_GET
def api_stats_hourly(_request):
    buckets = Counter(a.occurred_at.hour for a in visible_accidents())
    data = [{"hour": h, "count": buckets.get(h, 0)} for h in range(24)]
    return JsonResponse(data, safe=False)


@require_GET
def api_stats_junctions(request):
    """Top N junctions by severity-weighted score. ?limit=10 (default), max 100."""
    try:
        limit = int(request.GET.get("limit", 10))
    except ValueError:
        limit = 10
    limit = max(1, min(100, limit))

    data = junction_severity_scores()[:limit]
    return JsonResponse(data, safe=False)


@require_GET
def api_stats_summary(request):
    qs = visible_accidents()
    return JsonResponse(
        {
            "total": qs.count(),
            "total_reports": qs.count(),
            "fatal": qs.filter(severity="fatal").count(),
            "serious": qs.filter(severity="serious").count(),
            "minor": qs.filter(severity="minor").count(),
            "critical": qs.filter(severity="critical").count(),
            "verified": qs.filter(verified=True).count(),
            "total_fatalities": qs.aggregate(s=Sum("fatalities"))["s"] or 0,
            "total_casualties": qs.aggregate(s=Sum("casualties"))["s"] or 0,
            "junction_count": visible_junctions().count(),
            "service": "roadsafety-dar",
            "server_time": timezone.now().isoformat(),
            "weighted_junctions": junction_severity_scores()[:5],
        }
    )


# ===================== Legacy aliases =====================


def api_heatmap(request):
    """
    GET /api/heatmap/

    Returns trust-weighted heatmap points for Leaflet.heat.

    Optional viewport filter:
        ?bbox=south,west,north,east
    """
    SEVERITY_WEIGHT = {"minor": 1, "serious": 2, "critical": 3, "fatal": 4}
    TRUST_MULTIPLIER = {"anonymous": 1.0, "community": 1.4, "verified": 2.0}

    bbox_param = request.GET.get("bbox", "")
    if bbox_param:
        try:
            south, west, north, east = [float(x) for x in bbox_param.split(",")]
            raw = accidents_in_bbox(south, west, north, east)
        except (ValueError, TypeError):
            raw = list(visible_accidents().values(
                "lat", "lng", "severity", "trust_level", "upvote_count"
            ))
    else:
        raw = list(visible_accidents().values(
            "lat", "lng", "severity", "trust_level", "upvote_count"
        ))

    points = []
    for a in raw:
        base = SEVERITY_WEIGHT.get(a["severity"], 1)
        multiplier = TRUST_MULTIPLIER.get(a.get("trust_level", "anonymous"), 1.0)
        upvote_bonus = min((a.get("upvote_count") or 0) * 0.15, 1.5)
        intensity = min(base * multiplier + upvote_bonus, 4)
        points.append([a["lat"], a["lng"], round(intensity, 2)])

    return JsonResponse(points, safe=False)


def api_vehicles(request):
    return api_stats_vehicles(request)


def api_severity(request):
    return api_stats_severity(request)


def api_monthly(request):
    return api_stats_monthly(request)


def api_hourly(request):
    return api_stats_hourly(request)


def api_junctions(request):
    return api_stats_junctions(request)


def api_summary(request):
    return api_stats_summary(request)
