"""
Seed accident records + junctions for Dar es Salaam.

Drops existing records and reseeds. Use --count to control size.

Run:  python manage.py seed_accidents --count 80
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from accidents.models import Accident, Junction

# Real Dar es Salaam accident hotspots (approximate, from OpenStreetMap + public reports)
HOTSPOTS = [
    ("Ubungo Interchange",          -6.7900, 39.2000),
    ("Kariakoo Market Junction",    -6.8200, 39.2600),
    ("Morocco Junction (Mwenge)",   -6.7600, 39.2300),
    ("Selander Bridge",             -6.8000, 39.2700),
    ("Bagamoyo Rd / Sam Nujoma",    -6.7500, 39.2700),
    ("Kimara Junction",             -6.7900, 39.1700),
    ("Mbezi Luis",                  -6.7400, 39.2200),
    ("Mikocheni B",                 -6.7700, 39.2400),
    ("Tegeta Kibaoni",              -6.7100, 39.2200),
    ("Kigamboni Ferry",             -6.8200, 39.3000),
    ("Buguruni",                    -6.8400, 39.2600),
    ("Ilala Boma",                  -6.8200, 39.2800),
    ("Tabata Dampo",                -6.8400, 39.2400),
    ("Sinza Kijitonyama",           -6.7800, 39.2300),
    ("Ali Hassan Mwinyi Rd",        -6.7600, 39.2400),
    ("Tandika",                     -6.8600, 39.2600),
    ("Mbagala Rangi Tatu",          -6.8900, 39.2900),
    ("Temeke Soko la Mpya",         -6.8700, 39.2700),
    ("Chang'ombe",                  -6.8300, 39.2700),
    ("Gerezani",                    -6.8200, 39.2700),
    ("Kibaha Border",               -6.7800, 39.0900),
    ("Mkuranga Junction",            -7.1100, 39.2000),
    ("Bagamoyo Rd / Mwenge",        -6.7600, 39.2200),
    ("Kawe Beach",                  -6.7400, 39.2700),
    ("Oyster Bay",                  -6.7600, 39.2900),
]

SEVERITY_W = [("minor", 5), ("serious", 3), ("critical", 1), ("fatal", 1)]
VEHICLE_W = [("motorcycle", 4), ("car", 3), ("bus", 2), ("truck", 1),
             ("bicycle", 1), ("pedestrian", 2), ("mixed", 1), ("auto_rickshaw", 1)]
REPORTER_W = [("community", 5), ("police", 3), ("hospital", 2),
              ("tanroads", 1), ("media", 1)]


def weighted_choice(pairs):
    total = sum(w for _, w in pairs)
    r = random.uniform(0, total)
    acc = 0
    for v, w in pairs:
        acc += w
        if r <= acc:
            return v
    return pairs[-1][0]


def random_vehicles():
    """PRD: vehicle_types is a list of one-or-more vehicles."""
    n = random.choices([1, 2, 3], weights=[8, 3, 1])[0]
    primary = weighted_choice(VEHICLE_W)
    out = [primary]
    pool = [v for v, _ in VEHICLE_W if v != primary and v != "pedestrian"]
    while len(out) < n and pool:
        choice = random.choice(pool)
        pool.remove(choice)
        out.append(choice)
    return out


from accidents.models import VEHICLE_CHOICES as VC


class Command(BaseCommand):
    help = "Seed accident records and known junctions for Dar es Salaam."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=80)
        parser.add_argument("--wipe", action="store_true", help="Delete existing accidents first")

    def handle(self, *args, **opts):
        fake = Faker()
        # 1. Junctions
        for name, lat, lng in HOTSPOTS:
            Junction.objects.get_or_create(name=name, defaults={"lat": lat, "lng": lng})
        self.stdout.write(self.style.SUCCESS(
            f"Created/verified {len(HOTSPOTS)} junctions."))

        if opts["wipe"]:
            n = Accident.objects.count()
            Accident.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Wiped {n} existing accident records."))

        # 2. Records
        now = timezone.now()
        for _ in range(opts["count"]):
            name, lat, lng = random.choice(HOTSPOTS)
            lat += random.uniform(-0.003, 0.003)
            lng += random.uniform(-0.003, 0.003)
            severity = weighted_choice(SEVERITY_W)
            vehicles = random_vehicles()
            days_ago = random.randint(0, 365)
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,2,3,5,6,4,3,3,3,3,3,4,5,6,7,6,5,4,2,1]
            )[0]
            minute = random.randint(0, 59)
            occurred = (now - timedelta(days=days_ago)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            casualties = {"minor": 0, "serious": random.randint(1, 3),
                          "critical": random.randint(3, 6),
                          "fatal": random.randint(0, 3)}[severity]
            fatalities = random.randint(0, 1) if severity == "fatal" else 0
            injuries = max(0, casualties - fatalities)

            Accident.objects.create(
                severity=severity,
                vehicle_types=vehicles,
                reporter_type=weighted_choice(REPORTER_W),
                lat=lat, lng=lng,
                junction_name=name,
                occurred_at=occurred,
                casualties=casualties,
                fatalities=fatalities,
                injuries=injuries,
                description=fake.sentence(nb_words=10),
                weather=random.choice(["clear", "rainy", "clear", "clear", "drizzle"]),
                road_condition=random.choice(["wet", "good", "potholed", "good"]),
                contact=fake.phone_number(),
                source_notes="Seeded via management command",
                verified=random.random() < 0.4,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Created {opts['count']} accident records. Total: {Accident.objects.count()}"
        ))
