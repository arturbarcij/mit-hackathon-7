# Agent: geo

You are the geo agent for Jani. Read `kb/MASTER_PROMPT.md` first (section 3.4 explains why this layer exists). It wins over this file.

## Mission
Build the cooperative's **outlier map**: which member farms produced much less than similar farms nearby this season, and the most likely reason. It answers Noor's question from Annex B, "my yields slipped and I am not sure why", with a first step anyone can trust: **is it me, or is it everyone?**

The map never diagnoses a disease. It decides **where to look**. The phone leaf check decides **what it is**. The extension officer decides **what to do**.

## Where you run
Cursor on Arthur's Windows laptop (it has internet; the cloud session does not). Python, conda env `jani` (shared with ml) or a new `geo` env:
`pip install pystac-client odc-stac rasterio shapely geopandas numpy pandas scikit-learn requests`

## You own (only you edit these)
- `app/geo/**` (scripts, notebooks, cached data under `app/geo/cache/` which is git-ignored)
- `app/public/geo/plots.geojson`, `app/public/geo/outliers.json`, `app/public/geo/area.json`
- `kb/geo/` (notes)

## Inputs and honesty rules
| Layer | Real or synthetic | Source |
|---|---|---|
| Area | Real | A coffee area in Nyeri county near (-0.42, 36.95), bbox about 6 x 6 km. State exact coordinates. |
| Plot locations and shapes | **Synthetic, labelled** | 40 plots of 0.5 to 2.5 ha placed on real cropland inside the bbox (use ESA WorldCover cropland or tree-cover pixels if quick, otherwise a jittered grid). Cooperatives hold real plot locations; we do not. |
| Satellite greenness | **Real** | Sentinel-2 L2A from Earth Search STAC (`https://earth-search.aws.element84.com/v1`, collection `sentinel-2-l2a`), cloud-masked with SCL, NDVI per plot per season (dry-season composites: Jan to Feb, Jul to Sep; the rainy seasons are too cloudy). 2022 to 2026. |
| Rainfall | **Real** | NASA POWER monthly precipitation for the bbox centre (no key needed; `kb/research/season_method.py` already calls it) or CHIRPS. Seasonal anomaly vs 1991 to 2020. |
| Deliveries (kg cherry per member per season) | **Synthetic, labelled** | Generated per plot for seasons 2021/22 to 2025/26. Base yield from KNBS cooperative average 414.7 kg/ha clean coffee (kb/research/EVIDENCE.md E3) converted with a stated cherry-to-clean ratio (cite or label assumption). Plant scenarios: (a) area-wide dip in the driest season, (b) 4 plots with a sharp drop AND an NDVI drop (canopy loss, rust-like), (c) 2 plots with a drop but normal NDVI (non-leaf cause: old trees, side-selling, labour), (d) 3 plots with too little history. Kenyan cooperatives record every delivery per member; this is the existing registry the brief says is the binding constraint. |

Every synthetic record has `"synthetic": true`. The map legend says so.

## The outlier model (small, explainable, runs on a laptop at the cooperative office)
For each plot and the latest season:
1. `own_change` = latest yield vs the plot's own median of previous seasons.
2. `peer_change` = median `own_change` of the 8 nearest plots (within 2 km).
3. `gap` = `own_change - peer_change`, robust z-score across plots (median and MAD).
4. `ndvi_change` = latest dry-season NDVI vs the plot's own median; robust z vs peers.
5. Reason code, first match wins:
   - fewer than 3 seasons or fewer than 5 peers: `not_enough_data` (grey) 
   - `peer_change` below -15% and rainfall anomaly below -20%: `area_wide_weather` (everyone dropped, weather likely)
   - `gap` z below -2 and NDVI z below -1.5: `canopy_loss_check_leaves` (red: suggest a leaf check)
   - `gap` z below -2 and NDVI normal: `drop_other_cause_ask_officer` (amber: not a leaf problem as far as we can see)
   - otherwise: `in_line_with_peers` (green)
6. Confidence: `low` when the plot has fewer than 6 clear Sentinel-2 observations in the composite, or the z-scores are near the thresholds (within 0.3). Low confidence always shows as "not sure".
Thresholds are assumptions; write them in `outliers.json` under `"assumptions"` with `"officer to confirm"`.

Also report how well the model finds the planted scenarios (it should; this is a sanity check, not evidence). Say clearly in `kb/geo/RESULTS.md` that the delivery data are synthetic, so this demonstrates the method, not a field result.

## Outputs (contract, read by the ui agent)
`app/public/geo/plots.geojson`: FeatureCollection; each feature has `plot_id`, `member_id` (e.g. `OCC0412`), `area_ha`, `synthetic: true`.
`app/public/geo/outliers.json`:
```json
{
  "generated": "2026-10-04T03:00:00Z",
  "season": "2025/26",
  "area": {"name": "Nyeri reference area", "bbox": [36.92, -0.45, 36.98, -0.39]},
  "rainfall": {"season_anomaly_pct": -12.0, "source": "NASA POWER", "synthetic": false},
  "assumptions": [{"name": "gap_z_threshold", "value": -2, "note": "officer to confirm"}],
  "plots": [
    {"plot_id": "P07", "member_id": "OCC0412", "own_change_pct": -38, "peer_change_pct": -6,
     "gap_z": -2.9, "ndvi_change": -0.11, "ndvi_z": -2.1, "clear_obs": 9,
     "reason": "canopy_loss_check_leaves", "confidence": "high",
     "sms_nudge_id": "nudge_leaf_check", "synthetic_deliveries": true}
  ],
  "sources": ["Sentinel-2 L2A via Earth Search (Copernicus data)", "NASA POWER", "KNBS 2025 Table 5.1.2"]
}
```
Also `app/public/geo/thumbs/<plot_id>.png`: small true-colour Sentinel-2 crops for flagged plots (optional, Tier 2).

## Tasks and times (CEST)
1. 23:00 to 23:45: environment, bbox, synthetic plots, STAC search returns items.
2. 23:45 to 01:15: NDVI per plot per dry-season composite, cached.
3. 01:15 to 01:45: rainfall anomaly, synthetic deliveries, outlier model, outputs.
4. **Cut line 02:00**: if Sentinel-2 is not working, ship deliveries plus rainfall only, set `ndvi_*` to null, reason codes fall back to `drop_check_leaves_or_ask` (amber), and write "satellite layer: next step" in RESULTS.md. Do not lose sleep on it.
5. Sun 08:00: hand outputs to ui; check the map renders.

## Rules
- Never present synthetic deliveries as real. Never name a farmer. Member IDs are fake.
- Copernicus Sentinel data attribution in the map footer.
- No em dashes. Plain British English.
- Update `kb/STATUS.md` rows G1 to G4.

## Done when
- `plots.geojson` and `outliers.json` validate against the contract and the planted scenarios are flagged with the right reason codes.
- `kb/geo/RESULTS.md` states what is real, what is synthetic, and the limits: 10 m pixels on 1 to 2 ha shaded plots are noisy; clouds limit observations; NDVI cannot tell rust from drought or pruning, which is why the map only says "check leaves".
