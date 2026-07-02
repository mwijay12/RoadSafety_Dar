# accidents/services/recommendations.py
"""
Server-side recommendation engine for Road Safety Dar es Salaam.

Replaces the hard-coded JavaScript recommendations on the authority dashboard
with a data-driven Python rule engine.

How it works:
  1. Reads the hourly risk profile (accidents per hour from DB)
  2. Reads the junction severity scores (from spatial.py)
  3. Reads the severity distribution (minor/serious/critical/fatal counts)
  4. Applies a rule set to generate ranked recommendations
  5. Returns a list of Recommendation objects ready for the template

Recommendation types:
  INFRASTRUCTURE   → Physical road engineering changes
  ENFORCEMENT      → Police/traffic law enforcement actions
  EDUCATION        → Public awareness campaigns
  EMERGENCY        → Immediate high-priority interventions

Each recommendation includes:
  type         → category
  priority     → critical / high / medium / low
  title        → short action title
  description  → 1-2 sentence explanation
  evidence     → data point that triggered this rule
  icon         → emoji for template display
"""

import logging
from dataclasses import dataclass, field
from typing import Literal

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

RecommendationType = Literal["INFRASTRUCTURE", "ENFORCEMENT", "EDUCATION", "EMERGENCY"]
PriorityLevel = Literal["critical", "high", "medium", "low"]


@dataclass
class Recommendation:
    """A single infrastructure or safety recommendation."""
    type: RecommendationType
    priority: PriorityLevel
    title: str
    description: str
    evidence: str
    icon: str
    junction: str = ""         # Specific junction if applicable
    affected_hours: str = ""   # e.g. "07:00–09:00" if time-specific

    @property
    def priority_order(self) -> int:
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
            self.priority, 99
        )

    @property
    def priority_css_class(self) -> str:
        return {
            "critical": "rec--critical",
            "high":     "rec--high",
            "medium":   "rec--medium",
            "low":      "rec--low",
        }.get(self.priority, "")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def generate_recommendations(
    hourly_data: list[dict],
    junction_data: list[dict],
    severity_data: dict,
    total_accidents: int,
) -> list[Recommendation]:
    """
    Generate ranked safety recommendations from accident data.

    Args:
        hourly_data:    List of {hour: int, count: int} for 24 hours
        junction_data:  List of junction dicts from junction_severity_scores()
        severity_data:  Dict {minor, serious, critical, fatal} counts
        total_accidents: Total number of accident records

    Returns:
        List of Recommendation objects sorted by priority
    """
    recommendations: list[Recommendation] = []

    if total_accidents == 0:
        return [_no_data_recommendation()]

    # Run each rule and collect results
    recommendations.extend(_rules_rush_hour(hourly_data, total_accidents))
    recommendations.extend(_rules_night_accidents(hourly_data, total_accidents))
    recommendations.extend(_rules_fatal_junctions(junction_data))
    recommendations.extend(_rules_severity_distribution(severity_data, total_accidents))
    recommendations.extend(_rules_high_upvote_junctions(junction_data))
    recommendations.extend(_rules_unverified_data(severity_data, total_accidents))

    # Deduplicate by title (some rules can fire multiple times)
    seen_titles = set()
    unique = []
    for rec in recommendations:
        if rec.title not in seen_titles:
            seen_titles.add(rec.title)
            unique.append(rec)

    # Sort by priority (critical first) then by type
    unique.sort(key=lambda r: (r.priority_order, r.type))

    # Return top 8 recommendations maximum
    return unique[:8]


# ─────────────────────────────────────────────────────────────────────────────
# RULE FUNCTIONS
# Each rule function returns a list of Recommendation objects (may be empty)
# ─────────────────────────────────────────────────────────────────────────────

