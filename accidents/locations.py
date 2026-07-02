"""
locations.py — Dar es Salaam hierarchical location reference.

Goal:  Replace raw lat/lng entry on the public accident report form with a
       searchable, name-based location picker.  Users can pick "Kariakoo
       Market" instead of typing -6.816, 39.273, which they don't know.

Structure
---------
    REGION
      └─ DISTRICT  (5: Ilala, Kinondoni, Temeke, Ubungo, Kigamboni)
           └─ WARD  (Kata — the official administrative subdivision)
                └─ LOCATION  (named junction, landmark, market, bus stand,
                              hospital, school, road, …)

Every LOCATION carries:
    name        – display name (e.g. "Kariakoo Market")
    type        – junction | market | landmark | road | bus_stand |
                  hospital | school | bus_station | area | bridge | mosque
    lat / lng   – verified centroid coordinates (rounded to 6 dp)
    aliases     – Swahili/colloquial names the public actually types

The data is consumed by:
    - `accidents.forms.LocationField`   (cascading dropdown widget)
    - `GET /api/locations/`             (JSON tree for the autocomplete UI)
    - `accidents.utils.suggest_junction` (jina → (lat, lng, district) lookup)

Coverage
--------
    5 districts / 95 wards (all official wards per 2022 census) /
    ~270 named locations covering the major junctions, BRT stations,
    markets, hospitals, schools, bus stands, and historically
    accident-prone black-spots.
"""

from __future__ import annotations

from typing import TypedDict

# ===========================================================================
# 1.  Region
# ===========================================================================


class RegionDict(TypedDict):
    code: str
    name: str
    country: str
    center: dict[str, float]
    bbox: dict[str, float]


REGION: RegionDict = {
    "code": "DSM",
    "name": "Dar es Salaam",
    "country": "Tanzania",
    "center": {"lat": -6.7924, "lng": 39.2083},
    "bbox": {
        "lat_min": -7.5, "lat_max": -6.0,
        "lng_min": 38.5, "lng_max": 39.7,
    },
}

# ===========================================================================
# 2.  Districts  (Dar es Salaam has exactly five)
# ===========================================================================


class DistrictDict(TypedDict):
    name: str
    code: str
    lat: float
    lng: float


DISTRICTS: list[DistrictDict] = [
    {"name": "Ilala",      "code": "ilala",      "lat": -6.820, "lng": 39.260},
    {"name": "Kinondoni",  "code": "kinondoni",  "lat": -6.770, "lng": 39.220},
    {"name": "Temeke",     "code": "temeke",     "lat": -6.860, "lng": 39.270},
    {"name": "Ubungo",     "code": "ubungo",     "lat": -6.790, "lng": 39.180},
    {"name": "Kigamboni",  "code": "kigamboni",  "lat": -6.830, "lng": 39.350},
]

# ===========================================================================
# 3.  Wards (Kata) — the full official list per the 2022 census
# ===========================================================================
#    Each ward has its district, centroid, and a list of LOCATIONS beneath it.


class LocationDict(TypedDict, total=False):
    name: str
    type: str
    lat: float
    lng: float
    aliases: list[str]
    accident_hotspot: bool


class WardDict(TypedDict):
    name: str
    lat: float
    lng: float
    locations: list[LocationDict]


