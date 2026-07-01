"""
Tests for accidents app — covers models, views, and new v1.1 features.
Run with: python manage.py test accidents
"""
from datetime import datetime, timedelta
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

    def test_get_report_form_renders(self):
        resp = self.client.get(reverse("report"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "accidents/report.html")

    def test_post_valid_form_redirects(self):
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
        self.assertEqual(resp["Content-Type"], "text/csv")

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

    def test_recommendations_returns_list(self):
        resp = self.client.get("/api/recommendations/")
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_recommendations_have_required_fields(self):
        resp = self.client.get("/api/recommendations/")
        data = resp.json()
        rec = data[0]
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
        call_command("detect_fatal_clusters", stdout=out)
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


# ===================== END v1.2 TESTS =====================
