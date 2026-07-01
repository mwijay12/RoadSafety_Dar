# 📝 RoadSafety Dar — Changelog

All notable changes to this project are documented here.
Format: [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`

---

## [1.2.0] — 2026-07-01 — "Mwangaza" (Light)

### ✨ Added
- **PDF monthly report generation** — SUMATRA-ready reports with KPIs, severity breakdown, top junctions, time-of-day analysis
- **Progressive Web App (PWA)** — Installable on Android/iOS, offline-capable, custom service worker
- **Telegram bot integration** — Instant fatal cluster alerts, daily digest, command interface (`/start`, `/stats`, `/hotspots`)
- **Real-time dashboard** — 30-second auto-refresh, notification on new reports
- **PostGIS migration script** — Drop-in spatial queries (500m radius, polygons, etc.)
- **Bulk CSV import** — TPF legacy data ingestion with validation + deduplication

### 🔧 Changed
- Dashboard template restructured for block inheritance
- Manifest.json moved to root scope for proper PWA
- Service worker uses network-first with 3s timeout for APIs

### 🐛 Fixed
- Telegram webhook decorator (`@require_http_methods` instead of `@require_GET`)
- Dashboard template had double `{% endblock %}` (now correct)
- Manifest `start_url` set to `/dashboard/` for PWA scope

### 📦 Dependencies
- Added: `reportlab==5.0.0` (PDF generation)
- Added: `python-telegram-bot==21.7` (bot integration)

---

## [1.1.0] — 2026-06-30 — "Taa" (Lamp)

### ✨ Added
- **Public CSV export** — `/api/export.csv` downloads all records
- **AI-powered recommendations** — `/api/recommendations/` returns risk-leveled junctions with actions
- **Swahili (sw) translation** — `accidents/locale/sw/LC_MESSAGES/django.po` (34 strings)
- **Fatal cluster detection** — `python manage.py detect_fatal_clusters`
- **i18n URL patterns** — `/sw/dashboard/`, `/en/dashboard/`, locale cookie support

### 🔧 Changed
- Settings: `LANGUAGE_CODE = "en"`, `LOCALE_PATHS` configured
- Middleware: Added `LocaleMiddleware` for automatic language detection

### 🐛 Fixed
- `railway.json` was YAML, now valid JSON
- `.po` file had 2 unpaired `msgid` lines
- CSV field order was inconsistent (now stable)

---

## [1.0.0] — 2026-06-29 — "Msingi" (Foundation)

### 🎉 Initial Release

- **Public Dashboard** with:
  - Hotspot heatmap (Leaflet)
  - Severity distribution chart
  - Vehicle types chart
  - Monthly trends
  - Top 10 worst-affected junctions

- **Mobile Report Form** with:
  - GPS auto-capture
  - Severity, vehicle type, weather, road condition
  - Anonymous or identified reporting

- **Authority Dashboard** with:
  - Rule-based recommendation engine
  - Junction risk scoring
  - Actionable insights

- **Admin Panel** with:
  - Bulk verify action
  - CRUD for all records
  - Junction management

- **API** with 8 endpoints:
  - `/api/accidents/` (list/create)
  - `/api/heatmap/`
  - `/api/severity/`
  - `/api/vehicles/`
  - `/api/monthly/`
  - `/api/hourly/`
  - `/api/junctions/`
  - `/api/summary/`

- **Seed data**:
  - 80+ realistic accident records
  - 20+ named Dar es Salaam junctions
  - Geographic bounding box validation

---

## Versioning Policy

- **MAJOR** bump for breaking changes (model schema, API contracts)
- **MINOR** bump for new features (additive, backward-compatible)
- **PATCH** bump for bug fixes, performance, docs

**Roadmap (next versions):**
- `1.3.0` (Q3 2026): PostGIS spatial queries in production, weather API integration
- `1.4.0` (Q4 2026): Mobile app wrapper, push notifications, offline sync
- `2.0.0` (2027): Multi-city (Dodoma, Mwanza, Arusha), national dashboard