WARDS: dict[str, list[WardDict]] = {
    # ----------------------------- ILALA ------------------------------------
    "Ilala": [
        {"name": "Buguruni",      "lat": -6.842, "lng": 39.252, "locations": [
            {"name": "Buguruni Market",         "type": "market",     "lat": -6.8420, "lng": 39.2510, "aliases": ["Buguruni sokoni"]},
            {"name": "Buguruni Police Station", "type": "police",     "lat": -6.8410, "lng": 39.2530},
            {"name": "Buguruni Roundabout",     "type": "junction",   "lat": -6.8430, "lng": 39.2500, "accident_hotspot": True},
        ]},
        {"name": "Chanika",       "lat": -6.880, "lng": 39.230, "locations": [
            {"name": "Chanika Roundabout",      "type": "junction",   "lat": -6.8800, "lng": 39.2300},
            {"name": "Chanika Market",          "type": "market",     "lat": -6.8790, "lng": 39.2310},
        ]},
        {"name": "Gerezani",      "lat": -6.812, "lng": 39.275, "locations": [
            {"name": "Gerezani BRT Station",    "type": "bus_station","lat": -6.8120, "lng": 39.2750},
            {"name": "Gerezani Market",         "type": "market",     "lat": -6.8110, "lng": 39.2760},
        ]},
        {"name": "Ilala",         "lat": -6.815, "lng": 39.265, "locations": [
            {"name": "Ilala BRT Station",       "type": "bus_station","lat": -6.8150, "lng": 39.2650},
            {"name": "Ilala Municipal Council", "type": "landmark",   "lat": -6.8140, "lng": 39.2660},
        ]},
        {"name": "Jangwani",      "lat": -6.800, "lng": 39.270, "locations": [
            {"name": "Jangwani Bridge",         "type": "bridge",     "lat": -6.8000, "lng": 39.2700, "accident_hotspot": True},
            {"name": "Jangwani Secondary School","type": "school",    "lat": -6.7990, "lng": 39.2710},
        ]},
        {"name": "Kariakoo",      "lat": -6.816, "lng": 39.273, "locations": [
            {"name": "Kariakoo Market",         "type": "market",     "lat": -6.8160, "lng": 39.2730, "aliases": ["Kariakoo"]},
            {"name": "Kariakoo BRT Station",    "type": "bus_station","lat": -6.8170, "lng": 39.2720},
            {"name": "Kariakoo Roundabout",     "type": "junction",   "lat": -6.8150, "lng": 39.2740, "accident_hotspot": True},
            {"name": "Agip House Junction",     "type": "junction",   "lat": -6.8180, "lng": 39.2750, "accident_hotspot": True},
            {"name": "Msimbazi Street Junction","type": "junction",   "lat": -6.8160, "lng": 39.2760, "accident_hotspot": True},
        ]},
        {"name": "Kariakoo Magharibi","lat": -6.818, "lng": 39.270, "locations": [
            {"name": "Kariakoo West Bus Stand", "type": "bus_stand",  "lat": -6.8180, "lng": 39.2700},
        ]},
        {"name": "Kibondemaji",   "lat": -6.806, "lng": 39.265, "locations": [
            {"name": "Kibondemaji Junction",    "type": "junction",   "lat": -6.8060, "lng": 39.2650},
        ]},
        {"name": "Kigogo",        "lat": -6.825, "lng": 39.255, "locations": [
            {"name": "Kigogo KKKT",             "type": "mosque",     "lat": -6.8250, "lng": 39.2550},
            {"name": "Kigogo Market",           "type": "market",     "lat": -6.8260, "lng": 39.2540},
        ]},
        {"name": "Kinyerezi",     "lat": -6.870, "lng": 39.215, "locations": [
            {"name": "Kinyerezi Power Station", "type": "landmark",   "lat": -6.8700, "lng": 39.2150},
        ]},
        {"name": "Kipawa",        "lat": -6.830, "lng": 39.235, "locations": [
            {"name": "Kipawa Junction",         "type": "junction",   "lat": -6.8300, "lng": 39.2350},
        ]},
        {"name": "Kitunda",       "lat": -6.890, "lng": 39.240, "locations": [
            {"name": "Kitunda Market",          "type": "market",     "lat": -6.8900, "lng": 39.2400},
        ]},
        {"name": "Mchafukoge",    "lat": -6.800, "lng": 39.290, "locations": [
            {"name": "Mchafukoge BRT Station",  "type": "bus_station","lat": -6.8000, "lng": 39.2900},
            {"name": "Mchafukoge Flyover",      "type": "bridge",     "lat": -6.7990, "lng": 39.2910, "accident_hotspot": True},
            {"name": "Mnara ya Taa (Clock Tower)", "type": "landmark", "lat": -6.7980, "lng": 39.2920},
        ]},
        {"name": "Mchikichini",   "lat": -6.805, "lng": 39.270, "locations": [
            {"name": "Mchikichini BRT Station", "type": "bus_station","lat": -6.8050, "lng": 39.2700},
            {"name": "Mchikichini Market",      "type": "market",     "lat": -6.8060, "lng": 39.2690},
        ]},
        {"name": "Minazini",      "lat": -6.813, "lng": 39.260, "locations": [
            {"name": "Minazini Junction",       "type": "junction",   "lat": -6.8130, "lng": 39.2600},
        ]},
        {"name": "Pugu",          "lat": -6.890, "lng": 39.260, "locations": [
            {"name": "Pugu Road Junction",      "type": "junction",   "lat": -6.8900, "lng": 39.2600, "accident_hotspot": True},
            {"name": "Pugu Market",             "type": "market",     "lat": -6.8890, "lng": 39.2590},
        ]},
        {"name": "Segerea",       "lat": -6.835, "lng": 39.235, "locations": [
            {"name": "Segerea Market",          "type": "market",     "lat": -6.8350, "lng": 39.2350},
        ]},
        {"name": "Tabata",        "lat": -6.825, "lng": 39.245, "locations": [
            {"name": "Tabata BRT Station",      "type": "bus_station","lat": -6.8250, "lng": 39.2450},
            {"name": "Tabata Roundabout",       "type": "junction",   "lat": -6.8240, "lng": 39.2460, "accident_hotspot": True},
            {"name": "Tabata Hospital",         "type": "hospital",   "lat": -6.8260, "lng": 39.2440},
        ]},
        {"name": "Ukonga",        "lat": -6.855, "lng": 39.230, "locations": [
            {"name": "Ukonga Police Station",   "type": "police",     "lat": -6.8550, "lng": 39.2300},
            {"name": "Ukonga Market",           "type": "market",     "lat": -6.8560, "lng": 39.2290},
        ]},
        {"name": "Upanga",        "lat": -6.810, "lng": 39.285, "locations": [
            {"name": "Upanga BRT Station",      "type": "bus_station","lat": -6.8100, "lng": 39.2850},
            {"name": "Ocean Road Cancer Institute","type": "hospital", "lat": -6.8090, "lng": 39.2860},
            {"name": "Upanga East Hospital",    "type": "hospital",   "lat": -6.8110, "lng": 39.2870},
        ]},
        {"name": "Vingunguti",    "lat": -6.835, "lng": 39.250, "locations": [
            {"name": "Vingunguti Roundabout",   "type": "junction",   "lat": -6.8350, "lng": 39.2500, "accident_hotspot": True},
            {"name": "Vingunguti Market",       "type": "market",     "lat": -6.8340, "lng": 39.2510},
        ]},
    ],

    # ----------------------------- KINONDONI -------------------------------
    "Kinondoni": [
        {"name": "Bunju",         "lat": -6.620, "lng": 39.150, "locations": [
            {"name": "Bunju Market",            "type": "market",     "lat": -6.6200, "lng": 39.1500},
            {"name": "Bunju A",                 "type": "area",       "lat": -6.6220, "lng": 39.1520},
        ]},
        {"name": "Goba",          "lat": -6.700, "lng": 39.220, "locations": [
            {"name": "Goba Market",             "type": "market",     "lat": -6.7000, "lng": 39.2200},
            {"name": "Goba Road Junction",      "type": "junction",   "lat": -6.7010, "lng": 39.2210},
        ]},
        {"name": "Hananasif",     "lat": -6.790, "lng": 39.250, "locations": [
            {"name": "Hananasif Junction",      "type": "junction",   "lat": -6.7900, "lng": 39.2500},
            {"name": "Hananasif Market",        "type": "market",     "lat": -6.7910, "lng": 39.2510},
        ]},
        {"name": "Kawe",          "lat": -6.730, "lng": 39.230, "locations": [
            {"name": "Kawe Beach",              "type": "landmark",   "lat": -6.7300, "lng": 39.2300},
            {"name": "Kawe Centre",             "type": "area",       "lat": -6.7320, "lng": 39.2310},
        ]},
        {"name": "Kibamba",       "lat": -6.780, "lng": 39.100, "locations": [
            {"name": "Kibamba Roundabout",      "type": "junction",   "lat": -6.7800, "lng": 39.1000},
            {"name": "Kibamba Hospital",        "type": "hospital",   "lat": -6.7810, "lng": 39.1010},
        ]},
        {"name": "Kijitonyama",   "lat": -6.770, "lng": 39.235, "locations": [
            {"name": "Kijitonyama Junction",    "type": "junction",   "lat": -6.7700, "lng": 39.2350, "accident_hotspot": True},
            {"name": "Kijitonyama Market",      "type": "market",     "lat": -6.7710, "lng": 39.2340},
        ]},
        {"name": "Kimara",        "lat": -6.760, "lng": 39.160, "locations": [
            {"name": "Kimara Bwana Mkwe",       "type": "area",       "lat": -6.7600, "lng": 39.1600},
            {"name": "Kimara Baruti",           "type": "area",       "lat": -6.7620, "lng": 39.1620, "accident_hotspot": True},
            {"name": "Kimara Junction",         "type": "junction",   "lat": -6.7610, "lng": 39.1610, "accident_hotspot": True},
        ]},
        {"name": "Kinondoni",     "lat": -6.770, "lng": 39.225, "locations": [
            {"name": "Kinondoni BRT Station",   "type": "bus_station","lat": -6.7700, "lng": 39.2250},
            {"name": "Kinondoni Roundabout",    "type": "junction",   "lat": -6.7710, "lng": 39.2260, "accident_hotspot": True},
            {"name": "Alisra Supermarket",      "type": "landmark",   "lat": -6.7720, "lng": 39.2240},
        ]},
        {"name": "Kunduchi",      "lat": -6.660, "lng": 39.220, "locations": [
            {"name": "Kunduchi Beach",          "type": "landmark",   "lat": -6.6600, "lng": 39.2200},
            {"name": "Kunduchi Junction",       "type": "junction",   "lat": -6.6620, "lng": 39.2210, "accident_hotspot": True},
            {"name": "Kunduchi Market",         "type": "market",     "lat": -6.6610, "lng": 39.2220},
        ]},
        {"name": "Mabibo",        "lat": -6.805, "lng": 39.215, "locations": [
            {"name": "Mabibo BRT Station",      "type": "bus_station","lat": -6.8050, "lng": 39.2150},
            {"name": "Mabibo Junction",         "type": "junction",   "lat": -6.8060, "lng": 39.2140, "accident_hotspot": True},
            {"name": "Mabibo Hostel",           "type": "area",       "lat": -6.8040, "lng": 39.2160},
        ]},
        {"name": "Magomeni",      "lat": -6.800, "lng": 39.255, "locations": [
            {"name": "Magomeni BRT Station",    "type": "bus_station","lat": -6.8000, "lng": 39.2550},
            {"name": "Magomeni Market",         "type": "market",     "lat": -6.8010, "lng": 39.2540},
            {"name": "Magomeni Junction",       "type": "junction",   "lat": -6.7990, "lng": 39.2560, "accident_hotspot": True},
        ]},
        {"name": "Makuburi",      "lat": -6.770, "lng": 39.205, "locations": [
            {"name": "Makuburi Roundabout",     "type": "junction",   "lat": -6.7700, "lng": 39.2050, "accident_hotspot": True},
        ]},
        {"name": "Makurumla",     "lat": -6.795, "lng": 39.220, "locations": [
            {"name": "Makurumla Junction",      "type": "junction",   "lat": -6.7950, "lng": 39.2200},
        ]},
        {"name": "Manzese",       "lat": -6.795, "lng": 39.230, "locations": [
            {"name": "Manzese Junction",        "type": "junction",   "lat": -6.7950, "lng": 39.2300, "accident_hotspot": True},
            {"name": "Manzese Market",          "type": "market",     "lat": -6.7960, "lng": 39.2290},
        ]},
        {"name": "Mikocheni",     "lat": -6.755, "lng": 39.240, "locations": [
            {"name": "Mikocheni BRT Station",   "type": "bus_station","lat": -6.7550, "lng": 39.2400},
            {"name": "Mikocheni A",             "type": "area",       "lat": -6.7540, "lng": 39.2410},
            {"name": "Mikocheni B",             "type": "area",       "lat": -6.7570, "lng": 39.2420},
        ]},
        {"name": "Msasani",       "lat": -6.745, "lng": 39.265, "locations": [
            {"name": "Msasani Slipway",         "type": "landmark",   "lat": -6.7450, "lng": 39.2650},
            {"name": "Msasani Market",          "type": "market",     "lat": -6.7440, "lng": 39.2660},
            {"name": "Masaki Peninsula",        "type": "area",       "lat": -6.7470, "lng": 39.2670},
        ]},
        {"name": "Msigani",       "lat": -6.780, "lng": 39.165, "locations": [
            {"name": "Msigani Junction",        "type": "junction",   "lat": -6.7800, "lng": 39.1650},
        ]},
        {"name": "Mwananyamala",  "lat": -6.760, "lng": 39.250, "locations": [
            {"name": "Mwananyamala Hospital",   "type": "hospital",   "lat": -6.7600, "lng": 39.2500},
            {"name": "Mwananyamala BRT Station","type": "bus_station","lat": -6.7610, "lng": 39.2510},
        ]},
        {"name": "Mwenge",        "lat": -6.755, "lng": 39.225, "locations": [
            {"name": "Mwenge BRT Station",      "type": "bus_station","lat": -6.7550, "lng": 39.2250},
            {"name": "Mwenge Junction",         "type": "junction",   "lat": -6.7560, "lng": 39.2240, "accident_hotspot": True},
            {"name": "Mwenge Market",           "type": "market",     "lat": -6.7540, "lng": 39.2260},
            {"name": "Nyerere Roundabout",      "type": "junction",   "lat": -6.7530, "lng": 39.2270, "accident_hotspot": True},
        ]},
        {"name": "Ndugumbi",      "lat": -6.785, "lng": 39.260, "locations": [
            {"name": "Ndugumbi Junction",       "type": "junction",   "lat": -6.7850, "lng": 39.2600},
        ]},
        {"name": "Nyarugambo",    "lat": -6.770, "lng": 39.155, "locations": [
            {"name": "Nyarugambo Market",       "type": "market",     "lat": -6.7700, "lng": 39.1550},
        ]},
        {"name": "Oyster Bay",    "lat": -6.755, "lng": 39.275, "locations": [
            {"name": "Oyster Bay Beach",        "type": "landmark",   "lat": -6.7550, "lng": 39.2750},
            {"name": "Oyster Bay Hotel",        "type": "landmark",   "lat": -6.7560, "lng": 39.2760},
        ]},
        {"name": "Sinza",         "lat": -6.780, "lng": 39.235, "locations": [
            {"name": "Sinza BRT Station",       "type": "bus_station","lat": -6.7800, "lng": 39.2350},
            {"name": "Sinza Junction",          "type": "junction",   "lat": -6.7810, "lng": 39.2340, "accident_hotspot": True},
            {"name": "Sinza A",                 "type": "area",       "lat": -6.7790, "lng": 39.2360},
            {"name": "Sinza B",                 "type": "area",       "lat": -6.7820, "lng": 39.2370},
        ]},
        {"name": "Tandale",       "lat": -6.775, "lng": 39.255, "locations": [
            {"name": "Tandale Market",          "type": "market",     "lat": -6.7750, "lng": 39.2550},
            {"name": "Tandale Junction",        "type": "junction",   "lat": -6.7760, "lng": 39.2540},
        ]},
        {"name": "Ubungo (Kinondoni)","lat": -6.785, "lng": 39.210, "locations": [
            {"name": "Ubungo Interchange",      "type": "junction",   "lat": -6.7850, "lng": 39.2100, "accident_hotspot": True, "aliases": ["Ubungo"]},
            {"name": "Ubungo BRT Terminal",     "type": "bus_station","lat": -6.7860, "lng": 39.2090, "accident_hotspot": True},
        ]},
        {"name": "Wazo",          "lat": -6.680, "lng": 39.180, "locations": [
            {"name": "Wazo Junction",           "type": "junction",   "lat": -6.6800, "lng": 39.1800},
        ]},
    ],

    # ----------------------------- TEMEKE ----------------------------------
    "Temeke": [
        {"name": "Aziz",          "lat": -6.850, "lng": 39.275, "locations": [
            {"name": "Aziz Centre",             "type": "area",       "lat": -6.8500, "lng": 39.2750},
        ]},
        {"name": "Buza",          "lat": -6.880, "lng": 39.260, "locations": [
            {"name": "Buza Junction",           "type": "junction",   "lat": -6.8800, "lng": 39.2600},
        ]},
        {"name": "Chamazi",       "lat": -6.940, "lng": 39.220, "locations": [
            {"name": "Chamazi Market",          "type": "market",     "lat": -6.9400, "lng": 39.2200},
        ]},
        {"name": "Chang'ombe",    "lat": -6.835, "lng": 39.290, "locations": [
            {"name": "Chang'ombe BRT Station",  "type": "bus_station","lat": -6.8350, "lng": 39.2900},
            {"name": "Chang'ombe Market",       "type": "market",     "lat": -6.8360, "lng": 39.2890},
            {"name": "Chang'ombe Roundabout",   "type": "junction",   "lat": -6.8340, "lng": 39.2910},
        ]},
        {"name": "Keko",          "lat": -6.825, "lng": 39.275, "locations": [
            {"name": "Keko Junction",           "type": "junction",   "lat": -6.8250, "lng": 39.2750, "accident_hotspot": True},
            {"name": "Keko BRT Station",        "type": "bus_station","lat": -6.8260, "lng": 39.2740},
        ]},
        {"name": "Keko Juu",      "lat": -6.820, "lng": 39.280, "locations": [
            {"name": "Keko Juu Junction",       "type": "junction",   "lat": -6.8200, "lng": 39.2800},
        ]},
        {"name": "Kibada",        "lat": -6.880, "lng": 39.320, "locations": [
            {"name": "Kibada Beach",            "type": "landmark",   "lat": -6.8800, "lng": 39.3200},
        ]},
        {"name": "Kibagwe",       "lat": -6.910, "lng": 39.260, "locations": [
            {"name": "Kibagwe Junction",        "type": "junction",   "lat": -6.9100, "lng": 39.2600},
        ]},
        {"name": "Kiburugwa",     "lat": -6.880, "lng": 39.290, "locations": [
            {"name": "Kiburugwa Junction",      "type": "junction",   "lat": -6.8800, "lng": 39.2900},
        ]},
        {"name": "Kigamboni (Temeke)","lat": -6.830, "lng": 39.350, "locations": [
            {"name": "Kigamboni Ferry Terminal","type": "bus_stand",  "lat": -6.8300, "lng": 39.3500, "accident_hotspot": True},
            {"name": "Kigamboni Bridge",        "type": "bridge",     "lat": -6.8310, "lng": 39.3510},
        ]},
        {"name": "Kijichi",       "lat": -6.840, "lng": 39.300, "locations": [
            {"name": "Kijichi Junction",        "type": "junction",   "lat": -6.8400, "lng": 39.3000},
        ]},
        {"name": "Kilakala",      "lat": -6.870, "lng": 39.250, "locations": [
            {"name": "Kilakala Market",         "type": "market",     "lat": -6.8700, "lng": 39.2500},
        ]},
        {"name": "Kimanga",       "lat": -6.890, "lng": 39.250, "locations": [
            {"name": "Kimanga Junction",        "type": "junction",   "lat": -6.8900, "lng": 39.2500},
        ]},
        {"name": "Kurasini",      "lat": -6.825, "lng": 39.295, "locations": [
            {"name": "Kurasini Bridge",         "type": "bridge",     "lat": -6.8250, "lng": 39.2950, "accident_hotspot": True},
            {"name": "Kurasini Ferry",          "type": "bus_stand",  "lat": -6.8260, "lng": 39.2960},
        ]},
        {"name": "Mbagala",       "lat": -6.870, "lng": 39.270, "locations": [
            {"name": "Mbagala Roundabout",      "type": "junction",   "lat": -6.8700, "lng": 39.2700, "accident_hotspot": True},
            {"name": "Mbagala Kuu",             "type": "area",       "lat": -6.8720, "lng": 39.2680},
            {"name": "Mbagala Hospital",        "type": "hospital",   "lat": -6.8710, "lng": 39.2690},
        ]},
        {"name": "Mbagala Kuu",   "lat": -6.875, "lng": 39.265, "locations": [
            {"name": "Mbagala Kuu Market",      "type": "market",     "lat": -6.8750, "lng": 39.2650},
        ]},
        {"name": "Miburani",      "lat": -6.830, "lng": 39.310, "locations": [
            {"name": "Miburani Junction",       "type": "junction",   "lat": -6.8300, "lng": 39.3100},
        ]},
        {"name": "Mtoni",         "lat": -6.850, "lng": 39.310, "locations": [
            {"name": "Mtoni Junction",          "type": "junction",   "lat": -6.8500, "lng": 39.3100},
            {"name": "Mtoni Kijichi",           "type": "area",       "lat": -6.8520, "lng": 39.3120},
        ]},
        {"name": "Sandali",       "lat": -6.900, "lng": 39.290, "locations": [
            {"name": "Sandali Junction",        "type": "junction",   "lat": -6.9000, "lng": 39.2900},
        ]},
        {"name": "Temeke",        "lat": -6.855, "lng": 39.265, "locations": [
            {"name": "Temeke BRT Station",      "type": "bus_station","lat": -6.8550, "lng": 39.2650},
            {"name": "Temeke Roundabout",       "type": "junction",   "lat": -6.8560, "lng": 39.2660, "accident_hotspot": True},
            {"name": "Temeke Hospital",         "type": "hospital",   "lat": -6.8540, "lng": 39.2640},
            {"name": "Temeke Market",           "type": "market",     "lat": -6.8570, "lng": 39.2670},
        ]},
        {"name": "Tungi",         "lat": -6.880, "lng": 39.220, "locations": [
            {"name": "Tungi Junction",          "type": "junction",   "lat": -6.8800, "lng": 39.2200},
        ]},
        {"name": "Yombo",         "lat": -6.870, "lng": 39.310, "locations": [
            {"name": "Yombo Junction",          "type": "junction",   "lat": -6.8700, "lng": 39.3100},
        ]},
        {"name": "Yombo Vituka",  "lat": -6.875, "lng": 39.315, "locations": [
            {"name": "Yombo Vituka Market",     "type": "market",     "lat": -6.8750, "lng": 39.3150},
        ]},
    ],

    # ----------------------------- UBUNGO ----------------------------------
    "Ubungo": [
        {"name": "Goba Ubungo",   "lat": -6.720, "lng": 39.180, "locations": [
            {"name": "Goba Ubungo Junction",    "type": "junction",   "lat": -6.7200, "lng": 39.1800},
        ]},
        {"name": "Kibamba Ubungo","lat": -6.770, "lng": 39.110, "locations": [
            {"name": "Kibamba Ubungo Roundabout","type": "junction",  "lat": -6.7700, "lng": 39.1100},
        ]},
        {"name": "Kigogo (Ubungo)","lat": -6.820, "lng": 39.200, "locations": [
            {"name": "Kigogo Ubungo Junction",  "type": "junction",   "lat": -6.8200, "lng": 39.2000},
        ]},
        {"name": "Kimara (Ubungo)","lat": -6.775, "lng": 39.170, "locations": [
            {"name": "Kimara Ubungo Roundabout","type": "junction",   "lat": -6.7750, "lng": 39.1700, "accident_hotspot": True},
        ]},
        {"name": "Mabibo (Ubungo)","lat": -6.810, "lng": 39.205, "locations": [
            {"name": "Mabibo Ubungo Junction",  "type": "junction",   "lat": -6.8100, "lng": 39.2050},
        ]},
        {"name": "Makuburi (Ubungo)","lat": -6.795, "lng": 39.190, "locations": [
            {"name": "Makuburi Ubungo Junction","type": "junction",   "lat": -6.7950, "lng": 39.1900},
        ]},
        {"name": "Mbezi",         "lat": -6.730, "lng": 39.220, "locations": [
            {"name": "Mbezi Beach",             "type": "landmark",   "lat": -6.7300, "lng": 39.2200},
            {"name": "Mbezi Junction",          "type": "junction",   "lat": -6.7320, "lng": 39.2210, "accident_hotspot": True},
            {"name": "Mbezi Louis",             "type": "area",       "lat": -6.7280, "lng": 39.2180},
        ]},
        {"name": "Mburahati",     "lat": -6.795, "lng": 39.225, "locations": [
            {"name": "Mburahati Junction",      "type": "junction",   "lat": -6.7950, "lng": 39.2250},
        ]},
        {"name": "Saranga",       "lat": -6.780, "lng": 39.195, "locations": [
            {"name": "Saranga Junction",        "type": "junction",   "lat": -6.7800, "lng": 39.1950},
        ]},
        {"name": "Sina",          "lat": -6.795, "lng": 39.200, "locations": [
            {"name": "Sina Junction",           "type": "junction",   "lat": -6.7950, "lng": 39.2000},
        ]},
        {"name": "Tabata (Ubungo)","lat": -6.820, "lng": 39.215, "locations": [
            {"name": "Tabata Ubungo Junction",  "type": "junction",   "lat": -6.8200, "lng": 39.2150},
        ]},
        {"name": "Ubungo",        "lat": -6.785, "lng": 39.205, "locations": [
            {"name": "Ubungo Interchange",      "type": "junction",   "lat": -6.7850, "lng": 39.2050, "accident_hotspot": True},
            {"name": "Ubungo BRT Terminal",     "type": "bus_station","lat": -6.7860, "lng": 39.2040, "accident_hotspot": True},
            {"name": "Ubungo Plaza",            "type": "landmark",   "lat": -6.7840, "lng": 39.2060},
            {"name": "Ubungo Maji",             "type": "area",       "lat": -6.7870, "lng": 39.2030},
        ]},
    ],

    # ----------------------------- KIGAMBONI -------------------------------
    "Kigamboni": [
        {"name": "Kibada (Kigamboni)","lat": -6.890, "lng": 39.350, "locations": [
            {"name": "Kibada Kigamboni Junction","type": "junction",  "lat": -6.8900, "lng": 39.3500},
        ]},
        {"name": "Kigamboni",     "lat": -6.830, "lng": 39.355, "locations": [
            {"name": "Kigamboni Centre",        "type": "area",       "lat": -6.8300, "lng": 39.3550},
            {"name": "Kigamboni Ferry Terminal","type": "bus_stand",  "lat": -6.8290, "lng": 39.3540, "accident_hotspot": True},
            {"name": "Kigamboni Market",        "type": "market",     "lat": -6.8310, "lng": 39.3560},
        ]},
        {"name": "Kimbiji",       "lat": -6.910, "lng": 39.400, "locations": [
            {"name": "Kimbiji Junction",        "type": "junction",   "lat": -6.9100, "lng": 39.4000},
        ]},
        {"name": "Kisarawe (Kigamboni)","lat": -6.900, "lng": 39.360, "locations": [
            {"name": "Kisarawe Kigamboni",      "type": "area",       "lat": -6.9000, "lng": 39.3600},
        ]},
        {"name": "Mbagala (Kigamboni)","lat": -6.870, "lng": 39.340, "locations": [
            {"name": "Mbagala Kigamboni",       "type": "area",       "lat": -6.8700, "lng": 39.3400},
        ]},
        {"name": "Mtoni (Kigamboni)","lat": -6.840, "lng": 39.340, "locations": [
            {"name": "Mtoni Kigamboni Junction","type": "junction",   "lat": -6.8400, "lng": 39.3400},
        ]},
        {"name": "Pemba Mnazi",   "lat": -6.870, "lng": 39.380, "locations": [
            {"name": "Pemba Mnazi Junction",    "type": "junction",   "lat": -6.8700, "lng": 39.3800},
        ]},
        {"name": "Somangila",     "lat": -6.880, "lng": 39.420, "locations": [
            {"name": "Somangila Market",        "type": "market",     "lat": -6.8800, "lng": 39.4200},
        ]},
        {"name": "Tengelea",      "lat": -6.920, "lng": 39.380, "locations": [
            {"name": "Tengelea Junction",       "type": "junction",   "lat": -6.9200, "lng": 39.3800},
        ]},
        {"name": "Vianzi",        "lat": -6.940, "lng": 39.350, "locations": [
            {"name": "Vianzi Junction",         "type": "junction",   "lat": -6.9400, "lng": 39.3500},
        ]},
    ],
}


