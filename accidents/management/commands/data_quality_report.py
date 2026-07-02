"""
Management command: data_quality_report

Generates a data quality scorecard for accident records, helping admin
users identify incomplete, suspicious, or outlier reports.

Usage:
    python manage.py data_quality_report
    python manage.py data_quality_report --output markdown  # plain|markdown
"""

import logging
from collections import Counter
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from accidents.models import SEVERITY_CHOICES, Accident

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate data quality scorecard for accident records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="plain",
            choices=["plain", "markdown"],
            help="Output format (default: plain)",
        )

    def _pct(self, part, total):
        if not total:
            return 0.0
        return round((part / total) * 100, 1)

    def _fmt(self, label, value, md=False):
        if md:
            return f"| {label} | {value} |"
        return f"  {label}: {value}"

    def handle(self, *args, **options):
        md = options["output"] == "markdown"
        out = self.stdout.write
        qs = Accident.objects.all()
        total = qs.count()

        if total == 0:
            out(self.style.WARNING("No accident records to analyse."))
            return

        # --- Completeness ---
        has_desc = qs.exclude(description="").count()
        has_weather = qs.exclude(weather="").count()
        has_road = qs.exclude(road_condition="").count()
        has_junction_name = qs.exclude(junction_name="").count()
        qs.exclude(junction=None).count()
        has_contact = qs.exclude(contact="").count()
        qs.exclude(source_notes="").count()
        has_all_five = (
            qs.exclude(description="")
            .exclude(weather="")
            .exclude(road_condition="")
            .exclude(junction_name="")
            .exclude(contact="")
            .count()
        )

        # --- Verification ---
        verified = qs.filter(verified=True).count()
        unverified = total - verified

        # --- Severity distribution ---
        severity_counts = {s: qs.filter(severity=s).count() for s, _ in SEVERITY_CHOICES}

        # --- Vehicle type distribution ---
        vehicle_counter = Counter()
        for obj in qs.iterator():
            for vt in obj.vehicle_types or []:
                vehicle_counter[vt] += 1

        # --- Temporal gaps ---
        old_unverified = qs.filter(
            verified=False,
            occurred_at__lt=timezone.now() - timedelta(days=30),
        ).count()

        # --- District coverage (via Junction) ---
        district_data = list(
            Accident.objects.values("junction__district")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # --- Output ---
        sep = "#" if md else "="

        def h(s):
            out(self.style.MIGRATE_LABEL(f"\n{sep * 4} {s} {sep * 4}"))

        def line():
            out("-" * 55)

        if md:
            out("# Data Quality Report")
            out(f"\nGenerated: {timezone.now():%Y-%m-%d %H:%M}")
            line()

        h("Overview")
        self._report_row(md, out, "Total records", str(total))
        self._report_row(
            md,
            out,
            "Date range",
            f"{qs.earliest('occurred_at').occurred_at.date() if total else 'N/A'} — "
            f"{qs.latest('occurred_at').occurred_at.date() if total else 'N/A'}",
        )
        line()

        h("Completeness")
        self._report_row(
            md, out, "Description filled", f"{has_desc} ({self._pct(has_desc, total)}%)"
        )
        self._report_row(
            md, out, "Weather filled", f"{has_weather} ({self._pct(has_weather, total)}%)"
        )
        self._report_row(
            md, out, "Road condition filled", f"{has_road} ({self._pct(has_road, total)}%)"
        )
        self._report_row(
            md,
            out,
            "Junction name filled",
            f"{has_junction_name} ({self._pct(has_junction_name, total)}%)",
        )
        self._report_row(
            md, out, "Contact filled", f"{has_contact} ({self._pct(has_contact, total)}%)"
        )
        self._report_row(
            md,
            out,
            "All 5 core fields filled",
            f"{has_all_five} ({self._pct(has_all_five, total)}%)",
        )
        line()

        h("Verification")
        self._report_row(md, out, "Verified", f"{verified} ({self._pct(verified, total)}%)")
        self._report_row(md, out, "Unverified", f"{unverified} ({self._pct(unverified, total)}%)")
        self._report_row(md, out, "Old unverified (30+ days)", str(old_unverified))
        line()

        h("Severity Distribution")
        for severity, label in SEVERITY_CHOICES:
            c = severity_counts.get(severity, 0)
            self._report_row(md, out, label, f"{c} ({self._pct(c, total)}%)")
        line()

        h("Vehicle Type Distribution")
        for vt, count in vehicle_counter.most_common():
            self._report_row(md, out, vt, str(count))
        line()

        h("District Coverage (via Junction FK)")
        if district_data:
            for d in district_data:
                district = d["junction__district"] or "Unassigned"
                self._report_row(md, out, district, str(d["count"]))
        else:
            self._report_row(md, out, "No junction FKs", "N/A")
        line()

        # --- Overall score ---
        completeness_score = self._pct(has_all_five, total)
        verification_score = self._pct(verified, total)
        overall = round((completeness_score * 0.5 + verification_score * 0.5), 1)
        grade = "A" if overall >= 90 else "B" if overall >= 75 else "C" if overall >= 50 else "D"

        h("Overall Data Quality Score")
        self._report_row(md, out, "Completeness (weighted 50%)", f"{completeness_score}%")
        self._report_row(md, out, "Verification (weighted 50%)", f"{verification_score}%")
        self._report_row(md, out, "Overall Score", f"{overall}%")
        self._report_row(md, out, "Grade", grade)

    def _report_row(self, md, out, label, value):
        out(self._fmt(label, value, md))
