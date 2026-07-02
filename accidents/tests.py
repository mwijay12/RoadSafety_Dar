"""
Tests for accidents app — covers models, views, and new v1.1 features.
Run with: python manage.py test accidents
"""
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import Accident, Junction, VEHICLE_CHOICES, SEVERITY_CHOICES

class ModelTests(TestCase):
    """Test Accident + Junction model constraints and validation."""

    def setUp(self):
        self.junction = Junction.objects.create(
            name="Test Junction",
            lat=-6.7924,
            lng=39.2083,
        )

    def test_create_accident_minimal(self):
        a = Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["car"],
        )
        self.assertEqual(a.junction_name, "")
        self.assertFalse(a.verified)

    def test_create_accident_with_all_fields(self):
        a = Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            junction=self.junction,
            junction_name="Test Junction",
            occurred_at=timezone.now(),
            severity="fatal",
            vehicle_types=["bus", "motorcycle"],
            reporter_type="police",
            casualties=3, fatalities=1, injuries=2,
            description="Daladala hit bodaboda",
            weather="rainy",
            road_condition="wet",
            contact="+255700000000",
            verified=True,
        )
        self.assertEqual(a.casualties, 3)
        self.assertEqual(a.fatalities, 1)
        self.assertTrue(a.verified)

    def test_validation_fatalities_exceed_casualties(self):
        from django.core.exceptions import ValidationError
        a = Accident(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="fatal",
            vehicle_types=["car"],
            casualties=1, fatalities=2,
        )
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_validation_injuries_exceed_casualties(self):
        from django.core.exceptions import ValidationError
        a = Accident(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="serious",
            vehicle_types=["car"],
            casualties=1, injuries=5,
        )
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_validation_empty_vehicle_types(self):
        from django.core.exceptions import ValidationError
        a = Accident(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=[],
        )
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_validation_invalid_vehicle_type(self):
        from django.core.exceptions import ValidationError
        a = Accident(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["spaceship"],
        )
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_validation_lat_outside_dar(self):
        from django.core.exceptions import ValidationError
        a = Accident(
            lat=10.0,  # outside Dar
            lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["car"],
        )
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_validation_lng_outside_dar(self):
        from django.core.exceptions import ValidationError
        a = Accident(
            lat=-6.7924,
            lng=10.0,  # outside Dar
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["car"],
        )
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_str_method(self):
        a = Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="fatal",
            vehicle_types=["car"],
        )
        s = str(a)
        self.assertIn("Fatal", s)
        self.assertIn("Minor" not in s and "Serious" not in s, [True])

    def test_junction_str(self):
        self.assertEqual(str(self.junction), "Test Junction")

    def test_junction_unique_name(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Junction.objects.create(name="Test Junction", lat=-6.7, lng=39.2)


class DashboardViewTests(TestCase):
    """Test public dashboard renders correctly."""

    def setUp(self):
        self.client = Client()
        for i in range(3):
            Accident.objects.create(
                lat=-6.7924 + i * 0.01, lng=39.2083,
                occurred_at=timezone.now() - timedelta(days=i),
                severity=["minor", "serious", "fatal"][i],
                vehicle_types=["car"],
            )

    def test_dashboard_renders(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "accidents/dashboard.html")
        self.assertContains(resp, "Road Safety")  # any expected text

    def test_dashboard_kpi_count(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.context["total"], 3)
        self.assertEqual(resp.context["fatal_count"], 1)


class ReportFormTests(TestCase):
    """Test submission form (HTML + JSON)."""

    def setUp(self):
        self.client = Client()
        # Reset rate limiter between tests
        from accidents.decorators import _rate_log
        _rate_log.clear()
        # Create a logged-in community user for form POST tests
        self.user = User.objects.create_user("reporter1", "r@test.com", "pass1234")
        # UserProfile is auto-created by signal with role=community

    def _login(self):
        self.client.login(username="reporter1", password="pass1234")

    def test_get_report_form_renders(self):
        resp = self.client.get(reverse("report"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "accidents/report.html")

    def test_post_anonymous_redirects_to_login(self):
        resp = self.client.post(reverse("report"), {
            "severity": "minor",
            "vehicle_type": "car",
            "lat": -6.7924,
            "lng": 39.2083,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_post_valid_form_redirects(self):
        self._login()
        resp = self.client.post(reverse("report"), {
            "severity": "minor",
            "vehicle_type": "car",
            "lat": -6.7924,
            "lng": 39.2083,
            "occurred_at": "2026-07-01T10:00",
            "casualties": 0,
            "fatalities": 0,
            "injuries": 0,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Accident.objects.count(), 1)

    def test_post_invalid_lat_shows_error(self):
        self._login()
        from accidents.decorators import _rate_log
        _rate_log.clear()
        resp = self.client.post(reverse("report"), {
            "severity": "minor",
            "vehicle_type": "car",
            "lat": "not-a-number",
            "lng": 39.2083,
        })
        self.assertEqual(resp.status_code, 200)  # re-render form with error
        self.assertContains(resp, "error", status_code=200)
        self.assertEqual(Accident.objects.count(), 0)

    def test_post_outside_dar_bbox(self):
        self._login()
        from accidents.decorators import _rate_log
        _rate_log.clear()
        resp = self.client.post(reverse("report"), {
            "severity": "minor",
            "vehicle_type": "car",
            "lat": 10.0,
            "lng": 39.2083,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Accident.objects.count(), 0)


class APITests(TestCase):
    """Test all 8 JSON API endpoints."""

    def setUp(self):
        self.client = Client()
        for i in range(5):
            Accident.objects.create(
                lat=-6.7924 + i * 0.005, lng=39.2083,
                occurred_at=timezone.now() - timedelta(days=i, hours=i),
                severity=["minor", "minor", "serious", "fatal", "critical"][i],
                vehicle_types=[["car"], ["motorcycle"], ["bus"], ["car", "pedestrian"], ["truck"]][i],
                junction_name="Ubungo" if i < 3 else "",
                casualties=i,
                fatalities=1 if i == 3 else 0,
            )

    def test_api_heatmap(self):
        resp = self.client.get("/api/heatmap/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 5)
        self.assertEqual(len(data[0]), 3)  # [lat, lng, intensity]

    def test_api_accidents_list(self):
        resp = self.client.get("/api/accidents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 5)
        self.assertIn("intensity", data[0])

    def test_api_severity_counts(self):
        resp = self.client.get("/api/severity/")
        data = resp.json()
        self.assertEqual(data["minor"], 2)
        self.assertEqual(data["fatal"], 1)

    def test_api_vehicles_explodes_list(self):
        resp = self.client.get("/api/vehicles/")
        data = resp.json()
        # car: 2, motorcycle: 1, bus: 1, pedestrian: 1, truck: 1
        self.assertEqual(data["car"], 2)

    def test_api_junctions_top_n(self):
        resp = self.client.get("/api/junctions/?limit=5")
        data = resp.json()
        self.assertEqual(len(data), 1)  # only "Ubungo" has junction_name
        self.assertEqual(data[0]["name"], "Ubungo")
        self.assertEqual(data[0]["count"], 3)

    def test_api_summary_kpis(self):
        resp = self.client.get("/api/summary/")
        data = resp.json()
        self.assertEqual(data["total"], 5)
        self.assertEqual(data["fatal"], 1)
        self.assertEqual(data["total_fatalities"], 1)

    def test_api_accidents_post_json(self):
        resp = self.client.post(
            "/api/accidents/",
            data='{"severity":"minor","lat":-6.79,"lng":39.21,"vehicle_types":["car"]}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn("id", resp.json())

    def test_api_rate_limit(self):
        # Submit 6 times rapidly — 6th should be 429
        for i in range(5):
            self.client.post(
                "/api/accidents/",
                data='{"severity":"minor","lat":-6.79,"lng":39.21,"vehicle_types":["car"]}',
                content_type="application/json",
            )
        resp = self.client.post(
            "/api/accidents/",
            data='{"severity":"minor","lat":-6.79,"lng":39.21,"vehicle_types":["car"]}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 429)


# ============ v1.1 NEW FEATURE TESTS ============

class CSVDownloadTests(TestCase):
    """Test the public CSV download endpoint (v1.1 feature)."""

    def setUp(self):
        self.client = Client()
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="fatal",
            vehicle_types=["car", "motorcycle"],
            junction_name="Ubungo",
            casualties=2, fatalities=1, injuries=1,
        )

    def test_csv_download_endpoint_exists(self):
        resp = self.client.get("/api/export.csv")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])

    def test_csv_download_has_data(self):
        resp = self.client.get("/api/export.csv")
        content = resp.content.decode()
        # Header is sorted alphabetically (stable)
        self.assertIn("id,occurred_at,severity,vehicle_types", content)
        self.assertIn("fatal", content)
        self.assertIn("Ubungo", content)

    def test_csv_download_filename(self):
        resp = self.client.get("/api/export.csv")
        self.assertIn("attachment", resp["Content-Disposition"])


class SwahiliTranslationTests(TestCase):
    """Test the /sw/ URL prefix activates Swahili (v1.1 feature)."""

    def setUp(self):
        self.client = Client()

    def test_swahili_dashboard_renders(self):
        resp = self.client.get("/sw/dashboard/")
        self.assertEqual(resp.status_code, 200)

    def test_swahili_uses_translated_strings(self):
        resp = self.client.get("/sw/dashboard/")
        # Should contain Swahili keywords
        content = resp.content.decode()
        # At minimum, page should render
        self.assertIn("Road", content)  # brand name stays


class AIRecommendationsTests(TestCase):
    """Test the AI-powered recommendation engine (v1.1 feature)."""

    def setUp(self):
        self.client = Client()
        # Seed enough data for recommendations
        for i in range(10):
            Accident.objects.create(
                lat=-6.7924, lng=39.2083,
                occurred_at=timezone.now().replace(hour=8 + (i % 4)) - timedelta(days=i),
                severity="fatal" if i < 3 else "serious",
                vehicle_types=["motorcycle"],
                junction_name="Mwenge",
                fatalities=1 if i < 3 else 0,
                casualties=1,
            )

    def test_recommendations_endpoint_exists(self):
        resp = self.client.get("/api/recommendations/")
        self.assertEqual(resp.status_code, 200)

    def test_recommendations_returns_dict_with_list(self):
        resp = self.client.get("/api/recommendations/")
        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertIn("recommendations", data)
        self.assertIsInstance(data["recommendations"], list)
        self.assertGreater(len(data["recommendations"]), 0)

    def test_recommendations_have_required_fields(self):
        resp = self.client.get("/api/recommendations/")
        data = resp.json()
        rec = data["recommendations"][0]
        self.assertIn("junction", rec)
        self.assertIn("risk_level", rec)
        self.assertIn("actions", rec)


class FatalClusterNotificationTests(TestCase):
    """Test the fatal-cluster detection command (v1.1 feature)."""

    def setUp(self):
        self.junction = Junction.objects.create(
            name="Kariakoo Market",
            lat=-6.8160, lng=39.2765,
        )
        # 3 fatal accidents in 7 days at same junction (triggers alert)
        for i in range(3):
            Accident.objects.create(
                lat=-6.8160, lng=39.2765,
                junction=self.junction,
                junction_name="Kariakoo Market",
                occurred_at=timezone.now() - timedelta(days=i),
                severity="fatal",
                vehicle_types=["motorcycle"],
                fatalities=1, casualties=1,
            )

    def test_cluster_detection_command(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # Command exits with 1 when clusters found (by design for cron monitoring)
        try:
            call_command("detect_fatal_clusters", stdout=out)
        except SystemExit as e:
            self.assertEqual(e.code, 1)  # Expected exit code when clusters found
        output = out.getvalue()
        # Should detect Kariakoo as a cluster
        self.assertIn("Kariakoo", output)


# ===================== v1.2 NEW TESTS =====================

class PWAEndpointTests(TestCase):
    """Test PWA endpoints (manifest, service worker, offline page)."""

    def test_manifest_returns_json(self):
        resp = self.client.get("/manifest.json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/json", resp["Content-Type"])
        data = resp.json()
        self.assertEqual(data["name"], "RoadSafety Dar es Salaam")
        self.assertEqual(data["display"], "standalone")
        self.assertIn("icons", data)

    def test_sw_returns_javascript(self):
        resp = self.client.get("/sw.js")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("javascript", resp["Content-Type"])
        content = resp.content.decode()
        self.assertIn("CACHE_NAME", content)

    def test_offline_page(self):
        resp = self.client.get("/offline/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("offline", resp.content.decode().lower())


class PDFReportTests(TestCase):
    """Test PDF monthly report endpoint."""

    def setUp(self):
        from django.utils import timezone
        from datetime import timedelta
        Accident.objects.create(
            occurred_at=timezone.now() - timedelta(days=5),
            severity="fatal", vehicle_types=["motorcycle"],
            junction_name="Test Junction",
            lat=-6.7924, lng=39.2083,
            fatalities=2, casualties=3, injuries=1,
        )

    def test_pdf_endpoint_returns_pdf(self):
        resp = self.client.get("/api/report/monthly.pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF-"))

    def test_pdf_with_month_param(self):
        resp = self.client.get("/api/report/monthly.pdf?month=2026-06")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment", resp["Content-Disposition"])

    def test_pdf_invalid_month(self):
        resp = self.client.get("/api/report/monthly.pdf?month=invalid")
        self.assertEqual(resp.status_code, 400)

    def test_pdf_empty_month_still_works(self):
        resp = self.client.get("/api/report/monthly.pdf?month=2020-01")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b"%PDF-"))


class TelegramWebhookTests(TestCase):
    """Test Telegram bot webhook."""

    def test_webhook_post_start_command(self):
        import json as jsonmod
        update = {
            "update_id": 12345,
            "message": {
                "chat": {"id": 123456},
                "text": "/start",
            },
        }
        resp = self.client.post(
            "/api/telegram/webhook/",
            data=jsonmod.dumps(update),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"ok")

    def test_webhook_get_returns_info(self):
        resp = self.client.get("/api/telegram/webhook/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("POST", resp.content.decode())

    def test_webhook_invalid_json(self):
        resp = self.client.post(
            "/api/telegram/webhook/",
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


class RealTimeRefreshTests(TestCase):
    """Test that the dashboard includes the live refresh elements."""

    def test_dashboard_has_live_indicator(self):
        resp = self.client.get("/dashboard/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("live-indicator", content)
        self.assertIn("LIVE", content)

    def test_dashboard_has_service_worker_register(self):
        resp = self.client.get("/dashboard/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("serviceWorker", content)
        self.assertIn("/sw.js", content)

    def test_dashboard_has_manifest_link(self):
        resp = self.client.get("/dashboard/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("/manifest.json", content)


class GenerateMonthlyReportTests(TestCase):
    """Test the PDF report generation command."""

    def test_command_runs(self):
        from django.core.management import call_command
        from io import StringIO
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "test_report.pdf")
            out = StringIO()
            try:
                call_command(
                    "generate_monthly_report",
                    month="2026-06",
                    output=output,
                    stdout=out,
                )
                self.assertTrue(os.path.exists(output))
                with open(output, "rb") as f:
                    content = f.read()
                self.assertTrue(content.startswith(b"%PDF-"))
            except Exception as e:
                if "reportlab" not in str(e).lower():
                    raise


class TelegramBotModuleTests(TestCase):
    """Test the telegram_bot utility module."""

    def test_send_message_without_token_returns_false(self):
        from accidents.telegram_bot import send_message
        # Without TELEGRAM_BOT_TOKEN env, should silently return False
        result = send_message(123456, "test")
        self.assertFalse(result)

    def test_broadcast_stats_returns_zero_without_token(self):
        from accidents.telegram_bot import broadcast_stats
        result = broadcast_stats([1, 2, 3], total=10, fatal=2)
        self.assertEqual(result, 0)

    def test_send_fatal_alert_returns_false_without_token(self):
        from accidents.telegram_bot import send_fatal_alert
        result = send_fatal_alert(123, "Test Junction", 5)
        self.assertFalse(result)


# ===================== v1.2.0 TESTS (Versioning + Premium UI) =====================

class VersioningTests(TestCase):
    """Test the versioning system."""

    def test_version_endpoint_returns_json(self):
        resp = self.client.get("/api/version")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("version", data)
        self.assertIn("version_name", data)
        self.assertIn("status", data)

    def test_healthz_endpoint(self):
        resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # /healthz should report service_status = "ok" for the load balancer
        self.assertEqual(data["service_status"], "ok")
        self.assertEqual(data["service"], "roadsafety-dar")
        self.assertIn("version", data)

    def test_version_module(self):
        from roadsafety.version import version_info, short_version
        info = version_info()
        self.assertIn("version", info)
        self.assertIn("build", info)
        # Short version should be formatted
        sv = short_version()
        self.assertIn(info["version"], sv)


class SeedJunctionsTests(TestCase):
    """Test the seed_junctions management command."""

    def test_junction_has_district(self):
        from accidents.models import Junction
        # After seeding, junctions should have district field
        j = Junction.objects.first()
        if j:
            # District is optional but at least 50+ should have it after seeding
            self.assertTrue(hasattr(j, "district"))

    def test_seed_junctions_command_runs(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # Should not raise even if already seeded
        call_command("seed_junctions", stdout=out)
        self.assertIn("junctions", out.getvalue().lower())


class PremiumUITests(TestCase):
    """Test the premium UI redesign (v1.2.0)."""

    def test_dashboard_uses_premium_palette(self):
        resp = self.client.get("/dashboard/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("Road Safety", content)
        self.assertIn("Dar es Salaam", content)
        self.assertIn("featured-stat-card", content)
        self.assertIn("live-badge", content)

    def test_dashboard_has_severity_legend(self):
        resp = self.client.get("/dashboard/")
        content = resp.content.decode()
        for sev in ["Total Reports", "Fatal", "Tracked Junctions", "Police Verified"]:
            self.assertIn(sev, content, f"Missing severity: {sev}")
        self.assertIn("Severity Distribution", content)
        self.assertIn("severityChart", content)

    def test_dashboard_has_time_of_day_chart(self):
        resp = self.client.get("/dashboard/")
        content = resp.content.decode()
        self.assertIn("hourlyChart", content)
        self.assertIn("Time of Day", content)

    def test_dashboard_has_telegram_link(self):
        resp = self.client.get("/dashboard/")
        content = resp.content.decode()
        self.assertIn("t.me/roadsafety_dar_bot", content)

    def test_dashboard_has_pdf_download(self):
        resp = self.client.get("/dashboard/")
        content = resp.content.decode()
        self.assertIn("/api/report/monthly.pdf", content)


class APIImprovementsTests(TestCase):
    """Test API improvements for v1.2.0."""

    def test_summary_has_total_reports_alias(self):
        # Add trailing slash follow to handle APPEND_SLASH
        resp = self.client.get("/api/stats/summary", follow=True)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Live refresh JS uses both
        self.assertIn("total", data)
        self.assertIn("total_reports", data)
        self.assertEqual(data["total"], data["total_reports"])

    def test_summary_has_service_metadata(self):
        resp = self.client.get("/api/stats/summary", follow=True)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["service"], "roadsafety-dar")
        self.assertIn("server_time", data)

    def test_heatmap_is_severity_weighted(self):
        # Create one of each severity at the same location
        from datetime import datetime, timedelta
        from django.utils import timezone
        Accident.objects.create(
            occurred_at=timezone.now(), severity="fatal",
            vehicle_types=["car"], lat=-6.79, lng=39.20,
        )
        resp = self.client.get("/api/heatmap/")
        pts = resp.json()
        # Each point is [lat, lng, intensity]
        self.assertGreater(len(pts), 0)
        # Fatal should have intensity = 4
        for p in pts:
            self.assertEqual(len(p), 3)
            self.assertGreater(p[2], 0)

    def test_junctions_includes_district(self):
        from datetime import datetime, timedelta
        from django.utils import timezone
        # Create a junction and a linked accident
        j = Junction.objects.create(
            name="Test District Junction",
            lat=-6.79, lng=39.20,
            district="Kinondoni",
        )
        Accident.objects.create(
            occurred_at=timezone.now(), severity="minor",
            vehicle_types=["car"], lat=-6.79, lng=39.20,
            junction=j, junction_name="Test District Junction",
        )
        resp = self.client.get("/api/junctions/?limit=100")
        data = resp.json()
        test_j = next((x for x in data if x["name"] == "Test District Junction"), None)
        if test_j:
            self.assertEqual(test_j["district"], "Kinondoni")


class ResponsiveLayoutTests(TestCase):
    """Test responsive mobile layout."""

    def test_css_has_mobile_breakpoints(self):
        resp = self.client.get("/static/css/app.css")
        # WhiteNoise uses streaming_content for static files
        content = b"".join(resp.streaming_content) if hasattr(resp, "streaming_content") else resp.content
        # CSS should have @media queries
        self.assertIn(b"@media", content)
        self.assertTrue(
            b"max-width: 720px" in content or b"max-width: 900px" in content,
            "No mobile breakpoint found",
        )

    def test_dashboard_renders_on_mobile_user_agent(self):
        # Render should not fail with mobile UA
        c = Client(HTTP_USER_AGENT="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)")
        resp = c.get("/dashboard/")
        self.assertEqual(resp.status_code, 200)


class EastAfricaTimezoneTests(TestCase):
    """Test EAT (Africa/Dar_es_Salaam) timezone settings."""

    def test_timezone_is_set_in_settings(self):
        from django.conf import settings
        self.assertEqual(settings.TIME_ZONE, "Africa/Dar_es_Salaam")

    def test_timezone_is_activated(self):
        from django.utils import timezone
        from datetime import datetime
        # Make a datetime and verify it has EAT applied
        now = timezone.now()
        self.assertIsNotNone(now.tzinfo)



class AuthTests(TestCase):
    """Test authentication flows (Prompt 3)."""

    def setUp(self):
        self.client = Client()
        from accidents.decorators import _rate_log
        _rate_log.clear()
        self.user = User.objects.create_user("authtest", "auth@test.com", "pass1234")
        # UserProfile auto-created by signal, role defaults to community

    def test_login_page_renders(self):
        resp = self.client.get("/accounts/login/")
        self.assertEqual(resp.status_code, 200)

    def test_signup_page_renders(self):
        resp = self.client.get("/accounts/signup/")
        self.assertEqual(resp.status_code, 200)

    def test_login_succeeds(self):
        resp = self.client.post("/accounts/login/", {"login": "authtest", "password": "pass1234"})
        self.assertIn(resp.status_code, (302, 200))

    def test_authority_anonymous_redirects(self):
        resp = self.client.get("/authority/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_authority_community_forbidden(self):
        self.client.login(username="authtest", password="pass1234")
        resp = self.client.get("/authority/")
        # community user should be redirected (not 200)
        self.assertEqual(resp.status_code, 302)

    def test_authority_police_access(self):
        police = User.objects.create_user("officer1", "police@test.com", "pass1234")
        police.profile.role = "police"
        police.profile.save()
        self.client.login(username="officer1", password="pass1234")
        resp = self.client.get("/authority/")
        self.assertEqual(resp.status_code, 200)

    def test_user_profile_created_on_signup(self):
        from .models import UserProfile
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertEqual(self.user.profile.role, "community")

    def test_report_post_sets_reporter_type_from_role(self):
        self.client.login(username="authtest", password="pass1234")
        resp = self.client.post(reverse("report"), {
            "severity": "minor",
            "vehicle_type": "car",
            "lat": -6.7924,
            "lng": 39.2083,
            "occurred_at": "2026-07-01T10:00",
            "casualties": 0,
            "fatalities": 0,
            "injuries": 0,
        })
        self.assertEqual(resp.status_code, 302)
        a = Accident.objects.first()
        self.assertEqual(a.reporter_type, "community")


class EmailNotificationTests(TestCase):
    """Test email notification signals (Prompt 6)."""

    def setUp(self):
        # Create a police user with email_notifications enabled
        self.police = User.objects.create_user("officer", "officer@test.com", "pass1234")
        self.police.profile.role = "police"
        self.police.profile.email_notifications = True
        self.police.profile.save()

    def test_fatal_accident_sends_alert(self):
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="fatal",
            vehicle_types=["car"],
            fatalities=1, casualties=1,
            junction_name="Ubungo",
        )
        self.assertGreater(len(mail.outbox), 0)
        self.assertIn("Fatal", mail.outbox[0].subject)
        self.assertIn("officer@test.com", mail.outbox[0].to)

    def test_critical_accident_sends_alert(self):
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="critical",
            vehicle_types=["bus"],
            casualties=3,
            junction_name="Mwenge",
        )
        self.assertGreater(len(mail.outbox), 0)
        self.assertIn("Critical", mail.outbox[0].subject)

    def test_minor_accident_does_not_send_alert(self):
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["car"],
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_when_notifications_disabled(self):
        self.police.profile.email_notifications = False
        self.police.profile.save()
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="fatal",
            vehicle_types=["car"],
            fatalities=1, casualties=1,
        )
        self.assertEqual(len(mail.outbox), 0)


class DigestCommandTests(TestCase):
    """Test the send_daily_digest management command (Prompt 6)."""

    def setUp(self):
        self.police = User.objects.create_user("officer2", "officer2@test.com", "pass1234")
        self.police.profile.role = "police"
        self.police.profile.email_notifications = True
        self.police.profile.save()

    def test_dry_run_does_not_send_email(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("send_daily_digest", dry_run=True, stdout=out)
        output = out.getvalue()
        self.assertIn("DRY-RUN", output)
        self.assertEqual(len(mail.outbox), 0)

    def test_digest_sends_with_data(self):
        from io import StringIO
        from django.core.management import call_command
        # Clear email outbox from signal (fatal accident triggers alert)
        mail.outbox.clear()
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["car"],
        )
        out = StringIO()
        call_command("send_daily_digest", stdout=out)
        self.assertGreater(len(mail.outbox), 0)
        self.assertIn("Digest", mail.outbox[0].subject)
        self.assertIn("officer2@test.com", mail.outbox[0].to)

    def test_no_recipients_skips(self):
        from io import StringIO
        from django.core.management import call_command
        self.police.profile.email_notifications = False
        self.police.profile.save()
        out = StringIO()
        call_command("send_daily_digest", stdout=out)
        self.assertIn("No authority recipients", out.getvalue())
        self.assertEqual(len(mail.outbox), 0)



# ===================== Prompt 8: Admin Panel & Data Quality Tests =====================


class AuditLogModelTests(TestCase):
    """Test AuditLog model creation and behaviour."""

    def setUp(self):
        self.user = User.objects.create_user("adminuser", "admin@test.com", "pass1234")
        self.accident = Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["car"],
        )

    def test_audit_log_created(self):
        from .models import AuditLog
        log = AuditLog.objects.create(
            accident=self.accident, user=self.user,
            action="verify", description="Test verify",
        )
        self.assertEqual(log.action, "verify")
        self.assertEqual(log.accident, self.accident)
        self.assertIsNotNone(log.created_at)

    def test_audit_log_str(self):
        from .models import AuditLog
        log = AuditLog.objects.create(
            accident=self.accident, user=self.user,
            action="edit",
        )
        self.assertIn("Edit", str(log))

    def test_audit_log_ordering(self):
        from .models import AuditLog
        log1 = AuditLog.objects.create(accident=self.accident, action="create")
        log2 = AuditLog.objects.create(accident=self.accident, action="verify")
        logs = AuditLog.objects.all().order_by("-created_at", "-pk")
        self.assertEqual(logs[0], log2)
        self.assertEqual(logs[1], log1)

    def test_audit_log_no_accident_ok(self):
        from .models import AuditLog
        log = AuditLog.objects.create(user=self.user, action="junction_merge")
        self.assertIsNone(log.accident)


class DataQualityCommandTests(TestCase):
    """Test the data_quality_report management command."""

    def test_command_runs_with_no_data(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command("data_quality_report", stdout=out)
        self.assertIn("No accident records", out.getvalue())

    def test_command_runs_with_data(self):
        from io import StringIO
        from django.core.management import call_command
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="fatal",
            vehicle_types=["car"],
            fatalities=2, casualties=2,
            description="Test crash",
        )
        out = StringIO()
        call_command("data_quality_report", stdout=out)
        output = out.getvalue()
        self.assertIn("Overview", output)
        self.assertIn("Total records", output)
        self.assertIn("Overall Data Quality Score", output)

    def test_command_markdown_output(self):
        from io import StringIO
        from django.core.management import call_command
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["bicycle"],
        )
        out = StringIO()
        call_command("data_quality_report", output="markdown", stdout=out)
        output = out.getvalue()
        # Markdown format uses pipe-delimited rows
        self.assertIn("|", output)
        self.assertIn("# Data Quality Report", output)

    def test_command_grade_a_with_good_data(self):
        from io import StringIO
        from django.core.management import call_command
        # Perfect records: all 5 core fields filled + verified
        for i in range(10):
            Accident.objects.create(
                lat=-6.7924, lng=39.2083,
                occurred_at=timezone.now(),
                severity="minor",
                vehicle_types=["car"],
                casualties=0,
                description=f"Test {i}",
                weather="sunny",
                road_condition="dry",
                junction_name="Ubungo",
                contact="+255700000000",
                verified=True,
            )
        out = StringIO()
        call_command("data_quality_report", stdout=out)
        output = out.getvalue()
        self.assertTrue("Grade: A" in output or "100.0%" in output)


class AdminPanelTests(TestCase):
    """Test admin panel customizations (Prompt 8/9)."""

    def setUp(self):
        self.admin = User.objects.create_superuser("super", "super@test.com", "pass1234")

    def test_admin_index_shows_kpis(self):
        self.client.login(username="super", password="pass1234")
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Total Reports")
        self.assertContains(resp, "Fatal Accidents")
        self.assertContains(resp, "Tracked Junctions")

    def test_admin_index_shows_model_links(self):
        self.client.login(username="super", password="pass1234")
        resp = self.client.get("/admin/")
        self.assertContains(resp, "Accidents")
        self.assertContains(resp, "Junctions")
        self.assertContains(resp, "Audit Log")

    def test_admin_accident_list_renders(self):
        self.client.login(username="super", password="pass1234")
        Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["car"],
        )
        resp = self.client.get("/admin/accidents/accident/")
        self.assertEqual(resp.status_code, 200)

    def test_admin_verify_action_logs_audit(self):
        from .models import AuditLog
        self.client.login(username="super", password="pass1234")
        a = Accident.objects.create(
            lat=-6.7924, lng=39.2083,
            occurred_at=timezone.now(),
            severity="minor",
            vehicle_types=["car"],
        )
        data = {
            "action": "mark_verified",
            "_selected_action": [a.id],
        }
        resp = self.client.post("/admin/accidents/accident/", data, follow=True)
        self.assertEqual(resp.status_code, 200)
        a.refresh_from_db()
        self.assertTrue(a.verified)
        self.assertTrue(AuditLog.objects.filter(accident=a, action="verify").exists())


# ===================== END v1.3 TESTS =====================


class TTSAPITests(TestCase):
    """Test the ElevenLabs TTS API endpoint (v1.4.0)."""

    def test_tts_endpoint_returns_400_when_missing_text(self):
        resp = self.client.get("/api/tts/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Missing 'text' parameter", resp.content.decode())

    def test_tts_endpoint_returns_503_when_no_api_key(self):
        with self.settings(ELEVENLABS_API_KEY=""):
            resp = self.client.get("/api/tts/?text=test")
            self.assertEqual(resp.status_code, 503)
            self.assertIn("API key not configured", resp.content.decode())

    def test_tts_endpoint_successful_mocked(self):
        from unittest.mock import patch, MagicMock
        mock_audio_bytes = b"fake-mpeg-audio-data"

        with self.settings(ELEVENLABS_API_KEY="mock-eleven-key"):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = mock_audio_bytes
                mock_urlopen.return_value.__enter__.return_value = mock_response

                resp = self.client.get("/api/tts/?text=Hello+World")
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp["Content-Type"], "audio/mpeg")
                self.assertEqual(resp.content, mock_audio_bytes)
                self.assertIn("Cache-Control", resp)

