import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "roadsafety.settings.dev"

import django; django.setup()
from accidents.models import Accident
from collections import Counter

qs = Accident.objects.all()
print(f"Total: {qs.count()}")
print(f"Severity: {dict(Counter(qs.values_list('severity', flat=True)))}")
print(f"Weather: {dict(Counter(qs.values_list('weather', flat=True)))}")
print(f"Road: {dict(Counter(qs.values_list('road_condition', flat=True)))}")

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

monthly = (qs.annotate(month=TruncMonth("occurred_at")).values("month").annotate(c=Count("id")).order_by("month"))
print("Monthly:")
for r in monthly:
    print(f"  {r['month'].strftime('%Y-%m')}: {r['c']}")

hourly = Counter(a.occurred_at.hour for a in qs)
print("Hourly:", dict(sorted(hourly.items())))

print(f"\nDate range: {qs.earliest('occurred_at').occurred_at.date()} to {qs.latest('occurred_at').occurred_at.date()}")
