"""
PostGIS migration script — v1.2 (production deployment only).

Switches the Accident model from plain lat/lng floats to a proper
PostGIS Point field for spatial queries (e.g., "find all accidents
within 500m of this junction").

Usage (on Railway/Render with Postgres + PostGIS):
    python manage.py migrate_to_postgis

This script:
1. Adds the location Point field
2. Backfills it from existing lat/lng
3. Creates a spatial index
4. Verifies no data loss
5. Recommends updating models.py to remove the old lat/lng fields

SAFE: It does NOT drop the old columns. The model continues to work
with both representations. You can keep both for backwards compat.
"""
import logging
from django.core.management.base import BaseCommand
from django.db import connection, transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate Accident to PostGIS — adds location Point field (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show SQL without running")

    def handle(self, *args, **options):
        # Detect DB type
        vendor = connection.vendor
        if vendor != "postgresql":
            self.stdout.write(self.style.ERROR(
                f"PostGIS migration requires PostgreSQL. Current vendor: {vendor}. "
                f"For local dev with SQLite, skip this — the model has lat/lng FloatFields."
            ))
            return

        self.stdout.write("🔍 Checking PostGIS extension...")
        with connection.cursor() as c:
            c.execute("SELECT extname FROM pg_extension WHERE extname = 'postgis';")
            has_postgis = c.fetchone()
            if not has_postgis:
                self.stdout.write(self.style.WARNING(
                    "PostGIS extension not installed. Adding it now..."
                ))
                if not options["dry_run"]:
                    c.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                self.stdout.write(self.style.SUCCESS("✅ PostGIS extension added"))
            else:
                self.stdout.write("✅ PostGIS already installed")

        # Add the location field if not exists
        self.stdout.write("\n📍 Adding location column (Point, 4326)...")
        sqls = [
            "ALTER TABLE accidents_accident ADD COLUMN IF NOT EXISTS location geometry(Point, 4326);",
            "CREATE INDEX IF NOT EXISTS accidents_accident_location_idx ON accidents_accident USING GIST (location);",
        ]
        for sql in sqls:
            if options["dry_run"]:
                self.stdout.write(f"  [DRY-RUN] {sql}")
                continue
            with connection.cursor() as c:
                c.execute(sql)
            self.stdout.write(self.style.SUCCESS(f"  ✅ {sql[:60]}..."))

        # Backfill
        self.stdout.write("\n🔄 Backfilling location from lat/lng...")
        with connection.cursor() as c:
            c.execute("SELECT COUNT(*) FROM accidents_accident WHERE location IS NULL;")
            null_count = c.fetchone()[0]
        self.stdout.write(f"  Records to backfill: {null_count}")

        if null_count == 0:
            self.stdout.write(self.style.SUCCESS("  ✅ All records have location"))
        else:
            if options["dry_run"]:
                self.stdout.write("  [DRY-RUN] would backfill")
            else:
                with connection.cursor() as c:
                    c.execute("""
                        UPDATE accidents_accident
                        SET location = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
                        WHERE location IS NULL;
                    """)
                self.stdout.write(self.style.SUCCESS(f"  ✅ Backfilled {null_count} records"))

        # Verify
        self.stdout.write("\n🔍 Verifying migration...")
        with connection.cursor() as c:
            c.execute("SELECT COUNT(*) FROM accidents_accident WHERE location IS NOT NULL;")
            ok = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM accidents_accident;")
            total = c.fetchone()[0]

        self.stdout.write(f"  Records with location: {ok}/{total}")
        if ok == total:
            self.stdout.write(self.style.SUCCESS("✅ Migration verified — no data loss"))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠ {total - ok} records missing location. Check logs."
            ))

        self.stdout.write(self.style.SUCCESS(
            "\n🎉 PostGIS migration complete! Next steps:\n"
            "1. Update accidents/models.py to add `location = models.PointField(...)`\n"
            "2. Run: python manage.py makemigrations accidents\n"
            "3. Update queries to use .annotate(distance=Distance('location', target_point))\n"
            "4. See docs/POSTGIS.md for spatial query examples"
        ))
