# Geo report: cooperative outlier map and officer visit plan

Owner: geo agent. Last rebuilt Sat 3 Oct 2026, evening. Sentinel-2 works, so NDVI is in (no 02:00 cut needed).

## What it is for
The officer reaches the sub-county twice a year at best. The cooperative already holds a delivery record per member. This map answers one question: **which plots should the officer's limited visits go to, and why?** It combines up to three independent signals, says plainly where the data is too thin to judge, and orders one visit day into a short route. It points the visits. It decides nothing.

Where it meets the leaf check: Noor's plot (OCC0412-2) is flagged by satellite and deliveries, and her own leaf-check referral (`JANI1 M:OCC0412 P:2 ... R:6 ...`) lands on the same plot. Three independent signals, one plot.

## Real and synthetic
| Part | Real or synthetic | Source |
|---|---|---|
| Land under plots, dry-season NDVI 2023 to 2026, wet-season NDVI 2025 | Real | Sentinel-2 L2A, Earth Search STAC, tile 37MBV |
| Rainfall, rain onset, wetness of each NDVI window | Real (model grid) | NASA POWER `PRECTOTCORR`, point 37.07 E, 0.46 S |
| Area | Real place | Mathira West, Nyeri County, 37.05 to 37.09 E, 0.44 to 0.48 S (about 4.4 x 4.4 km) |
| Members, plot polygons, tree counts, deliveries | **Synthetic**, seed 20261004 | `app/geo/make_plots.py` |
| 18 seed leaf-check referrals | **Synthetic** | `app/geo/visit_plan.py` |
| Yield baseline 3.0 kg cherry per tree | Cited | MOALF 2014 via Mugendi et al. 2015, Nyeri, 2013/14 |
| 1,300 trees per ha | Cited | Coffee Directorate, Coffee Year Book 2022/23 |
| Cooperative factor per year (0.85, 1.05, 1.00, 0.85), 15% delivery noise | **Assumption** | Loosely follows the real rainfall pattern |
| Visit capacity (8 plots a day), road factor 1.4, priority weights, office location | **Assumption** | No real visit data exists |

Plots are placed only on land that looks perennial: dry-season NDVI 0.55 to 0.88 in the prior years, wet-season NDVI at least 0.60, and under 0.15 NDVI between the 2025 dry and wet composites (coffee is evergreen; annual crops swing). This removes 12% of pixels. It is a plausibility filter, not a coffee map. We do not know that coffee grows inside any polygon.

Noor's drop (deliveries x0.40, no noise) is scripted so the demo story is stable. Every other plot follows its random draw.

## What the real data says
**NDVI.** Dry-season medians over the area: 0.52 (2023), 0.71 (2024), 0.69 (2025), 0.65 (2026), from 12, 13, 15 and 15 scenes. Wet-season 2025: 0.69 from 22 scenes.

**Rain onset (NASA POWER, simplified rule, assumption).** Onset is the first day from 15 Sep (short rains) or 1 Mar (long rains) with 3 days totalling 20 mm or more and no dry run over 7 days in the next 21.
| | Median onset 1991 to 2020 | Spread (sd) | Earliest to latest |
|---|---|---|---|
| Short rains | 19 Oct | 17 days | 17 Sep to 8 Dec |
| Long rains | 21 Mar | 15 days | 1 Mar to 22 Apr |

Share of years with short-rains onset by date: 13% by 1 Oct, 47% by 15 Oct, 87% by 31 Oct, 97% by 15 Nov. Recent onsets: 25 Sep 2019, 22 Sep 2020, 18 Oct 2021, 29 Oct 2022, 4 Oct 2023, 4 Nov 2024, 2 Oct 2025.

**This year.** NASA POWER ends 30 Sep 2026. September rain was 68 mm against a 57 mm mean (z +0.5), 6.7 mm in the last 7 days. Short-rains onset is not confirmed yet.

**Why this matters for the decision.** The master prompt says copper sprays start in mid October, before the short rains. That fits the median onset (19 Oct), but in about half of years the rains are already under way by 15 Oct. A fixed calendar window is right about half the time. See requests in `kb/STATUS.md`.