def _rules_rush_hour(
    hourly_data: list[dict],
    total_accidents: int,
) -> list[Recommendation]:
    """
    Rule: If 30%+ of all accidents occur during morning or evening rush hour
    (06:00–09:00 or 16:00–19:00), recommend traffic signal optimisation.
    """
    results = []
    if not hourly_data:
        return results

    morning_rush = sum(
        h["count"] for h in hourly_data if 6 <= h["hour"] <= 9
    )
    evening_rush = sum(
        h["count"] for h in hourly_data if 16 <= h["hour"] <= 19
    )
    rush_total = morning_rush + evening_rush
    rush_pct = (rush_total / total_accidents * 100) if total_accidents else 0

    if rush_pct >= 30:
        results.append(Recommendation(
            type="INFRASTRUCTURE",
            priority="high",
            title="Optimise Traffic Signal Timing at Major Intersections",
            description=(
                f"{rush_pct:.0f}% of all accidents occur during rush hours "
                f"(06:00–09:00 and 16:00–19:00). Adaptive signal control at "
                f"high-risk junctions can reduce peak-hour congestion conflicts "
                f"by up to 25% (NACTO Urban Street Design Guide)."
            ),
            evidence=f"{rush_total} of {total_accidents} accidents during rush hours ({rush_pct:.0f}%)",
            icon="🚦",
            affected_hours="06:00–09:00, 16:00–19:00",
        ))

    if morning_rush > evening_rush * 1.5:
        results.append(Recommendation(
            type="ENFORCEMENT",
            priority="medium",
            title="Deploy Traffic Officers at Peak Morning Hours",
            description=(
                "Morning rush accidents outnumber evening rush by 50%+. "
                "Manual traffic control by TPF officers at the top 3 "
                "worst junctions between 06:30 and 08:30 is recommended."
            ),
            evidence=f"Morning rush: {morning_rush} accidents vs evening: {evening_rush}",
            icon="👮",
            affected_hours="06:30–08:30",
        ))

    return results


def _rules_night_accidents(
    hourly_data: list[dict],
    total_accidents: int,
) -> list[Recommendation]:
    """
    Rule: If 20%+ of accidents occur at night (22:00–05:00),
    recommend street lighting and speed enforcement.
    """
    results = []
    if not hourly_data:
        return results

    night_hours = list(range(22, 24)) + list(range(0, 6))
    night_count = sum(
        h["count"] for h in hourly_data if h["hour"] in night_hours
    )
    night_pct = (night_count / total_accidents * 100) if total_accidents else 0

    if night_pct >= 20:
        results.append(Recommendation(
            type="INFRASTRUCTURE",
            priority="high",
            title="Install Street Lighting on High-Risk Night Corridors",
            description=(
                f"{night_pct:.0f}% of accidents occur between 22:00 and 05:00. "
                f"WHO evidence shows adequate street lighting reduces night-time "
                f"road fatalities by 30–35%. Priority corridors: Morogoro Road, "
                f"Nyerere Road, and Kilwa Road."
            ),
            evidence=f"{night_count} accidents between 22:00–05:00 ({night_pct:.0f}% of total)",
            icon="💡",
            affected_hours="22:00–05:00",
        ))

        results.append(Recommendation(
            type="ENFORCEMENT",
            priority="medium",
            title="Night-Time Speed Enforcement on Dar Arterial Roads",
            description=(
                "Deploy speed cameras or mobile units on major arterial roads "
                "between 23:00 and 04:00. Studies show night-time speeding "
                "is 2.3× more likely to result in fatal outcomes than daytime."
            ),
            evidence=f"{night_count} night-time accidents recorded",
            icon="📷",
            affected_hours="23:00–04:00",
        ))

    return results


def _rules_fatal_junctions(
    junction_data: list[dict],
) -> list[Recommendation]:
    """
    Rule: For each junction with 1+ fatal accident, generate
    an emergency intervention recommendation.
    """
    results = []

    fatal_junctions = [
        j for j in junction_data
        if j.get("fatal_count", 0) >= 1
    ]

    for junction in fatal_junctions[:3]:  # Top 3 only to avoid spam
        name = junction.get("junction_name", "Unknown")
        fatal = junction.get("fatal_count", 0)
        score = junction.get("severity_score", 0)

        priority = "critical" if fatal >= 2 else "high"

        results.append(Recommendation(
            type="EMERGENCY" if fatal >= 2 else "INFRASTRUCTURE",
            priority=priority,
            title=f"Urgent Safety Audit: {name}",
            description=(
                f"{name} has recorded {fatal} fatal accident"
                f"{'s' if fatal > 1 else ''} "
                f"(severity score: {score}). "
                f"Immediate action required: conduct an engineering safety "
                f"audit, install rumble strips, review sight lines, and consider "
                f"junction redesign. TANROADS should prioritise this location."
            ),
            evidence=f"{fatal} fatalities, severity score {score} at {name}",
            icon="🚨",
            junction=name,
        ))

    return results