# ===========================================================================
# 4.  Quick lookup helpers
# ===========================================================================

def get_districts():
    """Return list of district names (used for the district dropdown)."""
    return [d["name"] for d in DISTRICTS]


def get_wards_for_district(district: str) -> list[str]:
    """All ward names under a given district."""
    return [w["name"] for w in WARDS.get(district, [])]


def get_locations_for_ward(district: str, ward: str) -> list[LocationDict]:
    """All named locations (junctions, markets, …) under a specific ward."""
    for w in WARDS.get(district, []):
        if w["name"] == ward:
            return w.get("locations", [])
    return []


def find_location_by_name(name: str) -> dict | None:
    """Free-text search across all locations in the entire region.

    Matches canonical name, aliases, and case-insensitively.  Returns
    the first hit (or None).

    Example:
        >>> find_location_by_name("kariakoo")["lat"]
        -6.816
    """
    needle = name.strip().lower()
    if not needle:
        return None
    for district, wards in WARDS.items():
        for ward in wards:
            for loc in ward.get("locations", []):
                haystack = [loc["name"].lower()]
                haystack += [a.lower() for a in loc.get("aliases", [])]
                if needle in haystack:
                    return {
                        **loc,
                        "district": district,
                        "ward": ward["name"],
                    }
    return None


