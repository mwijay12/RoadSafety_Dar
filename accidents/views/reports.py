"""
Report submission views — HTML form + JSON API.
"""

import json
import logging

from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from ..decorators import get_client_ip, rate_limit, login_required_custom
from ..forms import AccidentForm
from ..models import Accident, AccidentUpvote, visible_accidents
from accidents.services.spatial import accidents_within_radius

logger = logging.getLogger(__name__)


def report_form(request):
    form = AccidentForm()
    if request.method == "POST":
        if not _rate_check_wrapper(request):
            return HttpResponse("Too many submissions. Please wait a minute.", status=429)
        form = AccidentForm(request.POST, user=request.user)
        if form.is_valid():
            accident = form.save(commit=False)
            if request.user.is_authenticated:
                accident.submitted_by = request.user
            accident.save()
            return redirect("dashboard")
    return render(request, "accidents/report.html", {"form": form})


def _rate_check_wrapper(request):
    """Inline rate check for the HTML form (returns bool)."""
    from ..decorators import _rate_check

    ip = get_client_ip(request)
    return _rate_check(ip)


def api_accidents(request):
    """GET /api/accidents — list of all accidents for heatmap + map."""
    user = request.user
    
    # Get IDs of accidents this user upvoted/submitted (empty set if anonymous)
    user_upvoted_ids = set()
    user_submitted_ids = set()
    
    if user.is_authenticated:
        user_upvoted_ids = set(
            AccidentUpvote.objects.filter(user=user)
            .values_list("accident_id", flat=True)
        )
        user_submitted_ids = set(
            Accident.objects.filter(submitted_by=user)
            .values_list("id", flat=True)
        )

    qs = visible_accidents().values(
        "id",
        "lat",
        "lng",
        "severity",
        "vehicle_types",
        "district",
        "junction_name",
        "occurred_at",
        "casualties",
        "fatalities",
        "verified",
        "trust_level",
        "upvote_count",
        "reported_at",
        "verification_status",
        "official_notes",
        "photo_url",
    ).order_by("-occurred_at")

    data = []
    weight = {"minor": 1, "serious": 2, "critical": 3, "fatal": 4}
    for a in qs:
        item = {
            **a,
            "submitted_by_me": a["id"] in user_submitted_ids,
            "user_has_upvoted": a["id"] in user_upvoted_ids,
            "address": a.get("junction_name") or "",
            "intensity": weight.get(a["severity"], 1),
        }
        if item["occurred_at"]:
            item["occurred_at"] = item["occurred_at"].isoformat()
        if item["reported_at"]:
            item["reported_at"] = item["reported_at"].isoformat()
        data.append(item)
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_POST
@rate_limit(max_requests=5, window_seconds=60, json_response=True)
def api_accidents_create(request):
    """POST /api/accidents — submit a new report (rate-limited, JSON or form).

    Returns 201 with the new record id, 400 on validation, 429 on rate limit.
    """
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body or b"{}")
        except json.JSONDecodeError as e:
            return JsonResponse({"error": "bad_json", "detail": str(e)}, status=400)
    else:
        data = request.POST

    form = AccidentForm(data, user=request.user)
    if form.is_valid():
        a = form.save(commit=False)
        if request.user.is_authenticated:
            a.submitted_by = request.user
        a.save()
        return JsonResponse(
            {
                "id": a.id,
                "created": True,
                "severity": a.severity,
                "vehicle_types": a.vehicle_types,
                "lat": a.lat,
                "lng": a.lng,
            },
            status=201,
        )

    return JsonResponse({"error": "validation", "detail": form.errors.get_json_data()}, status=400)


@require_http_methods(["POST"])
@login_required_custom
def api_upvote(request, accident_id):
    """POST /api/accidents/<id>/upvote/

    Toggles a logged-in user's upvote on an accident.
    """
    try:
        accident = Accident.objects.get(id=accident_id)
    except Accident.DoesNotExist:
        return JsonResponse({"error": "Accident not found"}, status=404)

    existing = AccidentUpvote.objects.filter(
        accident=accident,
        user=request.user,
    ).first()

    if existing:
        existing.delete()
        Accident.objects.filter(id=accident_id).update(
            upvote_count=F("upvote_count") - 1
        )
        accident.refresh_from_db()
        upvoted = False
    else:
        AccidentUpvote.objects.create(
            accident=accident,
            user=request.user,
        )
        Accident.objects.filter(id=accident_id).update(
            upvote_count=F("upvote_count") + 1
        )
        accident.refresh_from_db()
        upvoted = True

    return JsonResponse({
        "upvoted": upvoted,
        "upvote_count": accident.upvote_count,
    })


def api_accidents_near(request):
    """
    GET /api/accidents/near/

    Returns accidents within a radius of a given point.
    Uses PostGIS ST_DWithin for metre-accurate geographic distance.
    Falls back to Haversine Python approximation if PostGIS unavailable.
    """
    # Validate required parameters
    try:
        lat = float(request.GET.get("lat", ""))
        lng = float(request.GET.get("lng", ""))
    except (TypeError, ValueError):
        return JsonResponse(
            {"error": "lat and lng are required and must be numbers"},
            status=400,
        )

    # Validate and clamp radius
    try:
        radius_m = int(request.GET.get("radius", 500))
    except (TypeError, ValueError):
        radius_m = 500

    if not (1 <= radius_m <= 5000):
        return JsonResponse(
            {"error": "radius must be between 1 and 5000 metres"},
            status=400,
        )

    # Validate Dar es Salaam bounding box
    if not (-7.5 <= lat <= -6.0 and 38.5 <= lng <= 39.7):
        return JsonResponse(
            {"error": "Coordinates must be within Dar es Salaam bounding box"},
            status=400,
        )

    results = accidents_within_radius(lat, lng, radius_m)

    return JsonResponse({
        "centre": {"lat": lat, "lng": lng},
        "radius_m": radius_m,
        "count": len(results),
        "accidents": results,
    })
