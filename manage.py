#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks.

    Selects the settings module based on DJANGO_ENV (defaults to ``dev``).
    Set ``DJANGO_ENV=prod`` in production. The split lives in
    ``roadsafety/settings/{base,dev,prod}.py``.
    """
    django_env = os.getenv("DJANGO_ENV", "dev").lower()
    if django_env not in {"dev", "prod"}:
        django_env = "dev"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"roadsafety.settings.{django_env}")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
