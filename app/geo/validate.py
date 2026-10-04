#!/usr/bin/env python3
"""Validate app/public/geo outputs against the contract in kb/agents/geo.md and check
that the planted scenarios get the intended reason codes. Exit 1 on failure.

    python app/geo/validate.py [--dir app/public/geo] [--strict] [--markdown]

--strict  also fail when real Sentinel-2 NDVI moves a planted plot to another code
--markdown  print the scenario sanity table as markdown
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import geo_core as core  # noqa: E402

REASONS = set(core.REASONS)
PLOT_KEYS = ["plot_id", "member_id", "own_change_pct", "peer_change_pct", "gap_z", "ndvi_change", "ndvi_z",
             "clear_obs", "reason", "confidence", "sms_nudge_id", "synthetic_deliveries"]
EXT_KEYS = ["synthetic_ndvi", "history", "peer_median_history", "ndvi_series", "centroid", "has_referral_seed"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(HERE), "public", "geo"))
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    a = ap.parse_args(argv)
    errors, warns = [], []

    def need(cond, msg):
        if not cond:
            errors.append(msg)
        return cond

    paths = {n: os.path.join(a.dir, n) for n in ("area.json", "plots.geojson", "outliers.json")}
    for n, p in paths.items():
        if not need(os.path.exists(p), f"missing {p}"):
            print("\n".join("FAIL " + e for e in errors))
            return 1
    area = json.load(open(paths["area.json"], encoding="utf-8"))
    gj = json.load(open(paths["plots.geojson"], encoding="utf-8"))
    out = json.load(open(paths["outliers.json"], encoding="utf-8"))

    # area.json
    for k in ("name", "bbox", "centre", "notes"):
        need(k in area, f"area.json lacks {k}")
    w, s, e, n = area["bbox"]
    need(w < e and s < n, "area bbox order must be [w, s, e, n]")

    # plots.geojson
    need(gj.get("type") == "FeatureCollection", "plots.geojson is not a FeatureCollection")
    feats = gj.get("features", [])
    need(len(feats) == 40, f"plots.geojson has {len(feats)} features, expected 40")
    gj_ids = {}
    for f in feats:
        p = f.get("properties", {})
        pid = p.get("plot_id")
        for k in ("plot_id", "member_id", "area_ha", "synthetic"):
            need(k in p, f"{pid}: geojson property {k} missing")
        need(p.get("synthetic") is True, f"{pid}: synthetic must be true")
        need(0.45 <= float(p.get("area_ha", 0)) <= 2.6, f"{pid}: area_ha {p.get('area_ha')} outside 0.5 to 2.5")
        g = f.get("geometry", {})
        need(g.get("type") == "Polygon", f"{pid}: geometry must be Polygon")
        ring = g.get("coordinates", [[]])[0]
        need(6 <= len(ring) <= 8 and ring[0] == ring[-1], f"{pid}: ring must be closed with 5 to 7 vertices")
        for x, y in ring:
            need(w <= x <= e and s <= y <= n, f"{pid}: vertex outside bbox")
            need(round(x, 5) == x and round(y, 5) == y, f"{pid}: coordinates not rounded to 5 decimals")
        ha = core.polygon_area_ha(ring)
        need(abs(ha - p.get("area_ha", 0)) < 0.05, f"{pid}: area_ha {p.get('area_ha')} vs polygon {ha:.2f}")
        gj_ids[pid] = p.get("member_id")
    for pid, mid in core.FIXED_MEMBERS.items():
        need(gj_ids.get(pid) == mid, f"{pid} must be member {mid}, found {gj_ids.get(pid)}")

    # outliers.json top level
    for k in ("generated", "season", "area", "rainfall", "assumptions", "plots", "sources", "ndvi_source"):
        need(k in out, f"outliers.json lacks {k}")
    need(out.get("season") == core.LATEST, "season must be 2025/26")
    need("name" in out["area"] and "bbox" in out["area"], "area needs name and bbox")
    rain = out["rainfall"]
    for k in ("season_anomaly_pct", "source", "synthetic"):
        need(k in rain, f"rainfall lacks {k}")
    ndvi_src = out["ndvi_source"]
    need(ndvi_src in ("synthetic", "sentinel-2", "unavailable"), f"bad ndvi_source {ndvi_src}")
    for asm in out["assumptions"]:
        need("officer to confirm" in asm.get("note", "") or asm["name"] == "base_yield_clean_kg_ha",
             f"assumption {asm.get('name')} lacks 'officer to confirm'")
    names = {x["name"] for x in out["assumptions"]}
    for k in ("gap_z_threshold", "ndvi_z_threshold", "peer_change_weather_pct", "rain_anomaly_weather_pct"):
        need(k in names, f"assumption {k} missing")
    if ndvi_src == "sentinel-2":
        need(bool(out.get("attribution")) and "Copernicus" in out["attribution"], "Copernicus attribution missing")

    plots = out["plots"]
    need(len(plots) == 40, f"outliers.json has {len(plots)} plots")
    by_id = {p["plot_id"]: p for p in plots}
    need(set(by_id) == set(gj_ids), "plot ids differ between plots.geojson and outliers.json")
    for p in plots:
        pid = p["plot_id"]
        for k in PLOT_KEYS + EXT_KEYS:
            need(k in p, f"{pid}: key {k} missing")
        need(p.get("member_id") == gj_ids.get(pid), f"{pid}: member id differs between files")
        need(p.get("reason") in REASONS, f"{pid}: unknown reason {p.get('reason')}")
        need(p.get("confidence") in ("high", "low"), f"{pid}: confidence must be high or low")
        need(p.get("synthetic_deliveries") is True, f"{pid}: synthetic_deliveries must be true")
        need(all(h.get("synthetic") is True for h in p.get("history", [])), f"{pid}: history rows must be synthetic")
        need(p.get("synthetic_ndvi") is (ndvi_src == "synthetic"), f"{pid}: synthetic_ndvi does not match ndvi_source")
        need(p.get("has_referral_seed") is (pid in core.REFERRAL_SEEDED), f"{pid}: has_referral_seed wrong")
        if ndvi_src == "unavailable":
            need(p["ndvi_change"] is None and p["ndvi_z"] is None, f"{pid}: NDVI fields must be null")
            need(p["reason"] not in ("canopy_loss_check_leaves", "drop_other_cause_ask_officer"),
                 f"{pid}: NDVI-based reason without NDVI")
        elif p["reason"] != "not_enough_data" and (p["clear_obs"] is None or p["clear_obs"] < 6):
            need(p["confidence"] == "low", f"{pid}: fewer than 6 clear observations must be low confidence")
        need(p.get("sms_nudge_id") == core.NUDGE[p["reason"]], f"{pid}: sms_nudge_id does not match reason")

    # Recompute the model from the file and compare (consistency).
    model_in = [{"plot_id": p["plot_id"], "centroid": p["centroid"], "area_ha": p["area_ha"],
                 "history": {h["season"]: h["kg"] for h in p["history"]},
                 "ndvi_change": p["ndvi_change"], "clear_obs": p["clear_obs"]} for p in plots]
    re = core.run_model(model_in, rain["season_anomaly_pct"], ndvi_src != "unavailable")
    for r in re:
        p = by_id[r["plot_id"]]
        need(r["reason"] == p["reason"], f"{r['plot_id']}: recomputed reason {r['reason']} != file {p['reason']}")
        if r["gap_z"] is not None and p["gap_z"] is not None:
            need(abs(r["gap_z"] - p["gap_z"]) < 0.05, f"{r['plot_id']}: gap_z not reproducible")

    # Area-wide dip in 2022/23.
    dips = []
    for p in plots:
        h = {x["season"]: x["kg"] for x in p["history"]}
        if core.DROUGHT_SEASON in h and len(h) >= 4:
            others = [v for k, v in h.items() if k not in (core.DROUGHT_SEASON, core.LATEST)]
            dips.append(h[core.DROUGHT_SEASON] / float(np.median(others)) - 1)
    need(dips and float(np.median(dips)) < -0.15, "area-wide 2022/23 dip not present in deliveries")

    # Planted scenarios.
    rain_low = rain["season_anomaly_pct"] is not None and rain["season_anomaly_pct"] < core.THRESHOLDS["rain_anomaly_weather_pct"]
    rows = []
    for pid in sorted(by_id):
        planted = core.PLANTED.get(pid, "in_line_with_peers")
        expect, hard = planted, True
        if planted in ("canopy_loss_check_leaves", "drop_other_cause_ask_officer"):
            if ndvi_src == "unavailable":
                expect = "drop_check_leaves_or_ask"
            elif ndvi_src == "sentinel-2":
                hard = a.strict
        if planted == "area_wide_weather" and not rain_low:
            expect = "in_line_with_peers"      # real rainfall decides; blue only when rain was low
        if planted == "in_line_with_peers":
            hard = False
        got = by_id[pid]["reason"]
        ok = got == expect
        if not ok:
            (errors if hard else warns).append(f"{pid}: expected {expect}, got {got}")
        if pid in core.PLANTED or not ok:
            rows.append((pid, by_id[pid]["member_id"], planted, expect, got, by_id[pid]["confidence"], "ok" if ok else "MISMATCH"))
    extra = sum(1 for pid, p in by_id.items() if pid not in core.PLANTED and p["reason"] != "in_line_with_peers")
    if extra > 3:
        warns.append(f"{extra} plots without a planted scenario are flagged")

    for name, limit in (("outliers.json", 47_000), ("plots.geojson", 20_000)):
        size = os.path.getsize(paths[name])
        if size > limit:
            warns.append(f"{name} is {size} bytes (target under {limit})")

    counts = {k: sum(1 for p in plots if p["reason"] == k) for k in core.REASONS}
    print(f"ndvi_source={ndvi_src} rainfall={rain['season_anomaly_pct']} ({'synthetic' if rain['synthetic'] else rain['source']})")
    print("counts:", counts)
    if a.markdown:
        print("\n| Plot | Member | Planted | Expected | Got | Confidence | Check |\n|---|---|---|---|---|---|---|")
        for r in rows:
            print("| " + " | ".join(r) + " |")
    else:
        for r in rows:
            print("  ".join(f"{c:<29}" if i in (2, 3, 4) else f"{c:<8}" for i, c in enumerate(r)))
    for wmsg in warns:
        print("WARN", wmsg)
    for emsg in errors:
        print("FAIL", emsg)
    print("RESULT:", "FAIL" if errors else "PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
