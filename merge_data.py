"""Merge every data/state_lakes_<code>.jsonl into data/all_states.json.

Since each state scraper now emits the common, already-normalized schema (see
``scrapers/base.py``), merging is just concatenation + a timestamp. The output
is slimmed for the web: coordinates are rounded, empty/default fields are
dropped, and the JSON is minified -- this shrinks the file the frontend loads
(~16.5 MB -> ~11.6 MB; ~1.7 MB -> ~1.2 MB gzipped) and speeds up parsing.
"""

import glob
import json
import os
from datetime import datetime

from elevation import backfill_elevations

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_ELEV_CACHE = os.path.join(DATA_DIR, "elevation_cache.json")

# ~5 decimal places of lat/lon is ~1 metre -- plenty for a map marker, and far
# smaller than the raw float noise the sources emit.
_COORD_DP = 5


def _slim(lake):
    """Drop empty/default fields and round coordinates for a lean web payload.

    The frontend already guards every optional field (``if (lk['county'])``
    etc.), so omitting them changes nothing visible.
    """
    out = {"name": lake.get("name"), "state": lake.get("state")}
    lat, lon = lake.get("lat"), lake.get("lon")
    if lat is not None:
        out["lat"] = round(lat, _COORD_DP)
    if lon is not None:
        out["lon"] = round(lon, _COORD_DP)
    if lake.get("species"):
        out["species"] = lake["species"]
    if lake.get("county"):
        out["county"] = lake["county"]
    if lake.get("elevation"):
        out["elevation"] = lake["elevation"]
    if lake.get("area") not in (None, "", "Unknown"):
        out["area"] = lake["area"]
    if lake.get("description"):
        out["description"] = lake["description"]
    if lake.get("url"):
        out["url"] = lake["url"]
    for flag in ("starting", "overabundant"):
        if lake.get(flag):
            out[flag] = lake[flag]
    return out


def merge_datasets():
    all_lakes = []
    paths = sorted(glob.glob(os.path.join(DATA_DIR, "state_lakes_*.jsonl")))
    if not paths:
        print("No state_lakes_*.jsonl files found. Run scrape_all.py first.")

    for path in paths:
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                all_lakes.append(_slim(json.loads(line)))
                count += 1
        print(f"Loaded {count} lakes from {os.path.basename(path)}")

    # Fill missing elevations from a DEM (cached), so the elevation filter works
    # for the ~90% of lakes whose source gives coordinates but no elevation.
    backfill_elevations(all_lakes, _ELEV_CACHE)

    output = {
        "lakes": all_lakes,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    out_path = os.path.join(DATA_DIR, "all_states.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"))  # minified

    print(f"Merged {len(all_lakes)} total lakes -> {out_path}")


if __name__ == "__main__":
    merge_datasets()
