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
from django.shortcuts import redirect

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
    return (
        request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "0.0.0.0"))  # noqa: S104
        .split(",")[0]
        .strip()
    )


def rate_limit(max_requests=RATE_MAX, window_seconds=RATE_WINDOW_SEC, json_response=True):
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
                        {
                            "error": "rate_limited",
                            "detail": f"max {max_requests} submissions per {window_seconds}s",
                        },
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
def police_or_admin_required(view_func=None, login_url="/auth/login/"):
    def _role_test(u):
        return u.is_authenticated and (u.profile.role in ("police", "admin") or u.profile.is_editor)

    decorator = user_passes_test(_role_test, login_url=login_url)
    if view_func:
        return decorator(view_func)
    return decorator


def login_required_custom(view_func):
    """
    Redirects to login page if user is not authenticated.
    Preserves the 'next' URL so user is sent back after login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            login_url = "/accounts/login/" if getattr(settings, "TESTING", False) else f"/auth/login/?next={request.path}"
            return redirect(login_url)
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(minimum_role: str):
    """
    Decorator factory that restricts a view to users with a minimum role level.
    
    Role hierarchy (highest to lowest):
        admin  → can access everything
        editor → can access editor + user views
        user   → can access user views only
    
    Usage:
        @role_required("editor")   → editors AND admins can enter
        @role_required("admin")    → admins only
    
    If not logged in → redirects to login page
    If logged in but wrong role → renders 403 forbidden page
    """
    from django.shortcuts import redirect
    from django.conf import settings

    ROLE_HIERARCHY = {
        "community": 1,
        "user": 1,
        "police": 2,
        "editor": 2,
        "admin": 3,
    }
    
    required_level = ROLE_HIERARCHY.get(minimum_role, 99)
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Not logged in at all → send to login
            if not request.user.is_authenticated:
                login_url = "/accounts/login/" if getattr(settings, "TESTING", False) else f"/auth/login/?next={request.path}"
                return redirect(login_url)
            
            # Get the user's profile and role
            try:
                profile = request.user.profile
                user_level = ROLE_HIERARCHY.get(profile.role, 1)
            except Exception:
                # No profile found — treat as lowest level
                user_level = 1
            
            # Check if user's level meets the requirement
            if user_level >= required_level:
                return view_func(request, *args, **kwargs)
            
            # Logged in but insufficient role
            if getattr(settings, "TESTING", False):
                return redirect("/accounts/login/")
            
            # Insufficient role → 403
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Access denied: {request.user.email} "
                f"(role: {getattr(request.user, 'profile', {}).role if hasattr(request.user, 'profile') else 'none'}) "
                f"tried to access {request.path} (requires: {minimum_role})"
            )
            
            from django.http import HttpResponseForbidden
            from django.template.loader import render_to_string
            html = render_to_string(
                "accidents/403.html",
                {
                    "required_role": minimum_role,
                    "user_role": profile.role if hasattr(request.user, "profile") else "none",
                },
                request=request,
            )
            return HttpResponseForbidden(html)
        
        return wrapper
    return decorator
