"""
Signal handlers for accident-related email notifications.

- fatal/critical accident created → email alert to police/admin users
- Uses console backend in dev, Resend SMTP in production
"""

import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from .models import Accident

logger = logging.getLogger(__name__)


def _get_authority_recipients():
    """Return list of email addresses for police/admin users who have
    email_notifications enabled."""
    return list(
        User.objects.filter(
            profile__role__in=("police", "admin"),
            profile__email_notifications=True,
        )
        .exclude(email="")
        .values_list("email", flat=True)
    )


@receiver(post_save, sender=Accident)
def notify_authorities_on_fatal(sender, instance, created, **kwargs):
    """Send email alert to all authority users when a fatal/critical
    accident is created."""
    if not created:
        return
    if instance.severity not in ("fatal", "critical"):
        return

    recipients = _get_authority_recipients()
    if not recipients:
        return

    sev = instance.get_severity_display()
    subject = f"[RoadSafety Dar] {sev} Accident Reported at {instance.junction_name or 'Unknown Location'}"

    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
    context = {
        "accident": instance,
        "severity": sev,
        "dashboard_url": f"{site_url}/dashboard/",
        "authority_url": f"{site_url}/authority/",
    }

    html_message = render_to_string("emails/alert_fatal.html", context)
    plain_message = (
        f"A {sev} accident was reported at {instance.junction_name or 'unknown location'}.\n"
        f"Date: {instance.occurred_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"Casualties: {instance.casualties}  Fatalities: {instance.fatalities}\n"
        f"Vehicles: {', '.join(instance.vehicle_types or [])}\n\n"
        f"View on authority dashboard: {context['authority_url']}"
    )

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Alert sent to %d recipients for accident #%d", len(recipients), instance.id)
    except Exception as e:
        logger.error("Failed to send accident alert email: %s", e)
