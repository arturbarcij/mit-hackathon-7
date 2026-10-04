"""Rain onset, season windows and NDVI-window wetness from NASA POWER.

Serves two uses:
1. Season calendar support for research and content-voice (the spray-before-the-
   short-rains decision): when do the short rains start, how variable is it, and
   what has this September looked like.
2. A check on the NDVI composites: how wet was each "dry-season" window?

Output: data/season_support.json (also copied to kb/geo/ by run.sh via this script).
POWER is a coarse model grid, so onset dates here are for the area, not a plot.
"""
import json
from datetime import date, timedelta

import numpy as np

import config as C

# Onset definition (assumption; common agro-meteorological form, simplified):
# first day on or after the search start where 3 consecutive days total at least
# 20 mm and the next 21 days contain no run of 10 or more days under 1 mm... see below.
ONSET_MM_3D = 20.0
DRY_DAY_MM = 1.0
MAX_DRY_RUN = 7          # days; a longer dry run in the next 21 days means a false start
FALSE_START_WINDOW = 21
SEARCH = {"short_rains": (9, 15), "long_rains": (3, 1)}   # (month, day) search start
SEARCH_DAYS = 90


def load():
    raw = json.loads((C.CACHE / "power_daily.json").read_text())["properties"]["parameter"]["PRECTOTCORR"]
    return {date(int(k[:4]), int(k[4:6]), int(k[6:])): v for k, v in raw.items() if v is not None and v >= 0}


def onset(days, year, season):
    m, d = SEARCH[season]
    start = date(year, m, d)
    for i in range(SEARCH_DAYS):
        t = start + timedelta(days=i)
        w = [days.get(t + timedelta(days=k)) for k in range(3)]
        if any(x is None for x in w) or sum(w) < ONSET_MM_3D:
            continue
        nxt = [days.get(t + timedelta(days=3 + k)) for k in range(FALSE_START_WINDOW)]
        if any(x is None for x in nxt):
            return None   # not enough data after this date to confirm (e.g. this year)
        run = best = 0
        for x in nxt:
            run = run + 1 if x < DRY_DAY_MM else 0
            best = max(best, run)
        if best <= MAX_DRY_RUN:
            return t
    return None


def doy(d, year_start_month=1):
    return (d - date(d.year, 1, 1)).days + 1


def fmt(day_of_year, year=2026):
    return (date(year, 1, 1) + timedelta(days=int(round(day_of_year)) - 1)).strftime("%d %b")


def window_rain(days, year, a, b):
    vals = [days[t] for t in (a + timedelta(n) for n in range((b - a).days + 1)) if t in days]
    return sum(vals), len(vals)


