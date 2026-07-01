"""
Development settings — inherits everything from base.py and loosens the
security + debug toggles so the project runs locally with no extra config.

Activate with:
    export DJANGO_SETTINGS_MODULE=roadsafety.settings.dev
    # (or just run ``python manage.py runserver`` — it defaults to dev)
"""
from .base import *  # noqa: F401,F403
from .base import BASE_DIR, REDIS_URL  # explicit re-import for clarity

DEBUG = True

# Permissive in dev: any host is allowed so the project works behind
# ngrok / localtunnel / LAN IPs without further configuration.
ALLOWED_HOSTS = ["*"]

# Console email backend prints messages to the runserver terminal — never
# accidentally send real emails during development.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# In-memory cache: zero-config, fine for the SQLite dev workflow.
# Upstash / Redis is only wired in prod.py.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "roadsafety-dev-cache",
    }
}

# Dev-only: enable Django's debug page for unhandled exceptions
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Serve static files via the dev runserver, not WhiteNoise's manifest storage.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Loosen security: don't force HTTPS cookies when there's no TLS locally.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
