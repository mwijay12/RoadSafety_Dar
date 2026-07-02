"""
Accident data model — PRD-compliant.

vehicle_types is a JSON list of one-or-more vehicle types
matching the PRD (e.g. ["bus", "motorcycle"] for a daladala+ boda crash).
We use Django's JSONField (works on SQLite 3.9+ and PostGIS alike).

H3 cell indexing (v1.2.1+):
Every new accident automatically gets an Uber H3 hex cell ID at resolution
10 (~68m edge) via ``h3.latlng_to_cell()``. This enables proper spatial
grouping for the junction heatmap without PostGIS.
"""

import logging

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger(__name__)


SEVERITY_CHOICES = [
    ("minor", "Minor (no casualties)"),
    ("serious", "Serious (injury, no fatality)"),
    ("fatal", "Fatal (1+ deaths)"),
    ("critical", "Critical (multiple casualties)"),
]

# Weight per severity for safety-score and clustering
SEVERITY_WEIGHT = {
    "minor": 1,
    "serious": 2,
    "fatal": 4,
    "critical": 3,
}

VEHICLE_CHOICES = [
    ("motorcycle", "Motorcycle / Bodaboda"),
    ("car", "Car"),
    ("bus", "Bus / Daladala"),
    ("truck", "Truck / Lorry"),
    ("bicycle", "Bicycle"),
    ("pedestrian", "Pedestrian only"),
    ("auto_rickshaw", "Auto-rickshaw / Bajaji"),
    ("mixed", "Mixed / Multiple"),
]

REPORTER_CHOICES = [
    ("police", "Tanzania Police Force"),
    ("community", "Community member"),
    ("hospital", "Hospital / EMS"),
    ("tanroads", "TANROADS"),
    ("media", "Media report"),
]

# Dar es Salaam bounding box — input validation
DAR_LAT_MIN, DAR_LAT_MAX = -7.5, -6.0
DAR_LNG_MIN, DAR_LNG_MAX = 38.5, 39.7


class Junction(models.Model):
    """Named intersections / black-spots we track separately."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(
        max_length=120,
        unique=False,
        blank=True,
        db_index=True,
        help_text="URL-safe identifier. Auto-generated from name on save.",
    )
    lat = models.FloatField()
    lng = models.FloatField()
    district = models.CharField(
        max_length=60,
        blank=True,
        db_index=True,
        help_text="Dar es Salaam district: Ilala, Kinondoni, Temeke, Ubungo, Kigamboni",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_demo = models.BooleanField(
        default=False,
        help_text="Demo/seed junction — hidden from public when demo data is toggled off",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["lat", "lng"]),
        ]

    def __str__(self):
        if self.district:
            return f"{self.name} ({self.district})"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug(self.name)
        super().save(*args, **kwargs)

    def _unique_slug(self, source: str) -> str:
        base = slugify(source)[:100]
        slug = base
        counter = 1
        while Junction.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    @property
    def safety_score(self) -> float:
        """Severity-weighted risk score (0–100). Higher = more dangerous."""
        qs = self.accidents.all()
        total = qs.count()
        if total == 0:
            return 0.0
        weighted = sum(SEVERITY_WEIGHT.get(a.severity, 1) for a in qs)
        return round((weighted / total) * 25, 1)

    def safety_score_from_queryset(self, qs) -> float:
        """Same as ``safety_score`` but accepts a pre-filtered accident queryset."""
        total = qs.count()
        if total == 0:
            return 0.0
        weighted = sum(SEVERITY_WEIGHT.get(a.severity, 1) for a in qs)
        return round((weighted / total) * 25, 1)


ROLE_CHOICES = [
    ("admin", "Admin"),
    ("editor", "Editor (Officer/TANROADS)"),
    ("user", "Community User"),
    ("police", "Police / TPF"),  # for backward compatibility
    ("community", "Community Member"),  # for backward compatibility
]


AUDIT_ACTION_CHOICES = [
    ("verify", "Verified"),
    ("unverify", "Unverified"),
    ("severity_change", "Severity Changed"),
    ("junction_merge", "Junction Merged"),
    ("bulk_update", "Bulk Update"),
    ("create", "Created"),
    ("edit", "Edited"),
]


class AuditLog(models.Model):
    """Simple audit trail for admin actions on accident records."""

    accident = models.ForeignKey(
        "Accident",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=30, choices=AUDIT_ACTION_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log"

    def __str__(self):
        return f"{self.get_action_display()} @ {self.created_at:%Y-%m-%d %H:%M}"


class UserProfile(models.Model):
    """Extra profile data tied to Django's built-in User model."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="community")
    phone = models.CharField(max_length=20, blank=True, help_text="Tanzania phone number")
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email alerts for fatal/critical incidents and daily digests",
    )
    supabase_uid = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Supabase Auth user UUID — auto-set on first Google login",
    )
    avatar_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Google profile picture — auto-set on login",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_editor(self):
        return self.role in ("admin", "editor", "police")

    @property
    def is_community_user(self):
        return self.role in ("user", "community")

    @property
    def display_name(self):
        """Return first name, or email prefix if no name set."""
        if self.user.first_name:
            return self.user.first_name
        return self.user.email.split("@")[0]


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile whenever a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


