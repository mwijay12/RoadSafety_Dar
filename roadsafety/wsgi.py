"""WSGI config — production-ready for Railway/Render/Fly.io/gunicorn.

Selects the settings module based on DJANGO_ENV (defaults to ``prod``).
Set ``DJANGO_ENV=dev`` for local runs.
"""

import os

from django.core.wsgi import get_wsgi_application

django_env = os.getenv("DJANGO_ENV", "prod").lower()
if django_env not in {"dev", "prod"}:
    django_env = "prod"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"roadsafety.settings.{django_env}")
application = get_wsgi_application()

# Expose version info at WSGI level for deployment scripts
from roadsafety.version import version_info  # noqa: E402

WSGI_VERSION = version_info()
