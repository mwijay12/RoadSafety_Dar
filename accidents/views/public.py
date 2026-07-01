"""
Public HTML pages + CSV export + recommendation engine.
"""
import csv
import json
import logging
from collections import Counter, defaultdict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from ..decorators import police_or_admin_required
from ..models import Accident, Junction, visible_accidents, visible_junctions

logger = logging.getLogger(__name__)


def dashboard(request):
    qs = visible_accidents()
    first = qs.first()
    context = {
        "total": qs.count(),
        "fatal_count": qs.filter(severity="fatal").count(),
        "critical_count": qs.filter(severity="critical").count(),
        "serious_count": qs.filter(severity="serious").count(),
        "minor_count": qs.filter(severity="minor").count(),
        "verified_count": qs.filter(verified=True).count(),
        "junction_count": visible_junctions().count(),
        "center": [first.lat if first else -6.7924, first.lng if first else 39.2083],
    }
    return render(request, "accidents/dashboard.html", context)


def offline_page(request):
    """PWA offline fallback."""
    return render(request, "accidents/offline.html")


def api_docs(request):
    """GET /api/docs/ — human-readable API documentation page."""
    endpoints = [
        ("GET", "/api/accidents", "None", "List all accidents for map/heatmap"),
        ("POST", "/api/accidents", "None", "Submit a new accident report (rate-limited)"),
        ("GET", "/api/stats/severity", "None", "Counts per severity level"),
        ("GET", "/api/stats/vehicles", "None", "Counts per vehicle type"),
        ("GET", "/api/stats/monthly", "None", "Monthly accident trend"),
        ("GET", "/api/stats/hourly", "None", "Hour-of-day accident distribution"),
        ("GET", "/api/stats/junctions", "None", "Top N junctions by accident count (?limit=10)"),
        ("GET", "/api/stats/summary", "None", "KPI bundle for dashboard"),
        ("GET", "/api/export.csv", "None", "Public CSV download of all records"),
        ("GET", "/api/recommendations", "None", "Rule-based + AI recommendations"),
        ("GET", "/api/report/monthly.pdf", "None", "Monthly PDF report (?month=YYYY-MM)"),
        ("POST", "/api/telegram/webhook", "None", "Telegram bot webhook"),
        ("GET", "/api/authority/filter", "Police/Admin", "Filtered KPI for authority dashboard"),
        ("GET", "/api/authority/export/csv", "Police/Admin", "Filtered CSV export for authorities"),
    ]
    return render(request, "accidents/api_docs.html", {"endpoints": endpoints})


