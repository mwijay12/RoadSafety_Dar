"""
Django forms for Accident report submission (HTML form + JSON API).

Replaces raw ``request.POST`` access from views.py with a single ``ModelForm``
that powers both the web form and the JSON API, keeping validation in one
place.
"""

from django import forms
from django.utils import timezone

from .models import (
    DAR_LAT_MAX,
    DAR_LAT_MIN,
    DAR_LNG_MAX,
    DAR_LNG_MIN,
    REPORTER_CHOICES,
    VEHICLE_CHOICES,
    Accident,
    Junction,
)

SUBMIT_FIELDS = [
    "lat",
    "lng",
    "occurred_at",
    "severity",
    "vehicle_types",
    "reporter_type",
    "district",
    "ward",
    "location_id",
    "casualties",
    "fatalities",
    "injuries",
    "description",
    "weather",
    "road_condition",
    "contact",
    "junction_name",
    "photo_url",
]


class AccidentForm(forms.ModelForm):
    """Single form for both ``/report/`` (HTML) and ``POST /api/accidents/`` (JSON).

    The model's ``vehicle_types`` is a JSON list, but the public form exposes
    a single-select dropdown. ``clean_vehicle_types()`` wraps the value in a
    list before the model field receives it.

    Backward-compatible: also accepts ``vehicle_types`` (array) from JSON API
    clients that were built against the old raw-POST endpoint.
    """

    vehicle_types = forms.ChoiceField(
        choices=VEHICLE_CHOICES,
        initial="car",
        label="Vehicle type",
        error_messages={"required": "Select a vehicle type."},
    )

    def __init__(self, *args, **kwargs):
        # pop custom kwargs before super().__init__
        user = kwargs.pop("user", None)
        # data may be positional (args[0]) or keyword (kwargs["data"])
        raw = args[0] if args else kwargs.get("data")
        if raw is not None:
            # Normalise to a plain dict whose values are single strings
            # (QueryDict stores values as lists, regular JSON dicts may as well).
            data = {}
            for k, v in raw.items():
                if isinstance(v, list | tuple):
                    data[k] = v[0] if v else ""
                else:
                    data[k] = v
            if "vehicle_type" in data and "vehicle_types" not in data:
                data["vehicle_types"] = data.pop("vehicle_type")
            if "vehicle_types" in data:
                vt = data["vehicle_types"]
                if isinstance(vt, list):
                    data["vehicle_types"] = vt[0] if vt else "car"
            # backward compat defaults (matching old _save_from_payload)
            data.setdefault("reporter_type", "community")
            data.setdefault("occurred_at", timezone.now().strftime("%Y-%m-%dT%H:%M"))
            for field in ("casualties", "fatalities", "injuries"):
                if field not in data:
                    data[field] = 0
            # Override reporter_type from authenticated user's profile role
            if user and user.is_authenticated:
                data["reporter_type"] = user.profile.role
            # --------------------------------------------------------------
            # Auto-fill lat / lng / district / ward / junction_name from the
            # location picker BEFORE the per-field validators run.  Done in
            # __init__ so that clean_lat() and clean_lng() see the values.
            # --------------------------------------------------------------
            from .locations import find_location_by_name

            loc_id = (data.get("location_id") or "").strip()
            if loc_id:
                loc = (
                    find_location_by_name(loc_id)
                    or find_location_by_name(loc_id.replace("-", " "))
                )
                if loc:
                    def _is_blank(v: object) -> bool:
                        if v is None:
                            return True
                        if isinstance(v, str):
                            return not v.strip()
                        return False
                    if _is_blank(data.get("lat")):
                        data["lat"] = loc["lat"]
                    if _is_blank(data.get("lng")):
                        data["lng"] = loc["lng"]
                    if _is_blank(data.get("junction_name")):
                        data["junction_name"] = loc["name"]
                    if _is_blank(data.get("ward")):
                        data["ward"] = loc.get("ward", "")
                    if loc.get("district"):
                        data["district"] = loc["district"]
            # Always pass data as keyword to avoid double-processing
            if args:
                kwargs["data"] = data
                args = args[1:]
            else:
                kwargs["data"] = data
        super().__init__(*args, **kwargs)

    reporter_type = forms.ChoiceField(
        choices=REPORTER_CHOICES,
        initial="community",
        label="Reporter type",
    )

    class Meta:
        model = Accident
        fields = SUBMIT_FIELDS  # excludes h3_cell, junction, reported_at, verified, source_notes
        widgets = {
            "lat": forms.NumberInput(attrs={"step": "any", "id": "lat"}),
            "lng": forms.NumberInput(attrs={"step": "any", "id": "lng"}),
            "occurred_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "description": forms.Textarea(
                attrs={"rows": 3, "placeholder": "What happened? (English or Swahili)"}
            ),
            "contact": forms.TextInput(attrs={"placeholder": "phone or email for follow-up"}),
            "district": forms.Select(attrs={"id": "id_district", "class": "location-select"}),
            "ward": forms.Select(
                attrs={"id": "id_ward", "class": "location-select"},
                choices=[("", "Select ward…")],
            ),
            "location_id": forms.HiddenInput(attrs={"id": "id_location_id"}),
            "junction_name": forms.TextInput(attrs={"placeholder": "e.g. Mlimani City area", "id": "id_junction_name"}),
            "weather": forms.TextInput(attrs={"placeholder": "clear / rainy / drizzle"}),
            "road_condition": forms.TextInput(attrs={"placeholder": "good / wet / potholed"}),
            "photo_url": forms.HiddenInput(attrs={"id": "photo_url"}),
        }
        error_messages = {
            "lat": {
                "required": "GPS latitude is required. Tap 'Use my current location' or enter it."
            },
            "lng": {
                "required": "GPS longitude is required. Tap 'Use my current location' or enter it."
            },
            "severity": {"required": "Select the severity of the accident."},
            "occurred_at": {"required": "When did the accident happen?"},
        }

    # -- Per-field validation ------------------------------------------------

    def clean_lat(self):
        val = self.cleaned_data["lat"]
        if not (DAR_LAT_MIN <= val <= DAR_LAT_MAX):
            raise forms.ValidationError(
                f"Latitude {val} is outside Dar es Salaam ({DAR_LAT_MIN} to {DAR_LAT_MAX})."
            )
        return val

    def clean_lng(self):
        val = self.cleaned_data["lng"]
        if not (DAR_LNG_MIN <= val <= DAR_LNG_MAX):
            raise forms.ValidationError(
                f"Longitude {val} is outside Dar es Salaam ({DAR_LNG_MIN} to {DAR_LNG_MAX})."
            )
        return val

    def clean_casualties(self):
        return self.cleaned_data.get("casualties") or 0

    def clean_fatalities(self):
        return self.cleaned_data.get("fatalities") or 0

    def clean_injuries(self):
        return self.cleaned_data.get("injuries") or 0

    def clean_vehicle_types(self):
        """Wrap the single-select value in a list for the model's JSONField."""
        val = self.cleaned_data["vehicle_types"]
        return [val] if isinstance(val, str) else (val or ["car"])

    # -- Cross-field validation ----------------------------------------------

    def clean(self):
        cleaned = super().clean()
        casualties = cleaned.get("casualties", 0) or 0
        fatalities = cleaned.get("fatalities", 0) or 0
        injuries = cleaned.get("injuries", 0) or 0

        if fatalities > casualties:
            raise forms.ValidationError("Fatalities cannot exceed total casualties.")
        if injuries > casualties:
            raise forms.ValidationError("Injuries cannot exceed total casualties.")

        return cleaned

    # -- Save ----------------------------------------------------------------

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.reported_at:
            instance.reported_at = timezone.now()

        jn = instance.junction_name
        if jn:
            instance.junction, _ = Junction.objects.get_or_create(
                name=jn,
                defaults={"lat": instance.lat, "lng": instance.lng},
            )
        else:
            instance.junction = None

        if commit:
            instance.save()

        return instance
