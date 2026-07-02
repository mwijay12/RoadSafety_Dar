"""
Base Django settings for RoadSafety_Dar.

SDG 11.2 alignment: safer urban transport in Dar es Salaam.
Local dev uses SQLite so the project runs out-of-the-box.
For production spatial queries, swap DATABASE_URL to PostGIS.

All values that vary between dev and prod live in ``dev.py`` and ``prod.py``.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-insecure-key-change-me-1234567890abcdefghijklmnopqrstuvwxyz",
)
DEBUG = False  # overridden by dev.py / prod.py
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]  # overridden in prod

# ── CSRF Trusted Origins ──────────────────────────────────────────────────────
# Required for POST requests on HTTPS domains (Render, custom domain)
# Add your Render URL here once you know it
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",       # all Render subdomains
    "http://localhost:8000",         # local dev
    "http://127.0.0.1:8000",        # local dev
]

INSTALLED_APPS = [
    "accidents.apps.AccidentsConfig",  # first so templates override admin/allauth
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "corsheaders",
    "turnstile",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "accidents.middleware.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "roadsafety.urls"
WSGI_APPLICATION = "roadsafety.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database: SQLite by default, swap to PostGIS in prod via DATABASE_URL
# ---------------------------------------------------------------------------
_db_url = os.getenv("DATABASE_URL")
if not _db_url:
    _sqlite_path = BASE_DIR / "db.sqlite3"
    if os.environ.get("VERCEL") == "1":
        # Vercel functions are read-only except /tmp
        _sqlite_path = Path("/tmp") / "db.sqlite3"
        _src_db = BASE_DIR / "db.sqlite3"
        if _src_db.exists() and not _sqlite_path.exists():
            import shutil
            try:
                shutil.copy2(_src_db, _sqlite_path)
            except Exception:
                pass
    _db_url = f"sqlite:///{_sqlite_path}"

DATABASES = {
    "default": dj_database_url.config(
        default=_db_url, conn_max_age=600
    )
}

# Force in-memory SQLite for all test runs (both pytest and manage.py test)
import sys
if "test" in sys.argv or any("pytest" in arg for arg in sys.argv):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
    TESTING = True



# ---------------------------------------------------------------------------
# Auth — Django AllAuth (email + password, no social providers yet)
# ---------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

SITE_ID = 1

ACCOUNT_LOGIN_REDIRECT_URL = "/dashboard/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_EMAIL_VERIFICATION = (
    "none"  # skip email verification for MVP (set to "optional" to enable)
)
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_NOTIFICATIONS = True
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en"
TIME_ZONE = "Africa/Dar_es_Salaam"
USE_I18N = True
USE_TZ = True

# Supported languages (v1.1 — Swahili added)
LANGUAGES = [
    ("en", "English"),
    ("sw", "Kiswahili"),
]
LOCALE_PATHS = [BASE_DIR / "accidents" / "locale"]

# ---------------------------------------------------------------------------
# AI provider configuration — multi-provider with graceful fallback.
# Primary: Groq (free tier, Llama 3.3 70B).
# Fallback 1: Cloudflare Workers AI (free 10k neurons/day).
# Fallback 2: Google Gemini 2.5 Flash (free 15 req/min).
# Last resort: rule-based engine in accidents/services/recommendations.py.
# Legacy: OpenRouter kept for backward compatibility with v1.1.
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_BASE = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1")

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_AI_MODEL = os.getenv("CLOUDFLARE_AI_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Legacy OpenRouter (kept so existing v1.1 code paths keep working)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "minimax/minimax-m3")

# ElevenLabs (TTS Alerts & Recommendations)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")


# ---------------------------------------------------------------------------
# Media storage — Cloudinary (free tier: 25 GB, 25k transforms/mo)
# Wired up in Prompt 3 (Public Report Flow v2). Keys are read here so all
# settings modules can reference them uniformly.
# ---------------------------------------------------------------------------
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")  # cloudinary://key:secret@cloud

# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")  # 3k emails/mo free
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "roadsafetydar@gmail.com")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "roadsafetydar@gmail.com")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

AFRICASTALKING_USERNAME = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
AFRICASTALKING_API_KEY = os.getenv("AFRICASTALKING_API_KEY", "")
AFRICASTALKING_SENDER_ID = os.getenv("AFRICASTALKING_SENDER_ID", "RoadSafety")

# ---------------------------------------------------------------------------
# Anti-spam — Cloudflare Turnstile (free, privacy-respecting CAPTCHA)
# ---------------------------------------------------------------------------
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY", "1x00000000000000000000AA")
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "0x00000000000000000000AA")
TURNSTILE_VERIFICATION_URL = os.getenv("TURNSTILE_VERIFICATION_URL", "http://localhost:8000/")

# ---------------------------------------------------------------------------
# Caching + background jobs — Upstash Redis free tier (10k commands/day)
# Optional in dev (falls back to LocMem); required for prod with real traffic.
# ---------------------------------------------------------------------------
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "")
REDIS_URL = os.getenv("REDIS_URL", UPSTASH_REDIS_URL)

# ---------------------------------------------------------------------------
# Monitoring — Sentry free tier (5k events/mo)
# Wired up in prod.py; the DSN is read here so base.py stays the source of truth.
# ---------------------------------------------------------------------------
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "production")

# ---------------------------------------------------------------------------
# Email backend — overridden in dev.py (console) and prod.py (Resend / SMTP)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_TIMEOUT = 10

# ---------------------------------------------------------------------------
# Static files — WhiteNoise serves compressed, cache-busted assets in prod.
# In dev the dev.py module uses the non-manifest storage; prod.py switches it.
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "accidents" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS — allowlist origins for third-party API consumers (Prompt 7).
# Comma-separated list in env var CORS_ALLOWED_ORIGINS (default: empty = no CORS).
# Set to "*" in dev for local frontends (not recommended for prod).
# ---------------------------------------------------------------------------
_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Base security headers — safe in dev, required in prod. prod.py tightens
# the cookie / HSTS / SSL settings further.
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Session/CSRF cookie name (kept consistent so deployments don't lose sessions)
SESSION_COOKIE_NAME = "roadsafety_sessionid"
CSRF_COOKIE_NAME = "roadsafety_csrftoken"

# ── Supabase Config ─────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

# ── Auth Settings ─────────────────────────────────────────────────────────────
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = os.environ.get("LOGIN_REDIRECT_URL", "/dashboard/")
LOGOUT_REDIRECT_URL = os.environ.get("LOGOUT_REDIRECT_URL", "/")

# Session settings — 7-day login persistence
SESSION_COOKIE_AGE = 86400 * 7        # 7 days in seconds
SESSION_COOKIE_HTTPONLY = True         # JS cannot read session cookie
SESSION_SAVE_EVERY_REQUEST = True      # refresh session on each request

