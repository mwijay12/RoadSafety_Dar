#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

echo "=========================================="
echo "  Road Safety Dar — Build Script"
echo "  Python version:"
python --version
echo "=========================================="

# Fail fast if wrong Python version
python -c "import sys; assert sys.version_info[:2] == (3, 11), f'Wrong Python: {sys.version}'; print('✅ Python 3.11 confirmed')"

echo ""
echo "→ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

echo ""
echo "→ Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "✅ Static files collected"

echo ""
echo "→ Running database migrations..."
python manage.py migrate --noinput
echo "✅ Migrations applied"

echo ""
echo "→ Build complete. Starting gunicorn next."
echo "=========================================="
