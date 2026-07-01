"""
Views: public dashboard, public report form, JSON API, authority dashboard.

Endpoint paths follow the PRD §6 minimum set:
  GET  /api/accidents               (list / heatmap)
  POST /api/accidents               (submit a new report, rate-limited)
  GET  /api/stats/severity          (counts per severity)
  GET  /api/stats/vehicles          (counts per vehicle type, exploded from list)
  GET  /api/stats/monthly           (counts per month)
  GET  /api/stats/hourly            (counts per hour-of-day, 0-23)
  GET  /api/stats/junctions         (top N junctions by count, ?limit=10)
  GET  /api/stats/summary           (KPI bundle for dashboard)
  GET  /api/export.csv              (public CSV download — v1.1)
  GET  /api/recommendations/        (AI-powered recommendations — v1.1)

Old paths (/api/severity/, /api/heatmap/ etc.) are kept as aliases
so the existing dashboard.html still works.
"""
import csv
import json
import logging
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.core.validators import ValidationError
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .models import Accident, Junction, VEHICLE_CHOICES, SEVERITY_CHOICES, REPORTER_CHOICES

logger = logging.getLogger(__name__)

# --- simple in-memory rate limiter for POST /api/accidents (PRD §7) ---
# Per-IP, sliding 60-second window, max 5 submissions/min.
_rate_log: dict[str, list[float]] = defaultdict(list)
RATE_WINDOW_SEC = 60
RATE_MAX = 5


def _rate_check(ip: str) -> bool:
    now = time.monotonic()
    bucket = [t for t in _rate_log[ip] if now - t < RATE_WINDOW_SEC]
    if len(bucket) >= RATE_MAX:
        _rate_log[ip] = bucket
        return False
    bucket.append(now)
    _rate_log[ip] = bucket
    return True


# ---------- Public dashboard ----------
def dashboard(request):
    qs = Accident.objects.all()
    first = qs.first()
    context = {
        "total": qs.count(),
        "fatal_count": qs.filter(severity="fatal").count(),
        "verified_count": qs.filter(verified=True).count(),
        "junction_count": Junction.objects.count(),
        "center": [first.lat if first else -6.7924, first.lng if first else 39.2083],
    }
    return render(request, "accidents/dashboard.html", context)


# ---------- Submission form (HTML, police & community) ----------
def report_form(request):
    error = None
    if request.method == "POST":
        ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "0.0.0.0"))
        if not _rate_check(ip):
            return HttpResponse("Too many submissions. Please wait a minute.", status=429)
        try:
            _save_from_payload(request.POST)
            return redirect("dashboard")
        except (ValueError, TypeError, ValidationError) as e:
            error = str(e) if isinstance(e, ValueError) else "; ".join(e.messages)
    return render(request, "accidents/report.html", {"error": error})


