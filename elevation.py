"""Backfill missing lake elevations from coordinates using a digital elevation
model (DEM), with an on-disk cache so re-runs only look up points we haven't
seen before.

Most state sources give coordinates but no elevation (~90% of lakes), which
makes the map's elevation filter nearly useless. This fills that gap.

Source: the Open-Elevation API (https://open-elevation.com), which serves the
NASA/USGS SRTM DEM. It accepts large batches per POST (no API key) and returns
metres -- we convert to feet to match the rest of the data. It occasionally
returns 0 for a DEM void; we treat 0 as "no data" and leave that lake unfilled
rather than assert a false sea-level elevation.

Looked-up values are cached in ``data/elevation_cache.json`` keyed by rounded
``lat,lon`` so the monthly pipeline only queries lakes that are new since the
last run. Existing elevations are never overwritten -- this only fills blanks.
"""

import json
import os
import time

import requests

_API = "https://api.open-elevation.com/api/v1/lookup"
_BATCH = 500                 # locations per POST (smaller = fewer gateway timeouts)
_M_TO_FT = 3.28084


def _key(lat, lon):
    return "{},{}".format(round(lat, 5), round(lon, 5))


def _load_cache(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, OSError):
            return {}
    return {}


def _save_cache(path, cache):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def _lookup_batch(coords):
    """coords: list of (lat, lon). Returns list of elevation-in-feet (or None).

    0 from the API means a DEM void, not sea level -> None.
    """
    locations = [{"latitude": la, "longitude": lo} for la, lo in coords]
    r = requests.post(_API, json={"locations": locations}, timeout=120)
    r.raise_for_status()
    results = r.json().get("results") or []
    out = []
    for x in results:
        m = x.get("elevation")
        out.append(round(m * _M_TO_FT) if m else None)   # m == 0/None -> None
    return out


def backfill_elevations(lakes, cache_path, sleep=0.5):
    """Fill ``elevation`` (feet) on lakes that have lat/lon but no elevation.

    Never overwrites an existing value. Uses and updates an on-disk cache, and
    degrades gracefully: if the API is unavailable, lakes simply keep whatever
    elevation (or none) they already had. Returns the number newly filled.
    """
    cache = _load_cache(cache_path)

    need = [lk for lk in lakes
            if not lk.get("elevation")
            and lk.get("lat") is not None and lk.get("lon") is not None]

    # Unique points not already cached, so we never re-query the same spot.
    to_query = {}
    for lk in need:
        k = _key(lk["lat"], lk["lon"])
        if k not in cache:
            to_query.setdefault(k, (lk["lat"], lk["lon"]))

    if to_query:
        items = list(to_query.items())
        print("[elev] {} lakes missing elevation; looking up {} new points "
              "({} cached) in batches of {}...".format(
                  len(need), len(items), len(cache), _BATCH))
        for i in range(0, len(items), _BATCH):
            chunk = items[i:i + _BATCH]
            coords = [c for _, c in chunk]
            elevs = None
            for attempt in range(3):
                try:
                    elevs = _lookup_batch(coords)
                    break
                except Exception as e:
                    print("[elev] batch at {} attempt {} failed: {}".format(
                        i, attempt + 1, e))
                    time.sleep(2 * (attempt + 1))
            if elevs is None:
                continue
            for (k, _), ev in zip(chunk, elevs):
                cache[k] = ev
            _save_cache(cache_path, cache)          # checkpoint every batch
            print("[elev]   {}/{} points looked up".format(
                min(i + _BATCH, len(items)), len(items)))
            time.sleep(sleep)

    filled = 0
    for lk in need:
        ev = cache.get(_key(lk["lat"], lk["lon"]))
        if ev is not None:
            lk["elevation"] = ev
            filled += 1
    print("[elev] filled {} lakes with elevation.".format(filled))
    return filled
