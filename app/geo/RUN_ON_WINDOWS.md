# Geo layer: live run on Windows

The cloud session and the Cowork VM cannot reach Earth Search or NASA POWER. Arthur's Windows laptop can. This run replaces the synthetic NDVI and rainfall in `app/public/geo/` with real data. Deliveries and plot shapes stay synthetic.

## 1. Set up (once, about 2 minutes)
Open "Anaconda Prompt" (or PowerShell with conda) in the repo root:

```
cd C:\Users\artur\Documents\MIT_Hackathon_7
conda activate jani
python -m pip install -r app\geo\requirements.txt
```

If `pip install rasterio` fails, use conda-forge instead:

```
conda install -c conda-forge rasterio requests numpy -y
```

Quick network check (both should print 200):

```
python -c "import requests;print(requests.get('https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a',timeout=30).status_code)"
python -c "import requests;print(requests.get('https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR&community=AG&longitude=36.975&latitude=-0.555&start=20260101&end=20260110&format=JSON',timeout=60).status_code)"
```

## 2. Run (one command)

```
python app\geo\build_geo.py --mode live
python app\geo\validate.py
```

Expected runtime: 10 to 40 minutes, almost all of it Sentinel-2 downloads. The script reads only the 6 x 6 km window of each scene (red, nir, scl), up to 10 dates per dry-season composite, 10 composites (Jan to Feb and Jul to Sep, 2022 to 2026), one or two MGRS tiles per date. That is roughly 100 to 200 scene windows, about 1 GB in total. NASA POWER takes under a minute. Everything is cached in `app\geo\cache\` (git-ignored), so a second run takes about a minute.

Slow connection: `python app\geo\build_geo.py --mode live --max-dates 6` (fewer dates per composite, so more plots end up "not sure" because of fewer than 6 clear observations).

## 3. What success looks like
- The log ends with `reason counts: {...}` and three `wrote ...` lines.
- `validate.py` prints `RESULT: PASS`. WARN lines are fine: with real NDVI a planted plot can land on a neighbouring code. That is the honest result; do not tune it away.
- `outliers.json` has `"ndvi_source":"sentinel-2"` and `"rainfall":{"synthetic":false,...}`.
- Blue (`area_wide_weather`) appears only if the real 2025/26 rainfall anomaly is below -20%. If rain was near normal, the corner cluster shows green. That is correct.

Then commit the three files (owner: geo):

```
git pull
git add app/public/geo/area.json app/public/geo/plots.geojson app/public/geo/outliers.json
git commit -m "geo: live outputs (Sentinel-2 NDVI, NASA POWER rainfall)"
git push
```

## 4. If Sentinel-2 fails (cut line 02:00 CEST)
If the Sentinel-2 step errors, hangs, or is not finished by 02:00, stop it (Ctrl+C) and ship rainfall only:

```
python app\geo\build_geo.py --mode live --skip-s2
python app\geo\validate.py
```

This writes `"ndvi_source":"unavailable"`, sets every NDVI field to null, and the red and amber plots become `drop_check_leaves_or_ask` (amber: "check leaves or ask the officer"). Write "satellite layer: next step" in kb/geo/RESULTS.md. If the build crashes inside Sentinel-2 it already falls back to this by itself.

If NASA POWER also fails, keep the offline files that are already in the repo (synthetic NDVI and rainfall, labelled synthetic). Do not hand-edit numbers.

## 5. Known failure modes
| Symptom | Fix |
|---|---|
| `CURL error: SSL certificate problem` | `python -m pip install certifi`, then `set CURL_CA_BUNDLE=` followed by the path that `python -c "import certifi;print(certifi.where())"` prints, and run again |
| `HTTP 429` or timeouts from Earth Search | run again; finished scenes are cached. Or add `--workers 3` |
| POWER `422` | the script already retries with an earlier end date; if it still fails, use `--skip-rain` and say so |
| Many plots "low" confidence | cloudy composites; try `--max-dates 14` |

## 6. Honest placement in live mode
Plots are synthetic shapes. In live mode they are placed only where the median Jul to Sep NDVI is at least 0.5 (vegetated pixels). The four planted canopy-loss plots (P07, P05, P11, P15) are then put on the plot positions where the real NDVI change, relative to neighbours, is most negative; the two other-cause plots (P04, P20) where it is closest to zero. Their delivery drops are synthetic. So the live map shows real satellite change under synthetic farms: it demonstrates the method, it is not evidence that it works.
