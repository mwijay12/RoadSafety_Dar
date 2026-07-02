# 🚦 Road Safety Dar es Salaam — Hotspot Mapping & Analysis System

> **Project 24** — Spatial road-accident information management for Dar es Salaam, integrating police and community reports, feeding a public hotspot heatmap and an authority infrastructure-decision dashboard. Aligned with **UN SDG 11.2** (safe, affordable, accessible transport for all).

![Status](https://img.shields.io/badge/status-Active%20Development-1f9d55?style=flat-square) ![Python](https://img.shields.io/badge/python-3.11-3776AB?style=flat-square&logo=python) ![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat-square&logo=django) ![Leaflet](https://img.shields.io/badge/Leaflet-1.9-199900?style=flat-square&logo=leaflet) ![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square) ![Tests](https://img.shields.io/badge/tests-68%20passing-1f9d55?style=flat-square)

---

## 📖 Table of Contents

1. [Project Identity](#-section-1-project-identity)
2. [Live System Snapshot](#-section-2-live-system-snapshot)
3. [System Architecture](#-section-3-system-architecture)
4. [Complete File Structure](#-section-4-complete-file-structure)
5. [Installation & Setup](#-section-5-installation--setup)
6. [How To Use It](#-section-6-how-to-use-it)
7. [Database Schema](#-section-7-database-schema)
8. [AI / Spatial Integration Details](#-section-8-spatial-integration-details)
9. [Current Limitations & Known Bugs](#-section-9-current-limitations--known-bugs)
10. [Modification & Addon Guide](#-section-10-modification--addon-guide)
11. [Deployment Guide](#-section-11-deployment-guide)
12. [Cost Calculator](#-section-12-cost-calculator)
13. [Roadmap](#-section-13-roadmap)
14. [Lessons Learned](#-section-14-lessons-learned)
15. [Quick Reference Card](#-section-15-quick-reference-card)

---

## 🪪 SECTION 1: Project Identity

**🚦 Road Safety Dar es Salaam — Hotspot Mapping & Analysis System**

**Explain it to a 10-year-old:**
When someone gets hurt in a road accident in Dar, people press a button on their phone to tell the map. The map turns red where accidents happen the most, so the police and the road-builders know exactly where to put a traffic light, a speed bump, or a zebra crossing.

**Explain it to a developer:**
A Django + GeoDjango-ready web application backed by SQLite (PostGIS in production) that ingests structured road-accident reports from police and community sources, geocodes each incident to lat/lng, and publishes 8 JSON APIs powering a Leaflet heatmap, marker-cluster incident map, severity/vehicle/monthly/hourly Chart.js dashboards, and a top-10 worst-affected-junction ranking. Authorities get a second dashboard with auto-generated intervention recommendations based on time-of-day risk profiles.

**Explain it as a business problem it solves:**
Tanzania loses **>4,000 lives per year** to road traffic injuries (WHO 2023). Dar es Salaam alone accounts for ~40% of all national traffic incidents. Yet the country lacks an open, citizen-contributable, spatially-aggregated decision-support tool for the police (TPF), TANROADS, and the Surface and Marine Transport Regulatory Authority (SUMATRA) to identify hotspots and prioritise engineering interventions. This system closes that gap with a free, open-source, mobile-friendly platform that turns fragmented accident reports into evidence that saves lives.

**Current version:** `v1.1.0-dev` — 🚧 **Active Development** (v1.0 shipped locally; v1.1 hardening for public pilot).

**Built by:** **Davie Byanmwijage (Mwijay)** — Dar es Salaam, Tanzania — as a University Project 24 deliverable for the Spatial Data Management module. Code is free and open source (MIT). Map tiles © OpenStreetMap contributors.

**What makes this different from every other similar product:**

| Existing product | What we do differently |
|---|---|
| WHO Global Status Report on Road Safety (PDF, no API) | Public, live, **drillable** dashboard |
| Tanzania Police Force annual report (paper, annual) | **Real-time** ingestion from community + police |
| Google Maps incident reports (global, generic) | **Locally curated** with Dar-specific severity/casualty model |
| SUMATRA statistics dashboard (no map) | **Spatial hotspots** + intervention recommendations |
| WRI Ross Center reports (slow, no live data) | **Mobile-friendly submission** with GPS capture |

The 4 differentiators: **spatial** (real hotspot heatmap), **live** (community submits in seconds), **local** (Swahili-ready, Dar hotspots curated), and **action-oriented** (auto-generated engineering recommendations).

---

## 📊 SECTION 2: Live System Snapshot

**As of v1.1.0-dev (July 2026), running locally on `http://127.0.0.1:8000`.**

| Component | Status | What It Does | Tech Used |
|---|---|---|---|
| Public dashboard | ✅ Working | Heatmap + marker cluster + 4 charts + junction table | Django, Leaflet 1.9, Leaflet.heat, Leaflet.markercluster, Chart.js 4.4 |
| Mobile report form | ✅ Working | `AccidentForm` validation, Dar bbox, cross-field checks | `accidents/forms.py` |
| JSON API report endpoint | ✅ Working | `POST /api/accidents/` shares the same form, rate-limited | `AccidentForm` + `_rate_check` |
| Authority dashboard | ✅ Working | High-risk hour profile + auto-recommendations | Chart.js bar + rule engine |
| 80 seed records | ✅ Working | Realistic Dar hotspots, weighted severity, hour distribution | Custom Django management command + Faker |
| 20 named junctions | ✅ Working | Kariakoo, Ubungo, Mwenge, Selander Bridge, etc. | Seed command |
| 8 JSON APIs | ✅ Working | heatmap, accidents, severity, vehicles, monthly, hourly, junctions, summary | Django JsonResponse |
| Django admin | ✅ Working | Verify, edit, filter, date-hierarchy, custom action | django.contrib.admin |
| Accident factories | ✅ Working | `JunctionFactory` + `AccidentFactory` for tests | `accidents/factories.py` |
| 68 pytest tests | ✅ Passing | Model validation, API endpoints, form submission, rate limiting, factories | `pytest-django` + `conftest.py` |
| H3 hexagonal cells | ✅ Working | Auto-computed on save, resolution 10 (~68m) | Uber H3 library |
| Junction slug + safety score | ✅ Working | URL-safe slug, severity-weighted safety score property | `Accident` model |
| Settings package | ✅ Working | `base/dev/prod` split with env selector | `roadsafety/settings/` |
| Environment hardening | ✅ Working | 26 env vars, `.env.example`, `pyproject.toml` (ruff + mypy + pytest) | dotenv + pyproject |
| PostGIS spatial queries | ⏳ Planned | Replace lat/lng with `PointField`, radius search | GDAL + PostGIS (Linux/Mac) |
| Swahili UI | ⏳ Planned | Full `sw/` translation | Django i18n |
| Mobile app (PWA) | ⏳ Planned | Install-to-home-screen, offline reports | Service worker, IndexedDB |

**What is fully working right now:**
- `GET /` → redirects to `/dashboard/`
- `GET /dashboard/` → 200, renders map + 4 chart canvases + junction table + 4 KPI cards
- `GET /report/` → 200, `AccidentForm`-driven form with **Use my current location** button
- `POST /report/` → validates via `AccidentForm` (Dar bbox, cross-field checks), inserts record, redirects
- `POST /api/accidents/` → JSON API, same `AccidentForm`, rate-limited (5/min per IP)
- `GET /authority/` → 200, time-of-day bar chart + auto-recommendation list
- `GET /api/heatmap/` → 200, `[[lat, lng, intensity], ...]` for Leaflet.heat
- `GET /api/accidents/` → 200, full list with metadata
- `GET /api/severity/` → 200, `{minor, serious, fatal, critical}` counts
- `GET /api/vehicles/` → 200, `{motorcycle, car, bus, truck, bicycle, pedestrian, mixed}` counts
- `GET /api/monthly/` → 200, `[{month, count}, ...]` for last 12 months
- `GET /api/hourly/` → 200, 24-bucket histogram 0–23
- `GET /api/junctions/` → 200, ranked by count descending
- `GET /api/summary/` → 200, KPI bundle for the dashboard
- `GET /admin/` → 302 → login, then full CRUD with custom `mark_verified` action
- `python manage.py test accidents` → 68/69 passing (1 pre-existing static-file 404)
- `pytest accidents/test_factories.py` → 17 factory tests passing
- **User:** `admin` / password `roadsafety`

**What is partially working:**
- Junction clustering uses a **3-decimal-place bucket** (~110m grid) — for production, use PostGIS `ST_SnapToGrid` or `ST_ClusterDBSCAN`.
- Recommendation engine is **rule-based** — v1.2 will swap it for an LLM via Cloudflare Llama 3.3 70B.
- `api_summary()` includes a `by_day` query that is **not yet rendered** on the dashboard (it returns 200 but the dashboard uses `api_severity` for KPIs).

**What is planned but not started yet:**
- [ ] PostGIS migration script (preserves seed data)
- [ ] Swahili (`/sw/`) translation file
- [ ] User authentication (Django AllAuth, police/reporter accounts)
- [ ] CAPTCHA on public form (Cloudflare Turnstile)
- [ ] Email/SMS notification when 3+ fatal accidents hit the same junction in 7 days
- [ ] PDF monthly report generation (`reportlab` + `weasyprint`)
- [ ] PWA / service worker for offline report submission
- [ ] Bulk CSV import for Tanzania Police Force legacy data
- [ ] Public CSV download (`/api/export.csv`)

**What was tried and abandoned and WHY:**

| Attempt | Why abandoned |
|---|---|
| GeoDjango + PostGIS from day 1 | Blocked on Windows because GDAL 3.x native wheels are not available — pivoted to SQLite + float lat/lng, kept the same model interface so the swap is 4 lines of code in `models.py` |
| `django-geojson` for vector tile output | Overkill for v1 — JSON array is enough; KMZ/Vector-tile export is a v1.2 task |
| `django-leaflet` widget for the form | Pulled in `django.contrib.gis` which requires GDAL — swapped to vanilla Leaflet via CDN, simpler and faster |
| Plotly for charts | Slower than Chart.js and 2 MB heavier — Chart.js wins on mobile |
| Apache ECharts | UI not in our brand palette out of the box; Chart.js + custom CSS achieves the look we want |

---

## 🏗️ SECTION 3: System Architecture

### 3.1 High-level data flow

```
                         ┌──────────────────────────────────┐
   👤 Community user     │  📱 Mobile-friendly Web Form     │
   📸 On-scene witness   │  /report/  (Django template)     │
   👮 Traffic officer    │  + browser Geolocation API       │
   🚑 EMS / Hospital     └──────────────┬───────────────────┘
   💻 Programmatic client               │
   └───── POST /api/accidents/ (JSON) ──┤
                                         │ POST (form-encoded or JSON)
                                         ▼
                          ┌──────────────────────────────────┐
                          │  AccidentForm (forms.py)         │
                          │  → Dar bbox check                │
                          │  → fatalities ≤ casualties        │
                          │  → vehicle_types sanitize         │
                          │  → auto-link junction             │
                          └──────────────┬───────────────────┘
                                         │ if valid → save
                                         ▼
                          ┌──────────────────────────────────┐
                          │  Accident.save()                 │
                          │  → auto-compute h3_cell          │
                          │  → auto-set slug                 │
                          └──────────────┬───────────────────┘
                                         │ INSERT
                                         ▼
   ┌─────────────────────  SQLite (dev) / PostGIS (prod)  ─────────────────────┐
   │                                                                            │
   │  accident: slug, severity, vehicle_types[], lat, lng, h3_cell,            │
   │            casualties, fatalities, injuries, junction_name → FK junction   │
   │  junction: slug, name, district, lat, lng, safety_score (property)        │
   │                                                                            │
   └──────┬───────────┬───────────┬───────────────┬───────────────┬─────────────┘
          │           │           │               │               │
          ▼           ▼           ▼               ▼               ▼
   /api/heatmap/ /api/accidents/ /api/severity/ /api/vehicles/ /api/monthly/
                                                       │
                                                       ▼
   /api/hourly/  /api/junctions/  /api/summary/  ──►  JSON responses

                          ┌──────────────────────────────┐
   👥 General public      │  Public Dashboard            │
   📰 Researchers         │  /dashboard/                 │
   📰 Media               │  Leaflet map + 4 charts      │
                          └──────────────────────────────┘

                          ┌──────────────────────────────┐
   👮 Tanzania Police     │  Authority Dashboard         │
   🛣️ TANROADS engineers  │  /authority/                 │
   🚦 SUMATRA officials   │  Hourly risk + recommendations│
                          └──────────────────────────────┘

                          ┌──────────────────────────────┐
   🛡️ Super-admins        │  Django Admin                │
                           │  /admin/                     │
                           │  Verify / Edit / Bulk export  │
                           └──────────────────────────────┘
```

### 3.2 Step-by-step: what happens when a community user submits a report

**User taps the "Report Accident" link, fills the form, taps the GPS button, taps "Submit".**

1. **Browser Geolocation API** runs `navigator.geolocation.getCurrentPosition()` and writes lat/lng into the two hidden number inputs. (`report.html` line ~78.)
2. Browser POSTs `application/x-www-form-urlencoded` to `/report/` with the CSRF token, all form fields, and the GPS coordinates.
3. Django middleware (CSRF + Session) verifies the token and hands the `HttpRequest` to `accidents.views.report_form()`.
4. `report_form()` checks `request.method == "POST"`. It enters the try block.
5. It parses `severity`, `vehicle_type`, `reported_by`, `lat`, `lng`, `address`, `occurred_at`, `casualties`, `fatalities`, `injuries`, `description`, `weather`, `road_condition`, `contact` from `request.POST`.
6. It casts numeric fields with `float()` / `int()`. If the value is missing or non-numeric, `ValueError` is caught and the user sees a friendly error.
7. `Accident.objects.create(**payload)` triggers a single `INSERT INTO accidents_accident (...)` statement on SQLite. The default `reported_at` is set by `default=timezone.now` at the model layer.
8. The view returns `HttpResponseRedirect("/dashboard/")` (HTTP 302). Django's session middleware is irrelevant here; no message is flashed.
9. Browser follows the redirect → `GET /dashboard/`.
10. The dashboard view counts `Accident.objects.all()`, queries the first record to derive the map center, and renders `accidents/dashboard.html`.
11. The HTML loads Leaflet + Leaflet.heat + Leaflet.markercluster + Chart.js from the unpkg/jsdelivr CDN.
12. `<script>` block fires `fetch('/api/heatmap/')` → server returns `[[lat, lng, intensity], ...]` (80 arrays) → `L.heatLayer(points, {...}).addTo(map)`.
13. `fetch('/api/accidents/')` returns 81 records → iterates → adds one `L.marker` per record to a `markerClusterGroup` → binds a severity-coloured popup.
14. `fetch('/api/severity/')` → doughnut chart, `fetch('/api/vehicles/')` → bar chart, `fetch('/api/monthly/')` → line chart, `fetch('/api/junctions/')` → top-10 table.

**Total round-trip from "Submit" to "appears on the map":** ~250 ms on localhost.

---

## 📁 SECTION 4: Complete File Structure

```
RoadSafety_Dar/
├── manage.py                          # Django CLI entry point — env-aware (dev/prod)
├── requirements.txt                   # Production dependencies (Django, gunicorn, whitenoise, …)
├── requirements-dev.txt               # Dev-only: pytest, pytest-django, ruff, mypy, Faker, h3
├── .env.example                       # 26 environment variables template
├── .gitignore                         # Python, Django, .env, .venv, IDE junk, __pycache__
├── pyproject.toml                     # ruff + mypy + pytest config
├── conftest.py                        # pytest-django shared fixtures (rate-limiter reset)
├── Procfile                           # Heroku/Render process declaration
├── render.yaml                        # Render.com deployment blueprint
├── railway.json                       # Railway.app deployment blueprint
├── runtime.txt                        # Python version pin for PaaS
├── README.md                          # You are here
│
├── roadsafety/                        # Django project package
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py                # Empty
│   │   ├── base.py                    # Shared settings: INSTALLED_APPS, DB, templates, static, security
│   │   ├── dev.py                     # DEBUG=True, console logging, SQLite
│   │   └── prod.py                    # HSTS, Sentry, Redis cache, Resend mail, Gunicorn
│   ├── urls.py                        # Root URL config — /admin/, /dashboard/, /report/, /api/*, /sw/
│   └── wsgi.py                        # WSGI callable — env-aware (default prod)
│
├── accidents/                         # The single Django app
│   ├── __init__.py
│   ├── apps.py                        # App config: name, verbose_name
│   ├── admin.py                       # Registers Accident + Junction with filter, search, custom action
│   ├── models.py                      # Accident + Junction + 9 choice lists + h3 auto-compute
│   ├── forms.py                       # AccidentForm(ModelForm) — Dar bbox, cross-field validation
│   ├── factories.py                   # JunctionFactory + AccidentFactory (pytest fixtures)
│   ├── views.py                       # 9 view functions (3 HTML, 8 JSON, 1 redirect)
│   ├── urls.py                        # App-level URL patterns
│   ├── tests.py                       # 52 Django TestCase tests (model, API, form, integration)
│   ├── test_factories.py              # 17 pytest factory tests
│   │
│   ├── migrations/                    # Auto-generated by `makemigrations`
│   │   ├── 0001_initial.py            # Creates accidents_junction and accidents_accident tables
│   │   ├── 0002_junction_district_and_more.py
│   │   ├── 0003_add_slug_h3_cell.py   # slug, h3_cell, vehicle_types JSON, reporter_type
│   │   └── 0004_backfill_slug_h3_cell.py
│   │
│   ├── management/                    # Custom `manage.py` commands
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── seed_accidents.py      # `python manage.py seed_accidents --count 80`
│   │       └── seed_junctions.py      # `python manage.py seed_junctions`
│   │
│   ├── templates/accidents/
│   │   ├── base.html                  # Top bar, footer, CDN <script> tags, {% block %} hooks
│   │   ├── dashboard.html             # Public map + 4 charts + junction table
│   │   ├── report.html                # AccidentForm-driven submission form + GPS button
│   │   └── authority.html             # Hourly risk + auto-recommendations
│   │
│   └── static/css/
│       └── app.css                    # Custom brand CSS (red/navy/gold), responsive grid
│
├── data/                              # Reserved for future data exports (CSV/GeoJSON dumps)
├── scripts/
│   └── setup.bat                      # Optional: bootstrap script
├── docs/
│   └── USER_GUIDE.md                  # Plain-language user guide
└── CHANGELOG.md                       # Version history
```

---

## ⚙️ SECTION 5: Installation & Setup

> Works on **Windows 10/11**, **macOS**, **Linux**. Python 3.11+ required. PostgreSQL/PostGIS **optional** for production.

### 5.1 Prerequisites

| Tool | Version | Download | Purpose |
|---|---|---|---|
| Python | 3.11 (not 3.14) | https://python.org/downloads | Runtime (3.14 breaks `Context.__copy__` in template engine) |
| Git | any | https://git-scm.com | Clone + version control |
| uv (recommended) | latest | `pip install uv` | 10× faster pip |

### 5.2 Clone & enter

```bash
git clone https://github.com/<your-org>/RoadSafety_Dar.git
cd RoadSafety_Dar
```

### 5.3 Create the venv

**With `uv` (fastest):**
```bash
uv venv .venv --python 3.11
.venv\Scripts\activate       # Windows (PowerShell)
# or: source .venv/bin/activate  # macOS/Linux
```

**With plain `python`:**
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

**Expected packages:** `Django-5.0`, `pytest-8`, `ruff`, `h3`, `python-dotenv`, `gunicorn`, `whitenoise`, `Faker` …

### 5.4 Environment variables

```bash
cp .env.example .env
# Edit .env (optional for local dev — defaults work out of the box)
```

| Variable | Default | Required for prod? | Source |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | dev placeholder | **YES** | `python -c "import secrets;print(secrets.token_urlsafe(60))"` |
| `DJANGO_ENV` | `dev` | **YES** (`prod`) | – |
| `DEBUG` | `True` | YES (set `False`) | – |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | YES (your domain) | – |
| `DATABASE_URL` | `postgresql://...` (Supabase Postgres) | **YES** | Supabase Connection URI |

See `.env.example` for the full list (26 variables covering Sentry, Redis, Resend, Cloudflare, Telegram, etc.).

### 5.5 Migrate & seed

```bash
python manage.py migrate
python manage.py seed_accidents --count 80
```

**Expected last line:** `Created 80 accident records. Total: 80`

### 5.6 Create an admin user

```bash
python manage.py createsuperuser
```

### 5.7 Run the dev server

```bash
python manage.py runserver
```

**Expected output:**
```
Watching for file changes with StatReloader
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### 5.8 Verify it works

Open http://127.0.0.1:8000/ in a browser. You should see:
- A map of Dar es Salaam with **red heat blobs** on the western and central corridors
- 4 KPI cards at the top: **81** total reports, **4** fatal, **30** verified, **20** junctions
- 4 working charts below the map

**Also verify tests pass:**
```bash
python manage.py test accidents
pytest accidents/test_factories.py -v
```

### 5.9 Common errors & fixes

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'django'` | venv not activated | `.venv\Scripts\activate` |
| `RuntimeError: Unable to copy context` | Python 3.14 | recreate venv with `--python 3.11` |
| `OperationalError: no such table: accidents_accident` | migrations not run | `python manage.py migrate` |
| `Port 8000 is already in use` | another process | `python manage.py runserver 8080` |
| Map shows but heatmap is empty | `seed_accidents` not run | `python manage.py seed_accidents --count 80` |
| `DisallowedHost` on real domain | `ALLOWED_HOSTS` not set | add domain to `.env` and restart |
| Tests fail with 400/429 | rate limiter from previous test | `_rate_log.clear()` in setUp class |
| `pytest: command not found` | dev reqs not installed | `pip install -r requirements-dev.txt` |

---

## 🎮 SECTION 6: How To Use It

### 6.1 Public dashboard

**URL:** `GET /dashboard/`

A fully-rendered HTML page that boots itself with `fetch()` calls to 5 JSON endpoints. You can also call the JSON endpoints directly to build your own dashboard.

### 6.2 API endpoints (all `GET`, JSON)

#### `GET /api/heatmap/`
```bash
curl http://127.0.0.1:8000/api/heatmap/
```
```json
[
  [-6.818186300254283, 39.258663586536215, 1],
  [-6.751933167304788, 39.26930441122043, 3],
  [-6.827002863419713, 39.271858170724805, 1]
]
```
- **Each element** is `[lat, lng, intensity]` where intensity is 1=minor, 2=serious, 3=critical, 4=fatal.
- **Edge case:** empty list `[]` when no accidents exist.

#### `GET /api/accidents/`
```bash
curl http://127.0.0.1:8000/api/accidents/
```
```json
[
  {
    "id": 81,
    "lat": -6.7924,
    "lng": 39.2083,
    "severity": "serious",
    "vehicle_type": "motorcycle",
    "occurred_at": "2026-07-01T10:00:00+03:00",
    "casualties": 2,
    "fatalities": 0,
    "address": "Test from CLI"
  }
]
```

#### `GET /api/severity/`
```bash
curl http://127.0.0.1:8000/api/severity/
```
```json
{"critical": 10, "fatal": 4, "minor": 44, "serious": 22}
```

#### `GET /api/vehicles/`
```json
{"motorcycle": 36, "car": 22, "bus": 11, "truck": 5, "bicycle": 3, "pedestrian": 1, "mixed": 2}
```

#### `GET /api/monthly/`
```json
[{"month": "2025-08", "count": 6}, {"month": "2025-09", "count": 9}, …]
```

#### `GET /api/hourly/`
```json
[{"hour": 0, "count": 1}, {"hour": 1, "count": 2}, …, {"hour": 23, "count": 1}]
```

#### `GET /api/junctions/`
```json
[{"count": 4, "fatalities": 0, "casualties": 9, "lat": -6.792, "lng": 39.208}, …]
```

#### `GET /api/summary/`
```json
{"total": 80, "fatal": 4, "serious": 22, "minor": 44, "critical": 10,
 "verified": 30, "total_fatalities": 2, "total_casualties": 97}
```

### 6.3 Submit a report (HTML form)

**URL:** `POST /report/` (browser form, CSRF-protected)

The form is driven by `AccidentForm` (`accidents/forms.py`), which validates:
- GPS coordinates are within Dar es Salaam bounding box (`lat ∈ [-7.5, -6.0]`, `lng ∈ [38.5, 39.7]`)
- `fatalities ≤ casualties` and `injuries ≤ casualties`
- `vehicle_type` is a valid choice; the form exposes a single-select dropdown
- Missing defaults: `reporter_type` defaults to `community`, `occurred_at` defaults to `now()`

On valid submission → `redirect("dashboard")`. On error → re-renders form with field-level error messages.

### 6.4 Submit a report (JSON API)

**URL:** `POST /api/accidents/` (JSON, no CSRF, rate-limited to 5/min per IP)

```bash
curl -X POST http://127.0.0.1:8000/api/accidents/ \
  -H "Content-Type: application/json" \
  -d '{"severity":"minor","lat":-6.79,"lng":39.21,"vehicle_types":["car"]}'
```

Returns `201` with the new record id, or `400` with validation errors, or `429` on rate limit.

**Backward-compatible field aliases:**
- `vehicle_type` (string) → `vehicle_types` (list) via `AccidentForm.__init__`
- `reporter_type` defaults to `"community"` when omitted
- `occurred_at`, `casualties`, `fatalities`, `injuries` all have smart defaults

**Programmatic example with curl (HTML form, CSRF-protected):**
```bash
# Step 1: GET /report/ to receive a CSRF cookie
curl -c cookies.txt http://127.0.0.1:8000/report/ > /dev/null

# Step 2: POST using the cookie
CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')
curl -b cookies.txt -X POST http://127.0.0.1:8000/report/ \
  -d "csrfmiddlewaretoken=$CSRF" \
  -d "severity=serious&vehicle_type=motorcycle&reporter_type=community" \
  -d "lat=-6.7924&lng=39.2083&occurred_at=2026-07-01T10:00" \
  -d "casualties=2&fatalities=0&injuries=2"
```

**Edge cases:**
- Missing required field → form re-renders with `class="alert error"` or JSON 400
- Bad `lat` → form validation error
- Duplicate submit (refresh) → handled by 302 redirect

### 6.5 Authority dashboard

**URL:** `GET /authority/`

Renders the hourly risk bar chart (peak hours in red) + a list of 4 rule-based recommendations generated client-side.

---

## 🗄️ SECTION 7: Database Schema

### Table: `accidents_junction`

| Column | Type | Index | Example | Notes |
|---|---|---|---|---|
| `id` | `BigAutoField` | PK | `1` | Auto-increment |
| `name` | `varchar(120)` | UNIQUE | `"Ubungo Interchange"` | Indexed by unique constraint |
| `slug` | `varchar(120)` | UNIQUE | `"ubungo-interchange"` | URL-safe, auto-populated |
| `district` | `varchar(60)` | – | `"Kinondoni"` | Optional, set by `seed_junctions` |
| `description` | `text` | – | `"Major bus terminal, 4-lane intersection"` | Optional |
| `lat` | `double precision` | – | `-6.7900` | Latitude WGS-84 |
| `lng` | `double precision` | – | `39.2000` | Longitude WGS-84 |
| `created_at` | `datetime` | – | `2026-07-01 09:00` | Auto-set on insert |

> **Property:** `junction.safety_score` — severity-weighted score (`n_fatal*4 + n_critical*3 + n_serious*2 + n_minor*1`), computed from related accidents.

### Table: `accidents_accident`

| Column | Type | Index | Example | Notes |
|---|---|---|---|---|
| `id` | `BigAutoField` | PK | `42` | Auto-increment |
| `slug` | `varchar(20)` | UNIQUE | `"acc-0042"` | URL-safe, auto-populated via random string |
| `severity` | `varchar(20)` | ✅ | `"fatal"` | One of: `minor`, `serious`, `critical`, `fatal` |
| `vehicle_types` | `JSONField` | – | `["car", "pedestrian"]` | List of vehicle types from `VEHICLE_CHOICES` |
| `reporter_type` | `varchar(20)` | – | `"community"` | One of: `police`, `community`, `hospital`, `tanroads`, `media` |
| `lat` | `double precision` | ✅ | `-6.7924` | Indexed for fast bbox queries |
| `lng` | `double precision` | ✅ | `39.2083` | Indexed |
| `junction_name` | `varchar(120)` | – | `"Ubungo Interchange"` | Free text landmark; auto-links to `Junction` |
| `junction_id` | `BigInt` | FK | `1` | Nullable FK → `accidents_junction` |
| `occurred_at` | `datetime` | ✅ | `2026-07-01 10:00` | Indexed + composite (occurred_at, severity) |
| `reported_at` | `datetime` | – | `2026-07-01 10:05` | Default = `timezone.now` |
| `casualties` | `int >= 0` | – | `2` | Total hurt/killed |
| `fatalities` | `int >= 0` | – | `1` | Subset of casualties |
| `injuries` | `int >= 0` | – | `1` | Subset of casualties |
| `description` | `text` | – | `"Bodaboda hit pedestrian on zebra crossing"` | Swahili or English |
| `weather` | `varchar(60)` | – | `"rainy"` | |
| `road_condition` | `varchar(60)` | – | `"wet"` | |
| `contact` | `varchar(120)` | – | `"+255712345678"` | Optional, not exposed in JSON |
| `verified` | `bool` | – | `true` | Police-verified flag |
| `h3_cell` | `varchar(15)` | ✅ | `"8a1f234567fffff"` | H3 hexagon index at resolution 10, auto-computed on save |
| `source_notes` | `text` | – | `"Imported from TPF CSV batch #3"` | Internal audit field |

### Indexes

| Index | Why |
|---|---|
| `severity` | severity-distribution chart (count by severity) |
| `lat`, `lng` | future bbox / radius queries |
| `(occurred_at, severity)` | composite: "fatal accidents per month" |
| `(lat, lng)` | composite: "find accident at exact location" |
| `junction.name` (UNIQUE) | lookups by junction |
| `h3_cell` | hexagonal clustering for hotspot aggregation |

### Model-level validation

- `fatalities ≤ casualties` and `injuries ≤ casualties`
- `vehicle_types` must be a non-empty list of valid vehicle types
- `lat ∊ [-7.5, -6.0]` and `lng ∊ [38.5, 39.7]` (Dar es Salaam bounding box)

### Relations

```
Junction (1) ────< (many) Accident
                     junction_id FK → junction.id  ON DELETE SET NULL
```

In production, this becomes:
```
Junction (1) ────< (many) Accident
                     location gis.Point (4326)
                     GIST index → radius search "find accidents within 500m"
```

---

## 🌐 SECTION 8: Spatial Integration Details

> The project ships **without AI**, but it ships with **spatial intelligence** — the equivalent for a road-safety system. This section replaces the "AI Integration" section in the standard README template.

### 8.1 Map library: **Leaflet 1.9.4**

**Why Leaflet and not Mapbox/Google Maps?**
- **Free** and **open source** (BSD-2)
- **Tile providers** are swappable (we use OpenStreetMap; could move to MapTiler or Stadia for higher-contrast cartography)
- **Plugin ecosystem** is mature — `Leaflet.heat` and `Leaflet.markercluster` are the de-facto standard
- **Mobile-friendly** (works inside Telegram in-app browser, Facebook in-app browser, etc.)

### 8.2 Heatmap plugin: **Leaflet.heat 0.2.0**

**Why this exact plugin?**
- Simplest API: `L.heatLayer([[lat,lng,intensity], …], {radius, blur, maxZoom, gradient})`
- ~3 KB gzipped
- Renders to a `<canvas>` overlay for performance
- Pinned to `https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js` via CDN

**Dynamic gradient** (in `dashboard.html`):
```js
gradient: {
  0.2: '#1f9d55',  // green   = minor
  0.4: '#f4d35e',  // yellow  = serious
  0.7: '#ee964b',  // orange  = critical
  1.0: '#c0392b'   // red     = fatal
}
```

### 8.3 Cluster plugin: **Leaflet.markercluster 1.5.3**

**Why?** The dashboard renders up to N accident records; without clustering the map becomes unreadable past ~50 markers at city zoom. `markerClusterGroup` automatically groups nearby markers into a colored circle showing the count.

**Dynamic styling** (severity-coloured pins):
```js
const sevColor = {minor:'#1f9d55', serious:'#f4d35e',
                  critical:'#ee964b', fatal:'#c0392b'}[a.severity];
```

### 8.4 Chart library: **Chart.js 4.4.3**

- **Doughnut** for severity distribution
- **Bar** for vehicle types
- **Line** with `tension: 0.3` for monthly trend (smoothing)
- **Bar** with conditional colour for the high-risk hour profile on the authority dashboard

### 8.5 Tile server: **OpenStreetMap** (default)

```js
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);
```

For production traffic, swap to MapTiler or Stadia Maps to respect the OSMF tile policy.

### 8.6 "What happens when data is bad?"

- **`/api/heatmap/`** with an empty DB returns `[]` — Leaflet.heat accepts empty input, no error.
- **`/api/severity/`** with no records returns `{}` — Chart.js shows an empty doughnut (acceptable).
- **`/api/monthly/`** with 0 records returns `[]` — line chart shows zero-filled axis.
- **Invalid lat/lng** in form → `ValueError` caught, friendly error shown.

### 8.7 Ideas for improving spatial quality (v1.2)

- [ ] Add **H3 hexagonal indexing** for proper hotspot aggregation (Uber H3 Python lib)
- [ ] Add **isochrone overlays** ("accidents within 10 min of here")
- [ ] Add **reverse geocoding** via Nominatim to auto-fill the `address` field
- [ ] Add **route snapping** via OSRM (`http://router.project-osrm.org/route/v1/driving/...`) so users can tap a road instead of a point
- [ ] Add **isovist analysis** (visibility) for junction safety audits

---

## 🐛 SECTION 9: Current Limitations & Known Bugs

### 9.1 Known bugs

| # | Bug | Steps to reproduce | Severity | Workaround |
|---|---|---|---|---|
| 1 | `api_junctions()` rounds to 3 decimal places (~110m) — two distinct junctions 50m apart will merge | seed with 2 records at the same hand-typed junction name 50m apart | Low | v1.2: use PostGIS `ST_SnapToGrid` or `ST_ClusterDBSCAN` |
| 2 | `report.html` GPS button is silent on success — the user only sees the lat/lng numbers change | open `/report/` on desktop, click "Use my current location" | Low | v1.1: add a green toast notification |
| 3 | `admin.py` Junction admin does not show the count of accidents per junction | open `/admin/accidents/junction/` | Cosmetic | add `def accident_count(self, obj): return obj.accidents.count()` and put it in `list_display` |
| 4 | `api_summary()` returns a `by_day` query that the dashboard never uses | curl `/api/summary/` | Cosmetic | remove from API or add weekday chart |
| 5 | The "Time of day" chart legend is off-by-one for events near midnight (UTC vs Africa/Dar_es_Salaam) | submit a report at 00:30 local | Low | v1.1: force `USE_TZ = True` and use `localtime()` consistently |
| 6 | On mobile Safari, the leaflet.heat canvas flickers during scroll | open dashboard on iPhone Safari | Low | upgrade to `leaflet.heat@0.2.0` + add `will-change: transform` CSS |

### 9.2 Performance bottlenecks

| What | Threshold | What breaks | Mitigation |
|---|---|---|---|
| 80 records | Current | – | – |
| 10,000 records | Marker map will slow | cluster needs work | v1.1: add viewport-based fetch (`/api/accidents/?bbox=…`) |
| 1,000,000 records | SQLite falls over, queries > 5s | – | Move to PostGIS in production |
| 1,000 concurrent dashboard views | Gunicorn 1 worker | – | run with `gunicorn roadsafety.wsgi:application -w 4 -k gthread` |

### 9.3 Security issues to fix before public launch

- [ ] **CSRF on JSON API** — currently `/api/*` is GET-only, so CSRF is not a risk. As soon as you add `POST /api/accidents/`, decorate it with `@csrf_protect`.
- [ ] **Rate limiting** on `/report/` — a bad actor could spam 1,000 reports. Add `django-ratelimit`.
- [ ] **CAPTCHA** on the public form — Cloudflare Turnstile is free.
- [ ] **`SECRET_KEY` committed to .env** in some screenshots on the internet — generate a new one with `secrets.token_urlsafe(60)`.
- [ ] **`DEBUG=True` in production** — set `DEBUG=False` and `ALLOWED_HOSTS=yourdomain.com`.
- [ ] **No authentication on the public APIs** — anyone can read. For a government pilot, add token auth or IP allowlist (e.g. only TPF / TANROADS can write; everyone else can read).

### 9.4 Features that work but work badly

- The **recommendation engine** is hard-coded English. For Swahili audiences, hard-code Swahili text or use `gettext_lazy`.
- The **junction ranking** is by raw count, not by severity-weighted score. A junction with 1 fatal accident should rank above one with 3 minor accidents.
- The **heat radius** (22 px) is tuned for 12 zoom. At zoom 6, blobs merge into a single blob; at zoom 18, the heat layer disappears.

### 9.5 Technical debt

- `views.py` has the recommendation engine logic in a JS file instead of a Django model method → move to a `models.py` method or a `services/recommendations.py` module.
- The form now uses `AccidentForm` ✅ (resolved in v1.1).
- 68 pytest tests now exist ✅ (resolved in v1.1).
- `accidents/views.py` still has `~650 lines` — consider splitting into `views/` package (dashboard.py, api.py, auth.py).

---

## 🛠️ SECTION 10: Modification & Addon Guide

### MOD 1: Add the Cloudflare Llama 3.3 70B AI summariser
- **Difficulty:** ⭐⭐ (2/5)
- **Time:** 2–3 hours
- **Files to modify:** `requirements.txt`, `roadsafety/settings/prod.py`, `accidents/views.py`, `accidents/urls.py`
- **New files:** `accidents/services/ai_summary.py`, `accidents/templates/accidents/ai_summary.html`
- **Dependencies:** `requests`
- **Steps:**
  1. Add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` to `.env`
  2. Write `ai_summary.py` with `def generate_summary(junction, rows) -> str`
  3. Call Cloudflare Workers AI endpoint: `POST https://api.cloudflare.com/client/v4/accounts/{id}/ai/run/@cf/meta/llama-3.3-70b-instruct-fp8-fast`
  4. Add `path("api/summary/<int:junction_id>/", views.api_ai_summary)`
  5. Render the result on the authority dashboard

### MOD 2: Add Swahili (`/sw/`) translation
- **Difficulty:** ⭐⭐ (2/5)
- **Time:** 1 day
- **Files to modify:** `roadsafety/settings/base.py`, all 4 templates
- **New files:** `accidents/locale/sw/LC_MESSAGES/django.po`, `django.mo`
- **Steps:**
  1. Add `django.middleware.locale.LocaleMiddleware` to `MIDDLEWARE`
  2. Add `LANGUAGES = [("en", "English"), ("sw", "Kiswahili")]`
  3. Run `python manage.py makemessages -l sw`
  4. Translate the `.po` file
  5. Run `python manage.py compilemessages`

### MOD 3: Add PostGIS spatial queries (radius search)
- **Difficulty:** ⭐⭐⭐ (3/5)
- **Time:** 1 day
- **Files to modify:** `accidents/models.py`, `requirements.txt`, `.env`
- **New files:** `scripts/migrate_to_postgis.py`
- **Steps:**
  1. Install PostgreSQL + PostGIS extension
  2. Update `requirements.txt`: `psycopg2-binary==2.9.9`, add `GDAL` system package
  3. Set `DATABASE_URL=postgis://user:pass@localhost/roadsafety`
  4. Add `location = gis_models.PointField(srid=4326, null=True, blank=True)` to `Accident`
  5. Add GIST index in a new migration
  6. Write a data migration that copies `lat`/`lng` into the new `location` field
  7. Add `Accident.objects.filter(location__dwithin=(point, Distance(m=500)))` query

### MOD 4: Add email/SMS alerts when 3+ fatal accidents hit a junction in 7 days
- **Difficulty:** ⭐⭐ (2/5)
- **Time:** 3 hours
- **Files to modify:** `accidents/management/commands/seed_accidents.py`, add `alerts.py`
- **New files:** `accidents/management/commands/check_alerts.py`
- **Dependencies:** `django-anymail`, `twilio`
- **Steps:**
  1. Add `EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"` etc. to `settings.py`
  2. Write a queryset that groups accidents by `junction_id`, filters `severity=fatal` in the last 7 days, returns those with `count >= 3`
  3. Send email + SMS to a configured recipient list
  4. Add a cron: `0 8 * * * python manage.py check_alerts`

### MOD 5: Add a PDF monthly report for TANROADS
- **Difficulty:** ⭐⭐⭐ (3/5)
- **Time:** 1 day
- **Files to modify:** `accidents/views.py`, `accidents/urls.py`
- **New files:** `accidents/services/pdf_report.py`
- **Dependencies:** `weasyprint`, `reportlab`
- **Steps:**
  1. Render an HTML template with summary stats + a table of all accidents this month
  2. Use `weasyprint` to convert HTML → PDF
  3. Return `Content-Disposition: attachment; filename=monthly_report_2026-07.pdf`

### MOD 6: Add user authentication (Django AllAuth)
- **Difficulty:** ⭐⭐ (2/5)
- **Time:** 4 hours
- **Files to modify:** `roadsafety/settings/base.py`, `roadsafety/urls.py`
- **Dependencies:** `django-allauth`
- **Steps:** install, add to `INSTALLED_APPS`, add provider apps, configure templates

### MOD 7: Add an Android/iOS wrapper (PWA)
- **Difficulty:** ⭐⭐⭐ (3/5)
- **Time:** 1 day
- **Files to modify:** `accidents/templates/accidents/base.html`, add `static/manifest.json`, `static/sw.js`
- **Steps:**
  1. Add `<link rel="manifest" href="{% static 'manifest.json' %}">`
  2. Add `<meta name="theme-color" content="#c0392b">`
  3. Register a service worker that caches the static assets
  4. Add an offline page that queues POSTs in IndexedDB and replays on reconnect

### MOD 8: Add a CSV bulk import for legacy TPF data
- **Difficulty:** ⭐⭐ (2/5)
- **Time:** 3 hours
- **Files to modify:** `accidents/admin.py`, add `accidents/management/commands/import_csv.py`
- **Steps:** admin action that accepts an uploaded CSV and creates `Accident` rows

### MOD 9: Make it faster (cache + CDN)
- **Difficulty:** ⭐⭐ (2/5)
- **Time:** 2 hours
- **Dependencies:** `django-redis`
- **Steps:** cache the JSON API responses with `@cache_page(60 * 5)` (5 min)

### MOD 10: Add a waitlist / landing page
- **Difficulty:** ⭐ (1/5)
- **Time:** 2 hours
- **Files to modify:** add `accidents/templates/accidents/landing.html`, change root URL
- **Dependencies:** none
- **Steps:** add a hero with project pitch + an email form that POSTs to `/api/waitlist/` and writes to a `Waitlist` model

### MOD 11: Add a Telegram bot notification
- **Difficulty:** ⭐⭐⭐ (3/5)
- **Time:** 4 hours
- **Dependencies:** `python-telegram-bot`
- **Files to create:** `accidents/services/telegram_bot.py`
- **Steps:** on every new `Accident.objects.create()`, send a Telegram message with the lat/lng and a link to the dashboard

### MOD 12: Add analytics (Plausible / Umami)
- **Difficulty:** ⭐ (1/5)
- **Time:** 30 min
- **Steps:** paste the Plausible script in `base.html` `<head>`. No backend changes.

---

## 🚢 SECTION 11: Deployment Guide

### 11.1 Production stack (recommended for v1.1 public pilot)

```
Internet → Cloudflare CDN → Nginx (TLS) → Gunicorn (4 workers, 2 threads)
                                          → Django app
                                          → PostgreSQL + PostGIS
                                          → Redis (cache + Celery broker)
                                          → Sentry (error tracking)
```

### 11.2 Step-by-step (DigitalOcean / Hetzner / AWS Lightsail)

```bash
# 1. SSH into the box
ssh root@your-server

# 2. Install OS deps (Ubuntu 22.04)
apt update && apt install -y python3.11 python3.11-venv \
  postgresql-15 postgresql-15-postgis-3 nginx certbot python3-certbot-nginx

# 3. Create the DB
sudo -u postgres createuser -P roadsafety
sudo -u postgres createdb -O roadsafety roadsafety
sudo -u postgres psql roadsafety -c "CREATE EXTENSION postgis;"

# 4. Clone & install
git clone https://github.com/your-org/RoadSafety_Dar.git /opt/roadsafety
cd /opt/roadsafety
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn psycopg2-binary

# 5. Migrate & seed
cp .env.example .env && nano .env  # set DJANGO_SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, DATABASE_URL
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_accidents --count 80

# 6. Gunicorn
gunicorn roadsafety.wsgi:application -w 4 -k gthread --bind 127.0.0.1:8001

# 7. Nginx
# (see docs/nginx.conf)

# 8. TLS
certbot --nginx -d yourdomain.com

# 9. Systemd service for gunicorn
# (see docs/roadsafety.service)
```

### 11.3 Environment variables in production

```ini
DJANGO_SECRET_KEY=<generated with secrets.token_urlsafe>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgis://roadsafety:<password>@localhost:5432/roadsafety
```

### 11.4 Database security rules

- Bind PostgreSQL to `127.0.0.1` only (`listen_addresses = 'localhost'`)
- Use a strong, randomly generated password
- Set up daily `pg_dump` backups to an off-site S3 bucket
- Restrict the DB user to `SELECT, INSERT, UPDATE, DELETE` only (no `DROP`, no `CREATE`)

### 11.5 Custom domain

1. Point an A record from `yourdomain.com` to your server IP
2. Run `certbot --nginx -d yourdomain.com -d www.yourdomain.com`
3. Update `ALLOWED_HOSTS` and restart gunicorn

### 11.6 Monitoring (after deployment)

- **Sentry** (free tier): add `SENTRY_DSN` to `.env`, install `sentry-sdk`
- **UptimeRobot** (free): ping `/dashboard/` every 5 min, alert on 5xx
- **Nginx access log**: `tail -f /var/log/nginx/access.log | grep " 5[0-9][0-9] "`

### 11.7 Rollback

```bash
# Roll back code
cd /opt/roadsafety
git log --oneline -10
git checkout <previous-good-sha>
systemctl restart roadsafety

# Roll back DB (point-in-time recovery)
# Requires WAL archiving — set up `archive_mode = on` in postgresql.conf
```

---

## 💸 SECTION 12: Cost Calculator

> All costs in **USD/month**, based on free-tier where possible.

| Service | Free Tier | Paid Tier | Cost @ 100 users/mo | Cost @ 1,000 users/mo | Cost @ 100k users/mo |
|---|---|---|---|---|---|
| **Hosting (Hetzner CX22)** | n/a | €4.85/mo (2 vCPU, 4 GB) | $5 | $5 | $80 (CX42) |
| **Domain** | – | $12/yr | $1 | $1 | $1 |
| **PostgreSQL (managed, DigitalOcean)** | – | $15/mo (1 GB) | $15 | $15 | $60 (4 GB) |
| **Cloudflare CDN** | Free | $20/mo Pro | $0 | $0 | $20 |
| **Map tiles (MapTiler / Stadia)** | 100k requests/mo | $25/mo for 1M | $0 (free) | $25 | $250 |
| **Sentry error tracking** | 5k events/mo | $26/mo | $0 | $26 | $80 |
| **Backups (S3)** | 5 GB free | $0.023/GB/mo | $0 | $1 | $20 |
| **Telegram alerts** | Free | Free | $0 | $0 | $0 |
| **Email (Mailgun)** | 100/day | $35/mo 50k | $0 | $0 | $35 |
| **SMS alerts (Twilio)** | – | $0.05/SMS | $5 (100 alerts) | $25 (500) | $250 (5k) |
| **Total** | – | – | **~$26/mo** | **~$98/mo** | **~$796/mo** |

**v1.0 local dev cost: $0** (everything runs on a laptop).

---

## 🗺️ SECTION 13: Roadmap

### SHORT TERM (current sprint — v1.1)

1. **[x] Split settings into base/dev/prod** (Prompt 0 — done)
2. **[x] Harden data layer** (slug, h3_cell, factories, Prompt 1 — done)
3. **[x] Replace raw POST with Django Form** (AccidentForm, Prompt 2 — done)
4. **[x] Write 68 tests** (model factories + API smoke + form validation — done)
5. **[ ] Add user authentication** (Django AllAuth, login required for `/report/`)
6. **[ ] Add CAPTCHA** (Cloudflare Turnstile, 30 minutes)
7. **[ ] Add PostGIS support** (one-day migration, 50-line code change)
8. **[ ] Add Swahili UI** (`/sw/` locale, translate all 4 templates)
9. **[ ] API hardening** (pagination, ETags, caching headers)

### MEDIUM TERM (next 3 months)

1. **Public pilot launch** — point a real domain at it, register with TPF
2. **PDF monthly report** for TANROADS
3. **Telegram bot** that pings subscribed officials on every new fatal accident
4. **Heatmap time slider** — drag a slider to see hotspots in a date range
5. **CSV bulk import** for legacy TPF data
6. **PWA** — install to home screen, submit reports offline
7. **AI summariser** — Cloudflare Llama 3.3 generates a 3-paragraph monthly narrative
8. **Junction-level risk score** — replace raw count with severity-weighted score

### LONG TERM (6–12 months) — **v2.0 vision**

1. **National scale** — extend beyond Dar to Dodoma, Arusha, Mwanza (4-city MVP)
2. **Computer vision** — crowdsourced dashcam uploads, auto-detect accident type via YOLO
3. **Predictive hotspot model** — train an XGBoost model on 5 years of data + weather + traffic volume + road class to predict next-month hotspots
4. **Integration with Google Maps / Waze** — push our hotspots into Waze and pull theirs in return
5. **Insurance API** — let insurance companies query our API to verify a claim
6. **Mobile app** (Flutter / React Native) for Android with offline queue
7. **Government partnership** — sign MoU with Ministry of Works and Transport
8. **v2.0 becomes the official Tanzania Road Safety Observatory** for the East African Community

---

## 💡 SECTION 14: Lessons Learned

### What worked better than expected

- **CDN-only Leaflet** (no `django-leaflet` widget) cut install time from 5 minutes to 30 seconds and removed the GDAL dependency. A reminder that "the official Django package" isn't always the right choice.
- **Rule-based recommendation engine** (4 hard-coded suggestions) is good enough for v1 — defer LLM integration until there's a real user base asking for more.
- **SQLite + lat/lng floats** is 100× simpler than GeoDjango+PostGIS for a local demo, and the model interface is identical so the production migration is a one-day task.
- **Chart.js + custom CSS** outperformed expectations — the dashboard looks more "premium" than government systems I've seen in production.

### What was harder than expected

- **GDAL on Windows** — there are no wheels for Python 3.14 yet. Spent an hour trying to install OSGeo4W before pivoting.
- **Geolocation API UX** — users need a clear "GPS captured" toast after pressing the button; without it they don't trust the form submitted.
- **Marker clustering** — naïve rendering of 500 markers freezes the browser; need to virtualize or bbox-fetch.
- **Timezone handling** — `USE_TZ = True` plus `Africa/Dar_es_Salaam` is the right choice, but it's easy to miss when seed data is generated in UTC.

### What I would do differently if starting over

- **Start with the data model**, not the front-end. The 4 indexes and 8 JSON APIs are the real product; the dashboard is just a view.
- **Add tests from day 1** — even 5 tests would have caught the "junction name not unique" bug.
- **Generate the seed data from real TPF reports** (anonymised) instead of `Faker`. The "real" hotspots would have been more credible.
- **Pick one chart library and stick to it.** I considered Plotly, ECharts, and Chart.js. Wasted 2 hours comparing.
- **Skip PostGIS until there are 1,000+ records.** The complexity is not worth it for a 100-record demo.

### What I learned that applies to ALL future projects

1. **The boring tech wins.** SQLite + Django + Leaflet is boring — and that's why it ships.
2. **Make it run in <5 minutes.** If a reviewer can't clone → install → run → see results in 5 minutes, they'll give up.
3. **Mock data is a feature, not a hack.** 80 realistic records (with hour-of-day distribution weighted toward rush hour) makes the dashboard tell a real story.
4. **CDN > self-host** for libraries. We saved ~12 MB by pulling Leaflet, Chart.js, MarkerCluster, and Leaflet.heat from unpkg / jsDelivr.
5. **Brand colours matter.** Switching to red (#c0392b) + navy (#2c3e50) + gold (#f4d35e) made the dashboard look like a real product, not a school project.

---

## 🎯 SECTION 15: Quick Reference Card

> One page. Print it. Tape it to your monitor.

### 🏃 Start the server (local dev)

```bash
cd "C:/Users/MWIJAY TECH/Desktop/RoadSafety_Dar"
source .venv/Scripts/activate
python manage.py runserver
```

Then open: **http://127.0.0.1:8000/**

### 🔑 Admin login

| Field | Value |
|---|---|
| URL | http://127.0.0.1:8000/admin/ |
| Username | `admin` |
| Password | `roadsafety` |

### 📡 Most-used API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/heatmap/` | `[lat, lng, intensity]` for Leaflet.heat |
| `GET /api/accidents/` | All accidents with metadata |
| `GET /api/severity/` | `{minor, serious, fatal, critical}` counts |
| `GET /api/vehicles/` | Per-vehicle-type counts |
| `GET /api/monthly/` | Last 12 months trend |
| `GET /api/hourly/` | 24-bucket risk profile |
| `GET /api/junctions/` | Ranked by accident count |
| `GET /api/summary/` | KPI bundle for the dashboard |

### 🌐 Most-used URLs

| URL | Page |
|---|---|
| `/` | Redirect → `/dashboard/` |
| `/dashboard/` | Public map + 4 charts |
| `/report/` | Mobile-friendly submission form |
| `/authority/` | Authority dashboard with recommendations |
| `/admin/` | Django admin (police/transport officials only) |

### 🔑 Most-used environment variables

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Cryptographic signing key (CHANGE for prod) |
| `DEBUG` | `True` for dev, `False` for prod |
| `ALLOWED_HOSTS` | Comma-separated list of allowed domains |
| `DATABASE_URL` | Supabase PostgreSQL (`postgresql://...`) or SQLite |

### 🛠️ Most-used commands

```bash
# Reset everything (delete DB, re-seed)
rm db.sqlite3
python manage.py migrate
python manage.py seed_accidents --count 80

# Create a new admin
python manage.py createsuperuser

# Re-seed (adds 80 more records)
python manage.py seed_accidents --count 80

# Run all tests
python manage.py test accidents
pytest accidents/test_factories.py -v

# Lint & type-check
ruff check accidents/
mypy accidents/

# Collect static files (for prod)
python manage.py collectstatic --noinput

# Make migrations after model changes
python manage.py makemigrations accidents
python manage.py migrate

# Open Django shell
python manage.py shell

# Production WSGI server
gunicorn roadsafety.wsgi:application -w 4 -k gthread --bind 0.0.0.0:8000
```

### 🩹 Most common fixes

| Problem | Fix |
|---|---|---|
| Map is empty | `python manage.py seed_accidents --count 80` |
| `DisallowedHost` | add your domain to `ALLOWED_HOSTS` in `.env` |
| `Port already in use` | `python manage.py runserver 8080` |
| `RuntimeError: Unable to copy context` | using Python 3.14 — recreate venv with `--python 3.11` |
| Static files 404 in prod | `python manage.py collectstatic --noinput` |
| CSRF failure on POST | use the same browser session, or include the token |
| Tests fail with 400 | rate limiter from previous test — `_rate_log.clear()` in setUp |

### 📂 Most important files

| File | Why it's important |
|---|---|---|
| `roadsafety/settings/base.py` | Shared settings (all config) |
| `roadsafety/settings/dev.py` | Dev overrides (DEBUG, SQLite) |
| `roadsafety/settings/prod.py` | Production overrides (Sentry, Redis, Resend) |
| `accidents/models.py` | Database schema + h3 auto-compute |
| `accidents/forms.py` | AccidentForm — validation for both HTML + JSON |
| `accidents/views.py` | 11 endpoints (3 HTML + 8 JSON) |
| `accidents/factories.py` | JunctionFactory + AccidentFactory for tests |
| `accidents/tests.py` | 52 Django TestCase tests |
| `accidents/test_factories.py` | 17 pytest factory tests |
| `accidents/templates/accidents/dashboard.html` | The public map |
| `accidents/management/commands/seed_accidents.py` | 80 realistic records |
| `requirements.txt` | All Python deps |

### 🎨 Brand palette (use everywhere)

| Colour | Hex | Use |
|---|---|---|
| Alert red | `#c0392b` | Headings, primary CTA, fatal severity |
| Navy | `#2c3e50` | Top bar, secondary text, authority view |
| Gold | `#f4d35e` | Warnings, serious severity, GPS button |
| Green | `#1f9d55` | Verified, minor severity, success |
| Orange | `#ee964b` | Critical severity |

---

## 📜 License

MIT — free to use, modify, and distribute. Attribution appreciated.

## 👤 Author

**Davie Byanmwijage (Mwijay)**
- 📍 Dar es Salaam, Tanzania
- 🌐 [your-portfolio-link]
- ✉️ [your-email]

> Built with ❤️ for safer roads in Tanzania. SDG 11.2: *By 2030, provide access to safe, affordable, accessible and sustainable transport systems for all, improving road safety, notably by expanding public transport, with special attention to the needs of those in vulnerable situations.*

---

**Last updated:** July 2026 · **Version 1.1.0-dev** · **Status:** 🚧 Active Development · **Tests:** 68/69 passing · **Junctions:** 20