def main():
    days = load()
    y0, y1 = C.CLIMATOLOGY
    res = {"source": "NASA POWER daily PRECTOTCORR (mm/day), community AG", "point": json.loads(
        (C.DATA / "rainfall.json").read_text())["point"],
        "definition": {
            "onset": f"first day from the search start where 3 days total at least {ONSET_MM_3D:.0f} mm and no run of more than "
                     f"{MAX_DRY_RUN} days under {DRY_DAY_MM:.0f} mm in the next {FALSE_START_WINDOW} days",
            "searchStart": {"short_rains": "15 Sep", "long_rains": "1 Mar"},
            "status": "assumption: simplified onset rule on a coarse model grid, not the Kenya Met Department definition"}}

    for season in SEARCH:
        yrs = range(1991, 2026) if season == "short_rains" else range(1991, 2027)
        dates = {y: onset(days, y, season) for y in yrs}
        found = {y: d for y, d in dates.items() if d is not None}
        d_ = np.array([doy(d) for d in found.values()])
        clim = np.array([doy(d) for y, d in found.items() if y0 <= y <= y1])
        res[season] = {
            "yearsWithOnset": len(found), "yearsChecked": len(list(yrs)),
            "climatology1991to2020": {"medianDate": fmt(np.median(clim)), "earliest": fmt(clim.min()), "latest": fmt(clim.max()),
                                      "sdDays": round(float(clim.std(ddof=1)), 1), "years": int(clim.size)},
            "byYear": {str(y): d.isoformat() for y, d in found.items() if y >= 2019},
            "shareOnsetBefore": {lab: round(float((clim <= doy(date(2026, m, dd))).mean()), 2)
                                 for lab, (m, dd) in {"1 Oct": (10, 1), "15 Oct": (10, 15), "31 Oct": (10, 31),
                                                      "15 Nov": (11, 15)}.items()} if season == "short_rains" else None,
        }
        if season == "long_rains":
            res[season]["shareOnsetBefore"] = {lab: round(float((clim <= doy(date(2026, m, dd))).mean()), 2)
                                               for lab, (m, dd) in {"15 Mar": (3, 15), "1 Apr": (4, 1), "15 Apr": (4, 15)}.items()}

    # This year's short rains: data end 30 Sep 2026, so onset cannot be confirmed yet.
    sept = [days[date(2026, 9, d)] for d in range(1, 31) if date(2026, 9, d) in days]
    sept_clim = [sum(v for t, v in days.items() if t.year == y and t.month == 9) for y in range(y0, y1 + 1)]
    last7 = sum(days[date(2026, 9, d)] for d in range(24, 31))
    res["thisYear"] = {
        "dataEnd": max(days).isoformat(),
        "shortRainsOnsetConfirmed": onset(days, 2026, "short_rains") is not None,
        "september2026Mm": round(sum(sept), 1), "september1991to2020MeanMm": round(float(np.mean(sept_clim)), 1),
        "septemberZ": round(float((sum(sept) - np.mean(sept_clim)) / np.std(sept_clim, ddof=1)), 2),
        "last7DaysMm": round(last7, 1),
        "note": "POWER stops at 30 Sep. The farmer app works from a bundled calendar, not live rain.",
    }

    # Suggested windows for the five SeasonWindow names, from monthly means (research owns season.json).
    monthly = {m: float(np.mean([sum(v for t, v in days.items() if t.year == y and t.month == m)
                                 for y in range(y0, y1 + 1)])) for m in range(1, 13)}
    res["monthlyMeanMm1991to2020"] = {str(m): round(v) for m, v in monthly.items()}
    sw = res["short_rains"]["climatology1991to2020"]["medianDate"]
    lw = res["long_rains"]["climatology1991to2020"]["medianDate"]
    res["suggestedWindows"] = {
        "note": "Proposal for the research agent. Months from POWER monthly means; onset dates from the rule above.",
        "pre_short_rains": f"about 15 Sep to the median short-rains onset ({sw})",
        "short_rains": f"{sw} to about 15 Dec",
        "pre_long_rains": "about 15 Feb to the median long-rains onset (" + lw + ")",
        "long_rains": f"{lw} to about 31 May",
        "dry": "the rest (Jun to mid Sep, Jan to mid Feb)",
    }

    # How wet was each NDVI composite window? Wet Febs/Marches make a "dry-season" composite less comparable.
    wins = {}
    for season, (a, b) in C.DRY_SEASONS.items():
        a, b = date.fromisoformat(a), date.fromisoformat(b)
        tot, n = window_rain(days, a.year, a, b)
        clim = [window_rain(days, y, date(y, a.month, a.day), date(y, b.month, b.day))[0] for y in range(y0, y1 + 1)]
        wins[season] = {"window": f"{a.isoformat()}/{b.isoformat()}", "rainMm": round(tot, 1),
                        "climatologyMm": round(float(np.mean(clim)), 1),
                        "z": round(float((tot - np.mean(clim)) / np.std(clim, ddof=1)), 2)}
    res["ndviWindowRain"] = wins

    (C.DATA / "season_support.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("short_rains", "long_rains", "thisYear", "ndviWindowRain", "suggestedWindows")}, indent=1))


if __name__ == "__main__":
    main()
