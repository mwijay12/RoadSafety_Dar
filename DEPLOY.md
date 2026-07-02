# 🚀 Deploy RoadSafety Dar

You can deploy this Django application using **Railway.app (recommended)** or **Vercel + Supabase**.

---

## Option 1: Vercel + Supabase (Free & Fully Serverless)

If you deploy to Vercel, Django's default SQLite database won't work properly because Vercel uses a read-only serverless filesystem. To fix this, we use **Supabase** to host a free, persistent PostgreSQL database.

### Step-by-Step Vercel + Supabase Setup:

1. **Create a Database on Supabase**:
   * Go to [supabase.com](https://supabase.com) and create a free project.
   * Note down your project database password.
   * Go to **Project Settings** -> **Database** -> **Connection string** (select **URI**).
   * Copy the URL (e.g. `postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REG].pooler.supabase.com:5432/postgres`).

2. **Configure Vercel Environment Variables**:
   Go to your project settings in the Vercel Dashboard and add:
   * `DATABASE_URL` = (Paste your Supabase URI connection string)
   * `DJANGO_SETTINGS_MODULE` = `roadsafety.settings.prod` (or set `DJANGO_ENV` = `prod`)
   * `DJANGO_SECRET_KEY` = (generate using `python -c "import secrets;print(secrets.token_urlsafe(60))"`)

3. **Run Migrations & Seed data locally on Supabase**:
   Since Vercel is serverless and doesn't run backend commands automatically, run these from your local terminal:
   * Temporary: Put your Supabase URI as `DATABASE_URL` in your local `.env`.
   * Run migrations: `python manage.py migrate`
   * Seed mock data: `python manage.py seed_accidents --count 50`
   * Create admin: `python manage.py createsuperuser`
   * Restore: Change `DATABASE_URL` in `.env` back to `sqlite:///db.sqlite3`.

4. **Deploy**: Push/deploy to Vercel. The application will connect directly to Supabase!

---

## Option 2: Deploy to Railway.app (FREE)

### 1. Sign up at https://railway.app
- Click "Login" → "GitHub"
- Authorize Railway to access your repos

### 2. Create new project from GitHub
- Click "New Project" → "Deploy from GitHub repo"
- Select `RoadSafety_Dar` (push to GitHub first if not already)

### 3. Add PostgreSQL database (free tier)
- Click "+ New" → "Database" → "PostgreSQL"
- Railway auto-creates a free Postgres instance
- Copy the `DATABASE_URL` connection string

### 4. Configure environment variables
In Railway dashboard, go to your service → "Variables" → add:

| Variable | Value | Required |
|----------|-------|----------|
| `DJANGO_SECRET_KEY` | (generate: `python -c "import secrets;print(secrets.token_urlsafe(60))"`) | ✅ |
| `DEBUG` | `False` | ✅ |
| `ALLOWED_HOSTS` | `.railway.app` | ✅ |
| `DATABASE_URL` | (paste from Postgres) | ✅ |
| `OPENROUTER_API_KEY` | `sk-or-v1-xxx` | optional |
| `OPENROUTER_MODEL` | `minimax/minimax-m3` | optional |

### 5. Update settings.py for Postgres (one change)
Already done! `dj-database-url` reads `DATABASE_URL` and connects to PostGIS or Postgres automatically.

### 6. Deploy!
- Railway auto-detects Python and runs `gunicorn roadsafety.wsgi`
- Wait 2-3 minutes
- Get a URL like `https://roadsafety-dar-production.up.railway.app`

### 7. Run migrations
- In Railway dashboard, click your service → "Settings" → "Deploy"
- Add a custom start command:
  ```
  python manage.py migrate && python manage.py collectstatic --noinput && python manage.py seed_accidents --count 100 && gunicorn roadsafety.wsgi
  ```
- Or use Railway's "Shell" tab to run commands manually

### 8. Create superuser
- Railway → your service → "Shell" tab
- Run: `python manage.py createsuperuser`
- Follow prompts

### 9. (Optional) Custom domain
- Railway → Settings → "Domains"
- Add your domain (e.g., `roadsafety.co.tz`)
- Update DNS per Railway's instructions
- Add your domain to `ALLOWED_HOSTS`

---

## Cost Breakdown

| Resource | Free Tier | After Free |
|----------|-----------|------------|
| Web service | $5 credit/month | ~$5/mo |
| Postgres | 500MB free | $5/mo (1GB) |
| **Total** | **$0 for ~1 month** | **~$10/mo at scale** |

**For your scale (Tanzania pilot): $0/mo for the first month is realistic.**

---

## Alternative: Render.com (also free)

If Railway doesn't work for you, Render has a free tier too:

1. Push to GitHub
2. Sign up at https://render.com (GitHub login)
3. New → "Web Service" → connect repo
4. Render auto-detects `render.yaml` we already created
5. Click "Apply" — done in 5 minutes
6. Free tier spins down after 15 min idle (cold start on first request)

For 24/7 uptime on Render, you need $7/mo Starter plan.

---

## After Deployment Checklist

- [ ] Test `/dashboard/` returns 200
- [ ] Test `/api/heatmap/` returns JSON
- [ ] Test `/api/export.csv` downloads file
- [ ] Test `/api/recommendations/` shows risk levels
- [ ] Test Swahili: `Accept-Language: sw` returns translated UI
- [ ] Login to `/admin/`, verify works
- [ ] Submit a test report, verify it appears
- [ ] Set up monitoring (Sentry free tier)
- [ ] (Optional) Buy domain, configure DNS
- [ ] (Optional) Set up email (SendGrid free tier)
- [ ] Submit to ProductHunt / Hacker News
- [ ] Email SUMATRA + TANROADS + TPF with the URL

---

## Custom Domain (Optional but Recommended)

A `.co.tz` domain costs ~TSh 50,000/year (~$20) from a TZ registrar.

Once you have one:
1. Railway → Settings → Domains → Add `roadsafety.co.tz`
2. Update your registrar's DNS:
   - CNAME `www` → your Railway URL
   - A `@` → Railway's IP (they provide)
3. Update `ALLOWED_HOSTS` in env vars to include `.co.tz`
4. HTTPS auto-provisioned by Railway

**You now have a professional Tanzanian URL: `https://roadsafety.co.tz`** 🇹🇿

---

## Files Added in v1.1

| File | Purpose |
|------|---------|
| `Procfile` | Railway start command |
| `runtime.txt` | Python version pin |
| `railway.json` | Railway-specific config |
| `render.yaml` | Render-specific config (alternative) |
| `roadsafety/wsgi.py` | WSGI entry point (gunicorn) |

**You're 5 minutes away from public deployment.** 🚀
