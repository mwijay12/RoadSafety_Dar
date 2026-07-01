from django.contrib import admin
from .models import Accident, Junction


@admin.register(Junction)
class JunctionAdmin(admin.ModelAdmin):
    list_display = ("name", "lat", "lng", "created_at")
    search_fields = ("name", "description")


@admin.register(Accident)
class AccidentAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "severity", "vehicle_types_display",
                    "reporter_type", "casualties", "fatalities", "lat", "lng", "verified")
    list_filter = ("severity", "reporter_type", "verified", "occurred_at")
    search_fields = ("junction_name", "description", "source_notes")
    date_hierarchy = "occurred_at"
    list_per_page = 50
    actions = ["mark_verified"]
    readonly_fields = ("reported_at",)

    @admin.display(description="Vehicles")
    def vehicle_types_display(self, obj):
        return ", ".join(obj.vehicle_types or []) or "—"

    @admin.action(description="Mark selected as verified")
    def mark_verified(self, request, queryset):
        queryset.update(verified=True)
