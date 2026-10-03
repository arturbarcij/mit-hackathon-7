"""Officer visit plan and synthetic leaf-check referrals.

The extension officer reaches the sub-county twice a year at best. This ranks
which plots deserve those visits by combining up to three independent signals,
then orders one visit day into a short route.

Signals (independent sources):
  satellite   real Sentinel-2 canopy change against the nearest plots
  deliveries  synthetic cooperative delivery record against the member's own history
  leaf_check  the farmer's own Jani check sent as an SMS referral (synthetic seed)

Priority points are a transparent sum, not a probability. The weights are
assumptions; there is no real visit-outcome data to fit them on.

Inputs : public/geo/outliers.json, plots.geojson, data/truth.json
Outputs: public/geo/referrals_seed.json, public/geo/visit_plan.json,
         priorityScore / tier / hasReferral added to plots.geojson,
         data/visit_eval.json
"""
import itertools
import json
import re
from datetime import date, datetime, timezone

import numpy as np

import config as C

CAPACITY = 8          # plots one officer can visit in a day (assumption)
CIRCUITY = 1.4        # road km per straight-line km on rural roads (assumption)
OFFICE = {"name": "Cooperative office (synthetic location)", "lon": 37.070, "lat": -0.478}
N_REFERRALS = 18
TIER_A, TIER_B = 40, 20

WEIGHTS = {"canopy_strong": 40, "canopy_moderate": 25, "delivery_drop": 30, "delivery_drop_moderate": 15,
           "delivery_spike": 20, "leaf_rust_high": 40, "leaf_other_problem": 25, "leaf_abstained": 25,
           "data_gap": 5}

# Referral dates fall on weekends: the smartphone is only home at weekends (MASTER_PROMPT 2.1).
REFERRAL_DATES = [date(2026, 9, 26), date(2026, 9, 27), date(2026, 10, 3)]
# Only checks that end in "ask the officer" become referrals, so no all-healthy seeds.
LABEL_P = {"rust": 0.58, "cercospora": 0.12, "phoma": 0.08, "miner": 0.10, "mixed": 0.12}
SMS_RE = re.compile(r"^JANI1 M:\S+ P:\d+ D:\d{8} N:\d+ R:\d+ C:\d+ H:\d+ L:\d+ U:\d+ A:[a-z_]+ Q:\d+ X:(act|wait|ask)$")


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(np.radians, (a[1], a[0], b[1], b[0]))
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return float(2 * 6371.0 * np.arcsin(np.sqrt(h)))


