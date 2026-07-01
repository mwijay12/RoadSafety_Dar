"""
Django settings package for RoadSafety_Dar.

Usage:
    export DJANGO_SETTINGS_MODULE=roadsafety.settings.dev   # local development
    export DJANGO_SETTINGS_MODULE=roadsafety.settings.prod  # production

The split keeps environment-specific secrets and toggles out of the common
base, so deploying to Railway / Render / Hetzner only requires setting the
DJANGO_SETTINGS_MODULE env var to ``prod`` and the rest of the env vars.
"""
