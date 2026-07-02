# accidents/auth_views.py
"""
Authentication views for Road Safety Dar es Salaam.

Routes handled:
    GET  /auth/login/      → Show login page with Google button
    GET  /auth/google/     → Redirect to Supabase Google OAuth
    GET  /auth/callback/   → Handle Supabase callback, create session
    POST /auth/callback/process/   → Handle Supabase process callback
    POST /auth/logout/     → Clear session, redirect home
"""

import logging

from django.conf import settings
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from accidents.services.supabase_auth import (
    get_or_create_django_user,
    verify_supabase_jwt,
)

logger = logging.getLogger(__name__)


# ── Login Page ────────────────────────────────────────────────────────────────

def login_page(request):
    """
    GET /auth/login/
    
    Shows the login page with a Google sign-in button.
    If user is already logged in, redirect to dashboard.
    """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    # Pass 'next' URL through to the template so we can
    # redirect back after login
    next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
    
    return render(request, "accidents/login.html", {
        "next": next_url,
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY,
    })


# ── Google OAuth Redirect ─────────────────────────────────────────────────────

def google_oauth_redirect(request):
    """
    GET /auth/google/
    
    Redirects the user to Supabase's Google OAuth URL.
    Supabase handles the entire Google OAuth dance and then
    redirects back to /auth/callback/ with a JWT token.
    """
    next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
    
    # Build the Supabase OAuth URL
    supabase_url = settings.SUPABASE_URL
    redirect_to = request.build_absolute_uri(f"/auth/callback/?next={next_url}")
    
    oauth_url = (
        f"{supabase_url}/auth/v1/authorize"
        f"?provider=google"
        f"&redirect_to={redirect_to}"
    )
    
    return redirect(oauth_url)


# ── OAuth Callback Handler ────────────────────────────────────────────────────

def auth_callback(request):
    """
    GET /auth/callback/
    
    Supabase redirects here after Google OAuth completes.
    
    Supabase sends the JWT token in the URL fragment (#access_token=...).
    Since URL fragments are NOT sent to the server, we use a small
    JavaScript snippet to extract the token from the fragment and POST
    it to /auth/callback/process/ which creates the Django session.
    
    Flow:
    1. Supabase → GET /auth/callback/#access_token=xxx&refresh_token=yyy
    2. JS extracts access_token from fragment
    3. JS POSTs to /auth/callback/process/ with the token
    4. Django verifies JWT, creates session, redirects to dashboard
    """
    next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
    
    return render(request, "accidents/auth_callback.html", {
        "next": next_url,
        "process_url": "/auth/callback/process/",
    })


@require_http_methods(["POST"])
def process_auth_callback(request):
    """
    POST /auth/callback/process/
    
    Receives the Supabase JWT access_token from the client-side JS.
    Verifies the token, creates/updates Django User + UserProfile,
    logs the user into Django session, returns success JSON.
    
    Request body (JSON):
        {"access_token": "eyJ...", "next": "/dashboard/"}
    
    Response:
        200 {"success": true, "redirect": "/dashboard/", "role": "user"}
        400 {"success": false, "error": "Invalid token"}
    """
    import json
    
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid request body"}, status=400)
    
    access_token = body.get("access_token", "")
    next_url = body.get("next", settings.LOGIN_REDIRECT_URL)
    
    if not access_token:
        return JsonResponse({"success": False, "error": "No access token provided"}, status=400)
    
    # Verify the JWT
    jwt_payload = verify_supabase_jwt(access_token)
    
    if not jwt_payload:
        logger.warning("Failed to verify Supabase JWT token in callback")
        return JsonResponse({"success": False, "error": "Invalid or expired token"}, status=400)
    
    # Create or update Django User + UserProfile
    try:
        user, profile, created = get_or_create_django_user(jwt_payload)
    except Exception as e:
        logger.error(f"Error creating user from JWT: {e}")
        return JsonResponse({"success": False, "error": f"Account creation failed: {str(e)}"}, status=500)
    
    # Log the user into Django session
    # (backend must be specified since user has no password)
    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend",
    )
    
    logger.info(
        f"{'New' if created else 'Returning'} user logged in: "
        f"{user.email} [role: {profile.role}]"
    )
    
    return JsonResponse({
        "success": True,
        "redirect": next_url,
        "role": profile.role,
        "name": profile.display_name,
        "created": created,
    })


# ── Logout ────────────────────────────────────────────────────────────────────

@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    GET or POST /auth/logout/
    
    Clears Django session and redirects to home page.
    Accepts both GET and POST for flexibility.
    """
    user_email = request.user.email if request.user.is_authenticated else "anonymous"
    logout(request)
    logger.info(f"User logged out: {user_email}")
    return redirect(settings.LOGOUT_REDIRECT_URL)
