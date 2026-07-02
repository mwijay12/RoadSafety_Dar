# RoadSafety_Dar — Multi-stage Docker build
# ============================================================================
# Builder:  install deps + static files
# Runtime:  minimal python:3.11-slim with gunicorn
# ============================================================================

# ----------------------------------------
# Stage 1 — Builder
# ----------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System build deps (GDAL for PostGIS, gcc for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Copy source code and collect static files
COPY . .
RUN DJANGO_ENV=prod \
    DJANGO_SECRET_KEY=placeholder-build-only \
    python manage.py collectstatic --noinput --settings=roadsafety.settings.prod

# ----------------------------------------
# Stage 2 — Runtime
# ----------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=prod \
    PORT=8000

WORKDIR /app

# Runtime system deps (GDAL for optional PostGIS support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application (including collected static files)
COPY --from=builder /app /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import http.client; c=http.client.HTTPConnection('localhost',8000); c.request('GET','/healthz'); r=c.getresponse(); exit(0) if r.status==200 else exit(1)"

CMD ["gunicorn", "roadsafety.wsgi", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "--log-file", "-"]
