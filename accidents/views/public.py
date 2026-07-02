"""
Public HTML pages + CSV export + recommendation engine.
"""

import csv
import json
import logging
from collections import Counter, defaultdict

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from ..models import visible_accidents, visible_junctions

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
        (
            "GET",
            "/api/authority/export/csv",
            "Police/Admin",
            "Filtered CSV export for authorities",
        ),
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
        "id",
        "occurred_at",
        "severity",
        "vehicle_types",
        "junction_name",
        "lat",
        "lng",
        "casualties",
        "fatalities",
        "injuries",
        "weather",
        "road_condition",
        "reporter_type",
        "verified",
        "description",
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

    junction_buckets = defaultdict(
        lambda: {
            "count": 0,
            "fatalities": 0,
            "casualties": 0,
            "vehicle_types": Counter(),
            "hourly": Counter(),
            "name": "",
        }
    )
    for a in qs.exclude(junction_name=""):
        b = junction_buckets[a.junction_name]
        b["name"] = a.junction_name
        b["count"] += 1
        b["fatalities"] += a.fatalities
        b["casualties"] += a.casualties
        for v in a.vehicle_types or []:
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

    top_junctions = sorted(ctx["junction_buckets"].values(), key=lambda b: -b["count"])[:3]
    for b in top_junctions:
        peak_h = sorted(b["hourly"].items(), key=lambda x: -x[1])[:1]
        peak_hour = peak_h[0][0] if peak_h else None
        top_vehicle = b["vehicle_types"].most_common(1)
        vehicle = top_vehicle[0][0] if top_vehicle else "vehicle"

        actions = []
        if b["fatalities"] >= 3:
            actions.append(
                f"⚠ {b['fatalities']} fatalities recorded — install speed camera immediately"
            )
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

        recs.append(
            {
                "junction": b["name"],
                "incidents": b["count"],
                "fatalities": b["fatalities"],
                "casualties": b["casualties"],
                "peak_hour": peak_hour,
                "top_vehicle": vehicle,
                "risk_level": "HIGH"
                if b["fatalities"] >= 3
                else ("MEDIUM" if b["count"] >= 5 else "LOW"),
                "actions": actions,
                "source": "rule-engine",
            }
        )

    return recs


def _ai_recommendations(ctx):
    """Try to enrich recommendations with LLM-generated narrative (Groq primary, OpenRouter fallback)."""
    if ctx is None:
        return []

    top_junctions = sorted(ctx["junction_buckets"].values(), key=lambda b: -b["count"])[:3]
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

    # Fallback chain:
    # 1. Groq (Primary)
    # 2. OpenRouter (Secondary / Legacy)
    providers = []

    import os

    groq_key = getattr(settings, "GROQ_API_KEY", None) or os.environ.get("GROQ_API_KEY")
    if groq_key:
        providers.append(
            {
                "name": "Groq",
                "url": getattr(settings, "GROQ_API_BASE", None)
                or "https://api.groq.com/openai/v1/chat/completions",
                "key": groq_key,
                "model": getattr(settings, "GROQ_MODEL", None) or "llama-3.3-70b-versatile",
            }
        )

    openrouter_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.environ.get(
        "OPENROUTER_API_KEY"
    )
    if openrouter_key:
        providers.append(
            {
                "name": "OpenRouter",
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "key": openrouter_key,
                "model": getattr(settings, "OPENROUTER_MODEL", None) or "minimax/minimax-m3",
            }
        )

    import urllib.request  # noqa: S310

    for provider in providers:
        try:
            logger.info("Attempting AI recommendations via %s...", provider["name"])

            url = provider["url"]
            if "chat/completions" not in url:
                url = url.rstrip("/") + "/chat/completions"

            body = json.dumps(
                {
                    "model": provider["model"],
                    "messages": [
                        {"role": "system", "content": "You are a road safety expert."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 400,
                }
            ).encode()

            req = urllib.request.Request(  # noqa: S310
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {provider['key']}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as r:  # noqa: S310
                data = json.loads(r.read())

            content = data["choices"][0]["message"]["content"].strip()
            if content:
                logger.info("AI recommendations successfully generated via %s", provider["name"])
                return [{"ai_narrative": content}]
        except Exception as e:
            logger.warning("AI recommendation via %s failed: %s", provider["name"], e)

    logger.warning(
        "All AI providers failed or none configured. Using rule-based fallback narrative."
    )
    fallback_lines = []
    for r in _rule_based_recommendations(ctx):
        actions_str = ", ".join(r["actions"][:2])
        fallback_lines.append(f"- {r['junction']}: {actions_str}")
    return [{"ai_narrative": "\n".join(fallback_lines)}]


@require_GET
def api_recommendations(_request):
    """GET /api/recommendations/ — AI + rule-based intervention suggestions."""
    ctx = _build_recommendation_engine_context()
    recs = _rule_based_recommendations(ctx)
    ai = _ai_recommendations(ctx)
    return JsonResponse(
        {
            "recommendations": recs,
            "ai_narrative": ai[0]["ai_narrative"] if ai else None,
            "generated_at": timezone.now().isoformat(),
        },
        safe=False,
    )


@require_GET
def api_tts(request):
    """GET /api/tts/ — Text-to-Speech using ElevenLabs Rachel voice."""
    text = request.GET.get("text", "").strip()
    if not text:
        return HttpResponse("Missing 'text' parameter.", status=400)

    # Limit text length to conserve ElevenLabs character quota
    text = text[:300]

    api_key = getattr(settings, "ELEVENLABS_API_KEY", "")
    if not api_key:
        return HttpResponse("ElevenLabs API key not configured.", status=503)

    try:
        import urllib.request  # noqa: S310

        # Rachel voice ID: 21m00Tcm4TlvDq8ikWAM
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        body = json.dumps(
            {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }
        ).encode()

        req = urllib.request.Request(  # noqa: S310
            url,
            data=body,
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "accept": "audio/mpeg",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310
            audio_data = r.read()

        response = HttpResponse(audio_data, content_type="audio/mpeg")
        # Cache identical responses for 2 hours
        response["Cache-Control"] = "public, max-age=7200"
        return response
    except Exception as e:
        logger.error("TTS generation failed: %s", e)
        return HttpResponse(f"TTS service unavailable: {e}", status=500)


def my_reports(request):
    """
    GET /my-reports/
    
    Shows all accident reports submitted by the currently logged-in user.
    Displays verification status, upvote count, and report details.
    Login required — redirects to /auth/login/ if not authenticated.
    """
    from ..decorators import login_required_custom
    from ..models import Accident, AccidentUpvote

    # Apply decorator inline to keep things clean
    @login_required_custom
    def _inner(req):
        user_accidents = (
            Accident.objects
            .filter(submitted_by=req.user)
            .order_by("-reported_at")
            .select_related("junction")
        )

        # Summary stats for the user
        total = user_accidents.count()
        verified_count = user_accidents.filter(verified=True).count()
        total_upvotes = sum(a.upvote_count for a in user_accidents)
        
        # Upvotes the user has given to other reports
        given_upvotes = (
            AccidentUpvote.objects.filter(user=req.user)
            .select_related("accident")
            .order_by("-created_at")[:10]
        )

        return render(req, "accidents/my_reports.html", {
            "accidents": user_accidents,
            "total": total,
            "verified_count": verified_count,
            "pending_count": total - verified_count,
            "total_upvotes": total_upvotes,
            "given_upvotes": given_upvotes,
        })
    return _inner(request)
