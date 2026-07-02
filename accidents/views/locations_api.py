"""
api_locations.py — JSON endpoints powering the cascading location picker
on the public accident report form.

Endpoints
---------
    GET /api/locations/                   — full tree (districts→wards→locations)
    GET /api/locations/?district=Ilala   — filter tree by district
    GET /api/locations/?q=kari           — free-text type-ahead search
    GET /api/locations/districts/        — flat list of districts
    GET /api/locations/wards/?district=  — wards for a district
    GET /api/locations/hotspots/         — accident hotspots only
"""

import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ..locations import (
    DISTRICTS,
    WARDS,
    get_hotspots,
    get_location_tree,
)

logger = logging.getLogger(__name__)


@require_GET
def api_locations(request):
    """Return the location tree, optionally filtered by district / query."""
    district = request.GET.get("district", "").strip()
    query = request.GET.get("q", "").strip()

    # Full tree
    if not district and not query:
        return JsonResponse(
            {
                "region": "Dar es Salaam",
                "districts": [
                    {"name": d["name"], "lat": d["lat"], "lng": d["lng"]}
                    for d in DISTRICTS
                ],
                "tree": get_location_tree(),
            }
        )

    # Free-text type-ahead search (used by the autocomplete widget)
    if query:
        results = []
        needle = query.lower()
        for d in DISTRICTS:
            dname = d["name"]
            for ward in WARDS.get(dname, []):
                for loc in ward.get("locations", []):
                    haystack = [loc["name"].lower()]
                    haystack += [a.lower() for a in loc.get("aliases", [])]
                    if any(needle in h for h in haystack):
                        results.append(
                            {
                                "name": loc["name"],
                                "type": loc.get("type", ""),
                                "lat": loc["lat"],
                                "lng": loc["lng"],
                                "district": dname,
                                "ward": ward["name"],
                                "accident_hotspot": loc.get(
                                    "accident_hotspot", False
                                ),
                            }
                        )
        return JsonResponse(
            {"query": query, "count": len(results), "results": results}
        )

    # Filter by district
    if district:
        wards_data = WARDS.get(district, [])
        return JsonResponse(
            {
                "district": district,
                "wards": [
                    {
                        "name": w["name"],
                        "lat": w["lat"],
                        "lng": w["lng"],
                        "locations": w.get("locations", []),
                    }
                    for w in wards_data
                ],
            }
        )

    return JsonResponse({"error": "bad request"}, status=400)


@require_GET
def api_locations_districts(request):
    """Flat list of districts (used to populate the first dropdown)."""
    return JsonResponse(
        {
            "districts": [
                {"name": d["name"], "code": d["code"]} for d in DISTRICTS
            ]
        }
    )


@require_GET
def api_locations_wards(request):
    """Wards for a given district (used to populate the ward dropdown)."""
    district = request.GET.get("district", "").strip()
    if not district:
        return JsonResponse({"error": "district is required"}, status=400)
    return JsonResponse(
        {
            "district": district,
            "wards": [
                {"name": w, "lat": w_data["lat"], "lng": w_data["lng"]}
                for w, ws in [(district, WARDS.get(district, []))]
                for w_data in ws
                for w in [w_data["name"]]
            ],
        }
    )


@require_GET
def api_locations_hotspots(request):
    """Accident hotspots only — used by the black-spot map layer."""
    return JsonResponse(
        {
            "count": len(get_hotspots()),
            "hotspots": get_hotspots(),
        }
    )
