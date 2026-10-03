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
| 3 | `make_plots.py` | `data/registry.geojson`, `data/truth.json` (synthetic) |
| 4 | `outliers.py` | `public/geo/plots.geojson`, `public/geo/outliers.json`, `public/geo/ndvi_change.png`, `data/eval.json` |

Steps 3 and 4 are deterministic (fixed seed) and run offline once the cache exists.

## Data

- **Sentinel-2 L2A**, Element 84 Earth Search STAC (AWS Open Data), tile 37MBV. One median composite per coffee year over the main dry season, 1 January to 15 March, 2023 to 2026. Pixels kept only where the Scene Classification Layer is 4 (vegetation) or 5 (not vegetated). 12 to 15 scenes per season. Copernicus Sentinel data terms.
- **NASA POWER** daily `PRECTOTCORR` at the area centre (37.07 E, 0.46 S), 1991 to September 2026. Anomalies against 1991 to 2020.
- **Yield baseline** for synthetic deliveries: Nyeri County average of about 3.0 kg cherry per tree (MOALF 2014, cited in Mugendi, Orero and Mwiti, Asian Journal of Business and Management 3(6), 2015, 2013/14 coffee year).
- **Tree density** for synthetic tree counts: 1,300 trees per ha for SL28 and SL34 (Coffee Directorate, Coffee Year Book 2022/23).

## Model

Robust z-scores, no machine learning. For each plot:

- Delivery score: log of this season's kg cherry per registered tree over the median of its prior seasons, scored against the cooperative median and MAD.
- Canopy score: plot median NDVI this dry season minus the median of prior dry seasons, scored the same way.

Peer-relative scores cancel area-wide effects such as a dry year. Reason codes, abstention rules and the output format are in `kb/geo/CONTRACT.md`. Results and limits are in `kb/geo/REPORT.md`.

## Gotcha

Earth Search pixels already have the Sentinel-2 `BOA_ADD_OFFSET` removed, but some 2025 items still say `earthsearch:boa_offset_applied: false` with `offset: -0.1`. Applying that offset sends red reflectance negative and NDVI to about 1. `fetch_ndvi.py` applies the offset only if the darkest clear red pixels are at or above 1,000 DN. None were in this build.
