# accidents/services/supabase_auth.py
"""
Supabase Auth utilities for Road Safety Dar es Salaam.

Handles:
  - JWT token verification (from Supabase Auth callback)
  - Creating/updating Django User + UserProfile from Supabase JWT claims
  - Supabase client singleton
"""

import logging
import os

import jwt
from django.conf import settings
from django.contrib.auth.models import User

from accidents.models import UserProfile

logger = logging.getLogger(__name__)


# ── Supabase client singleton ─────────────────────────────────────────────────

def get_supabase_client():
    """
    Returns an authenticated Supabase client using the service role key.
    Use this for server-side operations only — never expose service key to browser.
    """
    from supabase import create_client, Client
    
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_KEY
    
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env"
        )
    
    return create_client(url, key)


# ── JWT Verification ──────────────────────────────────────────────────────────

def verify_supabase_jwt(token: str) -> dict | None:
    """
    Verifies a Supabase Auth JWT token and returns the decoded payload.
    
    Args:
        token: The JWT access token from Supabase Auth callback
        
    Returns:
        Decoded payload dict if valid, None if invalid/expired
        
    Payload contains:
        sub          → Supabase user UUID
        email        → user email
        user_metadata → {full_name, avatar_url, email}
        role         → 'authenticated'
        exp          → expiry timestamp
    """
    jwt_secret = settings.SUPABASE_JWT_SECRET
    
    if not jwt_secret:
        logger.error("SUPABASE_JWT_SECRET is not set in settings")
        return None
    
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": True},
            audience="authenticated",
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Supabase JWT token has expired")
        return None
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid Supabase JWT token: {e}")
        return None


# ── User Creation / Update ────────────────────────────────────────────────────

def get_or_create_django_user(jwt_payload: dict) -> tuple[User, UserProfile, bool]:
    """
    Given a verified Supabase JWT payload, find or create the matching
    Django User and UserProfile.
    
    Args:
        jwt_payload: Decoded JWT dict from verify_supabase_jwt()
        
    Returns:
        (user, profile, created) tuple
        created = True if this is the user's first login
        
    Logic:
        1. Extract supabase_uid (jwt_payload['sub'])
        2. Try to find existing UserProfile by supabase_uid
        3. If not found, create Django User + UserProfile
        4. Update avatar_url and name on every login (Google may update them)
    """
    supabase_uid = jwt_payload.get("sub")
    email = jwt_payload.get("email", "")
    
    # Extract name and avatar from Google OAuth metadata
    user_metadata = jwt_payload.get("user_metadata", {})
    full_name = user_metadata.get("full_name", "") or user_metadata.get("name", "")
    avatar_url = user_metadata.get("avatar_url", "") or user_metadata.get("picture", "")
    
    # Split full name into first/last
    name_parts = full_name.strip().split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Try to find existing profile by Supabase UID
    try:
        profile = UserProfile.objects.select_related("user").get(
            supabase_uid=supabase_uid
        )
        user = profile.user
        created = False
        
        # Update fields that may have changed in Google profile
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save(update_fields=["first_name", "last_name", "email"])
        
        profile.avatar_url = avatar_url
        profile.save(update_fields=["avatar_url", "updated_at"])
        
        logger.info(f"Existing user logged in: {email} [{profile.role}]")
        
    except UserProfile.DoesNotExist:
        # First login — create Django User + UserProfile
        # Use email as username (truncate to 150 chars for Django's username field)
        username = email[:150]
        
        # Handle username collision (unlikely but possible)
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username[:147]}_{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            # No password — login is via Google OAuth only
            password=None,
        )
        
        # Ensure UserProfile creation signal didn't already create it automatically
        profile, profile_created = UserProfile.objects.get_or_create(user=user)
        profile.supabase_uid = supabase_uid
        profile.avatar_url = avatar_url
        profile.role = "user"  # All new signups start as 'user' role
        profile.save()
        
        created = True
        logger.info(f"New user created: {email} [user role]")
    
    return user, profile, created


# ── Email + Password Auth ─────────────────────────────────────────────────────

def sign_in_with_email(email: str, password: str) -> dict | None:
    """
    Sign in with email and password via Supabase Auth.

    Returns the session dict with access_token on success, None on failure.
    """
    try:
        client = get_supabase_client()
        result = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        return {
            "access_token": result.session.access_token,
            "user": result.user,
        }
    except Exception as e:
        logger.warning(f"Email/password sign-in failed for {email}: {e}")
        return None


def sign_up_with_email(email: str, password: str, full_name: str = "") -> dict | None:
    """
    Register a new user with email and password via Supabase Auth.

    Returns the session dict with access_token on success, None on failure.
    """
    try:
        client = get_supabase_client()
        result = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name},
            },
        })
        if result.session:
            return {
                "access_token": result.session.access_token,
                "user": result.user,
            }
        # If email confirmation is required, result.session may be None
        # but result.user will exist
        if result.user:
            return {"user": result.user, "confirmation_sent": True}
        return None
    except Exception as e:
        logger.warning(f"Email/password sign-up failed for {email}: {e}")
        return None


def send_otp_email(email: str) -> bool:
    """
    Send a one-time password (OTP) to the user's email via Supabase Auth.
    Returns True if sent successfully.
    """
    try:
        client = get_supabase_client()
        client.auth.sign_in_with_otp({
            "email": email,
        })
        return True
    except Exception as e:
        logger.warning(f"Failed to send OTP to {email}: {e}")
        return False


def verify_otp(email: str, token: str) -> dict | None:
    """
    Verify an OTP token sent to the user's email.

    Returns the session dict with access_token on success, None on failure.
    """
    try:
        client = get_supabase_client()
        result = client.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "email",
        })
        return {
            "access_token": result.session.access_token,
            "user": result.user,
        }
    except Exception as e:
        logger.warning(f"OTP verification failed for {email}: {e}")
        return None