def _save_from_payload(payload):
    """Shared validation + create path for HTML form and JSON API."""
    severity = (payload.get("severity") or "").strip()
    reporter = (payload.get("reporter_type") or payload.get("reported_by") or "community").strip()
    occurred_raw = payload.get("occurred_at") or payload.get("datetime")

    if severity not in dict(SEVERITY_CHOICES):
        raise ValueError(f"invalid severity: {severity!r}")
    if reporter not in dict(REPORTER_CHOICES):
        raise ValueError(f"invalid reporter_type: {reporter!r}")

    if "lat" in payload or "latitude" in payload:
        lat = float(payload.get("lat", payload.get("latitude")))
    else:
        raise ValueError("missing required field: lat")
    if "lng" in payload or "longitude" in payload:
        lng = float(payload.get("lng", payload.get("longitude")))
    else:
        raise ValueError("missing required field: lng")
    # Range check (PRD §7: server-side bounds)
    if not (-7.5 <= lat <= -6.0):
        raise ValueError(f"latitude {lat} outside Dar es Salaam bbox (-7.5..-6.0)")
    if not (38.5 <= lng <= 39.7):
        raise ValueError(f"longitude {lng} outside Dar es Salaam bbox (38.5..39.7)")

    # vehicle_types: accept csv string OR JSON list
    vt_raw = payload.get("vehicle_types")
    if vt_raw is None:
        vt_raw = payload.get("vehicle_type") or "car"
    if isinstance(vt_raw, str):
        try:
            vt = json.loads(vt_raw)
        except json.JSONDecodeError:
            vt = [v.strip() for v in vt_raw.split(",") if v.strip()]
    else:
        vt = list(vt_raw)
    if not vt:
        vt = ["car"]
    for v in vt:
        if v not in dict(VEHICLE_CHOICES):
            raise ValueError(f"unknown vehicle_types value: {v!r}")

    if occurred_raw:
        try:
            occurred_at = datetime.fromisoformat(str(occurred_raw).replace("Z", "+00:00"))
        except ValueError:
            occurred_at = timezone.now()
    else:
        occurred_at = timezone.now()

    # Casualty bound checks
    casualties = int(payload.get("casualties") or 0)
    fatalities = int(payload.get("fatalities") or 0)
    injuries = int(payload.get("injuries") or 0)
    if not (0 <= fatalities <= casualties):
        raise ValueError("fatalities must be between 0 and casualties")
    if not (0 <= injuries <= casualties):
        raise ValueError("injuries must be between 0 and casualties")

    junction_name = (payload.get("junction_name") or "").strip()
    junction = None
    if junction_name:
        junction, _ = Junction.objects.get_or_create(
            name=junction_name,
            defaults={"lat": lat, "lng": lng},
        )

    return Accident.objects.create(
        lat=lat, lng=lng,
        junction_name=junction_name[:120],
        junction=junction,
        occurred_at=occurred_at,
        severity=severity,
        vehicle_types=vt,
        reporter_type=reporter,
        casualties=casualties,
        fatalities=fatalities,
        injuries=injuries,
        description=(payload.get("description") or "")[:5000],
        weather=(payload.get("weather") or "")[:60],
        road_condition=(payload.get("road_condition") or "")[:60],
        contact=(payload.get("contact") or "")[:120],
        source_notes=(payload.get("source_notes") or "")[:1000],
        verified=payload.get("verified") in (True, "true", "True", "1", "on"),
    )


# ---------- Authority dashboard ----------
def authority(request):
    qs = Accident.objects.all()
    by_hour = qs.annotate(hour=TruncMonth("occurred_at")).values("hour").annotate(c=Count("id"))
    hour_profile = [{"hour": 0, "count": 0} for _ in range(24)]
    return render(request, "accidents/authority.html", {
        "total": qs.count(),
        "fatal": qs.filter(severity="fatal").count(),
        "hour_profile": hour_profile,
    })


