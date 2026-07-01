# 📝 RoadSafety Dar — Changelog

All notable changes to this project are documented here.
Format: [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`

---

## [1.3.1] — 2026-07-02 — "Mwitikio" (Responsive)

### ✨ Added
- **Full responsive design** — Hero, nav, forms, action bar, map, KPIs, charts all scale across mobile/tablet/desktop
- **Polished PDF monthly report** — Executive summary, severity breakdown, vehicle types, peak hours, top junctions — all styled in Skylearn palette

### 🔧 Changed
- Responsive breakpoints: 900px (tablet charts), 720px (tablet layout), 480px (phone), 400px (small phone)
- Hero column-stacks on tablet; hero-actions hidden on mobile
- Buttons go full-width in action bar on tablet; font-size shrinks on phone
- Map height reduces (520px → 380px → 300px)
- Featured stat cards: `auto-fit` grid → single column on phone; smaller values/labels
- Topbar brand shrinks on phone; nav gaps tighten
- PDF now shows: severity breakdown table, vehicle type distribution, hourly peak hours, top 10 junctions table
- All root-level old icon PNGs added to `.gitignore`

### 🐛 Fixed
- `vehicle_types` is JSON array (not CharField) — PDF now handles correctly
- Duplicate `@media` rules consolidated into single breakpoints

---

## [1.3.0] — 2026-07-01 — "Chombo" (Container)

### ✨ Added
- **Docker multi-stage build** — `python:3.11-slim` base, GDAL for PostGIS, health check
- **Docker Compose** — One-command local dev with Django + PostGIS + Redis
- **Makefile Docker commands** — `docker-build`, `docker-up`, `docker-test`, etc.
- **`.dockerignore`** — Excludes caches, virtualenvs, SQLite from image

### 🔧 Changed
- `render.yaml` and `railway.json` kept for backward compatibility (non-Docker deploys)
- Version bumped to 1.3.0 "Chombo"

---

## [1.2.0] — 2026-07-01 — "Mwangaza" (Light)

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
- `1.4.0` (Q3 2026): PostGIS spatial queries in production, weather API integration
- `1.5.0` (Q4 2026): Mobile app wrapper, push notifications, offline sync
- `2.0.0` (2027): Multi-city (Dodoma, Mwanza, Arusha), national dashboard