**Wetness of the NDVI windows.** The "dry season" window (1 Jan to 15 Mar) was not equally dry each year:
| Window | Rain (mm) | Mean (mm) | z |
|---|---|---|---|
| 2023 | 89 | 137 | -0.5 |
| 2024 | 324 | 137 | +2.0 |
| 2025 | 138 | 137 | 0.0 |
| 2026 (current) | 396 | 137 | +2.8 |

The current window was far wetter than normal. Plots are scored against nearby plots, which cancels most area-wide effects, but small canopy changes should be read with care. This is exposed in `outliers.json` as `context.ndviWindowRain`.

## Cross-checks against the research files
- **Rain onset.** `kb/research/season.json` (NASA POWER at 36.95 E, 0.42 S, its own onset method) gives a short-rains median of 16 Oct counting from 15 Sep (middle half of years 7 to 28 Oct) and a long-rains median of 20 Mar. Geo's rule at 37.07 E, 0.46 S gives 19 Oct and 21 Mar. Two methods and two grid points agree to within three days, so the spread (about two to three weeks between years) is a real feature of the data and not an artefact. `kb/research/raw/` also notes a KMSA forecast of onset in the second to third week of October for the coffee counties in 2026.
- **Yield level (E3).** Cooperatives delivered 414.7 kg/ha of clean coffee in 2023/24 and the national figure for 2024 is 435.7 kg/ha. The synthetic plots deliver a median of about 2,500 to 3,150 kg cherry per ha in the three prior seasons. At an assumed cherry-to-clean ratio of 6 to 1 (**assumption, not in the kb, officer to confirm**) that is about 410 to 525 kg/ha clean. Same range as the national figures. It is a sanity check on scale, not a validation: the synthetic baseline comes from the Nyeri per-tree figure, not from E3.
- **Do not claim a national decline.** E3 says Kenya's yield series is not a steady fall. The synthetic "decline" here is a planted plot-level scenario and a 13% cooperative-wide dip tied to the weak 2025 short rains. It illustrates the tool and says nothing about Kenya.

## Planted scenarios and results (synthetic, seed 20261004)
| Scenario | Count | What was planted | Result |
|---|---|---|---|
| `decline_with_canopy_loss` | 4 | Deliveries x0.45 on a real NDVI-loss patch | 4 `drop_with_canopy_loss` or equivalent outlier |
| `delivery_gap_canopy_ok` | 4 | Deliveries x0.40, stable real NDVI | 3 outlier; 1 `unsure` (real canopy z -1.7 is unclear, so the model declined to call it) |
| `over_delivery` | 2 | Deliveries x2.3 | 2 outlier |
| `canopy_loss_early` | 2 | Normal deliveries on a real NDVI-loss patch | 2 `canopy_loss` |
| `new_member`, `tiny_plot`, `missing_record` | 5 | Thin history, under 0.10 ha, no record | 5 `unsure` |
| `normal` | 63 | Nothing | 62 normal; 1 flagged `canopy_loss` |

78 of 80 plots got the expected status and reason. The one false flag (OCC0459-1) is a real satellite signal: its canopy fell (local z -3.3) while deliveries were normal. We did not plant that, but it is in the real data. The model is right to show it.

Cooperative median delivery change this season: -13.0% (context only, not held against any member). Noor: deliveries -58%, NDVI 0.83 to 0.36, delivery z -3.8, canopy z -13.8.

### Seed sweep (30 synthetic registries, real NDVI and rainfall fixed)
`app/geo/sweep.py`, output `app/geo/data/sweep.json`. One seed flatters a model, so the registry and noise were rebuilt 30 times.
| Measure | Mean | Worst seed |
|---|---|---|
| Plots with expected status and reason | 97.7% | 93.8% |
| Planted cases given the expected status | 92.2% | 70.6% |
| Normal plots flagged as outlier per seed (of 63) | 0.27 | 1 |

Of 1,890 normal plot-runs, 8 were flagged outlier: 7 `canopy_loss` on real NDVI falls and 1 from delivery noise. Weakest scenarios: `over_delivery` missed 17 of 60 times (28%) and `delivery_gap_canopy_ok` 23 of 120 (19%). A x2.3 jump is only about 3.4 robust z-scores against the cooperative's spread, so it sits near the threshold. We did not lower the threshold to win these back: it would add false flags on real, noisier records.