class SiteSettings(models.Model):
    """Singleton model — toggle demo/real data visibility across the public site."""

    show_demo_data = models.BooleanField(
        default=True,
        help_text="When ON, demo records appear alongside real data. When OFF, only real data is shown.",
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"Site Settings (show_demo={'ON' if self.show_demo_data else 'OFF'})"

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


def visible_accidents():
    """All accidents if show_demo_data is ON; real-data-only if OFF.

    Use in PUBLIC views so the dashboard/API respect the toggle.
    Authority views and admin always see everything.
    """
    settings = SiteSettings.get_settings()
    qs = Accident.objects.all()
    if not settings.show_demo_data:
        qs = qs.filter(is_demo=False)
    return qs


def visible_junctions():
    """All junctions if show_demo_data is ON; real-data-only if OFF."""
    settings = SiteSettings.get_settings()
    qs = Junction.objects.all()
    if not settings.show_demo_data:
        qs = qs.filter(is_demo=False)
    return qs


class Accident(models.Model):
    """Core accident report — PRD schema §5."""

    # Spatial
    lat = models.FloatField(
        db_index=True,
        validators=[MinValueValidator(DAR_LAT_MIN), MaxValueValidator(DAR_LAT_MAX)],
    )
    lng = models.FloatField(
        db_index=True,
        validators=[MinValueValidator(DAR_LNG_MIN), MaxValueValidator(DAR_LNG_MAX)],
    )
    h3_cell = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text="Uber H3 hex cell ID at resolution 10 (~68m). Auto-set on save.",
    )
    junction_name = models.CharField(
        max_length=120,
        blank=True,
        help_text="Closest named intersection (PRD §5 field)",
    )
    junction = models.ForeignKey(
        Junction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accidents",
    )

    # Time
    occurred_at = models.DateTimeField(db_index=True)
    reported_at = models.DateTimeField(default=timezone.now)

    # Severity & classification
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, db_index=True)
    vehicle_types = models.JSONField(
        default=list,
        help_text='List of one or more vehicle types, e.g. ["bus","motorcycle"]',
    )
    reporter_type = models.CharField(
        max_length=20,
        choices=REPORTER_CHOICES,
        default="community",
    )

    # Casualties
    casualties = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(500)])
    fatalities = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(500)])
    injuries = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(500)])

    # Narrative
    description = models.TextField(blank=True)
    weather = models.CharField(max_length=60, blank=True)
    road_condition = models.CharField(max_length=60, blank=True)
    contact = models.CharField(max_length=120, blank=True)
    source_notes = models.TextField(
        blank=True, help_text="PRD §5: e.g. 'Reported via mobile form'"
    )

    # Meta
    verified = models.BooleanField(default=False, help_text="Police-verified record")
    is_demo = models.BooleanField(
        default=False,
        help_text="Demo/seed record — hidden from public when demo data is toggled off",
    )

    # Who submitted this report (null for anonymous)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_accidents",
        help_text="Django user who submitted this report. Null = anonymous.",
    )

    # Trust level — affects heatmap intensity
    TRUST_CHOICES = [
        ("anonymous", "Anonymous"),        # No account — lowest weight
        ("community", "Community User"),   # Logged-in user — medium weight
        ("verified",  "Verified Report"),  # Editor/police verified — highest weight
    ]
    trust_level = models.CharField(
        max_length=20,
        choices=TRUST_CHOICES,
        default="anonymous",
        db_index=True,
        help_text="Trust level affects heatmap intensity weight.",
    )

    # Cached upvote counter — updated when upvotes are added/removed
    upvote_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of users who confirmed they saw this incident.",
    )

    # Tracks the full verification lifecycle
    VERIFICATION_STATUS_CHOICES = [
        ("pending",  "Pending Review"),    # default — not yet reviewed
        ("verified", "Verified"),          # editor confirmed it is real
        ("rejected", "Rejected"),          # editor determined it is invalid
    ]
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="pending",
        db_index=True,
        help_text="Current verification status of this accident report.",
    )

    # Official notes added by editor after reviewing
    official_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Official notes added by verifying officer. Visible to public.",
    )

    # Reason provided when rejecting a report
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for rejection — shown to the original submitter.",
    )

    # Which editor verified/rejected this report
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_accidents",
        help_text="Editor who verified or rejected this report.",
    )

    # When the verification action happened
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of when verification action was taken.",
    )

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["occurred_at", "severity"]),
            models.Index(fields=["lat", "lng"]),
        ]

    def __str__(self):
        return f"{self.get_severity_display()} @ {self.occurred_at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        # Sync verification_status with legacy 'verified' bool and trust_level
        if self.verified and self.verification_status != "verified":
            self.verification_status = "verified"

        if self.verification_status == "verified":
            self.verified = True
            self.trust_level = "verified"
        elif self.verification_status == "rejected":
            self.verified = False
        else:
            # pending
            self.verified = False
            if self.submitted_by is not None:
                self.trust_level = "community"
            else:
                self.trust_level = "anonymous"

        if not self.h3_cell:
            self._compute_h3_cell()
        super().save(*args, **kwargs)

    @property
    def severity_weight(self):
        """Numeric weight for sorting — used in editor queue ordering."""
        return {"minor": 1, "serious": 2, "critical": 3, "fatal": 4}.get(
            self.severity, 1
        )

    def _compute_h3_cell(self) -> None:
        """Compute ``h3_cell`` from ``lat``/``lng`` at resolution 10 (~68m).

        Gracefully no-ops if the ``h3`` package is not installed.
        Compatible with both h3 v3.x (``geo_to_h3``) and v4.x
        (``latlng_to_cell``).
        """
        try:
            import h3

            if hasattr(h3, "latlng_to_cell"):
                # h3 v4.x
                self.h3_cell = h3.latlng_to_cell(self.lat, self.lng, 10)
            else:
                # h3 v3.x
                self.h3_cell = h3.geo_to_h3(self.lat, self.lng, 10)
        except Exception:
            logger.debug("h3 computation skipped (package missing or invalid coords)")

    def clean(self):
        """Cross-field validation per PRD §7."""
        super().clean()
        if self.fatalities > self.casualties:
            from django.core.exceptions import ValidationError

            raise ValidationError("fatalities cannot exceed casualties")
        if self.injuries > self.casualties:
            from django.core.exceptions import ValidationError

            raise ValidationError("injuries cannot exceed casualties")
        if not self.vehicle_types:
            from django.core.exceptions import ValidationError

            raise ValidationError("vehicle_types must contain at least one value")
        for v in self.vehicle_types:
            if v not in dict(VEHICLE_CHOICES):
                from django.core.exceptions import ValidationError

                raise ValidationError(f"unknown vehicle type: {v}")


class AccidentUpvote(models.Model):
    """
    Records when a logged-in user confirms they witnessed or can verify
    an accident. One upvote per user per accident.
    
    Upvotes increase the accident's trust score and heatmap intensity.
    They also help editors prioritise which reports to verify first.
    """

    accident = models.ForeignKey(
        Accident,
        on_delete=models.CASCADE,
        related_name="upvotes",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="upvoted_accidents",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Accident Upvote"
        verbose_name_plural = "Accident Upvotes"
        # ONE upvote per user per accident — enforced at DB level
        unique_together = [("accident", "user")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} → Accident #{self.accident.id}"
