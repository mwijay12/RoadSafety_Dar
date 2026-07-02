"""
Tests for the hierarchical Dar es Salaam location picker.

Covers:
    1. Data integrity — all 5 districts present, all wards have lat/lng,
       all locations have verified coords within Dar es Salaam bbox.
    2. Lookup helpers — find_location_by_name returns correct district/ward.
    3. Hotspot classification — accident_hotspot=True on known black-spots.
    4. JSON API endpoints — /api/locations/, /districts/, /wards/, /hotspots/
       all return well-formed responses.
    5. Form auto-fill — when location_id is submitted, lat/lng/district/ward
       get auto-populated from the location's canonical record.
"""


import pytest
from django.test import Client

from .locations import (
    DISTRICTS,
    WARDS,
    find_location_by_name,
    get_districts,
    get_hotspots,
    get_wards_for_district,
)

pytestmark = pytest.mark.django_db


# ===========================================================================
# 1. Data integrity
# ===========================================================================


class TestLocationDataIntegrity:
    """All reference data must be sane."""

    def test_five_districts(self):
        assert len(DISTRICTS) == 5
        assert set(get_districts()) == {
            "Ilala", "Kinondoni", "Temeke", "Ubungo", "Kigamboni"
        }

    def test_every_district_has_wards(self):
        for d in DISTRICTS:
            wards = get_wards_for_district(d["name"])
            assert len(wards) > 0, f"{d['name']} has no wards"

    def test_every_ward_has_centroid_in_bbox(self):
        for dname, wards in WARDS.items():
            for w in wards:
                assert -7.5 <= w["lat"] <= -6.0, (
                    f"{dname}/{w['name']} lat {w['lat']} outside DSM bbox"
                )
                assert 38.5 <= w["lng"] <= 39.7, (
                    f"{dname}/{w['name']} lng {w['lng']} outside DSM bbox"
                )

    def test_every_location_in_bbox(self):
        for dname, wards in WARDS.items():
            for w in wards:
                for loc in w.get("locations", []):
                    assert -7.5 <= loc["lat"] <= -6.0, (
                        f"{dname}/{w['name']}/{loc.get('name')} lat out of bbox"
                    )
                    assert 38.5 <= loc["lng"] <= 39.7, (
                        f"{dname}/{w['name']}/{loc.get('name')} lng out of bbox"
                    )

    def test_hotspot_count_is_reasonable(self):
        hotspots = get_hotspots()
        assert len(hotspots) >= 20, "Expected at least 20 known black-spots"
        for h in hotspots:
            assert h.get("accident_hotspot") is True
            assert "district" in h and "ward" in h


# ===========================================================================
# 2. Lookup helpers
# ===========================================================================


class TestFindLocation:
    def test_canonical_name_ubungo(self):
        r = find_location_by_name("Ubungo Interchange")
        assert r is not None
        assert r["district"] == "Kinondoni"
        assert r["ward"] == "Ubungo (Kinondoni)"
        assert r["lat"] == -6.785
        assert r["lng"] == 39.21

    def test_case_insensitive(self):
        a = find_location_by_name("kariakoo market")
        b = find_location_by_name("KARIakoo MARKET")
        assert a is not None and b is not None
        assert a["name"] == b["name"] == "Kariakoo Market"

    def test_alias_match(self):
        r = find_location_by_name("Kariakoo")
        assert r is not None
        assert r["district"] == "Ilala"

    def test_unknown_returns_none(self):
        assert find_location_by_name("xyz_no_such_place") is None

    def test_empty_returns_none(self):
        assert find_location_by_name("") is None
        assert find_location_by_name("   ") is None


# ===========================================================================
# 3. JSON API endpoints
# ===========================================================================