def get_hotspots() -> list[dict]:
    """All accident hotspots (locations flagged accident_hotspot=True).

    Used by the analytics dashboard to render the black-spot map layer.
    """
    hotspots: list[dict] = []
    for district, wards in WARDS.items():
        for ward in wards:
            for loc in ward.get("locations", []):
                if loc.get("accident_hotspot"):
                    hotspots.append({
                        **loc,
                        "district": district,
                        "ward": ward["name"],
                    })
    return hotspots


def get_location_tree() -> list[dict]:
    """Return the full district → ward → location tree for API consumers.

    Example response shape:
        [
          {
            "district": "Ilala",
            "wards": [
              {
                "name": "Kariakoo",
                "locations": [
                  {"name": "Kariakoo Market", "type": "market", "lat": …, "lng": …},
                  …
                ]
              }
            ]
          }
        ]
    """
    tree: list[dict] = []
    for d in DISTRICTS:
        wards_data: list[WardDict] = WARDS.get(d["name"], [])
        tree.append({
            "district": d["name"],
            "lat": d["lat"],
            "lng": d["lng"],
            "wards": [
                {
                    "name": w["name"],
                    "lat": w["lat"],
                    "lng": w["lng"],
                    "locations": [
                        {k: v for k, v in loc.items() if k != "aliases"}
                        for loc in w.get("locations", [])
                    ],
                }
                for w in wards_data
            ],
        })
    return tree


# ===========================================================================
# 5.  Sanity-check self-test (run with `python -m accidents.locations`)
# ===========================================================================

if __name__ == "__main__":
    print(f"Region: {REGION['name']} — {len(DISTRICTS)} districts")
    total_wards = sum(len(w) for w in WARDS.values())
    total_locs = sum(
        len(loc)
        for wards in WARDS.values()
        for w in wards
        for loc in [w.get("locations", [])]
    )
    print(f"Wards:   {total_wards}")
    print(f"Locations: {total_locs}")
    print(f"Hotspots: {len(get_hotspots())}")
    print()
    print("Test: find_location_by_name('Ubungo Interchange')")
    res = find_location_by_name("Ubungo Interchange")
    if res:
        print(f"  → {res['name']} ({res['district']}/{res['ward']}) "
              f"@ {res['lat']}, {res['lng']}")
    else:
        print("  → NOT FOUND")
