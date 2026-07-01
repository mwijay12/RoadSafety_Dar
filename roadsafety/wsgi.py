"""WSGI config — production-ready for Railway/Render/gunicorn."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roadsafety.settings")
application = get_wsgi_application()

# Expose version info at WSGI level for deployment scripts
from roadsafety.version import version_info  # noqa: E402
WSGI_VERSION = version_info()
