import json, urllib.request, datetime as dt, statistics as st, collections, sys

LAT, LON = -0.42, 36.95
URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
    f"?parameters=PRECTOTCORR&community=AG&longitude={LON}&latitude={LAT}"
    "&start=19910101&end=20201231&format=JSON"
)
raw = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()
open("power_nyeri_raw.json", "wb").write(raw)
d = json.loads(raw)
print("header api version:", d.get("header", {}).get("api", {}))
print("geometry:", d.get("geometry"))
print("sources:", d.get("header", {}).get("sources"), "| title:", d.get("header", {}).get("title"))
print("fill value:", d.get("header", {}).get("fill_value"))
p = d["properties"]["parameter"]["PRECTOTCORR"]
fill = d["header"].get("fill_value", -999)
days = {}
for k, v in p.items():
    day = dt.datetime.strptime(k, "%Y%m%d").date()
    days[day] = None if v == fill else v
print("n days", len(days), "missing", sum(v is None for v in days.values()))

years = list(range(1991, 2021))

def monthly_total(y, m):
    s = 0.0
    d0 = dt.date(y, m, 1)
    d = d0
    while d.month == m:
        s += days[d] or 0.0
        d += dt.timedelta(days=1)
    return s
monthly = {}
for m in range(1, 13):
    vals = [monthly_total(y, m) for y in years]
    monthly[m] = {"mean_mm": round(st.mean(vals), 1), "min_mm": round(min(vals), 1), "max_mm": round(max(vals), 1), "stdev_mm": round(st.pstdev(vals), 1)}
print("MONTHLY (mean of monthly totals, 1991-2020):")
for m in range(1, 13):
    print(m, monthly[m])
annual = [sum(monthly_total(y, m) for m in range(1, 13)) for y in years]
print("annual mean mm", round(st.mean(annual), 1))

# semi-monthly (1-15, 16-end) mean totals
print("SEMI-MONTHLY mean totals:")
semi = {}
for m in range(1, 13):
    a = []
    b = []
    for y in years:
        sa = sum(days[dt.date(y, m, dd)] or 0 for dd in range(1, 16))
        d = dt.date(y, m, 16)
        sb = 0.0
        while d.month == m:
            sb += days[d] or 0.0
            d += dt.timedelta(days=1)
        a.append(sa)
        b.append(sb)
    semi[f"{m}a"] = round(st.mean(a), 1)
    semi[f"{m}b"] = round(st.mean(b), 1)
print(semi)

# onset by a Marteau-style rule: first day on/after start date where 3-day total >= 20 mm
# and no dry spell (daily < 1 mm) longer than 10 consecutive days in the next 30 days.
def onset(y, start, last):
    d = start
    while d <= last:
        r3 = sum(days.get(d + dt.timedelta(days=i)) or 0 for i in range(3))
        if r3 >= 20:
            # check dry spell in next 30 days
            run = 0
            ok = True
            for i in range(3, 33):
                v = days.get(d + dt.timedelta(days=i))
                if v is None:
                    continue
                if v < 1:
                    run += 1
                    if run > 10:
                        ok = False
                        break
                else:
                    run = 0
            if ok:
                return d
        d += dt.timedelta(days=1)
    return None

def summarise(label, start_md, last_md):
    doys = []
    dates = []
    for y in years:
        o = onset(y, dt.date(y, *start_md), dt.date(y, *last_md))
        if o is None:
            continue
        doys.append(o.timetuple().tm_yday - (1 if (o.year % 4 == 0 and o.month > 2) else 0))
        dates.append(o)
    doys_sorted = sorted(doys)
    n = len(doys_sorted)
    def q(p):
        i = int(round((n - 1) * p))
        return doys_sorted[i]
    base = dt.date(2001, 1, 1)  # non-leap
    def to_date(doy):
        return (base + dt.timedelta(days=doy - 1)).strftime("%d %b")
    print(label, "n=", n, "of", len(years), "| p10", to_date(q(0.1)), "p25", to_date(q(0.25)), "median", to_date(q(0.5)), "p75", to_date(q(0.75)), "p90", to_date(q(0.9)))
    return {"n_years": n, "p10": to_date(q(0.1)), "p25": to_date(q(0.25)), "median": to_date(q(0.5)), "p75": to_date(q(0.75)), "p90": to_date(q(0.9))}

res = {}
res["long_rains_onset"] = summarise("LONG RAINS onset (from 1 Mar)", (3, 1), (5, 31))
res["short_rains_onset"] = summarise("SHORT RAINS onset (from 1 Oct)", (10, 1), (12, 31))
res["short_rains_onset_from_sep15"] = summarise("SHORT RAINS onset (from 15 Sep)", (9, 15), (12, 31))

json.dump({"monthly": monthly, "semi_monthly": semi, "annual_mean_mm": round(st.mean(annual), 1), "onset": res}, open("power_summary.json", "w"), indent=1)
