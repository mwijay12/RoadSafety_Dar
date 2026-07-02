import os
from django.core.wsgi import get_wsgi_application

django_env = os.environ.get("DJANGO_ENV", "prod")

settings_map = {
    "dev": "roadsafety.settings.dev",
    "prod": "roadsafety.settings.prod",
}

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    settings_map.get(django_env, "roadsafety.settings.prod")
)

application = get_wsgi_application()
