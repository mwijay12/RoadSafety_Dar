"""
Production settings — locked-down, cache-first, monitored.

Activate with:
    export DJANGO_SETTINGS_MODULE=roadsafety.settings.prod

Required environment variables in production (see .env.example for the full
list and free-tier source links):
    DJANGO_SECRET_KEY   long, random; generate with secrets.token_urlsafe(60)
    DEBUG               False (forced below)
    ALLOWED_HOSTS       comma-separated list of public hostnames
    DATABASE_URL        sqlite:///... for demos, postgis://... for real traffic
    SENTRY_DSN          optional but recommended; Sentry free tier = 5k events/mo
    REDIS_URL           optional but recommended; Upstash free tier = 10k cmd/day
    RESEND_API_KEY      optional; Resend free tier = 3k emails/mo
    CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, GROQ_API_KEY, GEMINI_API_KEY
                        optional; used by the AI recommendation engine
    CLOUDINARY_*        optional; enables photo / video evidence uploads
    TURNSTILE_SITE_KEY, TURNSTILE_SECRET_KEY
                        optional; enables Cloudflare Turnstile CAPTCHA
    TELEGRAM_BOT_TOKEN  optional; enables the Telegram bot integration
"""

import logging
import os

from .base import *  # noqa: F401,F403
from .base import (
    REDIS_URL,
    RESEND_API_KEY,
    SENTRY_DSN,
    SENTRY_ENVIRONMENT,
    SENTRY_TRACES_SAMPLE_RATE,
)

DEBUG = False

# ALLOWED_HOSTS is required in production. We read it from the env (comma
# separated) but fall back to a safe default that will still be rejected by
# Django if DEBUG is False and the host doesn't match.
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()] or [
    ".onrender.com",
    ".railway.app",
    ".fly.dev",
    ".herokuapp.com",
    ".vercel.app",
]

# ---------------------------------------------------------------------------
# Cookies + TLS — full lockdown behind the Cloudflare / load balancer proxy.
# ---------------------------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# WhiteNoise manifest storage for cache-busted, fingerprinted static assets.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------------------------------------------------------------------
# Cache — Upstash Redis (free tier) when REDIS_URL is set, else local memory.
# Local-memory cache is still safe in prod for a single-worker demo but
# breaks the moment you scale to 2+ gunicorn workers, so Redis is the path.
# ---------------------------------------------------------------------------
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "roadsafety",
            "TIMEOUT": 60 * 5,  # 5-minute default
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "roadsafety-prod-cache",
        }
    }

# ---------------------------------------------------------------------------
# Email — Resend if the API key is set, else Django's SMTP backend (which
# reads EMAIL_HOST / EMAIL_PORT / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD).
# ---------------------------------------------------------------------------
if RESEND_API_KEY:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.resend.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "resend")
    EMAIL_HOST_PASSWORD = RESEND_API_KEY

# ---------------------------------------------------------------------------
# Sentry — wire up only if SENTRY_DSN is present, so dev runs never touch
# the network or count against the free tier.
# ---------------------------------------------------------------------------
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=False,
            environment=SENTRY_ENVIRONMENT,
            release=os.getenv("GIT_COMMIT_SHA", "unknown"),
        )
    except ImportError:
        logging.getLogger(__name__).warning(
            "SENTRY_DSN is set but sentry-sdk is not installed; skipping init."
        )

# ---------------------------------------------------------------------------
# Logging — JSON-ish structured logs in production so log aggregators
# (Papertrail, Logtail, BetterStack free tier) can parse them.
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "accidents": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
