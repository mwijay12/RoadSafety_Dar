"""
Management command: detect_fatal_clusters

Scans the accident database for junctions where 3+ fatal accidents
occurred within 7 days. Logs to console and (optionally) sends email
notifications to a configured list.

Usage:
    python manage.py detect_fatal_clusters
    python manage.py detect_fatal_clusters --days 7 --min-fatal 3
    python manage.py detect_fatal_clusters --email admin@example.com
"""
import logging
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from accidents.models import Accident

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Detect clusters of fatal accidents at the same junction and alert."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Window in days to look back (default: 7)",
        )
        parser.add_argument(
            "--min-fatal",
            type=int,
            default=3,
            help="Minimum fatal accidents to trigger alert (default: 3)",
        )
        parser.add_argument(
            "--email",
            type=str,
            default=None,
            help="Optional email address to send alerts to",
        )

    def handle(self, *args, **options):
        days = options["days"]
        min_fatal = options["min_fatal"]
        email_to = options.get("email")

        window_start = timezone.now() - timedelta(days=days)

        # Group recent fatal accidents by junction
        recent_fatal = Accident.objects.filter(
            severity="fatal",
            occurred_at__gte=window_start,
        ).exclude(junction_name="")

        junction_counts = defaultdict(lambda: {"count": 0, "accidents": []})
        for a in recent_fatal:
            junction_counts[a.junction_name]["count"] += 1
            junction_counts[a.junction_name]["accidents"].append(a)

        # Filter to clusters
        clusters = {
            name: data
            for name, data in junction_counts.items()
            if data["count"] >= min_fatal
        }

        self.stdout.write(
            self.style.NOTICE(
                f"\n=== Fatal Cluster Detection (window: {days}d, threshold: {min_fatal}) ==="
            )
        )
        self.stdout.write(
            f"Scanned {recent_fatal.count()} fatal accidents since {window_start.date()}"
        )

        if not clusters:
            self.stdout.write(
                self.style.SUCCESS("✅ No fatal clusters detected. All clear.")
            )
            return

        # Report each cluster
        for junction, data in clusters.items():
            count = data["count"]
            total_fatalities = sum(a.fatalities for a in data["accidents"])
            self.stdout.write(
                self.style.ERROR(
                    f"\n🚨 ALERT: {junction} — {count} fatal accidents "
                    f"({total_fatalities} deaths) in {days} days"
                )
            )
            for a in data["accidents"]:
                self.stdout.write(
                    f"   - {a.occurred_at:%Y-%m-%d %H:%M} | "
                    f"fatalities: {a.fatalities} | "
                    f"vehicles: {','.join(a.vehicle_types or [])} | "
                    f"verified: {'YES' if a.verified else 'NO'}"
                )

        # Optional email notification
        if email_to:
            subject = (
                f"[RoadSafety Dar] {len(clusters)} fatal cluster(s) detected in last {days}d"
            )
            body_lines = [
                f"Fatal cluster alert — {timezone.now():%Y-%m-%d %H:%M}",
                "",
                f"Window: last {days} days",
                f"Threshold: {min_fatal}+ fatal accidents",
                "",
            ]
            for junction, data in clusters.items():
                body_lines.append(
                    f"- {junction}: {data['count']} fatal accidents"
                )
            body_lines += [
                "",
                "Recommended action: deploy traffic police, install speed camera,",
                "coordinate with TANROADS for engineering review.",
                "",
                "— RoadSafety Dar automation",
            ]
            try:
                send_mail(
                    subject=subject,
                    message="\n".join(body_lines),
                    from_email=getattr(
                        settings, "DEFAULT_FROM_EMAIL", "noreply@roadsafety.local"
                    ),
                    recipient_list=[email_to],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"\n📧 Email alert sent to {email_to}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"\n⚠ Email send failed: {e}")
                )

        # Exit with non-zero status code if clusters found (useful for cron)
        if clusters:
            raise SystemExit(1)
