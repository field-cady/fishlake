"""California state scraper (CDFW Fishing Guide).

Source: CDFW "Fishing Locations" (BIOS ds2880), the layer behind CDFW's public
Fishing Guide app. It carries real per-water species PRESENCE FLAGS (bass,
striped bass, salmon, inland salmon/kokanee, sturgeon, panfish, steelhead,
catfish, and per-species trout) plus name, county, coordinates, elevation and
acreage -- far broader than the old trout/catfish-only planting feed (ds2897).

The layer is token-gated, so it is queried through CDFW's own public proxy
(apps.wildlife.ca.gov/fishing/proxy.ashx) exactly as the web app does. That
proxy is undocumented and could change; if it starts returning an error the
scraper yields nothing and last month's data is kept.

Layer: https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds2880_fms/FeatureServer/0
"""

import re

import requests

from .base import make_record

STATE_NAME = "California"
STATE_CODE = "ca"

_LAYER = "https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds2880_fms/FeatureServer/0"
_PROXY = "https://apps.wildlife.ca.gov/fishing/proxy.ashx?"
_HEADERS = {"Referer": "https://apps.wildlife.ca.gov/fishing/"}
_URL = "https://apps.wildlife.ca.gov/fishing/"

# Presence-flag column -> species label. (Categories are coarse: kokanee is
# CDFW's "InlandSalmon"; bass species are rolled into "Bass".)
_FLAG_SPECIES = {
    "Bass": "Bass", "StripedBass": "Striped Bass", "AdSalmon": "Salmon",
    "InlandSalmon": "Kokanee", "Sturgeon": "Sturgeon", "Panfish": "Panfish",
    "Shad": "American Shad", "Steelhead": "Steelhead", "Catfish": "Catfish",
    "bcBrookTrout": "Brook Trout", "bcBrownTrout": "Brown Trout",
    "bcGoldenTrout": "Golden Trout", "bcRainbowTrout": "Rainbow Trout",
    "bcLahontanCutthroatTrout": "Lahontan Cutthroat Trout", "bcTrout": "Trout",
    "TroutHatchery": "Trout", "TroutWild": "Trout", "TroutWH": "Trout",
}


def _fetch(limit=None):
    features, offset, page = [], 0, 2000
    while True:
        target = (f"{_LAYER}/query?where=1=1&outFields=*&returnGeometry=false"
                  f"&f=json&resultOffset={offset}&resultRecordCount={page}")
        r = requests.get(_PROXY + target, headers=_HEADERS, timeout=60)
        try:
            data = r.json()
        except ValueError:
            print("[CA] proxy returned non-JSON; aborting CA fetch")
            break
        if "error" in data:
            print(f"[CA] proxy error: {data['error']}; aborting CA fetch")
            break
        batch = data.get("features", [])
        if not batch:
            break
        features.extend(batch)
        if limit is not None and len(features) >= limit:
            return features[:limit]
        if len(batch) < page:
            break
        offset += len(batch)
    return features


# No lake in the continental US sits anywhere near this high (Mt. Whitney, the
# highest point, is 14,505 ft). A larger value is a source data-entry error --
# e.g. Conway Lake's real ~6,823 ft stored as 68230 (a dropped decimal / extra
# zero) -- so we discard it and let the merge-step DEM backfill supply the true
# elevation from the coordinates.
_MAX_PLAUSIBLE_ELEVATION_FT = 14500


def _parse_elevation(val):
    if not val:
        return None
    m = re.search(r"[\d,]+", str(val))
    if not m:
        return None
    elev = float(m.group(0).replace(",", ""))
    if elev > _MAX_PLAUSIBLE_ELEVATION_FT:
        return None   # implausible -> drop; DEM backfill fills it from coords
    return elev


def scrape(limit=None):
    print("[CA] Fetching CDFW Fishing Guide locations (ds2880 via proxy)...")
    features = _fetch(limit=limit)
    print(f"[CA] {len(features)} fishing locations.")

    records = []
    for feat in features:
        a = feat.get("attributes", {})
        name = (a.get("NAME") or "").strip()
        lat, lon = a.get("Latitude"), a.get("Longitude")
        if not name or lat is None or lon is None:
            continue
        reach = (a.get("AcresReach") or "").strip()
        if "mile" in reach.lower():
            continue  # river/stream reach, not a lake

        species = [label for col, label in _FLAG_SPECIES.items()
                   if str(a.get(col)).strip() in ("1", "1.0")]
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            county=a.get("County"),
            elevation=_parse_elevation(a.get("Elevation")),
            area=reach if "acre" in reach.lower() else "Unknown",
            species=species, url=_URL,
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[CA] Collected {len(records)} lakes/reservoirs.")
    return records
