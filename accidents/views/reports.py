"""
Report submission views — HTML form + JSON API.
"""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from ..decorators import get_client_ip, rate_limit
from ..forms import AccidentForm
from ..models import visible_accidents

logger = logging.getLogger(__name__)


def report_form(request):
    form = AccidentForm()
    if request.method == "POST":
        if not _rate_check_wrapper(request):
            return HttpResponse("Too many submissions. Please wait a minute.", status=429)
        form = AccidentForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    return render(request, "accidents/report.html", {"form": form})


def _rate_check_wrapper(request):
    """Inline rate check for the HTML form (returns bool)."""
    from ..decorators import _rate_check

    ip = get_client_ip(request)
    return _rate_check(ip)


@require_GET
def api_accidents(_request):
    """GET /api/accidents — list of all accidents for heatmap + map."""
    qs = visible_accidents().values(
        "id",
        "lat",
        "lng",
        "severity",
        "vehicle_types",
        "junction_name",
        "occurred_at",
        "casualties",
        "fatalities",
    )
    data = []
    weight = {"minor": 1, "serious": 2, "critical": 3, "fatal": 4}
    for a in qs:
        data.append(
            {
                **a,
                "occurred_at": a["occurred_at"].isoformat(),
                "address": a.get("junction_name", ""),
                "intensity": weight.get(a["severity"], 1),
            }
        )
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

    form = AccidentForm(data)
    if form.is_valid():
        a = form.save()
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
