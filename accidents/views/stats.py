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

from ..models import Accident, Junction, visible_accidents, visible_junctions

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
    qs = (visible_accidents()
          .annotate(month=TruncMonth("occurred_at"))
          .values("month").annotate(c=Count("id"))
          .order_by("month"))
    data = [{"month": r["month"].strftime("%Y-%m"), "count": r["c"]} for r in qs]
    return JsonResponse(data, safe=False)


@require_GET
def api_stats_hourly(_request):
    buckets = Counter(a.occurred_at.hour for a in visible_accidents())
    data = [{"hour": h, "count": buckets.get(h, 0)} for h in range(24)]
    return JsonResponse(data, safe=False)


@require_GET
def api_stats_junctions(request):
    """Top N junctions by accident count. ?limit=10 (default), max 100."""
    try:
        limit = int(request.GET.get("limit", 10))
    except ValueError:
        limit = 10
    limit = max(1, min(100, limit))

    buckets = defaultdict(lambda: {"count": 0, "fatalities": 0, "casualties": 0,
                                    "lat": 0.0, "lng": 0.0, "name": "", "district": ""})
    for a in visible_accidents().exclude(junction_name=""):
        b = buckets[a.junction_name]
        b["name"] = a.junction_name
        b["count"] += 1
        b["fatalities"] += a.fatalities
        b["casualties"] += a.casualties
        b["lat"] = a.lat
        b["lng"] = a.lng
        if not b.get("district") and a.junction:
            b["district"] = a.junction.district
    ranked = sorted(buckets.values(), key=lambda x: x["count"], reverse=True)[:limit]
    return JsonResponse(ranked, safe=False)


@require_GET
def api_stats_summary(_request):
    qs = visible_accidents()
    return JsonResponse({
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
    })


# ===================== Legacy aliases =====================

def api_heatmap(_request):
    """[[lat, lng, intensity], ...] for Leaflet.heat."""
    weight = {"minor": 1, "serious": 2, "critical": 3, "fatal": 4}
    pts = []
    for a in visible_accidents().values("lat", "lng", "severity"):
        pts.append([a["lat"], a["lng"], weight.get(a["severity"], 1)])
    return JsonResponse(pts, safe=False)


def api_vehicles(_request):
    return api_stats_vehicles(_request)


def api_severity(_request):
    return api_stats_severity(_request)


def api_monthly(_request):
    return api_stats_monthly(_request)


def api_hourly(_request):
    return api_stats_hourly(_request)


def api_junctions(_request):
    return api_stats_junctions(_request)


def api_summary(_request):
    return api_stats_summary(_request)
