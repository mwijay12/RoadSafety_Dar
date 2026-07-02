#!/usr/bin/env bash
# build.sh
# Render runs this script during the build phase (before server starts).
# Runs on every deploy — keep it fast.

set -o errexit   # Exit immediately if any command fails
set -o nounset   # Treat unset variables as errors
set -o pipefail  # Catch errors in pipes

echo "=========================================="
echo "  Road Safety Dar — Build Script"
echo "=========================================="

# ── 1. Install Python dependencies ──────────────────────────────────────────
echo ""
echo "→ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# ── 2. Collect static files ──────────────────────────────────────────────────
echo ""
echo "→ Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "✅ Static files collected to /staticfiles/"

# ── 3. Run database migrations ───────────────────────────────────────────────
echo ""
echo "→ Running database migrations..."
python manage.py migrate --noinput
echo "✅ Migrations applied"

# ── 4. Verify health check endpoint responds ─────────────────────────────────
echo ""
echo "→ Build complete."
echo "   Render will start the web server with gunicorn."
echo "   Health check: GET /health/"
echo "=========================================="
