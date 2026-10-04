"""Check public/geo outputs against kb/geo/CONTRACT.md. Exit 1 on any failure."""
import json
import math
import re
import sys
from datetime import date

import config as C

REASONS = {"drop_with_canopy_loss", "drop_canopy_normal", "delivery_drop", "delivery_spike",
           "above_plausible_yield", "canopy_loss"}
ABSTAIN = {"short_history", "missing_delivery_record", "plot_too_small", "few_clear_pixels", "canopy_signal_unclear"}
NEXT = {"visit", "call_member", "check_records", "ask_officer", "none"}
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def no_nan(o, path="$"):
    if isinstance(o, float):
        check(math.isfinite(o), f"non-finite number at {path}")
    elif isinstance(o, dict):
        for k, v in o.items():
            no_nan(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            no_nan(v, f"{path}[{i}]")


def main():
    gj = json.loads((C.OUT / "plots.geojson").read_text())
    oj = json.loads((C.OUT / "outliers.json").read_text())
    no_nan(gj, "plots"); no_nan(oj, "outliers")
    check(gj.get("synthetic") is True, "plots.geojson must carry synthetic: true")
    check(oj["version"] == "geo-1" and oj["season"] == C.CURRENT_SEASON, "version or season")
    check(oj["synthetic"]["plots"] and oj["synthetic"]["deliveries"], "synthetic flags")
    check(not oj["synthetic"]["ndvi"] and not oj["synthetic"]["rainfall"], "ndvi and rainfall are real")
    ids = {f["properties"]["plotId"] for f in gj["features"]}
    check(len(ids) == len(gj["features"]), "duplicate plotId")
    check({p["plotId"] for p in oj["plots"]} == ids, "plots.geojson and outliers.json plotIds differ")
    check(sum(oj["counts"].values()) == len(ids), "counts do not add up")

    lon0, lat0, lon1, lat1 = C.BBOX
    for f in gj["features"]:
        p = f["properties"]
        check(p["synthetic"] is True, f"{p['plotId']} not tagged synthetic")
        check(p["plotId"] == f"{p['memberId']}-{p['plot']}", f"{p['plotId']} id format")
        ring = f["geometry"]["coordinates"][0]
        check(ring[0] == ring[-1] and len(ring) >= 4, f"{p['plotId']} ring not closed")
        check(all(lon0 <= x <= lon1 and lat0 <= y <= lat1 for x, y in ring), f"{p['plotId']} outside bbox")
        check(p["status"] in {"outlier", "unsure", "normal"}, f"{p['plotId']} status")
        check(len(p["ndviSeries"]) == len(C.COFFEE_YEARS), f"{p['plotId']} ndviSeries length")
        check("name" not in p and "phone" not in p, f"{p['plotId']} personal fields")
    for o in oj["plots"]:
        i = o["plotId"]
        check(set(o["reasons"]) <= REASONS, f"{i} unknown reason")
        check(set(o["abstainReasons"]) <= ABSTAIN, f"{i} unknown abstain code")
        check(o["nextStep"] in NEXT, f"{i} next step")
        check((o["confidence"] == "low") == (o["status"] == "unsure"), f"{i} confidence/status")
        check(o["status"] != "outlier" or o["reasons"], f"{i} outlier without reason")
        check(o["status"] != "unsure" or o["abstainReasons"] or o["metrics"]["clearPx"] < C.MIN_CLEAR_PIXELS,
              f"{i} unsure without a stated reason")
        check(o["status"] != "normal" or o["nextStep"] == "none", f"{i} normal with action")
        check(o["synthetic"] is True, f"{i} not tagged synthetic")
    for code in REASONS | ABSTAIN:
        check(code in oj["legend"], f"legend missing {code}")
    check(all(s in oj["nextSteps"] for s in NEXT), "nextSteps incomplete")
    b = oj["overlay"]["bounds"]
    check(b[0][0] < b[1][0] and b[0][1] < b[1][1], "overlay bounds order")
    check((C.OUT / "ndvi_change.png").stat().st_size > 1000, "overlay image missing")
    noor = next((o for o in oj["plots"] if o["plotId"] == "OCC0412-2"), None)
    check(noor is not None and noor["status"] == "outlier", "contract example plot OCC0412-2 must be flagged")
    vp = json.loads((C.OUT / "visit_plan.json").read_text())
    rs = json.loads((C.OUT / "referrals_seed.json").read_text())
    no_nan(vp, "visit_plan"); no_nan(rs, "referrals_seed")
    check(rs["synthetic"] is True and vp["synthetic"]["referrals"], "referral seed must be tagged synthetic")
    sms_re = re.compile(r"^JANI1 M:\S+ P:\d+ D:\d{8} N:\d+ R:\d+ C:\d+ H:\d+ L:\d+ U:\d+ A:[a-z_]+ Q:\d+ X:(act|wait|ask)$")
    check(15 <= len(rs["referrals"]) <= 20, "seed referrals should number 15 to 20")
    for r in rs["referrals"]:
        check(r["synthetic"] is True and r["geoPlotId"] in ids, f"{r['id']} synthetic or plot link")
        check(bool(sms_re.match(r["sms"])) and len(r["sms"]) <= 160 and r["sms"].isascii(), f"{r['id']} SMS format")
        check(r["sms"].startswith(f"JANI1 M:{r['member_id']} P:{r['plot_id']} "), f"{r['id']} SMS does not match its fields")
        check(date.fromisoformat(r["check_date"]).weekday() >= 5, f"{r['id']} check date is not a weekend")
        check(sum(r["counts"].values()) + r["uncertain"] == 10, f"{r['id']} counts do not add to 10")
    stops = vp["route"]["stops"]
    check(len(stops) <= vp["assumptions"]["capacityPerVisitDay"], "route longer than capacity")
    check(all(s["plotId"] in ids and s["tier"] == "A" for s in stops), "route stop not a tier A plot")
    check(all(r["signals"] for r in vp["ranking"]), "ranked plot without a stated signal")
    check(vp["route"]["totalKm"] <= vp["route"]["randomOrderMeanKm"] + 0.01, "optimised route longer than random order")
    check(all("priorityPoints" in f["properties"] and f["properties"]["tier"] in "ABC" for f in gj["features"]), "plots.geojson priority fields")
    text = (C.OUT / "outliers.json").read_text() + (C.OUT / "visit_plan.json").read_text() + (C.OUT / "referrals_seed.json").read_text()
    check("\u2014" not in text, "em dash in geo outputs")

    if errors:
        print("FAIL")
        print("\n".join(errors[:30]))
        sys.exit(1)
    print(f"OK: {len(ids)} plots, {oj['counts']}, all checks passed")


if __name__ == "__main__":
    main()