@require_GET
def api_export_csv(_request):
    """GET /api/export.csv — public CSV download of all accident records."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="roadsafety_dar_{timestamp}.csv"'

    writer = csv.writer(response)
    field_order = [
        "id", "occurred_at", "severity", "vehicle_types",
        "junction_name", "lat", "lng", "casualties", "fatalities", "injuries",
        "weather", "road_condition", "reporter_type", "verified", "description",
    ]
    writer.writerow(field_order)

    for a in visible_accidents().order_by("-occurred_at"):
        row = {
            "id": a.id,
            "occurred_at": a.occurred_at.isoformat(),
            "severity": a.severity,
            "vehicle_types": ",".join(a.vehicle_types or []),
            "junction_name": a.junction_name,
            "lat": a.lat,
            "lng": a.lng,
            "casualties": a.casualties,
            "fatalities": a.fatalities,
            "injuries": a.injuries,
            "weather": a.weather,
            "road_condition": a.road_condition,
            "reporter_type": a.reporter_type,
            "verified": "yes" if a.verified else "no",
            "description": (a.description or "").replace("\n", " ").replace("\r", " "),
        }
        writer.writerow([row[k] for k in field_order])

    logger.info("CSV export generated: %d records", visible_accidents().count())
    return response


# ===================== Recommendation Engine =====================

def _build_recommendation_engine_context():
    """Aggregate stats used by the AI recommender (and the rule engine fallback)."""
    qs = visible_accidents()
    total = qs.count()
    if total == 0:
        return None

    junction_buckets = defaultdict(lambda: {
        "count": 0, "fatalities": 0, "casualties": 0,
        "vehicle_types": Counter(), "hourly": Counter(), "name": "",
    })
    for a in qs.exclude(junction_name=""):
        b = junction_buckets[a.junction_name]
        b["name"] = a.junction_name
        b["count"] += 1
        b["fatalities"] += a.fatalities
        b["casualties"] += a.casualties
        for v in (a.vehicle_types or []):
            b["vehicle_types"][v] += 1
        b["hourly"][a.occurred_at.hour] += 1

    hourly = Counter(a.occurred_at.hour for a in qs)
    peak_hours = sorted(hourly.items(), key=lambda x: -x[1])[:3]

    vehicle_counter = Counter()
    for vt in qs.values_list("vehicle_types", flat=True):
        for v in vt or []:
            vehicle_counter[v] += 1

    return {
        "total": total,
        "fatal": qs.filter(severity="fatal").count(),
        "junction_buckets": dict(junction_buckets),
        "peak_hours": peak_hours,
        "vehicle_counter": dict(vehicle_counter),
    }


def _rule_based_recommendations(ctx):
    """Fallback: rule-based recommendations when LLM is unavailable."""
    recs = []
    if ctx is None:
        return recs

    top_junctions = sorted(
        ctx["junction_buckets"].values(), key=lambda b: -b["count"]
    )[:3]
    for b in top_junctions:
        peak_h = sorted(b["hourly"].items(), key=lambda x: -x[1])[:1]
        peak_hour = peak_h[0][0] if peak_h else None
        top_vehicle = b["vehicle_types"].most_common(1)
        vehicle = top_vehicle[0][0] if top_vehicle else "vehicle"

        actions = []
        if b["fatalities"] >= 3:
            actions.append(f"⚠ {b['fatalities']} fatalities recorded — install speed camera immediately")
        if peak_hour is not None:
            actions.append(
                f"Deploy traffic police between {peak_hour:02d}:00–{(peak_hour+2)%24:02d}:00 "
                f"(peak accident window)"
            )
        if vehicle in ("motorcycle", "bicycle"):
            actions.append("Targeted bodaboda helmet & lane discipline enforcement")
        elif vehicle in ("bus", "truck"):
            actions.append("Enforce PSV speed governors and loading limits")
        elif vehicle == "pedestrian":
            actions.append("Install zebra crossing + pedestrian signal at junction")
        actions.append("Improve road signage and reflective markings")
        actions.append("Coordinate with TANROADS for engineering review")

        recs.append({
            "junction": b["name"],
            "incidents": b["count"],
            "fatalities": b["fatalities"],
            "casualties": b["casualties"],
            "peak_hour": peak_hour,
            "top_vehicle": vehicle,
            "risk_level": "HIGH" if b["fatalities"] >= 3 else ("MEDIUM" if b["count"] >= 5 else "LOW"),
            "actions": actions,
            "source": "rule-engine",
        })

    return recs


def _ai_recommendations(ctx):
    """Try to enrich recommendations with LLM-generated narrative."""
    if ctx is None:
        return []

    api_key = getattr(settings, "OPENROUTER_API_KEY", None) or __import__("os").environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return []

    try:
        import urllib.request
        top_junctions = sorted(
            ctx["junction_buckets"].values(), key=lambda b: -b["count"]
        )[:3]
        if not top_junctions:
            return []

        prompt = (
            "You are a road safety analyst for Dar es Salaam, Tanzania. "
            "Given these accident stats, suggest 1-2 SHORT (max 18 words) "
            "engineering interventions for each junction. Be specific and practical. "
            "Output as bullet points only, no preamble.\n\n"
        )
        for b in top_junctions:
            peak_h = sorted(b["hourly"].items(), key=lambda x: -x[1])[:1]
            top_v = b["vehicle_types"].most_common(1)
            prompt += (
                f"- {b['name']}: {b['count']} incidents, {b['fatalities']} deaths, "
                f"peak {peak_h[0][0] if peak_h else '?'}:00, "
                f"top vehicle: {top_v[0][0] if top_v else 'mixed'}\n"
            )

        body = json.dumps({
            "model": "minimax/minimax-m3",
            "messages": [
                {"role": "system", "content": "You are a road safety expert."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 400,
        }).encode()

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return [{"ai_narrative": data["choices"][0]["message"]["content"]}]
    except Exception as e:
        logger.warning("AI recommendation failed: %s", e)
        return []


@require_GET
def api_recommendations(_request):
    """GET /api/recommendations/ — AI + rule-based intervention suggestions."""
    ctx = _build_recommendation_engine_context()
    recs = _rule_based_recommendations(ctx)
    ai = _ai_recommendations(ctx)
    return JsonResponse({
        "recommendations": recs,
        "ai_narrative": ai[0]["ai_narrative"] if ai else None,
        "generated_at": timezone.now().isoformat(),
    }, safe=False)
