"""
Bulk CSV import for Tanzania Police Force legacy data — v1.2.

Imports historical accident data from CSV files (SUMATRA, TPF, hospitals).
Auto-deduplicates, validates coordinates, and verifies records.

Usage:
    python manage.py import_accidents --file data/tpf_legacy.csv
    python manage.py import_accidents --file data/tpf_legacy.csv --source tpf --auto-verify
    python manage.py import_accidents --directory data/bulk/ --auto-verify

Expected CSV columns (in any order, header required):
    id,occurred_at,severity,vehicle_types,junction_name,lat,lng,
    casualties,fatalities,injuries,weather,road_condition,
    reporter_type,description
"""
import csv
import json
import logging
import os
from datetime import datetime
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from django.utils import timezone

from accidents.models import Accident, Junction

logger = logging.getLogger(__name__)

# Validation ranges for Dar es Salaam
DAR_BBOX = {
    "min_lat": -7.0, "max_lat": -6.5,
    "min_lng": 39.0, "max_lng": 39.6,
}

ALLOWED_SEVERITY = {"fatal", "critical", "serious", "minor"}


class Command(BaseCommand):
    help = "Bulk import accident records from CSV files."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Single CSV file to import")
        parser.add_argument("--directory", type=str, help="Directory of CSV files")
        parser.add_argument("--source", type=str, default="tpf",
                          help="Reporter type (tpf, hospital, community, tanroads)")
        parser.add_argument("--auto-verify", action="store_true",
                          help="Auto-mark imported records as verified")
        parser.add_argument("--dry-run", action="store_true",
                          help="Validate without saving")
        parser.add_argument("--batch-size", type=int, default=100,
                          help="Insert in batches (default 100)")

    def handle(self, *args, **options):
        if not options["file"] and not options["directory"]:
            raise CommandError("Provide --file or --directory")

        files = []
        if options["file"]:
            if not os.path.exists(options["file"]):
                raise CommandError(f"File not found: {options['file']}")
            files.append(options["file"])
        if options["directory"]:
            if not os.path.exists(options["directory"]):
                raise CommandError(f"Directory not found: {options['directory']}")
            for fname in sorted(os.listdir(options["directory"])):
                if fname.lower().endswith(".csv"):
                    files.append(os.path.join(options["directory"], fname))

        if not files:
            self.stdout.write(self.style.WARNING("No CSV files found."))
            return

        total_created = 0
        total_skipped = 0
        total_errors = 0
        for fpath in files:
            self.stdout.write(f"\n📂 Processing: {fpath}")
            created, skipped, errors = self._import_file(fpath, options)
            total_created += created
            total_skipped += skipped
            total_errors += errors
            self.stdout.write(
                f"  ✅ Created: {created}  ⏭ Skipped: {skipped}  ❌ Errors: {errors}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Total: {total_created} created, {total_skipped} skipped, {total_errors} errors"
        ))

    def _import_file(self, fpath, options):
        created = 0
        skipped = 0
        errors = 0
        batch = []

        with open(fpath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"occurred_at", "severity", "lat", "lng"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                self.stdout.write(self.style.ERROR(
                    f"  Missing required columns: {missing}"
                ))
                return 0, 0, 1

            for row_num, row in enumerate(reader, start=2):  # row 1 = header
                try:
                    obj = self._build_accident(row, options)
                    if obj is None:
                        skipped += 1
                        continue
                    batch.append(obj)
                    if len(batch) >= options["batch_size"]:
                        created += self._save_batch(batch, options)
                        batch = []
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"  Row {row_num}: {e}"
                    ))
                    errors += 1

            if batch:
                created += self._save_batch(batch, options)

        return created, skipped, errors

    def _build_accident(self, row, options):
        """Build an Accident object from a CSV row. Returns None if invalid."""
        # Parse occurred_at
        occurred_str = row.get("occurred_at", "").strip()
        if not occurred_str:
            raise ValueError("occurred_at is empty")
        try:
            # Try ISO 8601 first
            if "T" in occurred_str:
                occurred_at = datetime.fromisoformat(occurred_str.replace("Z", "+00:00"))
            else:
                # Common format: "2026-01-15 14:30:00"
                occurred_at = datetime.strptime(occurred_str, "%Y-%m-%d %H:%M:%S")
            if timezone.is_naive(occurred_at):
                occurred_at = timezone.make_aware(occurred_at)
        except ValueError as e:
            raise ValueError(f"Invalid occurred_at: {occurred_str}") from e

        # Parse lat/lng
        try:
            lat = float(row.get("lat", "").strip())
            lng = float(row.get("lng", "").strip())
        except (ValueError, AttributeError):
            raise ValueError("Invalid lat/lng")

        # Validate coordinates are within Dar es Salaam
        if not (DAR_BBOX["min_lat"] <= lat <= DAR_BBOX["max_lat"]):
            raise ValueError(f"lat {lat} outside Dar bbox")
        if not (DAR_BBOX["min_lng"] <= lng <= DAR_BBOX["max_lng"]):
            raise ValueError(f"lng {lng} outside Dar bbox")

        # Validate severity
        severity = row.get("severity", "minor").strip().lower()
        if severity not in ALLOWED_SEVERITY:
            raise ValueError(f"Invalid severity: {severity}")

        # Parse vehicle types
        vt_str = row.get("vehicle_types", "").strip()
        vehicle_types = [v.strip() for v in vt_str.split(",") if v.strip()]

        # Parse numeric fields with safe defaults
        def intfield(key, default=0):
            try:
                return int(row.get(key, str(default)) or default)
            except (ValueError, TypeError):
                return default

        # Dedupe by (occurred_at, junction_name, severity)
        junction_name = row.get("junction_name", "").strip()
        existing = Accident.objects.filter(
            occurred_at=occurred_at,
            junction_name=junction_name,
            severity=severity,
        ).first()
        if existing:
            return None  # skip duplicate

        return Accident(
            occurred_at=occurred_at,
            severity=severity,
            vehicle_types=vehicle_types,
            junction_name=junction_name,
            lat=lat,
            lng=lng,
            casualties=intfield("casualties"),
            fatalities=intfield("fatalities"),
            injuries=intfield("injuries"),
            weather=row.get("weather", "clear").strip().lower() or "clear",
            road_condition=row.get("road_condition", "good").strip().lower() or "good",
            reporter_type=options["source"],
            verified=options["auto_verify"],
            description=row.get("description", "").strip(),
        )

    @transaction.atomic
    def _save_batch(self, batch, options):
        if options["dry_run"]:
            return 0
        try:
            Accident.objects.bulk_create(batch, batch_size=len(batch))
            return len(batch)
        except IntegrityError as e:
            self.stdout.write(self.style.WARNING(f"  Batch failed: {e}"))
            # Fall back to one-by-one
            count = 0
            for obj in batch:
                try:
                    obj.save()
                    count += 1
                except IntegrityError:
                    pass
            return count
