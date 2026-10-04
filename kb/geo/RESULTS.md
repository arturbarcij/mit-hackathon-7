# Geo layer: results

Status (Sun 4 Oct, about 00:15 CEST): **offline outputs done, live run pending on Windows.** The files in `app/public/geo/` use **synthetic NDVI and synthetic rainfall** until Arthur runs `app/geo/RUN_ON_WINDOWS.md`. Deliveries, plot shapes, plot locations and member ids are synthetic in every mode. This demonstrates the method; it is not a field result.

## What is real and what is synthetic
| Layer | Offline build (now) | Live build (Windows) |
|---|---|---|
| Area | Real place, approximate choice: 6 x 6 km box south-east of Othaya town, Nyeri County. Centre -0.555, 36.975. Bbox [36.94805, -0.58213, 37.00195, -0.52787] (w, s, e, n). Chosen by hand from general knowledge of the Othaya coffee belt, not checked against a land-cover map. Othaya town centre (about -0.547, 36.943) lies just west of the box. | Same |
| Plot locations and shapes | Synthetic. 40 plots of 0.5 to 2.5 ha, 5 to 7 vertex polygons, in five clusters (one per notional coffee factory catchment) | Synthetic, but placed only where the median Jul to Sep NDVI is at least 0.5 (vegetated pixels) |
| Member ids | Synthetic. P01 to P12 use the fixed ids that the officer dashboard referral seed already uses (P07 = OCC0412, Noor) | Same |
| Deliveries (kg cherry per member per season, 2021/22 to 2025/26) | Synthetic, from the KNBS co-operative yield 414.7 kg/ha clean coffee (2023/24, EVIDENCE E3) times a cherry-to-clean ratio of 6.0 (assumption, not verified for Nyeri; officer to confirm), plot factor (log-normal, sd 0.25) and season noise (sd 0.07) | Same |
| NDVI | **Synthetic** (`"ndvi_source":"synthetic"`, `"synthetic_ndvi":true` per plot) | Real: Sentinel-2 L2A from Earth Search, SCL cloud mask, dry-season composites Jan to Feb and Jul to Sep, 2022 to 2026 |
| Rainfall | **Synthetic** (`"rainfall":{"synthetic":true}`), 2025/26 anomaly set to -24% | Real: NASA POWER daily PRECTOTCORR at the box centre, season Oct to Sep vs the 1991 to 2020 mean of the same calendar days |

Note: kb/agents/geo.md suggested a box near (-0.42, 36.95), and kb/research/season.json uses that point. The lead moved the box to the Othaya coffee area. The rainfall point for the map is now (-0.555, 36.975).

## Method (as kb/agents/geo.md)
1. `own_change` = 2025/26 delivery vs the plot's own median of earlier seasons.
2. `peer_change` = median `own_change` of the 8 nearest plots within 2 km that have at least 3 seasons.
3. `gap = own_change - peer_change`, robust z across plots (median and 1.4826 x MAD).
4. `ndvi_change` = latest Jul to Sep 2026 composite minus the plot's own median of Jul to Sep 2022 to 2025. `ndvi_z` = robust z of (`ndvi_change` minus the peers' median `ndvi_change`), so an area-wide browning does not count against one farm.
5. Reason code, first match wins: `not_enough_data` (fewer than 3 seasons or fewer than 5 peers), `area_wide_weather` (peer change below -15% and rainfall anomaly below -20%), `drop_check_leaves_or_ask` (gap z below -2 and no NDVI), `canopy_loss_check_leaves` (gap z below -2 and NDVI z below -1.5), `drop_other_cause_ask_officer` (gap z below -2, NDVI normal), otherwise `in_line_with_peers`.
6. Confidence `low` when the latest composite has fewer than 6 clear observations, when gap z is within 0.3 of -2, or when NDVI z is within 0.3 of -1.5 and the gap is past (or within 0.3 of) its threshold. `not_enough_data` is always low. With no NDVI layer at all, the clear-observation rule is not applied.
All thresholds are in `outliers.json` under `assumptions` with "officer to confirm".

Planted scenarios: canopy loss on P07, P05, P11, P15 (2025/26 delivery x 0.55 and Jul to Sep 2026 NDVI -0.12); delivery drop with normal NDVI on P04, P20 (x 0.57); new members with two seasons on P30, P31, P32; a corner cluster P33 to P38 whose deliveries all fell (x 0.68); an area-wide dip in 2022/23 (East African drought) on about 85% of plots. P15 has no referral yet: the officer should nudge her.

## Scenario sanity check (offline build, seed 7)
Command: `python3 app/geo/build_geo.py --mode offline` then `python3 app/geo/validate.py --markdown` (run on the Cowork VM, Python 3.10, PASS).

Reason counts: canopy_loss_check_leaves 4, drop_other_cause_ask_officer 2, area_wide_weather 6, not_enough_data 3, in_line_with_peers 25, drop_check_leaves_or_ask 0.

