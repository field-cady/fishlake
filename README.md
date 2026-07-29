# Fishing Lakes of the United States

An interactive map of fishable lakes across the continental US — with species,
size, elevation, county, and a link to each water's source page. Live map:
**https://field-cady.github.io/fishlake/** (installable as a PWA).

- **~55,000 lakes across 46 states.** Only Arizona and Mississippi have no
  usable public data source (see `scrapers/README.md`).
- Data comes from each state's fish & wildlife agency (ArcGIS/APIs, a few HTML
  scrapes). Coverage and known gaps per state are documented in
  `scrapers/README.md`.

## Layout

```
index.html          # the map (Leaflet + supercluster), loads data/all_states.json
all_scripts.js      # map rendering, category filter, popups
manifest.json, sw.js, icon-*.png   # PWA (installable, offline app shell)
scrapers/           # one module per state (base.py = shared schema + helpers)
scrape_all.py       # run every state scraper -> data/state_lakes_<code>.jsonl
merge_data.py       # concatenate + slim those into data/all_states.json
data/               # scraped outputs (per-state jsonl + merged all_states.json)
```

## Regenerating the data

```bash
pip install -r requirements.txt
python scrape_all.py        # scrape all states (add --smoke for a quick check)
python merge_data.py        # build data/all_states.json (what the map loads)
```

Adding a state = drop a `scrapers/<state>.py` implementing
`STATE_NAME`, `STATE_CODE`, `scrape(limit=None)` (see `scrapers/base.py` for the
common record schema) and add it to `SCRAPERS` in `scrapers/__init__.py`.

## Viewing locally

Serve over HTTP (the map fetches JSON via XHR, and the service worker needs a
secure context — `localhost` counts):

```bash
python -m http.server 8000   # then open http://127.0.0.1:8000/
```

## Automation

`.github/workflows/update_data.yml` re-runs the full scrape + merge on the 1st
of every month and commits any data changes.