def tour_km(points, order):
    pts = [OFFICE_XY] + [points[i] for i in order] + [OFFICE_XY]
    return sum(haversine_km(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) * CIRCUITY


OFFICE_XY = (OFFICE["lon"], OFFICE["lat"])


def best_tour(points):
    idx = range(len(points))
    if len(points) <= 9:
        return list(min(itertools.permutations(idx), key=lambda o: tour_km(points, o)))
    order, left, cur = [], set(idx), OFFICE_XY
    while left:
        nxt = min(left, key=lambda i: haversine_km(cur, points[i]))
        order.append(nxt); left.remove(nxt); cur = points[nxt]
    return order


def answer_for(counts, unsure):
    """Mirror of the example rule table in kb/agents/content-voice.md. Replace with engine output."""
    problems = {k: v for k, v in counts.items() if k != "healthy" and v > 0}
    affected = sum(problems.values())
    if unsure >= 3:
        return "too_many_unsure"
    if len(problems) >= 2:
        return "mixed_problems"
    if counts["rust"] >= 3:
        return "rust_high_pre_rains"   # all seed dates fall before the median short-rains onset
    if counts["rust"] >= 1:
        return "rust_low"
    if affected == 0:
        return "healthy_all"
    return next(iter(problems))        # cercospora, phoma or miner share their label with the answer id


def make_referrals(plots, rng):
    by_id = {p["plotId"]: p for p in plots}
    flagged = [p["plotId"] for p in plots if p["status"] == "outlier" and p["plotId"] != "OCC0412-2"]
    unsure = [p["plotId"] for p in plots if p["status"] == "unsure"]
    normal = [p["plotId"] for p in plots if p["status"] == "normal" and p["plotId"] != "OCC0412-1"]
    pick = (["OCC0412-2"] + list(rng.choice(sorted(flagged), 5, replace=False))
            + list(rng.choice(sorted(unsure), 2, replace=False))
            + list(rng.choice(sorted(normal), N_REFERRALS - 8, replace=False)))
    out = []
    for i, pid in enumerate(pick):
        p = by_id[pid]
        if pid == "OCC0412-2":
            counts = {"healthy": 3, "rust": 6, "cercospora": 0, "phoma": 0, "miner": 0}
            unsure_n, conf, d = 1, 87, date(2026, 10, 3)
        else:
            kind = rng.choice(list(LABEL_P), p=list(LABEL_P.values()))
            unsure_n = int(rng.choice([0, 1, 2, 3, 4], p=[0.45, 0.25, 0.15, 0.1, 0.05]))
            affected = int(rng.integers(3, 9)) if kind in ("rust", "mixed") else (0 if kind == "healthy" else int(rng.integers(1, 6)))
            affected = min(affected, 10 - unsure_n)
            counts = {"healthy": 0, "rust": 0, "cercospora": 0, "phoma": 0, "miner": 0}
            if kind == "mixed":
                counts["rust"] = max(1, affected - 1); counts["cercospora"] = 1
            elif kind != "healthy":
                counts[kind] = affected
            counts["healthy"] = 10 - unsure_n - sum(v for k, v in counts.items() if k != "healthy")
            conf = int(rng.integers(55, 70)) if unsure_n >= 3 else int(rng.integers(72, 96))
            d = REFERRAL_DATES[int(rng.integers(0, len(REFERRAL_DATES)))]
        ans = answer_for(counts, unsure_n)
        sms = (f"JANI1 M:{p['memberId']} P:{p['plot']} D:{d:%Y%m%d} N:10 R:{counts['rust']} C:{counts['cercospora']} "
               f"H:{counts['phoma']} L:{counts['miner']} U:{unsure_n} A:{ans} Q:{conf} X:ask")
        assert SMS_RE.match(sms) and len(sms) <= 160 and sms.isascii(), sms
        out.append({
            "id": f"seed-{i + 1:02d}", "created_at": f"{d.isoformat()}T{int(rng.integers(8, 19)):02d}:{int(rng.integers(0, 60)):02d}:00+03:00",
            "member_id": p["memberId"], "plot_id": str(p["plot"]), "geoPlotId": pid, "check_date": d.isoformat(),
            "counts": counts, "uncertain": unsure_n, "answer_id": ans, "confidence": round(conf / 100, 2),
            "photos_shared": False, "status": "new", "sms": sms, "synthetic": True,
        })
    out.sort(key=lambda r: r["created_at"], reverse=True)
    return out


def score_plot(o, ref):
    pts, signals = 0, []
    m = o["metrics"]
    zn, zd = m["zNdvi"], m["zDelivery"]
    if o["status"] != "unsure" or "plot_too_small" not in o["abstainReasons"]:
        if zn is not None and "few_clear_pixels" not in o["abstainReasons"]:
            if zn <= -3:
                pts += WEIGHTS["canopy_strong"]
                signals.append(("satellite", f"Canopy fell much more than nearby plots (NDVI {m['ndviBaseline']} to {m['ndvi']}). Real Sentinel-2."))
            elif zn <= -2:
                pts += WEIGHTS["canopy_moderate"]
                signals.append(("satellite", f"Canopy fell more than nearby plots (NDVI {m['ndviBaseline']} to {m['ndvi']}). Real Sentinel-2."))
    if zd is not None and "short_history" not in o["abstainReasons"]:
        if zd <= -3:
            pts += WEIGHTS["delivery_drop"]
            signals.append(("deliveries", f"Deliveries fell {abs(m['changePct']):.0f}% against the cooperative median. Synthetic record."))
        elif zd <= -2:
            pts += WEIGHTS["delivery_drop_moderate"]
            signals.append(("deliveries", f"Deliveries fell {abs(m['changePct']):.0f}%, a moderate drop. Synthetic record."))
        elif zd >= 3:
            pts += WEIGHTS["delivery_spike"]
            signals.append(("deliveries", f"Deliveries rose {m['changePct']:.0f}% against the cooperative median. Check the records. Synthetic."))
    if ref:
        c = ref["counts"]
        if ref["answer_id"] in ("too_many_unsure",):
            pts += WEIGHTS["leaf_abstained"]
            signals.append(("leaf_check", f"Farmer's leaf check could not decide ({ref['uncertain']} of 10 leaves unsure). Asked for the officer. Synthetic."))
        elif c["rust"] >= 3:
            pts += WEIGHTS["leaf_rust_high"]
            signals.append(("leaf_check", f"Farmer's leaf check: {c['rust']} of 10 leaves show rust. Asked for the officer. Synthetic."))
        elif ref["answer_id"] not in ("healthy_all",):
            pts += WEIGHTS["leaf_other_problem"]
            signals.append(("leaf_check", f"Farmer's leaf check asked for the officer ({ref['answer_id'].replace('_', ' ')}). Synthetic."))
    if not signals and o["status"] == "unsure":
        pts += WEIGHTS["data_gap"]
        signals.append(("records", "Data too thin to judge: " + ", ".join(a.replace("_", " ") for a in o["abstainReasons"]) + "."))
    return pts, signals


def main():
    oj = json.loads((C.OUT / "outliers.json").read_text())
    gj = json.loads((C.OUT / "plots.geojson").read_text())
    truth = json.loads((C.DATA / "truth.json").read_text())["plots"]
    cen = {}
    for f in gj["features"]:
        ring = np.array(f["geometry"]["coordinates"][0][:-1])
        cen[f["properties"]["plotId"]] = (float(ring[:, 0].mean()), float(ring[:, 1].mean()))
    plots = oj["plots"]
    rng = np.random.default_rng(C.SEED + 1)
    refs = make_referrals(plots, rng)
    ref_by_plot = {r["geoPlotId"]: r for r in refs}
    for r in refs:
        r["lon"], r["lat"] = (round(v, 6) for v in cen[r["geoPlotId"]])

    scored = []
    for o in plots:
        pts, sig = score_plot(o, ref_by_plot.get(o["plotId"]))
        sources = {s for s, _ in sig if s != "records"}
        scored.append({"o": o, "points": pts, "signals": sig, "independent": len(sources)})
    scored.sort(key=lambda s: (-s["points"], -s["independent"], s["o"]["plotId"]))

    def tier(s):
        return "A" if s["points"] >= TIER_A else ("B" if s["points"] >= TIER_B else "C")
    for s in scored:
        s["tier"] = tier(s)

    visit_pool = [s for s in scored if s["tier"] == "A"][:CAPACITY]
    pts = [cen[s["o"]["plotId"]] for s in visit_pool]
    order = best_tour(pts) if pts else []
    route_km = tour_km(pts, order) if pts else 0.0
    rand = np.random.default_rng(7)
    rand_km = float(np.mean([tour_km(pts, list(rand.permutation(len(pts)))) for _ in range(300)])) if pts else 0.0

    stops, prev = [], OFFICE_XY
    for n, i in enumerate(order, 1):
        s = visit_pool[i]; o = s["o"]; here = cen[o["plotId"]]
        stops.append({"stop": n, "plotId": o["plotId"], "memberId": o["memberId"], "plot": o["plot"], "lon": round(here[0], 6),
                      "lat": round(here[1], 6), "legKm": round(haversine_km(prev, here) * CIRCUITY, 1),
                      "points": s["points"], "independentSignals": s["independent"], "tier": s["tier"],
                      "signals": [{"source": a, "text": b} for a, b in s["signals"]]})
        prev = here
    ranking = [{"rank": r, "plotId": s["o"]["plotId"], "memberId": s["o"]["memberId"], "plot": s["o"]["plot"],
                "points": s["points"], "tier": s["tier"], "independentSignals": s["independent"],
                "geoStatus": s["o"]["status"], "nextStep": s["o"]["nextStep"],
                "referralId": ref_by_plot[s["o"]["plotId"]]["id"] if s["o"]["plotId"] in ref_by_plot else None,
                "signals": [{"source": a, "text": b} for a, b in s["signals"]]}
               for r, s in enumerate(scored, 1) if s["points"] > 0]

    # Does the satellite-plus-deliveries ranking beat chance on the planted problems? (synthetic)
    problem = {"decline_with_canopy_loss", "delivery_gap_canopy_ok", "over_delivery", "canopy_loss_early"}
    needs = {pid for pid, sc in truth.items() if sc in problem}
    geo_only = []
    for o in plots:
        p, sig = score_plot(o, None)
        geo_only.append((p, o["plotId"]))
    geo_only.sort(key=lambda t: (-t[0], t[1]))
    prec = {}
    for k in (CAPACITY, 12):
        hit = sum(1 for _, pid in geo_only[:k] if pid in needs)
        prec[f"top{k}"] = {"hits": hit, "precision": round(hit / k, 2), "recall": round(hit / len(needs), 2)}
    visit_need = {pid for pid, sc in truth.items() if sc in ("decline_with_canopy_loss", "canopy_loss_early")}
    eval_ = {"synthetic": True,
             "note": "Geo signals only (no referrals), scored on our own planted scenarios. Shows the ranking logic works as designed, not that it works in the field.",
             "plots": len(plots), "plantedProblems": len(needs), "randomPrecision": round(len(needs) / len(plots), 2),
             "precisionRecall": prec, "plantedCanopyLossInTopCapacity": sum(1 for _, pid in geo_only[:CAPACITY] if pid in visit_need),
             "plantedCanopyLoss": len(visit_need),
             "route": {"stops": len(pts), "optimisedKm": round(route_km, 1), "randomOrderMeanKm": round(rand_km, 1),
                       "savingPct": round(100 * (1 - route_km / rand_km), 0) if rand_km else None}}
    (C.DATA / "visit_eval.json").write_text(json.dumps(eval_, indent=1))

    tiers = {t: sum(1 for s in scored if s["tier"] == t) for t in "ABC"}
    plan = {
        "version": "geo-1", "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "season": C.CURRENT_SEASON,
        "synthetic": {"deliveries": True, "referrals": True, "plots": True, "satellite": False},
        "assumptions": {"capacityPerVisitDay": CAPACITY, "circuity": CIRCUITY, "office": OFFICE,
                        "weights": WEIGHTS, "tiers": {"A": f"{TIER_A} points or more: visit now",
                                                       "B": f"{TIER_B} to {TIER_A - 1}: call the member or check records",
                                                       "C": "below: no action from this map"},
                        "note": "Points are a transparent sum of signals, not a probability. Weights are assumptions and need real visit outcomes to tune."},
        "tiers": tiers, "route": {"stops": stops, "totalKm": round(route_km, 1), "randomOrderMeanKm": round(rand_km, 1),
                                  "note": "Straight-line distance times 1.4, closed loop from the office. Not road routing."},
        "ranking": ranking, "referralsLinked": sum(1 for r in ranking if r["referralId"]),
        "independentAgreement": sum(1 for r in ranking if r["independentSignals"] >= 2),
    }
    (C.OUT / "visit_plan.json").write_text(json.dumps(plan, indent=1))
    (C.OUT / "referrals_seed.json").write_text(json.dumps(
        {"synthetic": True, "note": "Seed referrals for the officer dashboard. Fake members, fake checks. answer_id values mirror the example rules in kb/agents/content-voice.md; replace with engine output when available.",
         "referrals": refs}, indent=1))

    meta = {s["o"]["plotId"]: s for s in scored}
    for f in gj["features"]:
        s = meta[f["properties"]["plotId"]]
        f["properties"].update({"priorityPoints": s["points"], "tier": s["tier"], "hasReferral": f["properties"]["plotId"] in ref_by_plot})
    (C.OUT / "plots.geojson").write_text(json.dumps(gj, separators=(",", ":")))
    print(json.dumps({"tiers": tiers, "eval": eval_, "agreement2plus": plan["independentAgreement"]}, indent=1))


if __name__ == "__main__":
    main()
