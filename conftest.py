"""
Pytest configuration for RoadSafety_Dar.

Django settings live in ``roadsafety.settings.dev`` so tests never touch
production secrets or the network. Add shared fixtures below as the test
suite grows.
"""
import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roadsafety.settings.dev")
django.setup()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear the in-memory rate limiter between tests.

    The rate limiter in ``accidents.views`` is a module-level dict that
    otherwise carries state from one test into the next and causes flaky
    429 responses.
    """
    from accidents.views import _rate_log

    _rate_log.clear()
    yield
    _rate_log.clear()
