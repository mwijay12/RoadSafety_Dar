# accidents/services/spatial.py
"""
PostGIS spatial query utilities for Road Safety Dar es Salaam.

All queries use raw SQL via Django's connection.cursor() so that
GeoDjango / GDAL do NOT need to be installed locally on Windows.

PostGIS runs server-side on Supabase. The local app only needs
psycopg2 (already installed) to send SQL strings.

Functions:
  accidents_within_radius(lat, lng, radius_m)
    → returns list of accident dicts within N metres of a point
    → uses ST_DWithin with ::geography cast for metre accuracy

  junction_severity_scores()
    → returns all junctions with severity-weighted safety score
    → score = (fatal×4) + (critical×3) + (serious×2) + (minor×1)
    → also returns upvote_total and verified_count per junction

  hotspot_hexagons(resolution=10)
    → groups accidents by h3_cell (already stored on Accident model)
    → returns hex cells with weighted accident counts
    → used for future vector tile output
"""

import logging
from django.db import connection, ProgrammingError

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# RADIUS SEARCH
# ─────────────────────────────────────────────────────────────────────────────

def accidents_within_radius(
    lat: float,
    lng: float,
    radius_m: int = 500,
) -> list[dict]:
    """
    Find all accidents within `radius_m` metres of (lat, lng).

    Uses PostGIS ST_DWithin with ::geography cast.
    Geography type uses metres as the unit — no projection needed.

    Args:
        lat:      Centre latitude  (WGS-84)
        lng:      Centre longitude (WGS-84)
        radius_m: Search radius in metres (default 500, max enforced by caller)

    Returns:
        List of dicts with accident data + distance_m field
        Sorted by distance ascending (nearest first)

    SQL explanation:
        ST_MakePoint(a.lng, a.lat) builds a PostGIS Point from our float cols.
        Note: ST_MakePoint takes (X, Y) = (longitude, latitude) — not lat/lng!
        ::geography casts to spherical coordinates for metre-accurate distance.
        ST_DWithin returns True if within radius_m metres.
        ST_Distance gives the exact distance in metres for sorting.

    Fallback:
        If PostGIS extension is not available (e.g. local SQLite),
        falls back to a Python Haversine bounding-box approximation.
    """
    sql = """
        SELECT
            a.id,
            a.lat,
            a.lng,
            a.severity,
            a.vehicle_types,
            a.occurred_at,
            a.casualties,
            a.fatalities,
            a.junction_name,
            a.verified,
            a.verification_status,
            a.trust_level,
            a.upvote_count,
            ROUND(
                ST_Distance(
                    ST_MakePoint(a.lng, a.lat)::geography,
                    ST_MakePoint(%s, %s)::geography
                )::numeric,
                1
            ) AS distance_m
        FROM accidents_accident a
        WHERE
            ST_DWithin(
                ST_MakePoint(a.lng, a.lat)::geography,
                ST_MakePoint(%s, %s)::geography,
                %s
            )
        ORDER BY distance_m ASC
        LIMIT 50
    """

    # Parameters: two sets of (lng, lat) for ST_Distance and ST_DWithin
    params = [lng, lat, lng, lat, radius_m]

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        results = []
        for row in rows:
            record = dict(zip(columns, row))
            # Convert datetime to ISO string for JSON serialisation
            if record.get("occurred_at"):
                record["occurred_at"] = record["occurred_at"].isoformat()
            # Convert distance to float for JSON
            record["distance_m"] = float(record["distance_m"])
            results.append(record)

        logger.info(
            f"Radius search: ({lat}, {lng}) r={radius_m}m → {len(results)} results"
        )
        return results

    except Exception as e:
        # PostGIS not available (e.g. SQLite database in tests) — fall back to Python approximation
        logger.info(f"PostGIS query unavailable, using Python fallback: {e}")
        return _haversine_fallback(lat, lng, radius_m)