| Plot | Member | Planted | Got | Own change % | Peer change % | Gap z | NDVI change | NDVI z | Clear obs | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| P07 | OCC0412 | canopy loss | canopy_loss_check_leaves | -47.2 | 5.1 | -4.41 | -0.141 | -4.14 | 9 | high |
| P05 | OCC0642 | canopy loss | canopy_loss_check_leaves | -49.5 | 2.6 | -4.39 | -0.134 | -4.48 | 10 | high |
| P11 | OCC1004 | canopy loss | canopy_loss_check_leaves | -53.0 | -2.2 | -4.29 | -0.126 | -3.56 | 12 | high |
| P15 | OCC1655 | canopy loss | canopy_loss_check_leaves | -34.2 | 3.2 | -3.18 | -0.109 | -3.36 | 9 | high |
| P04 | OCC0521 | other cause | drop_other_cause_ask_officer | -47.2 | -0.3 | -3.97 | 0.011 | 0.37 | 7 | high |
| P20 | OCC1840 | other cause | drop_other_cause_ask_officer | -43.3 | 3.2 | -3.93 | -0.022 | -0.69 | 7 | high |
| P30 to P32 | | two seasons only | not_enough_data | | | | | | | low |
| P33 to P38 | | cluster all dropped | area_wide_weather | -20 to -45 | -35 to -37 | -0.93 to 1.27 | | | | high |

All 15 planted plots get the intended code. None of the 25 unplanted plots is flagged. Three unplanted plots (P16, P25, P29) show "low" confidence because their synthetic latest composite has 3 to 5 clear observations; they stay green. The 2022/23 dip is visible in the deliveries (median plot about 30% below its other seasons) and is not flagged, because the model only looks at the latest season.

Sensitivity, said plainly: across 40 random seeds, 37 put every planted plot on its intended code; in 3 seeds one planted plot moved to the neighbouring code (other cause read as canopy loss, or the reverse), because synthetic NDVI noise crossed the -1.5 threshold. In 3 seeds one or two unplanted plots were flagged amber. We ship seed 7. This is a check that the code does what it says on data built to test it, not evidence that it finds real problems.

## Limits
- 10 m pixels on 1 to 2 ha plots: a 1 ha plot is about 100 pixels, and Nyeri coffee is often under shade trees (grevillea, banana), so NDVI mixes coffee canopy, shade canopy and paths. Small canopy changes are noise.
- Clouds: the long and short rains are too cloudy, so only Jan to Feb and Jul to Sep are used; even then some composites have few clear dates. Fewer than 6 clear observations makes the plot "not sure".
- NDVI cannot tell coffee leaf rust from drought stress, pruning, stumping, or shade-tree removal. That is why the map only says "check leaves"; the phone leaf check decides what it is and the officer decides what to do.
- Rainfall is one NASA POWER point (about 0.5 degree grid) for the whole box. It cannot see rain differences between hill and valley farms. The weather rule leans on peers having dropped, not on rain alone.
- In live mode the planted canopy-loss plots are placed where real NDVI fell most, and their delivery drops are synthetic. The live map shows real satellite change under synthetic farms.
- Deliveries are not production: side-selling to middlemen, theft and late picking all lower a member's cooperative deliveries without any change on the farm (agronomist F18). The amber code says "ask the officer" for that reason.
- Biennial bearing: Arabica alternates heavier and lighter years. `own_change` uses the median of all four earlier seasons, which spans both, rather than last season alone; a farm on a different cycle from its neighbours can still look low in an off year (agronomist F19, mathematician).
- Pruning and stumping happen after harvest, around Jan to Feb, so the NDVI change uses Jul to Sep composites only; Jan to Feb is computed but not used for the decision. The reason note for red says "can be leaf rust, drought stress, pruning or stumping" (agronomist F16).
- Gap, not fixed: when nearby farms all dropped but rain was normal (for example a coffee berry disease year or input cuts), the model says `in_line_with_peers`, because the question it answers is "is it me or everyone". The green reason note tells the officer to ask in that case. A separate code (`area_wide_other_ask_officer`, agronomist F17) would need a UI change, so it waits until after the freeze.
- Peer comparisons need neighbours: an isolated farm with fewer than 5 peers in 2 km is always grey.
- Earth Search reflectance offset (processing baseline 04.00): the script decides per scene from the data whether the +1000 DN offset is still present (1st percentile of clear red DN at least 900). Untested against the live service from here.

## Live run
Not yet run. Command for Arthur (Windows, conda env `jani`): `python app\geo\build_geo.py --mode live` then `python app\geo\validate.py`. Cut line 02:00 CEST: if Sentinel-2 fails, `--skip-s2` ships real rainfall only and reasons fall back to `drop_check_leaves_or_ask`; then write "satellite layer: next step" here. After the live run, replace this section with the real counts, the rainfall anomaly, and the validate table.

## Files
- `app/geo/build_geo.py` (entry point), `geo_core.py` (model, synthetic data, numpy only), `geo_live.py` (NASA POWER, STAC, rasterio), `validate.py`, `tests/test_geo.py` (30 tests, no network; one needs rasterio), `requirements.txt`, `RUN_ON_WINDOWS.md`.
- `app/public/geo/area.json`, `plots.geojson` (about 14 KB), `outliers.json` (about 47 KB, includes `reason_notes` per code).
- Cache: `app/geo/cache/` (git-ignored).
