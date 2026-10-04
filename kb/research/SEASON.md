# Season calendar for the reference area

Output: `kb/research/season.json`. Sources: `kb/research/_sources_season.json`. Same JSON shape as the engine placeholder (`app/src/engine/placeholders/season.json`), plus a `source` list the engine ignores.

## Reference point

- Mathira West, Nyeri county, Kenya. Latitude -0.42, longitude 36.95 (decimal degrees, WGS84).
- NASA POWER returns elevation 2115.76 m for its grid cell at this point. That is the cell average from MERRA-2, not the farm altitude. Mathira coffee is grown lower, roughly 1,500 to 1,900 m (not checked against a source; treat as context only).

## Data pulled (accessed 2026-10-03)

1. NASA POWER Daily API, `PRECTOTCORR`, 1991-01-01 to 2020-12-31, community AG. 10,958 days, source MERRA-2, no fill values used.
2. NASA POWER Monthly API, same point, 1991 to 2020 (check on the daily totals; they agree to 0.1 mm per month).
3. NASA POWER Climatology API, same point, 2001 to 2020 (second check; same shape).
4. Published descriptions: Nyeri PCRA 2023, Nyeri CIDP 2013 to 2017, MoALF Nyeri Climate Risk Profile 2016, KMD Nyeri MAM 2026 outlook.
5. Agronomy 2021, 11(12):2590, for the spray timing the windows must support.

CHIRPS was not pulled (time). It would be a useful second gridded source.

## Monthly table (NASA POWER PRECTOTCORR, 1991 to 2020 daily mean)

| Month | mm per day | mm per month | 2001 to 2020 climatology, mm per day |
|---|---|---|---|
| Jan | 1.91 | 59.1 | 1.57 |
| Feb | 1.35 | 37.9 | 1.29 |
| Mar | 3.34 | 103.4 | 3.22 |
| Apr | 7.00 | 209.9 | 7.56 |
| May | 4.69 | 145.2 | 4.46 |
| Jun | 2.12 | 63.7 | 2.12 |
| Jul | 1.95 | 60.5 | 1.82 |
| Aug | 2.25 | 69.6 | 2.28 |
| Sep | 1.89 | 56.6 | 2.06 |
| Oct | 4.18 | 129.6 | 4.32 |
| Nov | 6.11 | 183.3 | 5.56 |
| Dec | 3.04 | 94.1 | 2.87 |
| Year | 3.32 | 1213 | 3.26 |

The peaks (April, November) and the driest month (February) match the Nyeri PCRA 2023 description: "highest monthly rainfall of about 200 mm in April while the lowest monthly rainfall is about 40 mm in February".

Dekadal means, mm per day (days 1 to 10, 11 to 20, 21 to end), for the months that set the boundaries:

| Month | Dekad 1 | Dekad 2 | Dekad 3 |
|---|---|---|---|
| Feb | 1.21 | 1.83 | 0.94 |
| Mar | 2.46 | 3.07 | 4.38 |
| May | 6.90 | 4.26 | 3.05 |
| Sep | 2.19 | 1.81 | 1.67 |
| Oct | 2.78 | 4.58 | 5.09 |
| Dec | 4.05 | 2.85 | 2.27 |

## Method

Onset and cessation use the cumulative anomaly method (daily rain minus the annual mean daily rain, 3.32 mm, summed through a search window; onset is the day after the minimum, cessation is the maximum). This is the approach of Liebmann et al. 2012 for East African rains; we cite the method by name only and have not re-read that paper today.

Applied three ways:

| Measure | Long rains onset | Long rains end | Short rains onset | Short rains end |
|---|---|---|---|---|
| 31-day smoothed climatology above annual mean | 16 Mar | 26 May | 9 Oct | 15 Dec |
| Cumulative anomaly on the mean daily climatology | 19 Mar | 21 May | 10 Oct | 14 Dec |
| Cumulative anomaly per year, median (25th to 75th percentile) | 21 Mar (3 to 26 Mar) | 23 May (13 May to 4 Jun) | 14 Oct (8 to 24 Oct) | 14 Dec (30 Nov to 18 Dec) |