def _haversine_fallback(lat: float, lng: float, radius_m: int) -> list[dict]:
    """
    Fallback radius search using Python Haversine formula.
    Used when PostGIS is not available (local SQLite dev).
    Less accurate than ST_DWithin but works without PostGIS.
    """
    import math
    from accidents.models import Accident

    def haversine(lat1, lng1, lat2, lng2):
        """Returns distance in metres between two WGS-84 points."""
        R = 6_371_000  # Earth radius in metres
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = (math.sin(dphi / 2) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    results = []
    accidents = Accident.objects.values(
        "id", "lat", "lng", "severity", "vehicle_types",
        "occurred_at", "casualties", "fatalities",
        "junction_name", "verified", "trust_level", "upvote_count",
    )

    for a in accidents:
        dist = haversine(lat, lng, a["lat"], a["lng"])
        if dist <= radius_m:
            record = dict(a)
            record["distance_m"] = round(dist, 1)
            record["verification_status"] = "verified" if a["verified"] else "pending"
            if record.get("occurred_at"):
                record["occurred_at"] = record["occurred_at"].isoformat()
            results.append(record)

    results.sort(key=lambda x: x["distance_m"])
    return results[:50]


# ─────────────────────────────────────────────────────────────────────────────
# SEVERITY-WEIGHTED JUNCTION SCORES
# ─────────────────────────────────────────────────────────────────────────────

def junction_severity_scores() -> list[dict]:
    """
    Returns all junctions ranked by severity-weighted safety score.

    Score formula:
        score = (fatal_count × 4) + (critical_count × 3)
              + (serious_count × 2) + (minor_count × 1)

    Higher score = more dangerous junction.

    Also includes:
        total_accidents    raw count
        verified_count     number of verified reports
        upvote_total       total community confirmations
        avg_lat, avg_lng   centroid of all accidents at this junction
                           (used when junction has no lat/lng set)

    Uses GROUP BY junction_name for junctions without a FK link.
    In PostGIS production this would use ST_Centroid + ST_Collect.
    """
    sql = """
        SELECT
            COALESCE(a.junction_name, 'Unknown Location') AS junction_name,
            COUNT(*)                                       AS total_accidents,
            SUM(CASE WHEN a.severity = 'fatal'    THEN 4 ELSE 0 END)
            + SUM(CASE WHEN a.severity = 'critical' THEN 3 ELSE 0 END)
            + SUM(CASE WHEN a.severity = 'serious'  THEN 2 ELSE 0 END)
            + SUM(CASE WHEN a.severity = 'minor'    THEN 1 ELSE 0 END)
                                                           AS severity_score,
            SUM(CASE WHEN a.severity = 'fatal'    THEN 1 ELSE 0 END) AS fatal_count,
            SUM(CASE WHEN a.severity = 'critical' THEN 1 ELSE 0 END) AS critical_count,
            SUM(CASE WHEN a.severity = 'serious'  THEN 1 ELSE 0 END) AS serious_count,
            SUM(CASE WHEN a.severity = 'minor'    THEN 1 ELSE 0 END) AS minor_count,
            SUM(a.casualties)                              AS total_casualties,
            SUM(a.fatalities)                              AS total_fatalities,
            SUM(a.upvote_count)                            AS upvote_total,
            SUM(CASE WHEN a.verified = TRUE THEN 1 ELSE 0 END) AS verified_count,
            ROUND(AVG(a.lat)::numeric, 6)                  AS avg_lat,
            ROUND(AVG(a.lng)::numeric, 6)                  AS avg_lng
        FROM accidents_accident a
        WHERE a.junction_name IS NOT NULL
          AND a.junction_name != ''
        GROUP BY a.junction_name
        ORDER BY severity_score DESC, total_accidents DESC
        LIMIT 20
    """

    from accidents.models import Junction
    junction_districts = {j["name"]: j["district"] for j in Junction.objects.values("name", "district")}

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        results = []
        for row in rows:
            record = dict(zip(columns, row))
            # Cast Decimal fields to float for JSON serialisation
            for field in ["avg_lat", "avg_lng"]:
                if record.get(field) is not None:
                    record[field] = float(record[field])
            for field in ["severity_score", "total_casualties", "total_fatalities",
                          "upvote_total"]:
                if record.get(field) is not None:
                    record[field] = int(record[field])

            # Legacy compatibility mapping
            record["name"] = record["junction_name"]
            record["count"] = record["severity_score"]
            record["fatalities"] = record["total_fatalities"]
            record["casualties"] = record["total_casualties"]
            record["lat"] = record["avg_lat"]
            record["lng"] = record["avg_lng"]
            record["district"] = junction_districts.get(record["junction_name"], "")
            results.append(record)

        return results

    except Exception as e:
        logger.error(f"Junction severity scores error: {e}")
        # Fallback to Python aggregation
        return _junction_scores_fallback()


def _junction_scores_fallback() -> list[dict]:
    """
    Python fallback for junction scoring when raw SQL fails.
    Used during local SQLite development.
    """
    from accidents.models import Accident, Junction
    from collections import defaultdict

    junction_districts = {j["name"]: j["district"] for j in Junction.objects.values("name", "district")}
    WEIGHTS = {"fatal": 4, "critical": 3, "serious": 2, "minor": 1}

    buckets = defaultdict(lambda: {
        "total_accidents": 0, "severity_score": 0,
        "fatal_count": 0, "critical_count": 0,
        "serious_count": 0, "minor_count": 0,
        "total_casualties": 0, "total_fatalities": 0,
        "upvote_total": 0, "verified_count": 0,
        "lats": [], "lngs": [],
    })

    for a in Accident.objects.values(
        "junction_name", "severity", "casualties", "fatalities",
        "upvote_count", "verified", "lat", "lng"
    ):
        name = a["junction_name"]
        if not name or not name.strip():
            continue
        b = buckets[name]
        b["total_accidents"] += 1
        b["severity_score"] += WEIGHTS.get(a["severity"], 1)
        b[f"{a['severity']}_count"] = b.get(f"{a['severity']}_count", 0) + 1
        b["total_casualties"] += a["casualties"] or 0
        b["total_fatalities"] += a["fatalities"] or 0
        b["upvote_total"] += a["upvote_count"] or 0
        b["verified_count"] += 1 if a["verified"] else 0
        b["lats"].append(a["lat"])
        b["lngs"].append(a["lng"])

    results = []
    for name, data in buckets.items():
        lats = data.pop("lats")
        lngs = data.pop("lngs")
        data["junction_name"] = name
        data["avg_lat"] = round(sum(lats) / len(lats), 6) if lats else 0
        data["avg_lng"] = round(sum(lngs) / len(lngs), 6) if lngs else 0

        # Legacy compatibility mapping
        data["name"] = name
        data["count"] = data["severity_score"]
        data["fatalities"] = data["total_fatalities"]
        data["casualties"] = data["total_casualties"]
        data["lat"] = data["avg_lat"]
        data["lng"] = data["avg_lng"]
        data["district"] = junction_districts.get(name, "")
        results.append(data)

    results.sort(key=lambda x: x["severity_score"], reverse=True)
    return results[:20]


# ─────────────────────────────────────────────────────────────────────────────
# BBOX FILTER FOR HEATMAP
# ─────────────────────────────────────────────────────────────────────────────

def accidents_in_bbox(
    south: float,
    west: float,
    north: float,
    east: float,
) -> list[dict]:
    """
    Returns accidents within a bounding box.
    Used for viewport-based heatmap fetching on the dashboard.

    Args:
        south, west, north, east: bounding box corners (WGS-84)

    Returns:
        List of {lat, lng, severity, trust_level, upvote_count} dicts
    """
    sql = """
        SELECT lat, lng, severity, trust_level, upvote_count
        FROM accidents_accident
        WHERE lat BETWEEN %s AND %s
          AND lng BETWEEN %s AND %s
    """
    params = [south, north, west, east]

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"BBox filter error: {e}")
        return []