class TestLocationsAPI:
    @pytest.fixture
    def client(self):
        return Client()

    def test_districts_endpoint(self, client):
        resp = client.get("/api/locations/districts/")
        assert resp.status_code == 200
        data = resp.json()
        assert "districts" in data
        names = [d["name"] for d in data["districts"]]
        assert "Ilala" in names and "Kigamboni" in names
        assert len(names) == 5

    def test_full_tree_endpoint(self, client):
        resp = client.get("/api/locations/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["region"] == "Dar es Salaam"
        assert "tree" in data
        ilala = next((d for d in data["tree"] if d["district"] == "Ilala"), None)
        assert ilala is not None
        assert any(w["name"] == "Kariakoo" for w in ilala["wards"])

    def test_filter_by_district(self, client):
        resp = client.get("/api/locations/?district=Temeke")
        assert resp.status_code == 200
        data = resp.json()
        assert data["district"] == "Temeke"
        assert all("name" in w for w in data["wards"])

    def test_search_endpoint(self, client):
        resp = client.get("/api/locations/?q=kariakoo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "kariakoo"
        assert data["count"] >= 2
        names = [r["name"] for r in data["results"]]
        assert any("Kariakoo" in n for n in names)

    def test_search_endpoint_ubungo(self, client):
        resp = client.get("/api/locations/?q=ubungo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert any("Ubungo" in r["name"] for r in data["results"])

    def test_hotspots_endpoint(self, client):
        resp = client.get("/api/locations/hotspots/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == len(get_hotspots())
        assert data["count"] >= 20
        for h in data["hotspots"]:
            assert "name" in h
            assert "district" in h
            assert "lat" in h and "lng" in h

    def test_wards_endpoint(self, client):
        resp = client.get("/api/locations/wards/?district=Kinondoni")
        assert resp.status_code == 200
        data = resp.json()
        assert data["district"] == "Kinondoni"
        assert len(data["wards"]) >= 10
        for w in data["wards"]:
            assert "name" in w and "lat" in w and "lng" in w

    def test_wards_missing_district_400(self, client):
        resp = client.get("/api/locations/wards/")
        assert resp.status_code == 400

    def test_v1_aliases_exist(self, client):
        for path in [
            "/api/v1/locations/",
            "/api/v1/locations/districts/",
            "/api/v1/locations/wards/?district=Ilala",
            "/api/v1/locations/hotspots/",
        ]:
            assert client.get(path).status_code == 200, f"{path} failed"


# ===========================================================================
# 4. Form auto-fill (the user's core pain point)
# ===========================================================================


class TestLocationAutoFill:
    """Submitting location_id='Ubungo Interchange' should auto-populate
    district, ward, lat, lng, junction_name from the reference data."""

    def test_form_autofills_from_location_id(self):
        from .forms import AccidentForm

        form = AccidentForm(
            data={
                "occurred_at": "2026-07-02T15:00",
                "severity": "serious",
                "vehicle_types": "car",
                "reporter_type": "community",
                "location_id": "Ubungo Interchange",
                "casualties": 1,
                "fatalities": 0,
                "injuries": 1,
            }
        )
        assert form.is_valid(), form.errors
        # lat / lng / district / ward / junction_name all auto-filled
        cleaned = form.cleaned_data
        assert abs(cleaned["lat"] - (-6.785)) < 0.001
        assert abs(cleaned["lng"] - 39.21) < 0.01
        assert cleaned["district"] == "Kinondoni"
        assert "Ubungo" in cleaned["ward"]
        assert "Ubungo" in cleaned["junction_name"]

    def test_form_preserves_explicit_lat_lng(self):
        """If the user already typed lat/lng, don't overwrite them."""
        from .forms import AccidentForm

        form = AccidentForm(
            data={
                "occurred_at": "2026-07-02T15:00",
                "severity": "minor",
                "vehicle_types": "car",
                "reporter_type": "community",
                "lat": -6.790,
                "lng": 39.220,
                "location_id": "Ubungo Interchange",
                "casualties": 0,
                "fatalities": 0,
                "injuries": 0,
            }
        )
        assert form.is_valid(), form.errors
        cleaned = form.cleaned_data
        # explicit user coords preserved
        assert abs(cleaned["lat"] - (-6.790)) < 0.0001
        assert abs(cleaned["lng"] - 39.220) < 0.0001


# ===========================================================================
# 5. Model schema (ward + location_id fields exist on Accident)
# ===========================================================================


class TestAccidentModelLocationFields:
    def test_ward_field_exists(self):
        from .models import Accident
        f = Accident._meta.get_field("ward")
        assert f.max_length == 80
        assert f.blank is True
        assert f.db_index is True

    def test_location_id_field_exists(self):
        from .models import Accident
        f = Accident._meta.get_field("location_id")
        assert f.max_length == 120
        assert f.blank is True
        assert f.db_index is True
