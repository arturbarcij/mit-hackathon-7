#!/usr/bin/env python3
"""Build the Jani outlier map files.

    python app/geo/build_geo.py --mode offline          # numpy only, synthetic NDVI and rainfall
    python app/geo/build_geo.py --mode live             # real NASA POWER rainfall + Sentinel-2 NDVI
    python app/geo/build_geo.py --mode live --skip-s2   # cut line: real rainfall, no satellite layer

Writes app/public/geo/area.json, plots.geojson, outliers.json.
Deliveries and plot shapes are always synthetic. See kb/geo/RESULTS.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geo_core as core  # noqa: E402

REPO_APP = os.path.dirname(HERE)          # .../app
DEFAULT_OUT = os.path.join(REPO_APP, "public", "geo")
DEFAULT_CACHE = os.path.join(HERE, "cache")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
def offline_assignment(slots: list[core.Slot]) -> dict[str, core.Slot]:
    out, by_cluster = {}, {}
    for s in slots:
        by_cluster.setdefault(s.cluster, []).append(s)
    for c, ids in core.OFFLINE_ASSIGNMENT.items():
        for pid, s in zip(ids, by_cluster[c]):
            out[pid] = s
    assert len(out) == 40, len(out)
    return out


def live_assignment(slots: list[core.Slot], series: list[dict]) -> dict[str, core.Slot]:
    """Put the planted canopy-loss plots where the real NDVI change (relative to peers) is
    most negative, and the other-cause plots where it is closest to zero. Honest placement:
    the delivery drop is synthetic and was put on purpose where the satellite shows thinning."""
    ch = []
    for s, ser in zip(slots, series):
        c, obs = core.ndvi_change_from_series(ser)
        ch.append((c, obs))
    ll = np.array([[s.lon, s.lat] for s in slots])
    dist = core.pairwise_km(ll)
    gap = np.full(len(slots), np.nan)
    for i in range(len(slots)):
        if ch[i][0] is None:
            continue
        nb = [j for j in np.argsort(dist[i]) if j != i and ch[j][0] is not None and dist[i, j] <= 2.0][:8]
        if nb:
            gap[i] = ch[i][0] - float(np.median([ch[j][0] for j in nb]))
    z = core.robust_z(gap)
    free = [i for i, s in enumerate(slots) if s.cluster != "E"]
    out: dict[str, core.Slot] = {}
    e_slots = [s for s in slots if s.cluster == "E"]
    for pid, s in zip(core.CORNER_CLUSTER, e_slots):
        out[pid] = s

    def good_obs(i):
        return ch[i][1] is not None and ch[i][1] >= core.THRESHOLDS["min_clear_obs"]

    cand = sorted([i for i in free if np.isfinite(z[i])], key=lambda i: (not good_obs(i), z[i]))
    for pid, i in zip(core.CANOPY_LOSS, cand[:4]):
        out[pid] = slots[i]
        free.remove(i)
    cand = sorted([i for i in free if np.isfinite(z[i])], key=lambda i: (not good_obs(i), abs(z[i])))
    for pid, i in zip(core.OTHER_CAUSE, cand[:2]):
        out[pid] = slots[i]
        free.remove(i)
    for pid, cl in zip(core.NOT_ENOUGH, ["A", "C", "D"]):
        i = next((k for k in free if slots[k].cluster == cl), free[0])
        out[pid] = slots[i]
        free.remove(i)
    rest = [f"P{n:02d}" for n in range(1, 41) if f"P{n:02d}" not in out]
    for pid, i in zip(rest, free):
        out[pid] = slots[i]
    assert len(out) == 40, len(out)
    return out


# ---------------------------------------------------------------------------
def get_rainfall(mode: str, cache: str, skip: bool) -> dict:
    synthetic = {
        "season_anomaly_pct": core.SYNTHETIC_RAIN[core.LATEST],
        "source": "synthetic (offline mode; replaced by NASA POWER in live mode)",
        "synthetic": True,
        "baseline": "1991 to 2020 mean of the same months (synthetic values)",
        "point": [core.CENTRE_LON, core.CENTRE_LAT],
        "series": [{"season": s, "anomaly_pct": core.SYNTHETIC_RAIN[s]} for s in core.SEASONS],
    }
    if mode == "offline":
        return synthetic
    unavailable = {"season_anomaly_pct": None, "source": "unavailable (NASA POWER request failed)",
                   "synthetic": False, "series": [], "point": [core.CENTRE_LON, core.CENTRE_LAT]}
    if skip:
        unavailable["source"] = "unavailable (skipped with --skip-rain)"
        return unavailable
    try:
        import geo_live as live
        days = live.fetch_power_daily(core.CENTRE_LON, core.CENTRE_LAT, cache)
        rows = live.season_anomalies(days, core.SEASONS)
        last = max(d for d, v in days.items() if v is not None)
        latest = next(r for r in rows if r["season"] == core.LATEST)
        log(f"rainfall anomalies: {[(r['season'], r['anomaly_pct']) for r in rows]} (data through {last})")
        return {
            "season_anomaly_pct": latest["anomaly_pct"],
            "source": "NASA POWER daily PRECTOTCORR at the box centre",
            "synthetic": False,
            "baseline": "1991 to 2020 mean of the same calendar days",
            "point": [core.CENTRE_LON, core.CENTRE_LAT],
            "through": last.isoformat(),
            "series": [{"season": r["season"], "anomaly_pct": r["anomaly_pct"]} for r in rows],
        }
    except Exception as e:  # noqa: BLE001
        log(f"NASA POWER failed: {e!r}; rainfall marked unavailable")
        return unavailable


def build(args) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    bbox = core.area_bbox()
    log(f"mode {args.mode}, seed {args.seed}, bbox {bbox}")
    rain = get_rainfall(args.mode, args.cache, args.skip_rain)

    ndvi_source = "synthetic"
    series_by_id: dict[str, dict] = {}
    s2_note = None
    if args.mode == "offline":
        slots = core.generate_slots(rng, bbox)
        assign = offline_assignment(slots)
        syn = core.synthetic_ndvi(rng, sorted(assign))
        series_by_id = {pid: syn[pid] for pid in assign}
    else:
        assign = None
        if not args.skip_s2:
            try:
                import geo_live as live
                grid, stack = live.fetch_ndvi_stack(bbox, args.cache, args.max_dates, args.workers)
                n_dates = sum(len(v) for v in stack.values())
                if n_dates == 0:
                    raise RuntimeError("no Sentinel-2 dates could be read")
                scorer = live.vegetation_scorer(grid, stack)
                slots = core.generate_slots(rng, bbox, accept=scorer)
                veg = [scorer(s.ring) for s in slots]
                log(f"plots on vegetated pixels: median share {np.median(veg):.0%}, min {min(veg):.0%}")
                series = [live.plot_ndvi_series(s.ring, grid, stack) for s in slots]
                assign = live_assignment(slots, series)
                idx = {id(s): k for k, s in enumerate(slots)}
                series_by_id = {pid: series[idx[id(s)]] for pid, s in assign.items()}
                ndvi_source = "sentinel-2"
            except Exception as e:  # noqa: BLE001
                log(f"Sentinel-2 failed: {e!r}; NDVI fields set to null")
                s2_note = f"Sentinel-2 step failed: {type(e).__name__}"
        if assign is None:
            ndvi_source = "unavailable"
            slots = core.generate_slots(rng, bbox)
            assign = offline_assignment(slots)
            series_by_id = {}

    ids = sorted(assign)
    area = {pid: assign[pid].area_ha for pid in ids}
    deliveries = core.synthetic_deliveries(rng, ids, area)
    ndvi_available = ndvi_source != "unavailable"

    model_in = []
    for pid in ids:
        s = assign[pid]
        ch, obs = core.ndvi_change_from_series(series_by_id[pid]) if ndvi_available else (None, None)
        model_in.append({"plot_id": pid, "centroid": core.ring_centroid(s.ring), "area_ha": s.area_ha,
                         "history": deliveries[pid], "ndvi_change": ch, "clear_obs": obs})
    results = core.run_model(model_in, rain["season_anomaly_pct"], ndvi_available)
    peer_hist = core.peer_median_history(model_in, results)

    plots_out, features = [], []
    for m, r in zip(model_in, results):
        pid = m["plot_id"]
        rec = {
            "plot_id": pid, "member_id": core.member_id(pid), "area_ha": m["area_ha"],
            "centroid": m["centroid"],
            "own_change_pct": r["own_change_pct"], "peer_change_pct": r["peer_change_pct"],
            "gap_z": r["gap_z"], "ndvi_change": r["ndvi_change"], "ndvi_z": r["ndvi_z"],
            "clear_obs": r["clear_obs"], "reason": r["reason"], "confidence": r["confidence"],
            "sms_nudge_id": r["sms_nudge_id"], "peer_ids": r["peer_ids"],
            "synthetic_deliveries": True, "synthetic_ndvi": ndvi_source == "synthetic",
            "has_referral_seed": pid in core.REFERRAL_SEEDED,
            "history": [{"season": s, "kg": deliveries[pid][s], "synthetic": True}
                        for s in core.SEASONS if deliveries[pid][s] is not None],
            "peer_median_history": peer_hist[pid],
            "ndvi_series": ([{"period": p, "ndvi": series_by_id[pid][p][0], "clear_obs": series_by_id[pid][p][1]}
                             for p in core.NDVI_PERIODS if p.endswith("JAS")] if ndvi_available else []),
        }
        plots_out.append(rec)
        features.append({"type": "Feature",
                         "properties": {"plot_id": pid, "member_id": rec["member_id"], "area_ha": m["area_ha"],
                                        "reason": r["reason"], "confidence": r["confidence"], "synthetic": True},
                         "geometry": {"type": "Polygon", "coordinates": [assign[pid].ring]}})

    counts = {k: sum(1 for r in results if r["reason"] == k) for k in core.REASONS}
    t = core.THRESHOLDS
    oc = "officer to confirm"
    assumptions = [
        {"name": "gap_z_threshold", "value": t["gap_z"], "note": oc},
        {"name": "ndvi_z_threshold", "value": t["ndvi_z"], "note": oc},
        {"name": "peer_change_weather_pct", "value": t["peer_change_weather_pct"], "note": oc},
        {"name": "rain_anomaly_weather_pct", "value": t["rain_anomaly_weather_pct"], "note": oc},
        {"name": "min_seasons", "value": t["min_seasons"], "note": oc},
        {"name": "min_peers", "value": t["min_peers"], "note": oc},
        {"name": "n_peers", "value": t["n_peers"], "note": oc},
        {"name": "peer_radius_km", "value": t["peer_radius_km"], "note": oc},
        {"name": "min_clear_obs", "value": t["min_clear_obs"], "note": oc},
        {"name": "near_threshold_margin", "value": t["near_threshold_margin"], "note": oc},
        {"name": "cherry_to_clean_ratio", "value": core.CHERRY_TO_CLEAN,
         "note": "assumption, kg cherry per kg clean coffee, not verified for Nyeri; officer to confirm"},
        {"name": "base_yield_clean_kg_ha", "value": core.BASE_YIELD_CLEAN_KG_HA,
         "note": "KNBS 2025 Table 5.1.2, co-operatives 2023/24; used only to size synthetic deliveries"},
    ]
    sources = ["KNBS 2025 Table 5.1.2 (base yield for synthetic deliveries)"]
    if ndvi_source == "sentinel-2":
        sources.insert(0, "Sentinel-2 L2A via Earth Search (Copernicus data)")
    if not rain["synthetic"] and rain["season_anomaly_pct"] is not None:
        sources.insert(0, "NASA POWER")
    notes = [
        "Deliveries, plot shapes, plot locations and member ids are synthetic.",
        "NDVI: " + {"synthetic": "synthetic in this build (offline mode).",
                    "sentinel-2": "real Sentinel-2 L2A dry-season composites; plots placed on vegetated pixels, "
                                  "planted canopy-loss plots placed where the real NDVI change is most negative.",
                    "unavailable": "not available in this build; reason codes fall back to drop_check_leaves_or_ask."}[ndvi_source],
        "Rainfall: " + ("synthetic in this build." if rain["synthetic"] else rain["source"] + "."),
        "The map decides where to look, the leaf check decides what it is, the officer decides what to do.",
    ]
    if s2_note:
        notes.append(s2_note)
    outliers = {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "season": core.LATEST,
        "mode": args.mode, "seed": args.seed,
        "area": {"name": core.AREA_NAME, "bbox": bbox, "centre": [core.CENTRE_LON, core.CENTRE_LAT]},
        "ndvi_source": ndvi_source,
        "ndvi_latest_period": core.LATEST_NDVI_PERIOD,
        "ndvi_periods_note": "ndvi_series = Jul to Sep composites; change = latest vs own median of earlier ones",
        "rainfall": rain,
        "synthetic_deliveries": True,
        "reason_notes": {
            "canopy_loss_check_leaves": "Canopy thinned more than nearby farms. Can be leaf rust, drought stress, pruning or stumping. A leaf check helps; the officer decides.",
            "drop_other_cause_ask_officer": "Delivered less than nearby farms but the canopy looks normal. Deliveries are not production (side-selling, late picking, old trees). Ask the officer.",
            "drop_check_leaves_or_ask": "Delivered less than nearby farms; no satellite layer. Check leaves or ask the officer.",
            "area_wide_weather": "Nearby farms dropped too and rain was low. Weather is the likely cause.",
            "in_line_with_peers": "In line with nearby farms. If nearby farms all dropped with normal rain, ask the officer (for example berry disease or input cuts).",
            "not_enough_data": "Too few seasons or too few nearby farms to compare.",
        },
        "counts": counts,
        "assumptions": assumptions,
        "attribution": "Contains modified Copernicus Sentinel data 2022 to 2026" if ndvi_source == "sentinel-2" else None,
        "sources": sources,
        "notes": notes,
        "plots": plots_out,
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "area.json"), "w", encoding="utf-8") as f:
        json.dump(core.area_json(), f, indent=1, ensure_ascii=False)
    with open(os.path.join(args.out, "plots.geojson"), "w", encoding="utf-8") as f:
        f.write('{"type":"FeatureCollection","name":"jani_plots_synthetic","features":[\n')
        f.write(",\n".join(json.dumps(ft, separators=(",", ":")) for ft in features))
        f.write("\n]}\n")
    with open(os.path.join(args.out, "outliers.json"), "w", encoding="utf-8") as f:
        head = {k: v for k, v in outliers.items() if k != "plots"}
        txt = json.dumps(head, separators=(",", ":"), ensure_ascii=False)
        f.write(txt[:-1] + ',"plots":[\n')
        f.write(",\n".join(json.dumps(p, separators=(",", ":")) for p in plots_out))
        f.write("\n]}\n")
    log(f"reason counts: {counts}")
    for name in ("area.json", "plots.geojson", "outliers.json"):
        log(f"wrote {os.path.join(args.out, name)} ({os.path.getsize(os.path.join(args.out, name))} bytes)")
    log(f"done in {time.time() - t0:.0f} s")
    return outliers


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["offline", "live"], default="offline")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--cache", default=DEFAULT_CACHE, help="download cache (git-ignored)")
    ap.add_argument("--max-dates", type=int, default=10, help="Sentinel-2 dates per composite (lowest cloud first)")
    ap.add_argument("--workers", type=int, default=6, help="parallel scene downloads")
    ap.add_argument("--skip-s2", action="store_true", help="live mode without Sentinel-2 (cut line)")
    ap.add_argument("--skip-rain", action="store_true", help="live mode without NASA POWER")
    args = ap.parse_args(argv)
    build(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
