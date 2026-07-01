"""
PDF monthly report generator — v1.2.

Generates a comprehensive monthly safety report for SUMATRA / TANROADS / Police.
Includes: KPI summary, severity breakdown, vehicle types, top junctions,
time-of-day analysis, and an executive summary.

Usage:
    python manage.py generate_monthly_report
    python manage.py generate_monthly_report --month 2026-06
    python manage.py generate_monthly_report --output reports/2026-06.pdf
"""
import os
import logging
from calendar import monthrange
from collections import Counter
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Sum
from django.utils import timezone

from accidents.models import Accident, Junction

logger = logging.getLogger(__name__)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class Command(BaseCommand):
    help = "Generate a monthly road safety PDF report."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=str,
            default=None,
            help="Month in YYYY-MM format (default: previous month)",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Output file path (default: reports/YYYY-MM.pdf)",
        )

    def handle(self, *args, **options):
        if not HAS_REPORTLAB:
            self.stderr.write(self.style.ERROR(
                "reportlab is not installed. Run: pip install reportlab"
            ))
            return

        # Determine target month
        if options["month"]:
            try:
                year, month = map(int, options["month"].split("-"))
                period_start = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
            except ValueError:
                self.stderr.write("Invalid month format. Use YYYY-MM.")
                return
        else:
            now = timezone.now()
            first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_start = first_of_this_month - timedelta(days=1)
            period_start = period_start.replace(day=1)

        # End of month
        last_day = monthrange(period_start.year, period_start.month)[1]
        period_end = period_start.replace(
            day=last_day, hour=23, minute=59, second=59,
        )

        self.stdout.write(f"Generating report for {period_start:%B %Y}...")
        self.stdout.write(f"  Period: {period_start} -> {period_end}")

        # Output path
        if options["output"]:
            output = options["output"]
        else:
            os.makedirs(os.path.join(settings.BASE_DIR, "reports"), exist_ok=True)
            output = os.path.join(
                settings.BASE_DIR, "reports",
                f"roadsafety_{period_start:%Y-%m}.pdf"
            )

        # Gather data
        qs = Accident.objects.filter(
            occurred_at__gte=period_start,
            occurred_at__lte=period_end,
        )
        data = self._gather_data(qs, period_start, period_end)

        # Build PDF
        doc = SimpleDocTemplate(
            output, pagesize=A4,
            topMargin=2*cm, bottomMargin=2*cm,
            leftMargin=2*cm, rightMargin=2*cm,
            title=f"Road Safety Dar — {period_start:%B %Y}",
        )
        story = self._build_story(data, period_start)
        doc.build(story)

        self.stdout.write(self.style.SUCCESS(f"✅ Report saved: {output}"))

    def _gather_data(self, qs, period_start, period_end):
        """Aggregate stats for the period."""
        total = qs.count()
        if total == 0:
            return {
                "total": 0, "period_start": period_start, "period_end": period_end,
                "severity": {}, "vehicles": {}, "monthly_trend": [],
                "top_junctions": [], "hourly": Counter(),
                "fatal_junctions": [], "fatal_total": 0,
                "total_fatalities": 0, "total_casualties": 0,
            }

        severity = dict(qs.values_list("severity").annotate(c=Count("id")))

        vehicles = Counter()
        for vt in qs.values_list("vehicle_types", flat=True):
            for v in vt or []:
                vehicles[v] += 1

        # Top junctions
        junction_buckets = {}
        for a in qs.exclude(junction_name=""):
            j = a.junction_name
            if j not in junction_buckets:
                junction_buckets[j] = {"count": 0, "fatalities": 0, "casualties": 0}
            junction_buckets[j]["count"] += 1
            junction_buckets[j]["fatalities"] += a.fatalities
            junction_buckets[j]["casualties"] += a.casualties
        top_junctions = sorted(
            junction_buckets.items(), key=lambda x: -x[1]["count"]
        )[:10]

        # Hourly distribution
        hourly = Counter(a.occurred_at.hour for a in qs)

        # Fatal junctions (3+ fatal)
        fatal_junctions = [
            (name, d["fatalities"]) for name, d in junction_buckets.items()
            if d["fatalities"] >= 3
        ]
        fatal_junctions.sort(key=lambda x: -x[1])

        return {
            "total": total,
            "period_start": period_start,
            "period_end": period_end,
            "severity": severity,
            "vehicles": dict(vehicles),
            "top_junctions": top_junctions,
            "hourly": hourly,
            "fatal_junctions": fatal_junctions,
            "fatal_total": severity.get("fatal", 0),
            "total_fatalities": qs.aggregate(s=Sum("fatalities"))["s"] or 0,
            "total_casualties": qs.aggregate(s=Sum("casualties"))["s"] or 0,
        }

    def _build_story(self, d, period_start):
        """Build the PDF content as a list of flowables."""
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "TitleStyle", parent=styles["Title"],
            fontSize=22, textColor=colors.HexColor("#c0392b"),
            spaceAfter=20, alignment=TA_CENTER,
        )
        h2 = ParagraphStyle(
            "H2", parent=styles["Heading2"],
            fontSize=14, textColor=colors.HexColor("#1a3a52"),
            spaceBefore=15, spaceAfter=10,
        )
        body = ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontSize=10, leading=14,
        )
        small = ParagraphStyle(
            "Small", parent=styles["Normal"],
            fontSize=8, textColor=colors.grey,
        )

        # === Title ===
        story.append(Paragraph(
            f"Road Safety Dar es Salaam<br/>Monthly Report — {period_start:%B %Y}",
            title_style,
        ))
        story.append(Paragraph(
            f"<b>Period:</b> {d['period_start']:%Y-%m-%d} to {d['period_end']:%Y-%m-%d}<br/>"
            f"<b>Generated:</b> {timezone.now():%Y-%m-%d %H:%M} EAT<br/>"
            f"<b>System:</b> RoadSafety_Dar v1.2 (UN SDG 11.2 aligned)",
            body,
        ))
        story.append(Spacer(1, 0.5*cm))

        # === Executive Summary ===
        story.append(Paragraph("Executive Summary", h2))
        if d["total"] == 0:
            story.append(Paragraph(
                "No accident reports were recorded in this period. This is either a "
                "very safe month or an indication that the reporting system needs more "
                "outreach. We recommend continued public awareness campaigns.",
                body,
            ))
        else:
            summary = (
                f"During {period_start:%B %Y}, <b>{d['total']} road traffic incidents</b> "
                f"were reported across Dar es Salaam. Of these, "
                f"<b><font color='#c0392b'>{d['fatal_total']} were fatal</font></b> "
                f"({d['total_fatalities']} deaths, {d['total_casualties']} total casualties). "
                f"The most accident-prone junction was "
                f"<b>{d['top_junctions'][0][0]}</b> with {d['top_junctions'][0][1]['count']} incidents. "
            )
            if d["fatal_junctions"]:
                summary += (
                    f"<b>{len(d['fatal_junctions'])} junction(s)</b> recorded 3+ fatalities and "
                    f"require immediate engineering intervention. "
                )
            if d["hourly"]:
                peak_h = d["hourly"].most_common(1)[0][0]
                summary += (
                    f"The peak accident hour was <b>{peak_h:02d}:00</b>. "
                    f"Recommended action: deploy traffic police during this window."
                )
            story.append(Paragraph(summary, body))
        story.append(Spacer(1, 0.3*cm))

        # === KPI Summary Table ===
        story.append(Paragraph("Key Performance Indicators", h2))
        kpi_data = [
            ["Metric", "Value"],
            ["Total Incidents", str(d["total"])],
            ["Fatal Incidents", str(d["fatal_total"])],
            ["Total Deaths", str(d["total_fatalities"])],
            ["Total Casualties", str(d["total_casualties"])],
            ["Tracked Junctions Affected", str(len(d["top_junctions"]))],
            ["High-Risk Junctions (3+ deaths)", str(len(d["fatal_junctions"]))],
        ]
        kpi_table = Table(kpi_data, colWidths=[10*cm, 5*cm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a52")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 0.5*cm))

        # === Severity Breakdown ===
        if d["severity"]:
            story.append(Paragraph("Severity Distribution", h2))
            sev_data = [["Severity", "Count", "% of Total"]]
            for sev in ["fatal", "critical", "serious", "minor"]:
                if sev in d["severity"]:
                    count = d["severity"][sev]
                    pct = (count / d["total"]) * 100 if d["total"] > 0 else 0
                    sev_data.append([
                        sev.capitalize(),
                        str(count),
                        f"{pct:.1f}%",
                    ])
            sev_table = Table(sev_data, colWidths=[8*cm, 4*cm, 3*cm])
            sev_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a52")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
            ]))
            # Color code severity rows
            sev_colors = {
                "fatal": colors.HexColor("#fadbd8"),
                "critical": colors.HexColor("#fae5d3"),
                "serious": colors.HexColor("#fcf3cf"),
                "minor": colors.HexColor("#d5f5e3"),
            }
            for i, row in enumerate(sev_data[1:], start=1):
                sev_name = row[0].lower()
                if sev_name in sev_colors:
                    sev_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, i), (-1, i), sev_colors[sev_name]),
                    ]))
            story.append(sev_table)
            story.append(Spacer(1, 0.5*cm))

        # === Vehicle Types ===
        if d["vehicles"]:
            story.append(Paragraph("Vehicle Types Involved", h2))
            veh_data = [["Vehicle Type", "Incidents"]]
            for v, c in sorted(d["vehicles"].items(), key=lambda x: -x[1]):
                veh_data.append([v.replace("_", " ").title(), str(c)])
            veh_table = Table(veh_data, colWidths=[10*cm, 5*cm])
            veh_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a52")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
            ]))
            story.append(veh_table)
            story.append(Spacer(1, 0.5*cm))

        # === Top Junctions ===
        if d["top_junctions"]:
            story.append(Paragraph("Top 10 Junctions by Incidents", h2))
            junc_data = [["#", "Junction", "Incidents", "Deaths", "Casualties"]]
            for i, (name, data) in enumerate(d["top_junctions"], start=1):
                junc_data.append([
                    str(i), name, str(data["count"]),
                    str(data["fatalities"]), str(data["casualties"]),
                ])
            junc_table = Table(junc_data, colWidths=[1*cm, 7*cm, 3*cm, 2.5*cm, 2.5*cm])
            junc_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a52")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
            ]))
            story.append(junc_table)
            story.append(Spacer(1, 0.5*cm))

        # === Hourly Distribution (text-based bar chart) ===
        if d["hourly"]:
            story.append(PageBreak())
            story.append(Paragraph("Time-of-Day Analysis", h2))
            max_h = max(d["hourly"].values()) if d["hourly"] else 0
            hour_data = [["Hour", "Count", "Bar"]]
            for h in range(24):
                count = d["hourly"].get(h, 0)
                bar_len = int((count / max_h) * 30) if max_h > 0 else 0
                bar = "█" * bar_len
                hour_data.append([f"{h:02d}:00", str(count), bar])
            hour_table = Table(hour_data, colWidths=[3*cm, 2*cm, 10*cm])
            hour_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a52")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (2, 1), (2, -1), "Courier"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
            ]))
            # Highlight peak hours
            if d["hourly"]:
                peak_hour = d["hourly"].most_common(1)[0][0]
                hour_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, peak_hour + 1), (-1, peak_hour + 1), colors.HexColor("#f5b7b1")),
                ]))
            story.append(hour_table)
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(
                f"<b>Peak accident hour:</b> {d['hourly'].most_common(1)[0][0]:02d}:00 "
                f"({d['hourly'].most_common(1)[0][1]} incidents). "
                f"Recommend deploying traffic police during this window.",
                body,
            ))

        # === Critical Alerts ===
        if d["fatal_junctions"]:
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("⚠ CRITICAL ALERTS", h2))
            alert_data = [["Junction", "Fatalities", "Recommended Action"]]
            for name, deaths in d["fatal_junctions"]:
                action = "URGENT: Install speed camera + traffic police 24/7"
                if deaths >= 5:
                    action = "EMERGENCY: Road closure review + full engineering audit"
                alert_data.append([name, str(deaths), action])
            alert_table = Table(alert_data, colWidths=[5*cm, 2.5*cm, 8.5*cm])
            alert_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c0392b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fadbd8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(alert_table)

        # === Recommendations ===
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Recommended Actions for SUMATRA / TANROADS / Police", h2))
        recs = [
            "1. IMMEDIATE: Deploy traffic police during peak accident hours identified above.",
            "2. URGENT: Conduct engineering audit at all junctions with 3+ fatalities.",
            "3. TARGETED: Increase bodaboda helmet enforcement at high-motorcycle junctions.",
            "4. INFRASTRUCTURE: Install speed cameras and reflective road markings at top-10 hotspots.",
            "5. PUBLIC: Launch awareness campaign targeting peak hours and vehicle types.",
            "6. DATA: Continue community reporting — every submission improves our model.",
        ]
        for r in recs:
            story.append(Paragraph(r, body))
            story.append(Spacer(1, 0.2*cm))

        # === Footer ===
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            "<i>This report was generated automatically by RoadSafety_Dar v1.2. "
            "For questions, contact davie@roadsafety.local. "
            "Data is collected from community, police, hospital, and TANROADS sources. "
            "Verified records are marked in the public dashboard at /dashboard/.</i>",
            small,
        ))

        return story
