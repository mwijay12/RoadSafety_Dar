"""
Pytest tests for the factory-boy factories (Prompt 1 data-layer hardening).
Run with: pytest accidents/test_factories.py -v
"""

import pytest

from .factories import AccidentFactory, JunctionFactory

pytestmark = pytest.mark.django_db


class TestJunctionFactory:
    def test_basic(self):
        j = JunctionFactory()
        assert j.pk is not None
        assert j.slug.startswith("junction-")
        assert -7.5 <= j.lat <= -6.0
        assert 38.5 <= j.lng <= 39.7
        assert j.district in ("Ilala", "Kinondoni", "Temeke", "Ubungo", "Kigamboni")

    def test_unique_slug_on_collision(self):
        """Different names that slugify to the same value get unique slugs.
        Example: 'Same Name' and 'Same-Name' both slug to 'same-name'."""
        j1 = JunctionFactory(name="Same Name")
        j2 = JunctionFactory(name="Same-Name")
        assert j1.slug == "same-name"
        assert j2.slug == "same-name-1"

    def test_custom_name(self):
        j = JunctionFactory(name="Ubungo Interchange")
        assert j.slug == "ubungo-interchange"

    def test_safety_score_no_accidents(self):
        j = JunctionFactory()
        assert j.safety_score == 0.0

    def test_safety_score_with_accidents(self):
        j = JunctionFactory()
        AccidentFactory.create_batch(4, junction=j, junction_name=j.name, severity="fatal")
        j = JunctionFactory._meta.model.objects.get(pk=j.pk)
        assert j.safety_score > 50.0  # (4 fatal * weight 4) / 4 * 25 = 100

    def test_safety_score_mixed_severity(self):
        j = JunctionFactory()
        AccidentFactory(junction=j, junction_name=j.name, severity="minor")
        AccidentFactory(junction=j, junction_name=j.name, severity="minor")
        AccidentFactory(junction=j, junction_name=j.name, severity="fatal")
        j = JunctionFactory._meta.model.objects.get(pk=j.pk)
        # (1+1+4) / 3 * 25 = 6 / 3 * 25 = 50.0
        assert j.safety_score == 50.0


class TestAccidentFactory:
    def test_basic(self):
        a = AccidentFactory()
        assert a.pk is not None
        assert a.h3_cell  # should be auto-computed on save
        assert len(a.h3_cell) > 10
        assert a.severity in ("minor", "serious", "fatal", "critical")

    def test_with_junction(self):
        j = JunctionFactory()
        a = AccidentFactory(junction=j, junction_name=j.name)
        a.refresh_from_db()
        assert a.junction_id == j.pk
        assert a.junction_name == j.name

    def test_batch_creates_multiple(self):
        count = 10
        accidents = AccidentFactory.create_batch(count)
        assert len(accidents) == count
        assert all(a.pk for a in accidents)

    def test_fatalities_never_exceed_casualties(self):
        a = AccidentFactory(casualties=2, fatalities=3)
        a.refresh_from_db()
        assert a.fatalities <= a.casualties

    def test_injuries_never_exceed_casualties(self):
        a = AccidentFactory(casualties=2, injuries=5)
        a.refresh_from_db()
        assert a.injuries <= a.casualties

    def test_h3_cell_is_consistent(self):
        """Same lat/lng should produce the same H3 cell."""
        a1 = AccidentFactory(lat=-6.7924, lng=39.2083)
        a2 = AccidentFactory(lat=-6.7924, lng=39.2083)
        assert a1.h3_cell == a2.h3_cell

    def test_different_coords_different_h3(self):
        a1 = AccidentFactory(lat=-6.7924, lng=39.2083)
        a2 = AccidentFactory(lat=-6.7500, lng=39.2500)
        assert a1.h3_cell != a2.h3_cell


class TestSafetyScoreProperty:
    """Verify the Junction.safety_score property works end-to-end."""

    def test_no_accidents(self):
        j = JunctionFactory()
        assert j.safety_score == 0.0

    def test_all_fatal(self):
        j = JunctionFactory()
        AccidentFactory.create_batch(3, junction=j, severity="fatal")
        j = JunctionFactory._meta.model.objects.get(pk=j.pk)
        # 3 fatal * weight 4 / 3 * 25 = 100.0
        assert j.safety_score == 100.0

    def test_all_minor(self):
        j = JunctionFactory()
        AccidentFactory.create_batch(3, junction=j, severity="minor")
        j = JunctionFactory._meta.model.objects.get(pk=j.pk)
        # 3 minor * weight 1 / 3 * 25 = 25.0
        assert j.safety_score == 25.0

    def test_mixed(self):
        j = JunctionFactory()
        AccidentFactory(junction=j, severity="minor")
        AccidentFactory(junction=j, severity="serious")
        AccidentFactory(junction=j, severity="fatal")
        j = JunctionFactory._meta.model.objects.get(pk=j.pk)
        # (1+2+4) / 3 * 25 = 58.33... approx 58.3
        assert j.safety_score == 58.3
