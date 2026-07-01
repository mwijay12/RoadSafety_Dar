"""
Admin configuration — operational tools for data stewards at TANROADS & TPF.

Features:
  - KPI dashboard with unverified report queue
  - Audit log for verification & severity changes
  - Bulk actions (verify, set severity, junction merge)
  - Completeness score display per report
"""
from django.contrib import admin
from django.db.models import Count, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from .models import Accident, Junction, UserProfile, AuditLog, SiteSettings


# ===================== Inlines =====================

class AuditLogInline(admin.TabularInline):
    model = AuditLog
    extra = 0
    readonly_fields = ("user", "action", "description", "created_at")
    can_delete = False
    max_num = 0
    verbose_name = "Audit Entry"
    verbose_name_plural = "Audit Trail"

    def has_add_permission(self, request, obj=None):
        return False


# ===================== Model Admins =====================

@admin.register(Accident)
class AccidentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "occurred_at", "severity_badge", "junction_name",
        "vehicle_types_display", "casualties", "fatalities",
        "completeness_score", "verified", "is_demo",
    )
    list_filter = (
        "severity", "verified", "is_demo", "reporter_type",
        "weather", "road_condition", "occurred_at",
    )
    search_fields = ("junction_name", "description", "id", "source_notes")
    date_hierarchy = "occurred_at"
    list_per_page = 50
    list_select_related = ("junction",)
    actions = ["mark_verified", "mark_unverified", "set_severity_fatal",
               "set_severity_critical", "set_severity_serious", "set_severity_minor"]
    readonly_fields = ("reported_at", "h3_cell", "completeness_score")
    fieldsets = (
        ("Location", {"fields": ("lat", "lng", "junction_name", "junction", "h3_cell")}),
        ("Time", {"fields": ("occurred_at", "reported_at")}),
        ("Classification", {"fields": ("severity", "vehicle_types", "reporter_type")}),
        ("Casualties", {"fields": ("casualties", "fatalities", "injuries")}),
        ("Details", {"fields": ("description", "weather", "road_condition", "verified")}),
        ("Meta", {"fields": ("contact", "source_notes", "completeness_score", "is_demo")}),
    )
    inlines = [AuditLogInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("junction")

    @admin.display(description="Severity")
    def severity_badge(self, obj):
        colors = {"fatal": "#c0392b", "critical": "#e67e22",
                  "serious": "#d4a017", "minor": "#2d8659"}
        c = colors.get(obj.severity, "#6b7280")
        label = obj.get_severity_display().split(" (")[0]
        return f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700;">{label}</span>'
    severity_badge.allow_tags = True

    @admin.display(description="Vehicles")
    def vehicle_types_display(self, obj):
        return ", ".join(obj.vehicle_types or []) or "—"

    @admin.display(description="Completeness")
    def completeness_score(self, obj):
        fields = [obj.description, obj.weather, obj.road_condition,
                  obj.junction_name, obj.contact]
        filled = sum(1 for f in fields if f and f.strip())
        pct = round((filled / len(fields)) * 100)
        color = "#2d8659" if pct >= 80 else "#e67e22" if pct >= 50 else "#c0392b"
        return f'<span style="color:{color};font-weight:700;">{pct}%</span>'
    completeness_score.allow_tags = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            AuditLog.objects.create(
                accident=obj, user=request.user,
                action="edit",
                description="Edited via admin",
            )

    # --- Admin Actions ---

    @admin.action(description="Mark selected as verified")
    def mark_verified(self, request, queryset):
        count = queryset.update(verified=True)
        for a in queryset:
            AuditLog.objects.create(
                accident=a, user=request.user,
                action="verify", description="Verified via admin action",
            )
        self.message_user(request, f"{count} incident(s) marked as verified.")

    @admin.action(description="Mark selected as unverified")
    def mark_unverified(self, request, queryset):
        count = queryset.update(verified=False)
        for a in queryset:
            AuditLog.objects.create(
                accident=a, user=request.user,
                action="unverify", description="Unverified via admin action",
            )
        self.message_user(request, f"{count} incident(s) marked as unverified.")

    @admin.action(description="Set severity to Fatal")
    def set_severity_fatal(self, request, queryset):
        self._bulk_set_severity(request, queryset, "fatal")

    @admin.action(description="Set severity to Critical")
    def set_severity_critical(self, request, queryset):
        self._bulk_set_severity(request, queryset, "critical")

    @admin.action(description="Set severity to Serious")
    def set_severity_serious(self, request, queryset):
        self._bulk_set_severity(request, queryset, "serious")

    @admin.action(description="Set severity to Minor")
    def set_severity_minor(self, request, queryset):
        self._bulk_set_severity(request, queryset, "minor")

    def _bulk_set_severity(self, request, queryset, severity):
        count = queryset.update(severity=severity)
        for a in queryset:
            AuditLog.objects.create(
                accident=a, user=request.user,
                action="severity_change",
                description=f"Bulk severity set to {severity}",
            )
        self.message_user(request, f"{count} incident(s) updated to {severity}.")


@admin.register(Junction)
class JunctionAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "safety_score_display",
                    "accident_count", "fatal_count", "lat", "lng", "is_demo")
    list_filter = ("district", "is_demo")
    search_fields = ("name", "description", "district")
    actions = ["merge_junctions"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("accidents")

    @admin.display(description="Safety Score")
    def safety_score_display(self, obj):
        score = obj.safety_score
        color = "#c0392b" if score >= 50 else "#e67e22" if score >= 25 else "#2d8659"
        return f'<span style="color:{color};font-weight:700;">{score}</span>'
    safety_score_display.allow_tags = True

    @admin.display(description="Incidents")
    def accident_count(self, obj):
        return obj.accidents.count()

    @admin.display(description="Fatal")
    def fatal_count(self, obj):
        return obj.accidents.filter(severity="fatal").count()

    @admin.action(description="Merge selected junctions (keep first, reassign accidents)")
    def merge_junctions(self, request, queryset):
        if queryset.count() < 2:
            self.message_user(request, "Select at least 2 junctions to merge.", level="ERROR")
            return
        primary = queryset.first()
        rest = queryset.exclude(pk=primary.pk)
        merged_count = 0
        for j in rest:
            count = j.accidents.all().update(junction=primary, junction_name=primary.name)
            merged_count += count
            j.delete()
        AuditLog.objects.create(
            user=request.user, action="junction_merge",
            description=f"Merged {rest.count()} junctions into {primary.name} "
                        f"({merged_count} accidents reassigned)",
        )
        self.message_user(request, f"Merged {rest.count()} junctions into {primary.name}. "
                                   f"{merged_count} accidents reassigned.")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "email_notifications")
    list_filter = ("role", "email_notifications")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("show_demo_data",)
    fieldsets = (
        (None, {
            "fields": ("show_demo_data",),
            "description": (
                "When ON, demo/seed data is shown alongside real data on the public dashboard. "
                "When OFF, only real data (is_demo=False) is visible to the public."
            ),
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "accident_link", "description")
    list_filter = ("action", "created_at")
    search_fields = ("description", "accident__junction_name")
    date_hierarchy = "created_at"
    readonly_fields = ("accident", "user", "action", "description", "created_at")
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Accident")
    def accident_link(self, obj):
        if obj.accident:
            url = reverse("admin:accidents_accident_change", args=[obj.accident.id])
            return f'<a href="{url}">#{obj.accident.id}</a>'
        return "—"
    accident_link.allow_tags = True


# ===================== Custom Admin Index =====================

original_index = admin.site.index


def kpi_index(request, extra_context=None):
    """Replace the default admin index with a KPI dashboard."""
    qs = Accident.objects.all()
    unverified = qs.filter(verified=False)
    settings = SiteSettings.get_settings()
    context = {
        "kpi_total": qs.count(),
        "kpi_fatal": qs.filter(severity="fatal").count(),
        "kpi_critical": qs.filter(severity="critical").count(),
        "kpi_serious": qs.filter(severity="serious").count(),
        "kpi_minor": qs.filter(severity="minor").count(),
        "kpi_unverified": unverified.count(),
        "kpi_junctions": Junction.objects.count(),
        "kpi_total_casualties": qs.aggregate(Sum("casualties"))["casualties__sum"] or 0,
        "kpi_total_fatalities": qs.aggregate(Sum("fatalities"))["fatalities__sum"] or 0,
        "show_demo_data": settings.show_demo_data,
        "unverified_list": unverified.order_by("-occurred_at")[:15],
        "audit_list": AuditLog.objects.select_related("user", "accident")[:15],
    }
    if extra_context:
        context.update(extra_context)
    return original_index(request, context)


admin.site.index = kpi_index
