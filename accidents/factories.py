"""
Factory-boy factories for Accident and Junction models.

Used by pytest tests (``test_factories.py``) and handy for seeding
development data via ``./manage.py shell``:

    >>> from accidents.factories import JunctionFactory, AccidentFactory
    >>> j = JunctionFactory()
    >>> a = AccidentFactory(junction=j, junction_name=j.name)
"""

import factory
from django.utils import timezone

from .models import REPORTER_CHOICES, SEVERITY_CHOICES, VEHICLE_CHOICES, Accident, Junction

SEVERITY_VALUES = [c[0] for c in SEVERITY_CHOICES]
VEHICLE_VALUES = [c[0] for c in VEHICLE_CHOICES]
REPORTER_VALUES = [c[0] for c in REPORTER_CHOICES]

# Dar bounding box
LAT_MIN, LAT_MAX = -7.5, -6.0
LNG_MIN, LNG_MAX = 38.5, 39.7


class JunctionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Junction

    name = factory.Sequence(lambda n: f"Junction-{n + 1}")
    lat = factory.Faker("pyfloat", min_value=LAT_MIN, max_value=LAT_MAX)
    lng = factory.Faker("pyfloat", min_value=LNG_MIN, max_value=LNG_MAX)
    district = factory.Iterator(["Ilala", "Kinondoni", "Temeke", "Ubungo", "Kigamboni"])
    description = factory.Faker("sentence", nb_words=8)


class AccidentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Accident
        skip_postgeneration_save = True

    lat = factory.Faker("pyfloat", min_value=LAT_MIN, max_value=LAT_MAX)
    lng = factory.Faker("pyfloat", min_value=LNG_MIN, max_value=LNG_MAX)
    occurred_at = factory.LazyFunction(timezone.now)
    severity = factory.Iterator(SEVERITY_VALUES)
    vehicle_types = factory.List(["car"])
    reporter_type = factory.Iterator(REPORTER_VALUES)
    casualties = factory.Faker("random_int", min=0, max=4)
    fatalities = 0
    injuries = 0
    description = factory.Faker("sentence", nb_words=6)
    weather = factory.Iterator(["sunny", "rainy", "cloudy", "foggy", ""])
    road_condition = factory.Iterator(["dry", "wet", "under_construction", ""])

    @factory.lazy_attribute
    def junction_name(self):
        return ""

    @factory.post_generation
    def set_fatalities(self, create, extracted, **kwargs):
        """Ensure fatalities <= casualties and injuries <= casualties."""
        if self.fatalities > self.casualties:
            self.fatalities = self.casualties
        if self.injuries > self.casualties:
            self.injuries = self.casualties
        if create:
            self.save()
