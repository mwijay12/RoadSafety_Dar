# accidents/views/editor_views.py
"""
Editor and Admin views for Road Safety Dar es Salaam.

Editor routes  (role: editor or admin):
  GET  /editor/queue/                   → Prioritised verification queue
  GET  /editor/accidents/<id>/          → Full accident detail for review
  POST /editor/accidents/<id>/verify/   → Mark as verified + add notes
  POST /editor/accidents/<id>/reject/   → Mark as rejected + add reason

Admin routes   (role: admin only):
  GET  /admin-panel/users/              → List all users + change roles
  POST /admin-panel/users/<id>/set-role/ → Update a user's role
"""

import logging
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from accidents.decorators import role_required
from accidents.models import Accident, UserProfile
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# EDITOR VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@role_required("editor")
def editor_queue(request):
    """
    GET /editor/queue/

    Shows all PENDING accident reports in priority order:
      1. Fatal accidents first
      2. Then by upvote count descending (most community-confirmed first)
      3. Then by most recent
    """
    # Main pending queue
    pending = (
        Accident.objects
        .filter(verification_status="pending")
        .select_related("submitted_by", "junction")
        .order_by("-upvote_count", "-occurred_at")
    )

    # Sort pending by severity weight + upvotes combined
    severity_order = {"fatal": 4, "critical": 3, "serious": 2, "minor": 1}
    pending_sorted = sorted(
        pending,
        key=lambda a: (severity_order.get(a.severity, 0) * 10 + a.upvote_count),
        reverse=True,
    )

    today = timezone.now().date()

    # Stats for the header
    verified_today = Accident.objects.filter(
        verification_status="verified",
        verified_at__date=today,
    ).count()

    rejected_today = Accident.objects.filter(
        verification_status="rejected",
        verified_at__date=today,
    ).count()

    high_priority = [
        a for a in pending_sorted
        if a.severity in ("fatal", "critical") or a.upvote_count >= 2
    ]

    # Recently verified (last 10)
    recently_verified = (
        Accident.objects
        .filter(verification_status="verified")
        .select_related("verified_by")
        .order_by("-verified_at")[:10]
    )

    return render(request, "accidents/editor_queue.html", {
        "pending": pending_sorted,
        "pending_count": len(pending_sorted),
        "high_priority_count": len(high_priority),
        "verified_today": verified_today,
        "rejected_today": rejected_today,
        "recently_verified": recently_verified,
        "editor_name": request.user.profile.display_name,
    })


@role_required("editor")
def editor_accident_detail(request, accident_id):
    """
    GET /editor/accidents/<id>/

    Full detail view of a single accident report for editor review.
    """
    accident = get_object_or_404(
        Accident.objects.select_related(
            "submitted_by", "junction", "verified_by"
        ),
        id=accident_id,
    )

    upvoters = accident.upvotes.select_related("user").order_by("-created_at")

    return render(request, "accidents/editor_accident_detail.html", {
        "accident": accident,
        "upvoters": upvoters,
        "upvote_count": upvoters.count(),
        "can_verify": accident.verification_status == "pending",
    })


@role_required("editor")
@require_http_methods(["POST"])
def editor_verify_accident(request, accident_id):
    """
    POST /editor/accidents/<id>/verify/

    Marks an accident as verified.
    """
    accident = get_object_or_404(Accident, id=accident_id)

    if accident.verification_status == "verified":
        messages.warning(request, f"Accident #{accident_id} is already verified.")
        return redirect("editor_queue")

    official_notes = request.POST.get("official_notes", "").strip()

    accident.verification_status = "verified"
    accident.official_notes = official_notes if official_notes else None
    accident.verified_by = request.user
    accident.verified_at = timezone.now()
    accident.save()

    logger.info(
        f"Accident #{accident_id} VERIFIED by {request.user.email} "
        f"at {accident.verified_at}"
    )

    messages.success(
        request,
        f"✅ Accident #{accident_id} verified successfully."
    )
    return redirect("editor_queue")


@role_required("editor")
@require_http_methods(["POST"])
def editor_reject_accident(request, accident_id):
    """
    POST /editor/accidents/<id>/reject/

    Marks an accident as rejected.
    """
    accident = get_object_or_404(Accident, id=accident_id)

    rejection_reason = request.POST.get("rejection_reason", "").strip()

    if not rejection_reason:
        messages.error(
            request,
            "Please provide a reason for rejection before submitting."
        )
        return redirect("editor_accident_detail", accident_id=accident_id)

    accident.verification_status = "rejected"
    accident.rejection_reason = rejection_reason
    accident.verified_by = request.user
    accident.verified_at = timezone.now()
    accident.save()

    logger.info(
        f"Accident #{accident_id} REJECTED by {request.user.email}."
    )

    messages.warning(
        request,
        f"⚠️ Accident #{accident_id} has been rejected."
    )
    return redirect("editor_queue")


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@role_required("admin")
def admin_users(request):
    """
    GET /admin-panel/users/

    Lists all registered users with their current roles.
    """
    profiles = (
        UserProfile.objects
        .select_related("user")
        .order_by("-created_at")
    )

    profile_data = []
    for profile in profiles:
        submitted = Accident.objects.filter(
            submitted_by=profile.user
        ).count()
        verified = Accident.objects.filter(
            verified_by=profile.user
        ).count()
        profile_data.append({
            "profile": profile,
            "submitted_count": submitted,
            "verified_count": verified,
        })

    return render(request, "accidents/admin_users.html", {
        "profile_data": profile_data,
        "total_users": len(profile_data),
        "role_choices": UserProfile.ROLE_CHOICES,
    })


@role_required("admin")
@require_http_methods(["POST"])
def admin_set_role(request, user_id):
    """
    POST /admin-panel/users/<id>/set-role/

    Updates a user's role. Admin only.
    """
    target_user = get_object_or_404(User, id=user_id)

    new_role = request.POST.get("role", "").strip()
    valid_roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]

    if new_role not in valid_roles:
        messages.error(request, f"Invalid role: {new_role}")
        return redirect("admin_users")

    if target_user == request.user and new_role != "admin":
        messages.error(
            request,
            "You cannot change your own role."
        )
        return redirect("admin_users")

    try:
        profile = target_user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect("admin_users")

    old_role = profile.role
    profile.role = new_role
    profile.save(update_fields=["role", "updated_at"])

    logger.info(
        f"Role changed: {target_user.email} "
        f"{old_role} → {new_role} "
        f"by {request.user.email}"
    )

    messages.success(
        request,
        f"✅ {target_user.email} role updated: "
        f"{old_role} → {new_role}"
    )
    return redirect("admin_users")
