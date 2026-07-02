"""
Management command: send_daily_digest

Sends a 24-hour summary of accident reports to all police/admin users who
have email_notifications enabled.

Usage:
    python manage.py send_daily_digest
    python manage.py send_daily_digest --dry-run  # preview only, no emails

Schedule via cron (or Render Cron Jobs free tier):
    0 7 * * * cd /app && .venv/bin/python manage.py send_daily_digest
"""

import logging
from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils import timezone

from accidents.models import Accident

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send a daily email digest of accident reports to authority users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview the digest without sending emails",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        since = now - timedelta(hours=24)

        qs = Accident.objects.filter(occurred_at__gte=since)
        total = qs.count()

        fatal_count = qs.filter(severity="fatal").count()
        critical_count = qs.filter(severity="critical").count()
        total_casualties = qs.aggregate(s=Sum("casualties"))["s"] or 0
        total_fatalities = qs.aggregate(s=Sum("fatalities"))["s"] or 0

        # Find worst junction
        junction_counts = Counter()
        for a in qs.exclude(junction_name=""):
            junction_counts[a.junction_name] += 1
        top_junction = junction_counts.most_common(1)
        top_junction_name = top_junction[0][0] if top_junction else None
        top_junction_count = top_junction[0][1] if top_junction else 0

        context = {
            "date": now.strftime("%Y-%m-%d"),
            "total": total,
            "fatal_count": fatal_count,
            "critical_count": critical_count,
            "total_casualties": total_casualties,
            "total_fatalities": total_fatalities,
            "top_junction": top_junction_name,
            "top_junction_count": top_junction_count,
            "dashboard_url": f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/dashboard/",
            "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
        }

        recipients = list(
            User.objects.filter(
                profile__role__in=("police", "admin"),
                profile__email_notifications=True,
            )
            .exclude(email="")
            .values_list("email", flat=True)
        )

        if not recipients:
            self.stdout.write(self.style.WARNING("No authority recipients found. Skipping."))
            return

        subject = f"[RoadSafety Dar] Daily Digest — {context['date']}"
        html_message = render_to_string("emails/digest.html", context)
        plain_message = (
            f"Daily Digest — {context['date']}\n"
            f"Total incidents (24h): {total}\n"
            f"Fatal: {fatal_count}  Critical: {critical_count}\n"
            f"Casualties: {total_casualties}  Fatalities: {total_fatalities}\n"
            f"Worst junction: {top_junction_name or 'N/A'} ({top_junction_count} incidents)\n"
            f"View dashboard: {context['dashboard_url']}"
        )

        if options["dry_run"]:
            self.stdout.write(f"[DRY-RUN] Would send to {len(recipients)} recipients:")
            for r in recipients:
                self.stdout.write(f"  - {r}")
            self.stdout.write(f"  Subject: {subject}")
            self.stdout.write(f"  Body: {plain_message[:200]}...")
            return

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Digest sent to {len(recipients)} recipients ({total} incidents, "
                    f"{fatal_count} fatal)"
                )
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to send digest: {e}"))
