"""
Backward-compat shim — re-exports everything from the views/ package.

All view functions remain accessible as ``accidents.views.<name>`` so
existing imports in urls.py, tests.py, and templates keep working.
"""
from accidents.views import *  # noqa: F401,F403
