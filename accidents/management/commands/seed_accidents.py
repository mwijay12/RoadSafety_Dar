"""
Seed accident records + junctions for Dar es Salaam (v1.3 — realistic).

Drops existing records and reseeds. Use --count to control size.

Run:  python manage.py seed_accidents --count 500
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from accidents.models import Accident, Junction

# Real Dar es Salaam accident hotspots (approximate, from OpenStreetMap + public reports)
HOTSPOTS = [
    ("Ubungo Interchange",          -6.7900, 39.2000, "Ubungo"),
    ("Kariakoo Market Junction",    -6.8200, 39.2600, "Ilala"),
    ("Morocco Junction (Mwenge)",   -6.7600, 39.2300, "Kinondoni"),
    ("Selander Bridge",             -6.8000, 39.2700, "Ilala"),
    ("Bagamoyo Rd / Sam Nujoma",    -6.7500, 39.2700, "Kinondoni"),
    ("Kimara Junction",             -6.7900, 39.1700, "Ubungo"),
    ("Mbezi Luis",                  -6.7400, 39.2200, "Kinondoni"),
    ("Mikocheni B",                 -6.7700, 39.2400, "Kinondoni"),
    ("Tegeta Kibaoni",              -6.7100, 39.2200, "Kinondoni"),
    ("Kigamboni Ferry",             -6.8200, 39.3000, "Kigamboni"),
    ("Buguruni",                    -6.8400, 39.2600, "Ilala"),
    ("Ilala Boma",                  -6.8200, 39.2800, "Ilala"),
    ("Tabata Dampo",                -6.8400, 39.2400, "Ilala"),
    ("Sinza Kijitonyama",           -6.7800, 39.2300, "Kinondoni"),
    ("Ali Hassan Mwinyi Rd",        -6.7600, 39.2400, "Kinondoni"),
    ("Tandika",                     -6.8600, 39.2600, "Temeke"),
    ("Mbagala Rangi Tatu",          -6.8900, 39.2900, "Temeke"),
    ("Temeke Soko la Mpya",         -6.8700, 39.2700, "Temeke"),
    ("Chang'ombe",                  -6.8300, 39.2700, "Ilala"),
    ("Gerezani",                    -6.8200, 39.2700, "Ilala"),
    ("Kibaha Border",               -6.7800, 39.0900, "Ubungo"),
    ("Mkuranga Junction",           -7.1100, 39.2000, "Temeke"),
    ("Bagamoyo Rd / Mwenge",        -6.7600, 39.2200, "Kinondoni"),
    ("Kawe Beach",                  -6.7400, 39.2700, "Kinondoni"),
    ("Oyster Bay",                  -6.7600, 39.2900, "Kinondoni"),
    ("Posta Haroub",                -6.8100, 39.2800, "Ilala"),
    ("Mnazi Mmoja",                 -6.8100, 39.2700, "Ilala"),
    ("Kivukoni Front",              -6.8100, 39.2900, "Ilala"),
    ("Manzese",                     -6.8100, 39.2200, "Ubungo"),
    ("Tandale",                     -6.8000, 39.2200, "Ubungo"),
    ("Vingunguti",                  -6.8400, 39.2400, "Ilala"),
    ("Keko",                        -6.8300, 39.2600, "Temeke"),
    ("Yombo Vituka",                -6.8700, 39.2400, "Temeke"),
    ("Kipawa",                      -6.8600, 39.2300, "Temeke"),
    ("Kwa Mnyenyani",               -6.8500, 39.2100, "Temeke"),
    ("Kongo",                       -6.8400, 39.2000, "Ubungo"),
    ("Urafiki",                     -6.8200, 39.2500, "Ilala"),
    ("Kwa Wazee",                   -6.8000, 39.2600, "Ilala"),
    ("Kisiwani",                    -6.7900, 39.2800, "Kinondoni"),
    ("Msasani",                     -6.7700, 39.2700, "Kinondoni"),
]

# Realistic weights — bodaboda dominant in Dar
VEHICLE_W = [
    ("motorcycle", 40), ("car", 25), ("bus", 12), ("truck", 6),
    ("pedestrian", 7), ("auto_rickshaw", 5), ("bicycle", 3), ("mixed", 2),
]

REPORTER_W = [("community", 5), ("police", 3), ("hospital", 2), ("tanroads", 1), ("media", 1)]


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
    n = random.choices([1, 2, 3], weights=[8, 3, 1])[0]
    primary = weighted_choice(VEHICLE_W)
    out = [primary]
    pool = [v for v, _ in VEHICLE_W if v != primary and v != "pedestrian"]
    while len(out) < n and pool:
        choice = random.choice(pool)
        pool.remove(choice)
        out.append(choice)
    return out


def pick_severity(hour, weather, road):
    """Realistic severity distribution based on conditions."""
    base = random.random()
    # Peak hours = more fatal due to speed + congestion
    if hour in (6, 7, 8, 17, 18, 19):
        if base < 0.12:
            return "fatal"
        elif base < 0.25:
            return "critical"
        elif base < 0.55:
            return "serious"
        else:
            return "minor"
    # Night = more fatal (speeding, drunk driving)
    elif hour in (22, 23, 0, 1, 2, 3):
        if base < 0.20:
            return "fatal"
        elif base < 0.35:
            return "critical"
        elif base < 0.60:
            return "serious"
        else:
            return "minor"
    # Rainy + potholed = more serious
    elif weather == "rainy" and road in ("potholed", "wet"):
        if base < 0.15:
            return "fatal"
        elif base < 0.30:
            return "critical"
        elif base < 0.55:
            return "serious"
        else:
            return "minor"
    # Default
    else:
        if base < 0.05:
            return "fatal"
        elif base < 0.15:
            return "critical"
        elif base < 0.40:
            return "serious"
        else:
            return "minor"


def pick_weather(month):
    """Dar es Salaam has two rainy seasons: March–May (long) and Oct–Dec (short)."""
    if month in (3, 4, 5):
        return random.choices(["rainy", "clear", "drizzle", "foggy"], weights=[5, 3, 2, 1])[0]
    elif month in (10, 11, 12):
        return random.choices(["rainy", "clear", "drizzle", "foggy"], weights=[4, 4, 2, 1])[0]
    else:
        return random.choices(["clear", "sunny", "cloudy", "drizzle"], weights=[5, 4, 3, 1])[0]


def pick_road(hour, weather):
    if weather == "rainy":
        return random.choices(["wet", "good", "potholed"], weights=[5, 2, 3])[0]
    if hour in (22, 23, 0, 1, 2, 3):
        return random.choices(["good", "potholed", "wet"], weights=[4, 4, 1])[0]
    return random.choices(["good", "dry", "potholed", "wet"], weights=[5, 3, 3, 1])[0]


class Command(BaseCommand):
    help = "Seed accident records and known junctions for Dar es Salaam."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=200)
        parser.add_argument("--wipe", action="store_true", help="Delete existing accidents first")

    def handle(self, *args, **opts):
        fake = Faker()

        self.stdout.write("Seeding junctions...")
        for name, lat, lng, district in HOTSPOTS:
            Junction.objects.get_or_create(
                name=name,
                defaults={"lat": lat, "lng": lng, "district": district, "is_demo": True},
            )
        self.stdout.write(self.style.SUCCESS(f"  OK  {len(HOTSPOTS)} junctions"))

        if opts["wipe"]:
            n = Accident.objects.count()
            Accident.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"  Wiped {n} existing accidents"))

        now = timezone.now()
        created = 0
        for _ in range(opts["count"]):
            name, lat, lng, district = random.choice(HOTSPOTS)
            lat += random.uniform(-0.005, 0.005)
            lng += random.uniform(-0.005, 0.005)

            month = random.randint(1, 12)
            weather = pick_weather(month)
            road = pick_road(0, weather)

            # Hour distribution: morning peak (6-9), evening peak (16-19), night lull
            hour = random.choices(
                range(24),
                weights=[2,1,1,1,1,2,5,7,6,4,3,3,3,3,3,4,5,7,8,6,4,3,2,2],
            )[0]

            severity = pick_severity(hour, weather, road)
            vehicles = random_vehicles()

            day = random.randint(1, 28)
            minute = random.randint(0, 59)
            occurred = now.replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
            # Spread across 12 months
            occurred -= timedelta(days=random.randint(0, 365))

            c_min = {"minor": 0, "serious": 1, "critical": 3, "fatal": 1}
            c_max = {"minor": 2, "serious": 3, "critical": 7, "fatal": 4}
            casualties = random.randint(c_min[severity], c_max[severity])

            if severity == "fatal":
                fatalities = random.randint(1, min(3, casualties))
            elif severity == "critical":
                fatalities = random.randint(0, min(2, casualties))
            else:
                fatalities = 0
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
                description=fake.sentence(nb_words=12),
                weather=weather,
                road_condition=road,
                contact=fake.phone_number(),
                source_notes="Seeded via management command",
                verified=random.random() < 0.35,
                is_demo=True,
            )
            created += 1

        total = Accident.objects.count()
        self.stdout.write(self.style.SUCCESS(f"  OK  Created {created} records -- total: {total}"))

        # Show distribution
        from collections import Counter
        qs = Accident.objects.all()
        sev = Counter(qs.values_list("severity", flat=True))
        self.stdout.write(f"\nDistribution:")
        self.stdout.write(f"  Severity: {dict(sev)}")
        from django.db.models.functions import TruncMonth
        from django.db.models import Count
        months = (qs.annotate(m=TruncMonth("occurred_at")).values("m").annotate(c=Count("id")).order_by("m"))
        first = months.first()
        last = months.last()
        if first and last:
            self.stdout.write(f"  Monthly span: {first['m'].strftime('%Y-%m')} - {last['m'].strftime('%Y-%m')}")
