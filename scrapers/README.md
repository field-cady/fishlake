# State scrapers — coverage & data sources

Each state is a module in this package exposing `STATE_NAME`, `STATE_CODE`, and
`scrape(limit=None)`, and is registered in `scrapers/__init__.py`. Running
`python scrape_all.py` writes `data/state_lakes_<code>.jsonl` for every
registered state; `python merge_data.py` concatenates them into
`data/all_states.json` (what the map loads).

All records share the common schema defined in `base.py`
(`name, state, lat, lon, elevation, area, county, species, url, description`).
Data availability varies wildly by state — see the notes below. Where a field
isn't available from a state's source it's left null / `"Unknown"` / empty.

## Source types (best → worst)

- **API / ArcGIS / open-data** — queryable, structured, re-runnable. Preferred.
- **KML / file download** — structured but static-ish.
- **HTML scrape** — brittle, parser-dependent.
- **None found** — no usable public source located; documented and skipped.

## Coverage

| State | Code | Source | Type | Notes |
|-------|------|--------|------|-------|
| Washington | wa | WDFW High Lakes (HTML) + Fish Washington lowland lakes (ArcGIS) | HTML + API | Union of alpine high lakes (elevation, `starting`/`overabundant` flags) and statewide lowland lakes with broad species (kokanee, bass, walleye, muskie, perch, crappie, panfish, catfish). |
| Oregon | or | ODFW hike-in lakes (Google My Maps KML) | KML | Descriptions common; county absent; some prose-only lakes have no coords. |
| Idaho | id | IDFG Fishing Planner API (`body=3` high-mountain subset) | API | County present; no elevation. |
| California | ca | CDFW Fishing Guide "Fishing Locations" (BIOS ds2880, via CDFW proxy) | API | ~1,885 lakes/reservoirs with per-water species presence flags (bass, striped bass, salmon, kokanee/inland salmon, sturgeon, panfish, steelhead, catfish, trout), county, elevation, acreage. Species are coarse categories; token-gated layer reached via CDFW's public proxy. |
| Montana | mt | Montana FWP FishViewer stocking records (layer 38) | API | Stocked waters only; rich species; no county/elevation/area. A few (~3) events carry bad coordinates. |
| Wyoming | wy | WGFD Fishing Guide "Lakes" ArcGIS FeatureServer | API | Lakes/reservoirs only; species from `GameFishPresent`; area present; elevation sparse (~9%); no county. Centroid of polygon used for lat/lon. |
| Colorado | co | CPW Fishing Atlas ArcGIS MapServer (Fishing locations) | API | Water bodies only (streams filtered out); county + elevation present; **no species list** exposed (only a stocking category, kept in `description`). |
| Utah | ut | UDWR Fish Stocking Events ArcGIS FeatureServer (lakes layer + species table) | API | Lakes only; species joined from related stocking table by water id; no county/elevation/area. |
| Nevada | nv | NDOW Fishable Waters ArcGIS FeatureServer (lakes layer) | API | Lakes/reservoirs only; species decoded from FISH1..FISH11 abbreviation codes (a few uncommon codes may pass through unmapped); county present; no elevation/area. |
| Arizona | az | AZGFD "Fish & Boat AZ" fishing-waters layer (`NEW_fishingWaters`, reached anonymously via AGOL's service proxy) | API | Still waters only (Lakes & Ponds + Community Fishing Waters; rivers/creeks/canals dropped); species from per-species Yes/No columns; acreage parsed from the description prose; no county/elevation. |
| New Mexico | nm | NMDGF Fishing Waters Map (ArcGIS layer 5) | API | Standing waters (streams dropped), deduped; species decoded from the layer's coded-value domain (~269/270). No county/elevation/area. |
| Texas | tx | TWDB Texas Reservoirs (ArcGIS) + TPWD lake pages (species) | API + HTML | Reservoir names/centroids; species scraped from TPWD "predominant fish species" pages, joined by name (~133/211 matched). |
| Minnesota | mn | MN DNR surveyed lakes (ArcGIS) + DNR LakeFinder API (species) | API | Name, county, acreage; per-lake species enriched from LakeFinder by DOW id. |
| Wisconsin | wi | WDNR 24k Hydro Waterbodies (ArcGIS) + WDNR stocking API (species) | API | Named lakes + acreage; species from the stocking API joined by name — **stocked species only** (no naturally-reproducing bass/panfish). |
| Michigan | mi | MI DNR IFR Lake Deep Points + DNR Fish Atlas (species) | API | Inland lakes with county + coords; species attached from Fish Atlas by a coordinate grid (best-effort; ~40% of lakes matched). |
| New York | ny | NYSDEC Recommended Fishing Lakes & Ponds (data.ny.gov Socrata) | API | Curated ~320 waters with species, county, acreage, coordinates. Not exhaustive. |
| Pennsylvania | pa | PFBC lakes via PASDA (ArcGIS) + companion species layers | API | County + acreage; species joined from PFBC warm/coolwater + trout layers by GIS_Key (~271/465). No elevation. |
| Georgia | ga | GADNR WRD Waterbodies + Reservoir Prospects (ArcGIS) | API | Named reservoirs with area; species from the Prospects table by WATER_CODE (~30 major reservoirs incl. bass/crappie/catfish). No county/elevation. |
| Illinois | il | IDNR Lake Depth & Capacity + iFishIllinois stocking | API | ~43 bathymetry lakes with area/elevation; species from iFishIllinois stocking by name (~8, stocked). No county. |
| Indiana | in | IDNR Fish Access sites (ArcGIS, IndianaMap) | API | Access sites deduped per waterbody; free-text species + county present; no area/elevation. |
| Kentucky | ky | KDFWR Fishing Access Sites + waterbody pages | API + HTML | Waterbodies deduped; species scraped from KDFWR detail pages by WID (~86/125). No county/area. |
| Missouri | mo | MDC Fishing Interactive Map (ArcGIS) | API | MDC-managed waters with acreage; **no per-lake species source** (MDC exposes species only in JS report pages), so species are omitted. |
| Ohio | oh | ODNR DOW Lakes + per-species fishing layers (ArcGIS) | API | 321 lakes with acreage; species from DOW per-species layers by name (~35 profiled lakes). No county/elevation. |
| Tennessee | tn | TWRA access sites + TWRA reservoir pages | API + HTML | Access sites deduped; county present; species keyword-scraped from TWRA reservoir pages (~41 major reservoirs). No area/elevation. |
| Virginia | va | Virginia DWR Public Fishing Lakes (ArcGIS) + DWR waterbody pages (species) | API + HTML | Centroids; species as broad categories (Bass/Catfish/Trout/Panfish/Crappie) scraped from DWR lake pages (~82/193). No county/elevation. |
| Alabama | al | ADCNR Public Fishing Lakes + Outdoor Alabama pages | API + HTML | 20 state public fishing lakes; species keyword-scraped from each lake page. No county/area/elevation. |
| Arkansas | ar | AGFC WaterBodyList + Family/Community Fishing (ArcGIS) | API | Lake-like waters with acreage; species only for ~27 community ponds (catfish/trout); broader per-water species not machine-queryable. |
| Florida | fl | FWC LAKES_POINTS (ArcGIS) + FWC county Fish Ranges (species) | API | Named lakes with county; species are **county-level** fish ranges (FWC has no per-lake survey), so all lakes in a county share the list. |
| Iowa | ia | Iowa DNR fishing reports + Fish Iowa pages | API + HTML | Waterbodies with coords; species from Fish Iowa 'Popular Fish Species' pages by code (~519/1244). No county/area/elevation. |
| Kansas | ks | KDWP Fishing Atlas + Fishing Forecast table (ArcGIS) | API | Reservoirs/SFL/community lakes with acreage; species from the KDWP fishing-forecast table by name (~40). No county/elevation. |
| North Carolina | nc | NCWRC Public Fishing Areas (ArcGIS) + ncpaws species API | API | LAKE/POND deduped; county; species from NCWRC ncpaws JSON API by name (~128/148). No area/elevation. |
| Oklahoma | ok | OWRB Lakes of Oklahoma + ODWC where-to-fish | API + HTML | Lakes with area + elevation; species from ODWC 'species of interest' pages by name (~84/147). No county. |
| South Carolina | sc | SCDNR Public Water Access (ArcGIS) | API | Lakes/ponds deduped from access points; species (SpeciesList) + county present; no area/elevation. |
| Louisiana | la | LDWF Inland Waterbodies (ArcGIS) | API | Named lakes/reservoirs with popular species (free text) + parsed acreage; polygon centroids; no parish/elevation. |
| Nebraska | ne | NGPC Public Fishing Spots (ArcGIS) | API | Precomputed centroids, county, species (comma list) and acreage. |
| North Dakota | nd | NDGF Fishing Waters (ArcGIS) | API | Rich: full species names, county, acreage and current elevation. |
| South Dakota | sd | SDGFP Urban Community Fisheries (ArcGIS) | API | Only the urban/community subset (~76); species, county, acreage, outlet elevation. No statewide public API. |
| West Virginia | wv | WVDNR Public Fishing Lakes (WV GIS Tech Center) | API | Species from nine presence-flag columns; county + acreage; polygon centroids; no elevation. |
| Maine | me | Maine GIS PublicMasterWaters + MDIFW Heritage Fish Waters (ArcGIS) | API | 5,781 lentic waters with acreage; species for ~597 heritage/managed waters (wild brook trout/charr, stocked trout/salmon) via MIDAS join. Broader species not machine-queryable. |
| Vermont | vt | Vermont ANR Fishing Access Areas (ArcGIS) | API | Access-area points with species (presence flags), county and acreage; no elevation. |
| Connecticut | ct | CT DEEP Stocked Lakes (ArcGIS) | API | 111 trout-stocked lakes (species = Trout); county present; centroids; no area/elevation. |
| Delaware | de | DNREC Public Ponds (ArcGIS FirstMap) | API | ~40 ponds merged from two layers; small ponds carry species flags; county + area on major ponds; no elevation. |
| Maryland | md | MD iMAP Lakes + DNR Angler Access (ArcGIS) | API | Named lakes with county + acreage; species from the Angler Access FishTypes list by name (~30). No elevation. |
| Massachusetts | ma | MassGIS Water Features + MassWildlife trout stocking (ArcGIS) | API | 2,267 named lakes/ponds with acreage; trout-stocked waters flagged Trout via PALIS (~240). Broader species live only in per-pond PDFs (not parsed). |
| New Hampshire | nh | NH GRANIT NHD waterbodies (ArcGIS) | API | Named lakes/ponds with acreage + sparse elevation; species deferred (NHFG survey layer uses ~150 uncoded columns, no public legend). No county. |
| New Jersey | nj | NJDEP Trout Stocked Lakes (ArcGIS, NJGIN) | API | 86 trout-stocked lakes (species = Trout) with acreage; no county/elevation. |
| Rhode Island | ri | RIGIS Lakes and Ponds 24K (ArcGIS) | API | 3,160 named waterbodies with acreage; trout-stocked ones tagged Trout; no county/elevation. |

## No usable source found (documented gaps)

These states were researched but no machine-queryable public source was located.
They are intentionally not registered in `SCRAPERS`; revisit if a source appears.

| State | Code | What was tried |
|-------|------|----------------|
| Mississippi | ms | MDWFP ArcGIS (`arcgis2.mdwfp.com`) is the likely home of the ~18 state fishing lakes + species, but it is unreachable here (incomplete TLS chain + a WAF that drops non-browser requests); state hydrography layers carry no names/species. Revisit from a browser to locate the Fisheries lakes layer. |
