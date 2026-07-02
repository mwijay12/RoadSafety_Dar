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
    send_otp_email,
    sign_in_with_email,
    sign_up_with_email,
    verify_otp,
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


# ── Register ──────────────────────────────────────────────────────────────────

def register_view(request):
    """
    GET /auth/register/ → show registration form
    POST /auth/register/ → create user via Supabase Auth
    
    Creates a new user with email + password.
    On success, logs the user into Django session if email confirmation is off.
    """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == "GET":
        return render(request, "accidents/register.html")

    # POST
    import json
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid request body"}, status=400)

    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    full_name = body.get("full_name", "").strip()

    if not email or not password:
        return JsonResponse({"success": False, "error": "Email and password are required"}, status=400)
    if len(password) < 6:
        return JsonResponse({"success": False, "error": "Password must be at least 6 characters"}, status=400)

    result = sign_up_with_email(email, password, full_name)

    if not result:
        return JsonResponse({"success": False, "error": "Registration failed. Email may already be in use."}, status=400)

    if result.get("confirmation_sent"):
        return JsonResponse({
            "success": True,
            "confirmation_sent": True,
            "message": "Check your email to confirm your account.",
        })

    access_token = result.get("access_token", "")
    jwt_payload = verify_supabase_jwt(access_token)
    if jwt_payload:
        user, profile, created = get_or_create_django_user(jwt_payload)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return JsonResponse({
            "success": True,
            "redirect": settings.LOGIN_REDIRECT_URL,
            "role": profile.role,
            "name": profile.display_name,
        })

    return JsonResponse({"success": True, "message": "Account created. Please sign in."})


# ── Email + Password Login ────────────────────────────────────────────────────

@require_http_methods(["POST"])
def email_login(request):
    """
    POST /auth/login/email/
    
    Authenticates with email + password via Supabase.
    Creates Django session on success.
    """
    import json
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid request body"}, status=400)

    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not email or not password:
        return JsonResponse({"success": False, "error": "Email and password are required"}, status=400)

    result = sign_in_with_email(email, password)
    if not result:
        return JsonResponse({"success": False, "error": "Invalid email or password"}, status=401)

    access_token = result.get("access_token", "")
    jwt_payload = verify_supabase_jwt(access_token)
    if not jwt_payload:
        return JsonResponse({"success": False, "error": "Authentication failed"}, status=401)

    try:
        user, profile, created = get_or_create_django_user(jwt_payload)
    except Exception as e:
        logger.error(f"Error creating user from email login: {e}")
        return JsonResponse({"success": False, "error": f"Account setup failed: {str(e)}"}, status=500)

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    logger.info(f"User logged in via email: {user.email} [{profile.role}]")

    return JsonResponse({
        "success": True,
        "redirect": settings.LOGIN_REDIRECT_URL,
        "role": profile.role,
        "name": profile.display_name,
        "created": created,
    })


# ── Email OTP / Magic Link ───────────────────────────────────────────────────

@require_http_methods(["POST"])
def send_login_otp(request):
    """
    POST /auth/login/otp/send/
    
    Sends a one-time password to the user's email via Supabase.
    """
    import json
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid request body"}, status=400)

    email = body.get("email", "").strip().lower()
    if not email:
        return JsonResponse({"success": False, "error": "Email is required"}, status=400)

    sent = send_otp_email(email)
    if not sent:
        return JsonResponse({"success": False, "error": "Failed to send OTP. Check the email address."}, status=500)

    return JsonResponse({"success": True, "message": "OTP sent to your email."})


@require_http_methods(["POST"])
def verify_login_otp(request):
    """
    POST /auth/login/otp/verify/
    
    Verifies the OTP sent to the user's email and creates Django session.
    """
    import json
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid request body"}, status=400)

    email = body.get("email", "").strip().lower()
    token = body.get("token", "").strip()

    if not email or not token:
        return JsonResponse({"success": False, "error": "Email and OTP token are required"}, status=400)

    result = verify_otp(email, token)
    if not result:
        return JsonResponse({"success": False, "error": "Invalid or expired OTP"}, status=401)

    access_token = result.get("access_token", "")
    jwt_payload = verify_supabase_jwt(access_token)
    if not jwt_payload:
        return JsonResponse({"success": False, "error": "Authentication failed"}, status=401)

    try:
        user, profile, created = get_or_create_django_user(jwt_payload)
    except Exception as e:
        logger.error(f"Error creating user from OTP login: {e}")
        return JsonResponse({"success": False, "error": f"Account setup failed: {str(e)}"}, status=500)

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    logger.info(f"User logged in via OTP: {user.email} [{profile.role}]")

    return JsonResponse({
        "success": True,
        "redirect": settings.LOGIN_REDIRECT_URL,
        "role": profile.role,
        "name": profile.display_name,
        "created": created,
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
