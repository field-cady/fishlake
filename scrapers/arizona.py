"""Arizona state scraper (AZGFD "Fish & Boat AZ" fishing waters).

Arizona Game & Fish has no plain public FeatureServer, but its Fish & Boat AZ
app (https://fishandboataz.azgfd.com) is backed by a public ArcGIS Online web
map whose "AZGFD Fishing Waters" layer is reachable anonymously through AGOL's
service proxy. That layer -- the department's canonical fishing-waters dataset
-- carries a point per water with coordinates and a Yes/No column per sport
fish species. This scraper reads it directly.

The direct hosted service (services2.arcgis.com/os1CphwIyxBDDUGn/...) is a
secured/registered service and returns "Token Required"; the proxy URL below is
the same path the public app uses, so we go through it.

Layer: NEW_fishingWaters/FeatureServer/7 (item a463165bec8d46a1927bcd8c3788aa19)
"""

import re

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Arizona"
STATE_CODE = "az"

_LAYER = ("https://utility.arcgis.com/usrsvcs/servers/"
          "a463165bec8d46a1927bcd8c3788aa19/rest/services/"
          "NEW_fishingWaters/FeatureServer/7")

# This is a lakes map, so keep still waters and drop flowing water
# (Rivers & Creeks, Canal).
_KEEP_TYPES = ("Lakes & Ponds", "Community Fishing Waters")

# Per-species Yes/No columns -> display name. These are more complete than the
# free-text "Species_Present" prose (which omits some species the columns flag).
_SPECIES_FIELDS = {
    "Rainbow_Trout": "Rainbow Trout",
    "Cutthroat_Trout": "Cutthroat Trout",
    "Brown_Trout": "Brown Trout",
    "Brook_Trout": "Brook Trout",
    "Tiger_Trout": "Tiger Trout",
    "Gila_Trout": "Gila Trout",
    "Apache_Trout": "Apache Trout",
    "Grayling_Trout": "Arctic Grayling",
    "Largemouth_Bass": "Largemouth Bass",
    "Smallmouth_Bass": "Smallmouth Bass",
    "Striped_Bass": "Striped Bass",
    "White_Bass": "White Bass",
    "Yellow_Bass": "Yellow Bass",
    "Northern_Pike": "Northern Pike",
    "walleye": "Walleye",
    "Channel_Catfish": "Channel Catfish",
    "Flathead_Catfish": "Flathead Catfish",
    "bullhead": "Bullhead",
    "White_Crappie": "White Crappie",
    "Black_Crappie": "Black Crappie",
    "bluegill": "Bluegill",
    "Redear_Sunfish": "Redear Sunfish",
    "Green_Sunfish": "Green Sunfish",
    "Hybrid_Sunfish": "Hybrid Sunfish",
    "Yellow_Perch": "Yellow Perch",
    "White_Amur": "White Amur",
    "Roundtail_Chub": "Roundtail Chub",
    "Common_Carp": "Common Carp",
    "Suckers": "Sucker",
    "buffalofish": "Buffalo",
    "tilapia": "Tilapia",
}

# Rollup columns -> (display name, child columns). Used only as a fallback when a
# water flags the group but none of its specific children, so we don't emit a
# vague "Trout" next to "Rainbow Trout".
_UMBRELLA = {
    "trout": ("Trout", ["Rainbow_Trout", "Cutthroat_Trout", "Brown_Trout",
                         "Brook_Trout", "Tiger_Trout", "Gila_Trout",
                         "Apache_Trout", "Grayling_Trout"]),
    "bass": ("Bass", ["Largemouth_Bass", "Smallmouth_Bass", "Striped_Bass",
                      "White_Bass", "Yellow_Bass"]),
    "catfish": ("Catfish", ["Channel_Catfish", "Flathead_Catfish", "bullhead"]),
    "crappie": ("Crappie", ["White_Crappie", "Black_Crappie"]),
    "sunfish": ("Sunfish", ["bluegill", "Redear_Sunfish", "Green_Sunfish",
                            "Hybrid_Sunfish"]),
}

_OUT_FIELDS = ",".join(["Water_Name", "Water_Type", "Water_Body_Description"]
                       + list(_SPECIES_FIELDS) + list(_UMBRELLA))


# The layer has no acreage field, but the prose description usually opens with
# it ("a 229-acre reservoir", "3,683 acres"). Grab the first such figure -- for
# a water it's the water itself, before any surrounding park/forest acreage.
_ACRE_RE = re.compile(r"([\d,]+(?:\.\d+)?)[\s-]acres?\b", re.IGNORECASE)


def _area_from_description(desc):
    m = _ACRE_RE.search(desc or "")
    if not m:
        return None
    return "{} Acres".format(m.group(1).replace(",", ""))


def _species(attrs):
    species = [name for col, name in _SPECIES_FIELDS.items()
               if attrs.get(col) == "Yes"]
    for col, (name, children) in _UMBRELLA.items():
        if attrs.get(col) == "Yes" and not any(attrs.get(c) == "Yes" for c in children):
            species.append(name)
    return species


def scrape(limit=None):
    types = "','".join(_KEEP_TYPES)
    where = "Water_Type IN ('{}')".format(types)
    features = fetch_arcgis(_LAYER, where=where, out_fields=_OUT_FIELDS,
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Water_Name") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        description = (p.get("Water_Body_Description") or "").strip()
        records.append(make_record(
            name=name,
            state=STATE_NAME,
            lat=lat,
            lon=lon,
            area=_area_from_description(description),
            species=_species(p),
            description=description,
            # No per-water public page; link to the water's location on a map.
            url="https://www.google.com/maps/search/?api=1&query={},{}".format(lat, lon),
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[AZ] Collected {len(records)} lakes ({withsp} with species).")
    return records
