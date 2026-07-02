"""WSGI config — production-ready for Railway/Render/Fly.io/gunicorn.

Selects the settings module based on DJANGO_ENV (defaults to ``prod``).
Set ``DJANGO_ENV=dev`` for local runs.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path for serverless environments (like Vercel)
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from django.core.wsgi import get_wsgi_application

django_env = os.getenv("DJANGO_ENV", "prod").lower()
if django_env not in {"dev", "prod"}:
    django_env = "prod"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"roadsafety.settings.{django_env}")
application = get_wsgi_application()
app = application

# Expose version info at WSGI level for deployment scripts
from roadsafety.version import version_info  # noqa: E402

WSGI_VERSION = version_info()