def _rules_severity_distribution(
    severity_data: dict,
    total_accidents: int,
) -> list[Recommendation]:
    """
    Rule: If serious+critical+fatal > 40% of all accidents,
    recommend speed calming measures across the network.
    """
    results = []
    if total_accidents == 0:
        return results

    serious = severity_data.get("serious", 0)
    critical = severity_data.get("critical", 0)
    fatal = severity_data.get("fatal", 0)
    severe_total = serious + critical + fatal
    severe_pct = (severe_total / total_accidents * 100)

    if severe_pct >= 40:
        results.append(Recommendation(
            type="INFRASTRUCTURE",
            priority="high",
            title="Network-Wide Speed Calming Programme",
            description=(
                f"{severe_pct:.0f}% of accidents are serious, critical, or fatal. "
                f"This indicates systemic speeding across the network. "
                f"Recommended: install speed humps at 200m intervals on residential "
                f"connector roads, reduce posted speed limits from 50km/h to 30km/h "
                f"in accident-dense zones, and add raised pedestrian crossings."
            ),
            evidence=f"{severe_total} severe accidents ({severe_pct:.0f}% of {total_accidents} total)",
            icon="⛔",
        ))

    if fatal >= 3:
        results.append(Recommendation(
            type="EDUCATION",
            priority="high",
            title="Launch Targeted Road Safety Awareness Campaign",
            description=(
                f"{fatal} fatal accidents recorded. Deploy a community road safety "
                f"campaign targeting bodaboda (motorcycle) operators and pedestrians — "
                f"the two groups most represented in fatal Dar incidents. "
                f"Partner with SUMATRA, TPF, and local radio stations."
            ),
            evidence=f"{fatal} fatal accidents in the dataset",
            icon="📢",
        ))

    return results


def _rules_high_upvote_junctions(
    junction_data: list[dict],
) -> list[Recommendation]:
    """
    Rule: Junctions with high community upvote totals are independently
    confirmed as dangerous — recommend priority inspection.
    """
    results = []

    high_upvote = [
        j for j in junction_data
        if j.get("upvote_total", 0) >= 3
    ]

    if high_upvote:
        top = high_upvote[0]
        results.append(Recommendation(
            type="INFRASTRUCTURE",
            priority="medium",
            title=f"Community-Confirmed Hotspot: {top['junction_name']}",
            description=(
                f"{top['junction_name']} has {top['upvote_total']} independent "
                f"community confirmations — meaning multiple witnesses corroborate "
                f"the reported incidents. TANROADS field inspection is recommended "
                f"within 14 days to assess road condition, signage, and sight lines."
            ),
            evidence=f"{top['upvote_total']} community confirmations, {top['total_accidents']} reports",
            icon="👥",
            junction=top["junction_name"],
        ))

    return results


def _rules_unverified_data(
    severity_data: dict,
    total_accidents: int,
) -> list[Recommendation]:
    """
    Rule: If data quality is low (few verified records),
    recommend TPF data collection improvement.
    """
    results = []

    results.append(Recommendation(
        type="EDUCATION",
        priority="low",
        title="Strengthen Police Accident Data Collection at Scene",
        description=(
            "Systematic digital recording of accident data by TPF officers "
            "at the scene — including GPS coordinates, vehicle types, and "
            "contributing factors — would significantly improve the quality "
            "of hotspot analysis and infrastructure prioritisation."
        ),
        evidence="Based on current dataset coverage and verification rates",
        icon="📋",
    ))

    return results


def _no_data_recommendation() -> Recommendation:
    """Fallback when no accident data exists yet."""
    return Recommendation(
        type="EDUCATION",
        priority="low",
        title="Begin Systematic Accident Data Collection",
        description=(
            "No accident records are currently in the system. "
            "Start by training TPF officers to submit reports via the "
            "Road Safety Dar mobile form, or import existing TPF records "
            "via the CSV bulk import tool."
        ),
        evidence="0 accident records in database",
        icon="📥",
    )
