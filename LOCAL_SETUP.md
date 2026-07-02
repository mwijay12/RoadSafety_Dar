# 🚦 Road Safety Dar es Salaam — Local Setup Guide
## Run this project on your laptop in under 10 minutes

---

### What you need before starting

| Requirement | Version | Download |
|---|---|---|
| Python | **3.11** (not 3.12, not 3.14) | https://python.org/downloads/release/python-3119/ |
| Git | Any | https://git-scm.com |

> **Windows users:** During Python install, tick ✅ "Add Python to PATH"

---

### Option A — Clone from GitHub (requires internet)

```bash
git clone https://github.com/YOUR-USERNAME/RoadSafety_Dar.git
cd RoadSafety_Dar
```

### Option B — From the ZIP file (offline)

1. Extract `RoadSafety_Dar.zip` to any folder
2. Open a terminal / command prompt inside that folder

---

### Setup (5 minutes)

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment file
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux
```

### 5. Edit the `.env` file

Open `.env` in any text editor and set:

```ini
DJANGO_ENV=dev
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

For full Supabase + Google Auth, ask Davie for the production `.env` values.

---

### Run the project

```bash
# Create database tables
python manage.py migrate

# Load sample data (80 accidents, 20 Dar junctions)
python manage.py seed_junctions
python manage.py seed_accidents --count 80

# Create an admin account
python manage.py createsuperuser
# Username: admin
# Password: (choose anything)

# Start the server
python manage.py runserver
```

Open your browser at: **http://127.0.0.1:8000**

---

### What you can see

| URL | What it shows |
|---|---|
| http://127.0.0.1:8000/ | Public heatmap dashboard |
| http://127.0.0.1:8000/report/ | Accident submission form |
| http://127.0.0.1:8000/admin/ | Admin panel (use your superuser) |
| http://127.0.0.1:8000/health/ | System health check |
| http://127.0.0.1:8000/api/heatmap/ | Raw heatmap data (JSON) |

---

### Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: django` | Run `.venv\Scripts\activate` first |
| `Python 3.14 RuntimeError` | Use Python 3.11 exactly |
| `no such table: accidents_accident` | Run `python manage.py migrate` |
| Map shows but no heatmap blobs | Run `python manage.py seed_accidents --count 80` |
| Port 8000 already in use | Run `python manage.py runserver 8080` |

---

*Built by Davie Byanmwijage (Mwijay) — Dar es Salaam, Tanzania*
*University Project 24 — Spatial Data Management Module*
*UN SDG 11.2 — Safe and Sustainable Transport for All*
