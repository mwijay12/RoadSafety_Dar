"""
Authority dashboard views — police/admin only.
"""

import csv
import logging
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from ..decorators import police_or_admin_required
from ..models import SEVERITY_CHOICES, SEVERITY_WEIGHT, VEHICLE_CHOICES, Accident

logger = logging.getLogger(__name__)


@login_required
@police_or_admin_required
def authority(request):
    return render(
        request,
        "accidents/authority.html",
        {
            "sev_choices": SEVERITY_CHOICES,
            "veh_choices": VEHICLE_CHOICES,
        },
    )


@login_required
@police_or_admin_required
def api_authority_filter(request):
    """GET /api/authority/filter/ — filtered KPI bundle for authority dashboard."""
    qs = Accident.objects.all()

    start = request.GET.get("start")
    end = request.GET.get("end")
    if start:
        qs = qs.filter(occurred_at__gte=start)
    if end:
        qs = qs.filter(occurred_at__lte=end)

    severity = request.GET.get("severity")
    if severity:
        sev_list = [s.strip() for s in severity.split(",")]
        qs = qs.filter(severity__in=sev_list)

    vt = request.GET.get("vehicle_type")
    if vt:
        qs = qs.filter(vehicle_types__contains=[vt])

    jn = request.GET.get("junction")
    if jn:
        qs = qs.filter(junction_name__icontains=jn)

    total = qs.count()
    fatal_count = qs.filter(severity="fatal").count()
    critical_count = qs.filter(severity="critical").count()
    verified_count = qs.filter(verified=True).count()
    total_casualties = qs.aggregate(s=Sum("casualties"))["s"] or 0
    total_fatalities = qs.aggregate(s=Sum("fatalities"))["s"] or 0

    recent = qs.order_by("-occurred_at")[:20].values(
        "id",
        "severity",
        "vehicle_types",
        "junction_name",
        "occurred_at",
        "casualties",
        "fatalities",
        "lat",
        "lng",
    )

    junction_buckets = defaultdict(lambda: {"count": 0, "weighted_sum": 0, "name": ""})
    for a in qs.exclude(junction_name=""):
        b = junction_buckets[a.junction_name]
        b["name"] = a.junction_name
        b["count"] += 1
        b["weighted_sum"] += SEVERITY_WEIGHT.get(a.severity, 1)

    junctions_ranked = []
    for name, b in junction_buckets.items():
        safety_score = round((b["weighted_sum"] / b["count"]) * 25, 1) if b["count"] else 0
        junctions_ranked.append({"name": name, "count": b["count"], "safety_score": safety_score})
    junctions_ranked.sort(key=lambda x: -x["safety_score"])

    return JsonResponse(
        {
            "total": total,
            "fatal_count": fatal_count,
            "critical_count": critical_count,
            "verified_count": verified_count,
            "verified_pct": round(verified_count / total * 100, 1) if total else 0,
            "total_casualties": total_casualties,
            "total_fatalities": total_fatalities,
            "avg_casualties": round(total_casualties / total, 1) if total else 0,
            "recent": list(recent),
            "junctions": junctions_ranked[:10],
        }
    )


@login_required
@police_or_admin_required
def api_authority_export_csv(request):
    """GET /api/authority/export/csv/ — filtered CSV download."""
    qs = Accident.objects.all()

    start = request.GET.get("start")
    end = request.GET.get("end")
    if start:
        qs = qs.filter(occurred_at__gte=start)
    if end:
        qs = qs.filter(occurred_at__lte=end)

    severity = request.GET.get("severity")
    if severity:
        sev_list = [s.strip() for s in severity.split(",")]
        qs = qs.filter(severity__in=sev_list)

    vt = request.GET.get("vehicle_type")
    if vt:
        qs = qs.filter(vehicle_types__contains=[vt])

    jn = request.GET.get("junction")
    if jn:
        qs = qs.filter(junction_name__icontains=jn)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="authority_export_{timezone.now():%Y-%m-%d}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Severity",
            "Vehicle Types",
            "Junction",
            "Lat",
            "Lng",
            "Occurred At",
            "Casualties",
            "Fatalities",
            "Injuries",
            "Weather",
            "Road Condition",
            "Verified",
        ]
    )
    for a in qs.iterator():
        writer.writerow(
            [
                a.id,
                a.severity,
                ", ".join(a.vehicle_types or []),
                a.junction_name,
                a.lat,
                a.lng,
                a.occurred_at.isoformat() if a.occurred_at else "",
                a.casualties,
                a.fatalities,
                a.injuries,
                a.weather,
                a.road_condition,
                "yes" if a.verified else "no",
            ]
        )

    return response