## Officer visit plan
`visit_plan.json` ranks every plot by priority points from three signals, groups them into tiers, and orders up to 8 tier A plots (one visit day, assumption) into a closed route from the cooperative office.
| Signal | Source | Points |
|---|---|---|
| Canopy fell much more than neighbours (z at most -3) | Real Sentinel-2 | 40 (25 if z at most -2) |
| Deliveries fell (z at most -3) | Synthetic record | 30 (15 if z at most -2) |
| Deliveries rose (z at least 3) | Synthetic record | 20 |
| Farmer sent a leaf check showing rust on 3 or more of 10 leaves | Synthetic referral | 40 |
| Farmer's check could not decide | Synthetic referral | 25 |
| Other problem referral | Synthetic referral | 25 |
| Data too thin, nothing else | Registry | 5 |

Tier A is 40 points or more (visit now), tier B is 20 to 39 (call the member or check records), tier C is below. Points are a transparent sum, not a probability. A plot with signals from several independent sources ranks above one with a single signal of the same size.

Result on the seed run: tier A 16, B 9, C 55. 18 plots have a linked referral. 9 plots have two or more independent signals. The 8-stop loop is 18.0 km against 28.1 km for the same stops in random order (straight-line times 1.4, not road routing).

**Does the ranking beat chance? (satellite and deliveries only, planted scenarios, synthetic).** Seed run: 7 of the top 8 are planted problems (88%), and all 6 planted canopy-loss plots are in the top 8. Chance is 15%. Over 30 seeds: 93% mean, 75% worst. Route saving against random order: 47% mean, 44% worst.

## What these numbers prove and do not prove
They show the rules do what they say on data built to test them, and that combining signals puts the planted problems first. They prove nothing about a real cooperative. The scenarios and noise are ours, so the hit rate mostly reflects how far the planted effects sit from the noise we chose. The priority weights are assumptions. They need real visit outcomes to tune, and until then the officer should treat the order as a starting point.

## Limits and what the data does not cover
- **No real delivery or visit data.** Thresholds and weights are set by reasoning. A real cooperative must check the false-flag rate on its own history first.
- **NDVI is not coffee health.** Loss can mean stumping or pruning (normal practice), felling, a new building, intercrop removal or disease. It cannot see leaf rust directly. That is the leaf check's job.
- **Shade trees and intercrops** mix into each 10 m pixel. A 0.15 ha plot is about 15 pixels, and fewer after the edge is excluded. Under 10 clear pixels the model abstains.
- **Regional gradient.** The north of the area shows a broad real NDVI decline in early 2026 (plot median change -0.003 in the south, -0.059 in the north). It is not cloud: clear-observation counts match north and south. Each plot is compared with its 12 nearest plots. We do not know the cause.
- **Wet "dry season" in 2026** (above). Four seasons are too few to model a rainfall adjustment.
- **One dry season per year.** January to mid March only. July to September is often overcast in the highlands.
- **Rainfall is one value for the whole area.** NASA POWER is about 0.5 x 0.625 degrees. It gives context, not per-plot cause. The onset rule is simplified and is not the Kenya Met Department definition. CHIRPS (about 5 km) would be the next step.
- **Registry quality.** Tree counts are the weakest number in any real registry. `above_plausible_yield` exists because a wrong tree count looks exactly like an outlier.
- **Side-selling.** `drop_canopy_normal` fits selling to a middleman, but also late picking, theft, illness or a record error. The officer asks; the map does not accuse.
- **Routing** is straight-line distance times a factor, not roads or terrain.

## Privacy
Member numbers only, no names. Plot polygons in a real deployment are personal data. They should stay on the cooperative's systems with member consent. The public demo uses synthetic polygons only. Seed referrals are fake members and fake checks.

## Files
- Code: `app/geo/` (`config.py`, `fetch_ndvi.py`, `fetch_rain.py`, `season.py`, `make_plots.py`, `outliers.py`, `visit_plan.py`, `validate.py`, `sweep.py`, `preview.py`, `run.sh`)
- Committed derived data: `app/geo/data/` (`rainfall.json`, `season_support.json`, `ndvi_scenes.json`, `registry.geojson`, `truth.json`, `eval.json`, `visit_eval.json`, `sweep.json`)
- Outputs: `app/public/geo/` (`plots.geojson`, `outliers.json`, `ndvi_change.png`, `visit_plan.json`, `referrals_seed.json`)
- Preview: `kb/geo/preview.png`
- Contract: `kb/geo/CONTRACT.md`
