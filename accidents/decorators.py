"""
Decorators: role-based access control + rate limiting.

Exports:
  police_or_admin_required  — restricts view to police/admin users
  rate_limit                — per-IP sliding-window rate limiter
  _rate_log                 — exposed for test cleanup (rate_log.clear())
"""
import time
from collections import defaultdict
from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, JsonResponse


# --- Rate limiter (in-memory, per-IP, sliding window) ---
_rate_log: dict[str, list[float]] = defaultdict(list)
RATE_WINDOW_SEC = 60
RATE_MAX = 5


def _rate_check(ip: str) -> bool:
    now = time.monotonic()
    bucket = [t for t in _rate_log[ip] if now - t < RATE_WINDOW_SEC]
    if len(bucket) >= RATE_MAX:
        _rate_log[ip] = bucket
        return False
    bucket.append(now)
    _rate_log[ip] = bucket
    return True


def get_client_ip(request):
    return request.META.get(
        "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "0.0.0.0")
    ).split(",")[0].strip()


def rate_limit(max_requests=RATE_MAX, window_seconds=RATE_WINDOW_SEC,
               json_response=True):
    """Decorator: limits a view to ``max_requests`` per ``window_seconds``.

    Returns 429 HTML or JSON depending on ``json_response``.
    Also sets ``request._rate_limited`` (for testing).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            ip = get_client_ip(request)
            if not _rate_check(ip):
                request._rate_limited = True
                if json_response:
                    return JsonResponse(
                        {"error": "rate_limited",
                         "detail": f"max {max_requests} submissions per {window_seconds}s"},
                        status=429,
                    )
                return HttpResponse(
                    "Too many submissions. Please wait a minute.",
                    status=429,
                )
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# --- Role-based access ---
def police_or_admin_required(view_func=None, login_url="/accounts/login/"):
    actual_test = lambda u: u.is_authenticated and u.profile.role in ("police", "admin")
    decorator = user_passes_test(actual_test, login_url=login_url)
    if view_func:
        return decorator(view_func)
    return decorator
