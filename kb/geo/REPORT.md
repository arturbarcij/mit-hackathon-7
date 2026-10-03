# Geo report: cooperative outlier map

Built Sat 3 Oct 2026, about 23:00 CEST, by the geo agent. Sentinel-2 works, so NDVI is in (no cut at 02:00 needed).

## What it is for
The officer comes twice a year. The cooperative already holds a delivery record per member. This map shows which plots fell or rose much more than their neighbours this season, adds a satellite canopy check, and says plainly where the data is too thin to judge. It points the officer's visits; it does not decide anything.

Where this sits next to the leaf check: Noor's plot (OCC0412-2) is flagged `drop_with_canopy_loss`, so the officer has a reason to visit before the short rains, and her own leaf check referral (`JANI1 M:OCC0412 P:2 ...`) lands on the same plot.

## Real and synthetic
| Part | Real or synthetic | Source |
|---|---|---|
| Land under plots, NDVI per season | Real | Sentinel-2 L2A, Earth Search STAC, tile 37MBV |
| Rainfall per season | Real | NASA POWER `PRECTOTCORR`, point 37.07 E, 0.46 S |
| Area | Real place | Mathira West, Nyeri County, 37.05 to 37.09 E, 0.44 to 0.48 S (about 4.4 x 4.4 km) |
| Members, plot polygons, tree counts, deliveries | **Synthetic**, seed 20261004 | `app/geo/make_plots.py` |
| Yield baseline 3.0 kg cherry per tree | Cited | MOALF 2014 via Mugendi et al. 2015, Nyeri, 2013/14 |
| 1,300 trees per ha | Cited | Coffee Directorate, Coffee Year Book 2022/23 |
| Year-to-year cooperative factor (0.85, 1.05, 1.00, 0.85), 15% delivery noise | **Assumption** | Loosely follows the real rainfall pattern |

Plots were placed only where the prior dry-season NDVI was 0.55 to 0.88 (woody, green in the dry season, not dense forest). We do not know that coffee grows inside any polygon.

## Real data found
Dry-season NDVI medians over the area: 0.52 (2023), 0.71 (2024), 0.69 (2025), 0.65 (2026). Scenes used per season: 12, 13, 15, 15.

Rainfall (NASA POWER, anomaly against 1991 to 2020):
| Coffee year | Short rains (Oct to Dec) | Long rains (Mar to May) |
|---|---|---|
| 2022/23 | -18% | +48% |
| 2023/24 | +85% | +123% |
| 2024/25 | +14% | +9% |
| 2025/26 | -13% | +18% |

The low 2023 NDVI follows the poor 2022 short rains. 2023/24 was very wet. This matches what we know of the 2022 drought and the 2024 floods, but we have not cross-checked against CHIRPS.

## Planted scenarios (synthetic) and results
| Scenario | Count | What was planted | Expected | Result |
|---|---|---|---|---|
| `decline_with_canopy_loss` | 4 | Deliveries x0.45, plot on a real NDVI-loss patch | `outlier`, `drop_with_canopy_loss` | 3 exact. 1 flagged `canopy_loss` (delivery z -2.95, just inside the threshold) |
| `delivery_gap_canopy_ok` | 4 | Deliveries x0.40, stable real NDVI | `outlier`, `drop_canopy_normal` | 3 caught. 1 missed (delivery z -2.67) |
| `over_delivery` | 2 | Deliveries x2.3 | `outlier`, `delivery_spike` | 2 caught |
| `canopy_loss_early` | 2 | Normal deliveries, real NDVI-loss patch | `outlier`, `canopy_loss` | 2 caught |
| `new_member` | 2 | One prior season only | `unsure` | 2 abstained |
| `tiny_plot` | 2 | 0.05 to 0.08 ha, deliveries x0.5 | `unsure` | 2 abstained |
| `missing_record` | 1 | No delivery this season | `unsure` | 1 abstained |
| `normal` | 63 | Nothing | `normal` | 63 normal, 0 false flags |

Overall: 78 of 80 plots got the expected status and reason. Cooperative median change this season: -12.5% (area-wide drop, flagged as context, not against any member).

**What these numbers prove:** the rules do what they say on data built to test them. **What they do not prove:** anything about a real cooperative. The scenarios and the noise were written by us, so the hit rate mostly reflects how far the planted effects sit from the noise we chose. The two misses are honest: a 55 to 60% fall can sit inside the threshold when a member's past seasons were noisy.

## Limits and what the data does not cover
- **No real delivery data.** Thresholds are set by reasoning, not tuned on real records. A real cooperative would need to check the false-flag rate on its own history first.
- **NDVI is not coffee health.** Loss can mean stumping or pruning (normal practice), felling, a new building, intercrop removal or disease. It cannot see leaf rust directly. That is the leaf check's job.
- **Shade trees and intercrops** mix into each 10 m pixel. Smallholder coffee plots of 0.15 ha are only about 15 pixels.
- **Regional gradient.** The north of the area shows a broad real NDVI decline in early 2026 (northern third, prior median 0.69 to 0.61) that is not plot-specific. Clear-observation counts are the same north and south (12 to 13), so it is not cloud. Peer scores use the whole area, so northern plots lean towards canopy flags. A local-neighbourhood baseline (for example 500 m) would fix this; not built.
- **One dry season per year.** January to mid March only. The July to September cool dry season is often overcast in the highlands and is not used.
- **Rainfall is one value for all plots.** NASA POWER is about 0.5 x 0.625 degrees. It gives context, not per-plot cause. CHIRPS (about 5 km) would be the next step.
- **Registry quality.** Tree counts are the weakest number in any real registry. `above_plausible_yield` exists because a wrong tree count looks exactly like an outlier.
- **Side-selling.** `drop_canopy_normal` is consistent with selling to a middleman, but also with late picking, theft, illness or a record error. The officer asks; the map does not accuse.

## Privacy
Member numbers only, no names. Plot polygons in a real deployment are personal data: they should stay on the cooperative's systems with member consent, and the public demo uses synthetic polygons only.

## Files
- Code: `app/geo/` (`config.py`, `fetch_ndvi.py`, `fetch_rain.py`, `make_plots.py`, `outliers.py`, `run.sh`)
- Committed derived data: `app/geo/data/` (`rainfall.json`, `ndvi_scenes.json`, `registry.geojson`, `truth.json`, `eval.json`)
- Outputs: `app/public/geo/` (`plots.geojson`, `outliers.json`, `ndvi_change.png`)
- Contract: `kb/geo/CONTRACT.md`
