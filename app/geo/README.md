# Geo: cooperative outlier map data

Builds the data behind the officer map: which member plots moved differently from the rest of the cooperative this season, why we think so, and where we are not sure.

**Synthetic:** members, plots, tree counts and deliveries.
**Real:** Sentinel-2 NDVI over the land under each plot, and NASA POWER rainfall.

## Run

```bash
pip install -r requirements.txt
./run.sh
```

| Step | Script | Output |
|---|---|---|
| 1 | `fetch_ndvi.py` | `cache/ndvi_<season>.tif` (git-ignored), `data/ndvi_scenes.json` |
| 2 | `fetch_rain.py` | `cache/power_daily.json` (git-ignored), `data/rainfall.json` |
| 2b | `season.py` | `data/season_support.json`: rain onset dates, season windows, wetness of each NDVI window |
| 3 | `make_plots.py` | `data/registry.geojson`, `data/truth.json` (synthetic) |
| 4 | `outliers.py` | `public/geo/plots.geojson`, `public/geo/outliers.json`, `public/geo/ndvi_change.png`, `data/eval.json` |
| 4b | `visit_plan.py` | `public/geo/visit_plan.json`, `public/geo/referrals_seed.json`, priority fields in `plots.geojson`, `data/visit_eval.json` |
| 5 | `validate.py` | Checks the outputs against `kb/geo/CONTRACT.md` (run by `run.sh`) |

Open `public/geo/map.html` through any static server (for example `python3 -m http.server` in `public/geo`) to see the officer map. `python3 -m pytest test_geo.py` runs the unit tests.

Optional: `sweep.py` scores the model over 30 seeds (`data/sweep.json`); `preview.py` draws `kb/geo/preview.png`.

Steps 3 and 4 are deterministic (fixed seed) and run offline once the cache exists.

Checks and review (offline):

| Script | What |
|---|---|
| `validate.py` | Checks outputs against `kb/geo/CONTRACT.md`; exits 1 on failure. Run by `run.sh`. |
| `sweep.py` | Rebuilds the synthetic registry for 30 seeds and scores the model: `data/sweep.json`. |
| `preview.py` | Static map for review: `kb/geo/preview.png`. |

## Data

- **Sentinel-2 L2A**, Element 84 Earth Search STAC (AWS Open Data), tile 37MBV. One median composite per coffee year over the main dry season, 1 January to 15 March, 2023 to 2026, plus a wet-season composite (1 April to 30 June 2025) used only to keep synthetic plots on perennial-looking land. Pixels kept only where the Scene Classification Layer is 4 (vegetation) or 5 (not vegetated). 12 to 15 scenes per season. Copernicus Sentinel data terms.
- **NASA POWER** daily `PRECTOTCORR` at the area centre (37.07 E, 0.46 S), 1991 to September 2026. Anomalies against 1991 to 2020.
- **Yield baseline** for synthetic deliveries: Nyeri County average of about 3.0 kg cherry per tree (MOALF 2014, cited in Mugendi, Orero and Mwiti, Asian Journal of Business and Management 3(6), 2015, 2013/14 coffee year).
- **Tree density** for synthetic tree counts: 1,300 trees per ha for SL28 and SL34 (Coffee Directorate, Coffee Year Book 2022/23).

## Model

Robust z-scores, no machine learning. For each plot:

- Delivery score: log of this season's kg cherry per registered tree over the median of its prior seasons, scored against the cooperative median and MAD.
- Canopy score: plot median NDVI this dry season minus the median of prior dry seasons, minus the median of that change over the 12 nearest plots, scored against the spread of those residuals.
- A moderate delivery drop (z -2) counts when the canopy loss is strong (z -3); otherwise the delivery threshold is z -3.

Peer-relative scores cancel area-wide effects such as a dry year. Reason codes, abstention rules and the output format are in `kb/geo/CONTRACT.md`. Results and limits are in `kb/geo/REPORT.md`.

## Gotcha

Earth Search pixels already have the Sentinel-2 `BOA_ADD_OFFSET` removed, but some 2025 items still say `earthsearch:boa_offset_applied: false` with `offset: -0.1`. Applying that offset sends red reflectance negative and NDVI to about 1. `fetch_ndvi.py` applies the offset only if the darkest clear red pixels are at or above 1,000 DN. None were in this build.
