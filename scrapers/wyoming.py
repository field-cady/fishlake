"""Wyoming state scraper (Wyoming Game & Fish Department).

Source: WGFD "Lakes_FishingGuide_PublicView" ArcGIS FeatureServer (layer 0),
the lakes layer behind the official Wyoming Fishing Guide. Polygon features
with a water name, comma-delimited species strings and acreage. (The source
Elevation field is unreliable -- see below -- so elevation comes from the DEM
backfill instead.) Streams live in a separate layer we don't use.

Layer: https://services6.arcgis.com/cWzdqIyxbijuhPLw/arcgis/rest/services/Lakes_FishingGuide_PublicView/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Wyoming"
STATE_CODE = "wy"

# WGFD's Elevation field is unreliable: it's populated for only ~200 of ~2150
# lakes and mixes units (most values are metres, a handful are already feet --
# verified against a DEM). Rather than guess per-record, we drop it and let the
# merge step's DEM backfill fill every Wyoming lake uniformly in feet.

_LAYER = "https://services6.arcgis.com/cWzdqIyxbijuhPLw/arcgis/rest/services/Lakes_FishingGuide_PublicView/FeatureServer/0"
_URL = "https://wgfd.wyo.gov/fishing-boating/where-to-fish"


def _split_species(value):
    if not value:
        return []
    value = value.strip()
    if value.lower() == "none":
        return []
    return [s.strip() for s in value.split(",") if s.strip() and s.strip().lower() != "none"]


def scrape(limit=None):
    print("[WY] Fetching WGFD fishing-guide lakes...")
    features = fetch_arcgis(
        _LAYER,
        out_fields="WaterName,GameFishPresent,CommonGameFish,Acres,WaterType",
        limit=limit, page_size=1000,
    )
    print(f"[WY] {len(features)} lake polygons.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WaterName") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        species = _split_species(p.get("GameFishPresent")) or _split_species(p.get("CommonGameFish"))
        acres = p.get("Acres")
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            elevation=None,   # unreliable in source; filled by DEM backfill
            area=f"{acres} Acres" if acres else "Unknown",
            species=species, url=_URL,
            description=p.get("WaterType") or "",
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[WY] Collected {len(records)} lakes.")
    return records
