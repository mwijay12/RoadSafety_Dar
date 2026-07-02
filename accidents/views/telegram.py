"""
Telegram bot webhook — receive and respond to updates.
"""

import json
import logging
from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from ..models import visible_accidents

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def api_telegram_webhook(request):
    """POST /api/telegram/webhook/ — Telegram bot webhook for instant reports."""
    if request.method == "POST":
        try:
            update = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return HttpResponse("bad json", status=400)

        message = update.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if text == "/start" and chat_id:
            from accidents.telegram_bot import send_message

            send_message(
                chat_id,
                (
                    "🚦 *RoadSafety Dar Bot*\n\n"
                    "Welcome! Commands:\n"
                    "/stats — latest accident stats\n"
                    "/hotspots — top 5 dangerous junctions\n"
                    "/report — how to report an accident\n"
                    "/help — all commands"
                ),
            )
        elif text == "/stats" and chat_id:
            from accidents.telegram_bot import send_message

            qs = visible_accidents()
            total = qs.count()
            fatal = qs.filter(severity="fatal").count()
            last24 = qs.filter(occurred_at__gte=timezone.now() - timedelta(days=1)).count()
            send_message(
                chat_id,
                (
                    f"📊 *Live Stats*\n\n"
                    f"Total incidents: {total}\n"
                    f"Fatal: {fatal}\n"
                    f"Last 24h: {last24}\n"
                    f"\n🔗 https://roadsafety.co.tz/dashboard/"
                ),
            )
        elif text == "/hotspots" and chat_id:
            from accidents.telegram_bot import send_message

            from .public import _build_recommendation_engine_context

            ctx = _build_recommendation_engine_context()
            top = ctx["junction_buckets"] if ctx else {}
            top5 = sorted(top.items(), key=lambda x: -x[1]["count"])[:5]
            msg = "🔥 *Top 5 Hotspots*\n\n"
            for i, (name, b) in enumerate(top5, 1):
                msg += f"{i}. {name}: {b['count']} incidents, {b['fatalities']} deaths\n"
            send_message(chat_id, msg)
        elif text == "/help" and chat_id:
            from accidents.telegram_bot import send_message

            send_message(
                chat_id,
                (
                    "📚 *Commands*\n\n"
                    "/start — welcome\n"
                    "/stats — current stats\n"
                    "/hotspots — top 5 junctions\n"
                    "/report — how to report\n"
                    "/fatal — fatal incidents (24h)\n"
                    "/subscribe — get daily digest"
                ),
            )

        return HttpResponse("ok", content_type="text/plain")
    return HttpResponse("Telegram webhook — POST only", content_type="text/plain")
