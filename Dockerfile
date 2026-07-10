# RoadSafety_Dar — Dockerfile for Railway.app
# Uses $PORT env variable (Railway sets this automatically)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system deps (GDAL for PostGIS, gcc for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --settings=roadsafety.settings.prod 2>/dev/null || true

EXPOSE $PORT

# Bind to $PORT — Railway sets this automatically
CMD gunicorn roadsafety.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --log-level info --access-logfile - --error-logfile -