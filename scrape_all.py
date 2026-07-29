"""Run every state scraper and write data/state_lakes_<code>.jsonl for each.

This is the single entry point for scraping. It loops over the scrapers
registered in ``scrapers.SCRAPERS`` and treats every state identically, so
adding a new state means adding a module to that registry -- nothing here
changes.

Usage::

    python scrape_all.py                 # full scrape of every state
    python scrape_all.py --smoke         # quick pipeline check (small subset)
    python scrape_all.py --limit 2       # custom per-scraper cap
    python scrape_all.py --states wa or   # only the named states
"""

import argparse
import sys
import traceback

from scrapers import SCRAPERS
from scrapers.base import data_path, write_jsonl, in_conus

SMOKE_LIMIT = 1


def run(limit=None, only=None):
    only = {c.lower() for c in only} if only else None
    failures = []
    for scraper in SCRAPERS:
        if only is not None and scraper.STATE_CODE not in only:
            continue
        out_path = data_path(f"state_lakes_{scraper.STATE_CODE}.jsonl")
        try:
            records = scraper.scrape(limit=limit)
            # Coordinate sanity: drop null-island / unprojected outliers.
            kept = [r for r in records if in_conus(r.get("lat"), r.get("lon"))]
            dropped = len(records) - len(kept)
            if dropped:
                print(f"[{scraper.STATE_CODE.upper()}] dropped {dropped} out-of-US coords")
            write_jsonl(out_path, kept)
            print(f"[{scraper.STATE_CODE.upper()}] Wrote {len(kept)} lakes -> {out_path}\n")
        except Exception:
            print(f"[{scraper.STATE_CODE.upper()}] FAILED:\n{traceback.format_exc()}")
            failures.append(scraper.STATE_CODE)
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scrape fishable lakes for every US state.")
    parser.add_argument("--smoke", action="store_true",
                        help=f"Quick run: cap each scraper at {SMOKE_LIMIT} unit of work.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap the work each scraper does (pages/regions/lakes).")
    parser.add_argument("--states", nargs="+", metavar="CODE",
                        help="Only run these state codes (e.g. wa or id).")
    args = parser.parse_args(argv)

    limit = args.limit
    if args.smoke and limit is None:
        limit = SMOKE_LIMIT

    failures = run(limit=limit, only=args.states)
    if failures:
        print(f"Completed with failures: {', '.join(failures)}")
        return 1
    print("All scrapers completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