# ---------- JSON endpoints (PRD §6) ----------
@require_GET
def api_accidents(_request):
    """GET /api/accidents — list of all accidents for the heatmap + map."""
    qs = Accident.objects.all().values(
        "id", "lat", "lng", "severity", "vehicle_types", "junction_name",
        "occurred_at", "casualties", "fatalities",
    )
    data = []
    weight = {"minor": 1, "serious": 2, "critical": 3, "fatal": 4}
    for a in qs:
        data.append({
            **a,
            "occurred_at": a["occurred_at"].isoformat(),
            "address": a.get("junction_name", ""),       # backward-compat alias
            "intensity": weight.get(a["severity"], 1),  # for the heatmap
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_POST
def api_accidents_create(request):
    """POST /api/accidents — submit a new report (rate-limited, JSON or form).

    Accepts:
      - application/json  -> {"lat":..., "lng":..., ...}
      - application/x-www-form-urlencoded -> standard form
    Returns 201 with the new record id, 400 on validation, 429 on rate limit.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "0.0.0.0"))
    if not _rate_check(ip):
        return JsonResponse({"error": "rate_limited", "detail": "max 5 submissions per minute"}, status=429)

    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body or b"{}")
        except json.JSONDecodeError as e:
            return JsonResponse({"error": "bad_json", "detail": str(e)}, status=400)
    else:
        payload = request.POST

    try:
        a = _save_from_payload(payload)
    except (ValueError, ValidationError) as e:
        msg = str(e) if isinstance(e, ValueError) else "; ".join(e.messages)
        return JsonResponse({"error": "validation", "detail": msg}, status=400)

    return JsonResponse({
        "id": a.id, "created": True, "severity": a.severity,
        "vehicle_types": a.vehicle_types, "lat": a.lat, "lng": a.lng,
    }, status=201)


@require_GET
def api_stats_severity(_request):
    qs = Accident.objects.values("severity").annotate(c=Count("id"))
    return JsonResponse({r["severity"]: r["c"] for r in qs}, safe=False)


@require_GET
def api_stats_vehicles(_request):
    """Explode vehicle_types list into per-type counts."""
    counter = Counter()
    for vt in Accident.objects.values_list("vehicle_types", flat=True):
        for v in vt or []:
            counter[v] += 1
    return JsonResponse(dict(counter), safe=False)


@require_GET
def api_stats_monthly(_request):
    qs = (Accident.objects
          .annotate(month=TruncMonth("occurred_at"))
          .values("month").annotate(c=Count("id"))
          .order_by("month"))
    data = [{"month": r["month"].strftime("%Y-%m"), "count": r["c"]} for r in qs]
    return JsonResponse(data, safe=False)


@require_GET
def api_stats_hourly(_request):
    buckets = Counter(a.occurred_at.hour for a in Accident.objects.all())
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
                                    "lat": 0.0, "lng": 0.0, "name": ""})
    for a in Accident.objects.exclude(junction_name=""):
        b = buckets[a.junction_name]
        b["name"] = a.junction_name
        b["count"] += 1
        b["fatalities"] += a.fatalities
        b["casualties"] += a.casualties
        b["lat"] = a.lat
        b["lng"] = a.lng
    ranked = sorted(buckets.values(), key=lambda x: x["count"], reverse=True)[:limit]
    return JsonResponse(ranked, safe=False)


@require_GET
def api_stats_summary(_request):
    qs = Accident.objects.all()
    return JsonResponse({
        "total": qs.count(),
        "fatal": qs.filter(severity="fatal").count(),
        "serious": qs.filter(severity="serious").count(),
        "minor": qs.filter(severity="minor").count(),
        "critical": qs.filter(severity="critical").count(),
        "verified": qs.filter(verified=True).count(),
        "total_fatalities": qs.aggregate(s=Sum("fatalities"))["s"] or 0,
        "total_casualties": qs.aggregate(s=Sum("casualties"))["s"] or 0,
        "junction_count": Junction.objects.count(),
    })


# ---------- Legacy aliases (so the existing dashboard.html keeps working) ----------
def api_heatmap(_request):
    """[[lat, lng, intensity], ...] for Leaflet.heat."""
    weight = {"minor": 1, "serious": 2, "critical": 3, "fatal": 4}
    pts = []
    for a in Accident.objects.all().values("lat", "lng", "severity"):
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


# ===================== v1.1 NEW FEATURES =====================

@require_GET
def api_export_csv(_request):
    """GET /api/export.csv — public CSV download of all accident records.

    Columns: id, occurred_at, severity, vehicle_types, junction_name,
             lat, lng, casualties, fatalities, injuries, weather, road_condition,
             reporter_type, verified, description
    """
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="roadsafety_dar_{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "id", "occurred_at", "severity", "vehicle_types",
        "junction_name", "lat", "lng", "casualties", "fatalities", "injuries",
        "weather", "road_condition", "reporter_type", "verified", "description",
    ])

    for a in Accident.objects.all().order_by("-occurred_at"):
        writer.writerow([
            a.id,
            a.occurred_at.isoformat(),
            a.severity,
            ",".join(a.vehicle_types or []),
            a.junction_name,
            a.lat,
            a.lng,
            a.casualties,
            a.fatalities,
            a.injuries,
            a.weather,
            a.road_condition,
            a.reporter_type,
            "yes" if a.verified else "no",
            (a.description or "").replace("\n", " ").replace("\r", " "),
        ])

    logger.info("CSV export generated: %d records", Accident.objects.count())
    return response


def _build_recommendation_engine_context():
    """Aggregate stats used by the AI recommender (and the rule engine fallback)."""
    qs = Accident.objects.all()
    total = qs.count()
    if total == 0:
        return None

    # Junction aggregates
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

    # Hour-of-day profile
    hourly = Counter(a.occurred_at.hour for a in qs)
    peak_hours = sorted(hourly.items(), key=lambda x: -x[1])[:3]

    # Vehicle type breakdown
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

    # Top-3 worst junctions
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
    """Try to enrich recommendations with LLM-generated narrative.
    Uses OpenRouter if OPENROUTER_API_KEY is set in env, else falls back gracefully.
    """
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
    """GET /api/recommendations/ — AI + rule-based intervention suggestions.

    Always returns rule-based recs; if OpenRouter key is set, also returns
    an `ai_narrative` summary.
    """
    ctx = _build_recommendation_engine_context()
    recs = _rule_based_recommendations(ctx)
    ai = _ai_recommendations(ctx)
    return JsonResponse({
        "recommendations": recs,
        "ai_narrative": ai[0]["ai_narrative"] if ai else None,
        "generated_at": timezone.now().isoformat(),
    }, safe=False)


# ===================== END v1.1 FEATURES =====================
