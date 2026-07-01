"""
Telegram bot integration for RoadSafety_Dar v1.2.

Two modes:
1. Webhook mode (production) — Telegram POSTs updates to /api/telegram/webhook/
2. Polling mode (local dev) — run `python manage.py telegram_poll`

Set TELEGRAM_BOT_TOKEN in .env to enable. Without a token, the integration
is dormant and never calls the API.
"""
import json
import logging
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _get_token():
    """Get Telegram bot token from env. Returns None if not set."""
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or None


def _api_url(method):
    token = _get_token()
    if not token:
        return None
    return TELEGRAM_API_BASE.format(token=token, method=method)


def send_message(chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
    """Send a message to a Telegram chat. Returns True on success.

    Silently no-ops if no TELEGRAM_BOT_TOKEN is set.
    """
    url = _api_url("sendMessage")
    if not url:
        logger.debug("TELEGRAM_BOT_TOKEN not set — skipping send_message")
        return False

    payload = urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode()

    try:
        req = Request(url, data=payload, method="POST")
        with urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        if not data.get("ok"):
            logger.warning("Telegram API error: %s", data)
            return False
        return True
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)
        return False


def send_fatal_alert(chat_id: int, junction: str, deaths: int, period: str = "7 days") -> bool:
    """Send a formatted fatal cluster alert."""
    msg = (
        f"🚨 *FATAL CLUSTER DETECTED*\n\n"
        f"Junction: *{junction}*\n"
        f"Deaths: *{deaths}*\n"
        f"Window: {period}\n\n"
        f"⚠ Immediate action required.\n"
        f"🔗 https://roadsafety.co.tz/authority/"
    )
    return send_message(chat_id, msg, parse_mode="Markdown")


def broadcast_stats(chat_ids: list, total: int, fatal: int) -> int:
    """Send daily stats to a list of subscribers. Returns success count."""
    msg = (
        f"📊 *Daily Road Safety Digest*\n\n"
        f"📍 Total incidents: {total}\n"
        f"💀 Fatal: {fatal}\n\n"
        f"View live: https://roadsafety.co.tz/dashboard/"
    )
    success = 0
    for cid in chat_ids:
        if send_message(cid, msg):
            success += 1
    return success
