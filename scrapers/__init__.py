"""State scrapers for the US fishing-lakes map.

Every state scraper is a module that exposes:

* ``STATE_NAME`` - human readable state name (e.g. ``"Washington"``).
* ``STATE_CODE`` - two letter lowercase code used in filenames (e.g. ``"wa"``).
* ``scrape(limit=None) -> list[dict]`` - returns normalized lake records using
  the common schema documented in :mod:`scrapers.base`.

To add a new state, create ``scrapers/<state>.py`` following that contract and
add the module to :data:`SCRAPERS` below. Nothing else in the pipeline needs to
change -- ``scrape_all.py`` will pick it up and write
``data/state_lakes_<code>.jsonl`` alongside the others.
"""

from . import (
    washington, oregon, idaho, california, montana, wyoming, colorado, utah, nevada,
    new_mexico, texas, minnesota, wisconsin, michigan, new_york, pennsylvania, georgia,
    illinois, indiana, kentucky, missouri, ohio, tennessee, virginia, alabama, arkansas,
    florida, iowa, kansas, north_carolina, oklahoma, south_carolina, louisiana, nebraska,
    north_dakota, south_dakota, west_virginia, maine, vermont, connecticut, delaware,
    maryland, massachusetts, new_hampshire, new_jersey, rhode_island,
)

# The ordered registry of state scrapers. All states are treated equally; the
# only thing that differs between them is which module does the scraping.
SCRAPERS = [
    washington, oregon, idaho, california, montana, wyoming, colorado, utah, nevada,
    new_mexico, texas, minnesota, wisconsin, michigan, new_york, pennsylvania, georgia,
    illinois, indiana, kentucky, missouri, ohio, tennessee, virginia, alabama, arkansas,
    florida, iowa, kansas, north_carolina, oklahoma, south_carolina, louisiana, nebraska,
    north_dakota, south_dakota, west_virginia, maine, vermont, connecticut, delaware,
    maryland, massachusetts, new_hampshire, new_jersey, rhode_island,
]

__all__ = [
    "SCRAPERS", "washington", "oregon", "idaho", "california", "montana", "wyoming",
    "colorado", "utah", "nevada", "new_mexico", "texas", "minnesota", "wisconsin",
    "michigan", "new_york", "pennsylvania", "georgia", "illinois", "indiana", "kentucky",
    "missouri", "ohio", "tennessee", "virginia", "alabama", "arkansas", "florida", "iowa",
    "kansas", "north_carolina", "oklahoma", "south_carolina", "louisiana", "nebraska",
    "north_dakota", "south_dakota", "west_virginia", "maine", "vermont", "connecticut",
    "delaware", "maryland", "massachusetts", "new_hampshire", "new_jersey", "rhode_island",
]
