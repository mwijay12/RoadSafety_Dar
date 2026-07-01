"""
Accident data model — PRD-compliant.

vehicle_types is a JSON list of one-or-more vehicle types
matching the PRD (e.g. ["bus", "motorcycle"] for a daladala+ boda crash).
We use Django's JSONField (works on SQLite 3.9+ and PostGIS alike).
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


SEVERITY_CHOICES = [
    ("minor", "Minor (no casualties)"),
    ("serious", "Serious (injury, no fatality)"),
    ("fatal", "Fatal (1+ deaths)"),
    ("critical", "Critical (multiple casualties)"),
]

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
    lat = models.FloatField()
    lng = models.FloatField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


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
    junction_name = models.CharField(
        max_length=120, blank=True,
        help_text="Closest named intersection (PRD §5 field)",
    )
    junction = models.ForeignKey(
        Junction, on_delete=models.SET_NULL, null=True, blank=True,
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
        max_length=20, choices=REPORTER_CHOICES, default="community",
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
    source_notes = models.TextField(blank=True, help_text="PRD §5: e.g. 'Reported via mobile form'")

    # Meta
    verified = models.BooleanField(default=False, help_text="Police-verified record")

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["occurred_at", "severity"]),
            models.Index(fields=["lat", "lng"]),
        ]

    def __str__(self):
        return f"{self.get_severity_display()} @ {self.occurred_at:%Y-%m-%d %H:%M}"

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