Per-year search windows: 1 Feb to 30 Jun (long rains, 30 years) and 1 Sep to 15 Jan (short rains, 29 seasons). Years where the result fell on a search-window edge (no clear season) were dropped: 9 for each season, leaving 21 and 20. That is a lot of dropped years. It reflects real variability and the coarse grid, and it is a limit on how firmly these dates can be stated.

Scripts: `/tmp/season/analyse.py`, `/tmp/season/peryear2.py`, `/tmp/season/check.py` (scratch, not committed).

## Final windows and justification

| Window | Dates | Days | Justification |
|---|---|---|---|
| `dry` | 16 Dec to 14 Feb | 61 | After short rains cessation (14 to 15 Dec in all three measures). January and February are the driest months (1.91 and 1.35 mm per day); PCRA 2023 names February the lowest month. |
| `pre_long_rains` | 15 Feb to 14 Mar | 28 | **Assumption: 4 weeks before long rains onset.** Contains the Agronomy 2021 long-rains first spray, "late February or early March". |
| `long_rains` | 15 Mar to 25 May | 72 | Onset measures 16 to 21 Mar; KMD MAM 2026 outlook gives onset in the 2nd to 3rd week of March. We take 15 Mar, the early side, so a pre-rains prompt is not late in an early year (judgement). End: measures 21 to 26 May; KMD gives cessation in the 3rd to 4th week of May. April is the peak (7.00 mm per day). Nyeri CIDP and PCRA: long rains March to May. |
| `dry` | 26 May to 16 Sep | 114 | June to September stay at 1.89 to 2.25 mm per day, below the annual mean. PCRA 2023: "a cold period is experienced from June to August". |
| `pre_short_rains` | 17 Sep to 14 Oct | 28 | **Assumption: 4 weeks before short rains onset.** Ends just before the Agronomy 2021 short-rains spray: "starts in mid-October, just before the start of short rains". |
| `short_rains` | 15 Oct to 15 Dec | 62 | Onset measures 9 to 14 Oct; October dekad 2 (11 to 20 Oct) is the first above the annual mean. We take 15 Oct, which matches the per-year median (14 Oct) and Agronomy 2021 "mid-October, just before the start of short rains". End 15 Dec: measures 14 to 15 Dec. November is the peak (6.11 mm per day). Nyeri CIDP and PCRA: short rains October to December. |

Coverage check (`/tmp/season/check.py`, run on 2025 and leap year 2024): every day falls in exactly one window, 0 gaps, 0 overlaps, 29 February falls in `pre_long_rains`. Days per window in 2025: dry 175, pre_long_rains 28, long_rains 72, pre_short_rains 28, short_rains 62, total 365.

## Assumptions

- Pre-rains windows are exactly 4 weeks (28 days) before the chosen onset. This is our choice, not a measured quantity. It is wide enough to contain the Agronomy 2021 spray dates.
- Onset dates of 15 Mar and 15 Oct are a judgement inside the measured range, rounded to mid-month and set on the early side.
- One fixed calendar for every year. Real onset moves by weeks: per-year 25th to 75th percentile is 3 to 26 Mar and 8 to 24 Oct. The answer bank should say "rains usually start around..." and not promise a date.

## What this does not cover

- One grid point from a reanalysis product (MERRA-2, about 0.5 by 0.625 degrees). It does not resolve slope, altitude or the Mt Kenya rain shadow. Values are modelled, not station observations.
- The MoALF 2016 profile reports a third, middle rain in July and August in zones LH2, LH3 and LH4. Our data shows only a small rise in late July and August (up to 2.37 mm per day). We label it `dry`. Farms in those zones may see more rain than this calendar suggests.
- The KMD outlook is a 2026 forecast for one season, used only as a sense check.
- No climate trend analysis. The Agronomy review and the MoALF profile both say rainfall timing is becoming less reliable.
- Only Nyeri. Other coffee counties (Kiambu, Murang'a, Kirinyaga, Embu) were not checked.
