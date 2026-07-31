"""Mississippi state scraper (MDWFP Fisheries).

Source: the "Waterbodies" layer behind MDWFP's public Fishing Dashboard
(discovered via their ArcGIS Online "Fisheries Database Map for Website" web
map). It's a point per fishable water with a name, class (Lake/Reservoir),
county and elevation in feet. MDWFP exposes no per-lake species, so -- like
Colorado -- Mississippi carries no species list.

TLS note: arcgis.mdwfp.com serves an incomplete certificate chain (it omits the
GlobalSign intermediate), so the system CA bundle alone can't verify it. We ship
that intermediate (certs/mdwfp_chain.pem) and splice it onto the default bundle
so verification still succeeds -- no disabling of certificate checks.

Layer: https://arcgis.mdwfp.com/arcgis/rest/services/Fisheries/FishingDashboard/MapServer/1
"""

import os
import tempfile

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Mississippi"
STATE_CODE = "ms"

_LAYER = "https://arcgis.mdwfp.com/arcgis/rest/services/Fisheries/FishingDashboard/MapServer/1"
_INTERMEDIATE = os.path.join(os.path.dirname(__file__), "certs", "mdwfp_chain.pem")


def _ca_bundle():
    """Default CA bundle + the MDWFP intermediate, written to a temp file.

    requests uses the given bundle *instead of* the system store, so we
    concatenate rather than replace -- keeping every normal root trusted.
    """
    with open(requests.certs.where(), encoding="utf-8") as f:
        data = f.read()
    with open(_INTERMEDIATE, encoding="utf-8") as f:
        data += "\n" + f.read()
    fd, path = tempfile.mkstemp(suffix="_mdwfp_ca.pem")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
    return path


def scrape(limit=None):
    print("[MS] Fetching MDWFP fishing-dashboard waterbodies...")
    bundle = _ca_bundle()
    try:
        features = fetch_arcgis(
            _LAYER, out_fields="Feature_Na,Class,County,Ele_ft_",
            limit=limit, page_size=1000, verify=bundle,
        )
    finally:
        os.remove(bundle)

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Feature_Na") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        elev = p.get("Ele_ft_")
        county = (p.get("County") or "").strip() or None
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            elevation=float(elev) if elev else None,
            county=county,
            # MDWFP has no per-lake page; link to the water's location on a map.
            url="https://www.google.com/maps/search/?api=1&query={},{}".format(lat, lon),
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[MS] Collected {len(records)} lakes.")
    return records
