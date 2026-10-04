"""Daily rainfall from NASA POWER at the AOI centre, summarised per coffee year.

Source: NASA POWER daily API, parameter PRECTOTCORR (bias-corrected
precipitation, mm/day), community AG. POWER is a coarse grid (0.5 x 0.625
degrees), so one value covers the whole cooperative. It cannot tell plots apart.
"""
import json
from datetime import date

import numpy as np
import requests

import config as C

SEASONS = {  # Kenyan central highlands bimodal rains
    "long_rains": (3, 5),    # March to May, main flowering and fruit set
    "short_rains": (10, 12), # October to December
}


def fetch():
    lon = (C.BBOX[0] + C.BBOX[2]) / 2
    lat = (C.BBOX[1] + C.BBOX[3]) / 2
    path = C.CACHE / "power_daily.json"
    if not path.exists():
        r = requests.get(C.POWER_URL, params=dict(
            parameters="PRECTOTCORR", community="AG", longitude=round(lon, 4), latitude=round(lat, 4),
            start=C.POWER_START, end=C.POWER_END, format="JSON"), timeout=120)
        r.raise_for_status()
        C.CACHE.mkdir(exist_ok=True)
        path.write_text(r.text)
    raw = json.loads(path.read_text())
    series = raw["properties"]["parameter"]["PRECTOTCORR"]
    days = {date(int(k[:4]), int(k[4:6]), int(k[6:])): v for k, v in series.items() if v is not None and v >= 0}
    return lon, lat, raw.get("geometry"), days


def season_total(days, year, months):
    m0, m1 = months
    vals = [v for d, v in days.items() if d.year == year and m0 <= d.month <= m1]
    expected = sum(1 for d in days if d.year == year and m0 <= d.month <= m1)
    full = len(vals) >= 0.95 * (31 + 30 + 31)
    return (sum(vals) if full else None), expected


def main():
    lon, lat, geom, days = fetch()
    y0, y1 = C.CLIMATOLOGY
    clim = {}
    for name, months in SEASONS.items():
        tots = [season_total(days, y, months)[0] for y in range(y0, y1 + 1)]
        tots = [t for t in tots if t is not None]
        clim[name] = {"meanMm": round(float(np.mean(tots)), 1), "sdMm": round(float(np.std(tots, ddof=1)), 1),
                      "years": len(tots)}

    out = {}
    for cy in C.COFFEE_YEARS:
        start = int(cy[:4])  # coffee year 2025/26 runs Oct 2025 to Sep 2026
        rows = {}
        # Short rains at the start of the coffee year (Oct to Dec of the first year),
        # long rains inside it (Mar to May of the second year).
        for name, yr in (("short_rains", start), ("long_rains", start + 1)):
            tot, _ = season_total(days, yr, SEASONS[name])
            c = clim[name]
            rows[name] = {
                "year": yr, "totalMm": None if tot is None else round(tot, 1),
                "anomalyPct": None if tot is None else round(100 * (tot - c["meanMm"]) / c["meanMm"], 1),
                "z": None if tot is None else round((tot - c["meanMm"]) / c["sdMm"], 2),
            }
        annual = [v for d, v in days.items() if date(start, 10, 1) <= d <= date(start + 1, 9, 30)]
        rows["coffeeYearTotalMm"] = round(sum(annual), 1)
        out[cy] = rows

    result = {
        "source": "NASA POWER daily API, PRECTOTCORR (mm/day), community AG",
        "url": C.POWER_URL,
        "point": {"lon": round(lon, 4), "lat": round(lat, 4)},
        "gridNote": "POWER grid is about 0.5 x 0.625 degrees; one value covers the whole cooperative area",
        "period": f"{C.POWER_START}/{C.POWER_END}",
        "climatology": {"years": f"{y0}-{y1}", **clim},
        "coffeeYears": out,
    }
    C.DATA.mkdir(exist_ok=True)
    (C.DATA / "rainfall.json").write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
