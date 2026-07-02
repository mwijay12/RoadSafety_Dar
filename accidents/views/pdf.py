"""
PDF report generation — monthly report as downloadable PDF.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from ..models import visible_accidents

logger = logging.getLogger(__name__)

# Skylearn palette
SKY = "#3B82F6"
SKY_DARK = "#1D4ED8"
CORAL = "#F87171"
SUN = "#FBBF24"
LEAF = "#22C55E"
INK = "#0F172A"
INK_MUTED = "#475569"
OUTLINE = "#E2E8F0"
WHITE = "#FFFFFF"
BG_LIGHT = "#F8FAFC"

SEVERITY_COLORS = {
    "fatal": CORAL,
    "critical": SUN,
    "serious": SKY,
    "minor": LEAF,
}


@require_GET
def api_monthly_report(_request):
    """GET /api/report/monthly.pdf — generate a PDF report on demand.

    Query params:
        ?month=YYYY-MM  (default: previous month)
    Returns: PDF file download
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        return HttpResponse(
            "reportlab not installed. Run: pip install reportlab",
            status=501,
            content_type="text/plain",
        )

    month_str = _request.GET.get("month")
    if month_str:
        try:
            year, month = map(int, month_str.split("-"))
            period_start = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
        except (ValueError, AttributeError):
            return HttpResponse("Invalid month format. Use YYYY-MM.", status=400)
    else:
        now = timezone.now()
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_start = first_of_this_month - timedelta(days=1)
        period_start = period_start.replace(day=1)

    from calendar import monthrange as mr

    last_day = mr(period_start.year, period_start.month)[1]
    period_end = period_start.replace(day=last_day, hour=23, minute=59, second=59)

    qs = visible_accidents().filter(occurred_at__gte=period_start, occurred_at__lte=period_end)
    total = qs.count()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="roadsafety_dar_{period_start:%Y_%m}.pdf"'
    )

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []
    W = A4[0] - 4 * cm  # usable width

    # ---- Custom styles ----
    styles.add(
        ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=colors.HexColor(INK),
            leading=28,
            alignment=TA_LEFT,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportSubtitle",
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor(INK_MUTED),
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=12 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionTitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=colors.HexColor(SKY_DARK),
            leading=18,
            alignment=TA_LEFT,
            spaceBefore=8 * mm,
            spaceAfter=4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor(INK),
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Footer",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=colors.HexColor(INK_MUTED),
            leading=10,
            alignment=TA_CENTER,
            spaceBefore=6 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "SeverityKey",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor(INK_MUTED),
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=2 * mm,
        )
    )

    # ---- Header bar ----
    header_data = [
        [
            Paragraph(
                f"<font color='{SKY}'><b>Road Safety</b></font>"
                f"<font color='{INK}'>  Dar es Salaam</font>",
                ParagraphStyle(
                    "hdr", fontName="Helvetica-Bold", fontSize=14, textColor=colors.HexColor(INK)
                ),
            ),
            Paragraph(
                f"{period_start:%B %Y}",
                ParagraphStyle(
                    "hdr2",
                    fontName="Helvetica",
                    fontSize=12,
                    textColor=colors.HexColor(INK_MUTED),
                    alignment=TA_RIGHT,
                ),
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[W * 0.6, W * 0.4])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor(SKY)),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 2 * mm))

    # ---- Subtitle ----
    story.append(
        Paragraph(
            f"Monthly accident intelligence report &mdash; "
            f"{period_start:%d %B} &ndash; {period_end:%d %B %Y}",
            styles["ReportSubtitle"],
        )
    )

    # ---- Summary section ----
    story.append(Paragraph("Executive Summary", styles["SectionTitle"]))

    fatal = qs.filter(severity="fatal").count()
    critical = qs.filter(severity="critical").count()
    serious = qs.filter(severity="serious").count()
    minor = qs.filter(severity="minor").count()
    total_fatalities = sum(qs.values_list("fatalities", flat=True) or [0])
    total_casualties = sum(qs.values_list("casualties", flat=True) or [0])
    total_vehicles = qs.exclude(vehicle_types__len=0).count() if total else 0

    if total == 0:
        story.append(Paragraph("No incidents recorded in this period.", styles["Body"]))
    else:
        summary_data = [
            ["Metric", "Value"],
            ["Total Incidents", str(total)],
            ["Fatal", f"{fatal}  ({fatal/total*100:.0f}%)"],
            ["Critical", f"{critical}  ({critical/total*100:.0f}%)"],
            ["Serious", f"{serious}  ({serious/total*100:.0f}%)"],
            ["Minor", f"{minor}  ({minor/total*100:.0f}%)"],
            ["Total Deaths", str(total_fatalities)],
            ["Total Casualties (injured)", str(total_casualties)],
            ["Vehicles Involved", str(total_vehicles)],
        ]
        t = Table(summary_data, colWidths=[W * 0.55, W * 0.45])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SKY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(OUTLINE)),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor(BG_LIGHT)],
                    ),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(t)

    # ---- Severity colour key ----
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            f"<font color='{CORAL}'><b>■ Fatal</b></font> &nbsp;&nbsp;"
            f"<font color='{SUN}'><b>■ Critical</b></font> &nbsp;&nbsp;"
            f"<font color='{SKY}'><b>■ Serious</b></font> &nbsp;&nbsp;"
            f"<font color='{LEAF}'><b>■ Minor</b></font>",
            styles["SeverityKey"],
        )
    )

    # ---- Severity breakdown ----
    story.append(Paragraph("Severity Breakdown", styles["SectionTitle"]))
    severity_data = [["Severity", "Count", "% of Total"]]
    for sev, label in [
        ("fatal", "Fatal"),
        ("critical", "Critical"),
        ("serious", "Serious"),
        ("minor", "Minor"),
    ]:
        count = qs.filter(severity=sev).count()
        pct = f"{count/total*100:.1f}%" if total else "—"
        severity_data.append(
            [
                Paragraph(
                    f"<font color='{SEVERITY_COLORS[sev]}'><b>■</b></font>  {label}",
                    ParagraphStyle(
                        "sc", fontName="Helvetica", fontSize=10, textColor=colors.HexColor(INK)
                    ),
                ),
                str(count),
                pct,
            ]
        )
    if total:
        severity_data.append(["Total", str(total), "100%"])
    st = Table(severity_data, colWidths=[W * 0.5, W * 0.25, W * 0.25])
    st.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SKY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(OUTLINE)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(BG_LIGHT)]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(st)

    # ---- Vehicle Type Breakdown ----
    raw_types = list(qs.values_list("vehicle_types", flat=True))
    if raw_types:
        story.append(Paragraph("Vehicle Types Involved", styles["SectionTitle"]))
        all_types = []
        for val in raw_types:
            if val and isinstance(val, list):
                all_types.extend(t.strip() for t in val)
        v_counts = Counter(all_types)
        total_v = sum(v_counts.values())
        v_data = [["Vehicle Type", "Count", "% of Total"]]
        for vt, count in v_counts.most_common():
            v_data.append(
                [vt.title() if vt else "Unknown", str(count), f"{count/total_v*100:.1f}%"]
            )
        vt = Table(v_data, colWidths=[W * 0.5, W * 0.25, W * 0.25])
        vt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SKY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(OUTLINE)),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor(BG_LIGHT)],
                    ),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(vt)

    # ---- Hourly distribution ----
    hours_list = list(qs.values_list("occurred_at__hour", flat=True))
    if hours_list:
        story.append(Paragraph("Hourly Distribution (Peak Hours)", styles["SectionTitle"]))
        hour_counts = Counter(hours_list)
        peak = hour_counts.most_common(5)
        hour_labels = {
            0: "Midnight",
            1: "1 AM",
            2: "2 AM",
            3: "3 AM",
            4: "4 AM",
            5: "5 AM",
            6: "6 AM",
            7: "7 AM",
            8: "8 AM",
            9: "9 AM",
            10: "10 AM",
            11: "11 AM",
            12: "Noon",
            13: "1 PM",
            14: "2 PM",
            15: "3 PM",
            16: "4 PM",
            17: "5 PM",
            18: "6 PM",
            19: "7 PM",
            20: "8 PM",
            21: "9 PM",
            22: "10 PM",
            23: "11 PM",
        }
        h_data = [["Hour", "Incidents"]]
        for h, c in sorted(peak):
            h_data.append([hour_labels.get(h, f"{h}:00"), str(c)])
        ht = Table(h_data, colWidths=[W * 0.6, W * 0.4])
        ht.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SKY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(OUTLINE)),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor(BG_LIGHT)],
                    ),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(ht)

    # ---- Top Junctions ----
    junctions = list(
        qs.values("junction__name", "junction__district")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")[:10]
    )
    if junctions:
        story.append(Paragraph("Top Junctions by Incidents", styles["SectionTitle"]))
        j_data = [["#", "Junction", "District", "Incidents"]]
        for i, j in enumerate(junctions, 1):
            j_data.append(
                [
                    str(i),
                    j["junction__name"] or "Unknown",
                    j["junction__district"] or "—",
                    str(j["cnt"]),
                ]
            )
        jt = Table(j_data, colWidths=[0.6 * cm, W * 0.35, W * 0.25, W * 0.2])
        jt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SKY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 1), (0, -1), "CENTER"),
                    ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(OUTLINE)),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor(BG_LIGHT)],
                    ),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(jt)

    # ---- Footer ----
    story.append(Spacer(1, 6 * mm))
    story.append(
        Paragraph(
            f"Generated by RoadSafety_Dar v1.3 on {timezone.now():%Y-%m-%d %H:%M} EAT &bull; "
            f"Data source: crowdsourced reports and police records.",
            styles["Footer"],
        )
    )

    doc.build(story)
    return response
