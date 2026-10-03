"""Robust-z outlier model for cooperative deliveries, with reason codes.

Not machine learning: median and MAD across the cooperative's own members.
Peer-relative scores remove area-wide effects (a dry year hits everyone), so a
plot is flagged only when it moves differently from its neighbours.

Inputs: data/registry.geojson (synthetic), cache/ndvi_*.tif (real Sentinel-2),
data/rainfall.json (real NASA POWER).
Outputs: public/geo/plots.geojson, public/geo/outliers.json,
public/geo/ndvi_change.png, data/eval.json.
"""
import json
import warnings
from datetime import datetime, timezone

import numpy as np
import rasterio
import rasterio.errors
from pyproj import Transformer
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, calculate_default_transform, reproject
from shapely.geometry import shape as shp_shape, mapping
from shapely.ops import transform as shp_transform

import config as C

warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)

VERSION = "geo-1"
PRIOR = [s for s in C.COFFEE_YEARS if s != C.CURRENT_SEASON]

LEGEND = {  # officer-facing labels; farmer-facing text lives in answers.json
    "delivery_drop": "Deliveries fell much more than at other members",
    "drop_with_canopy_loss": "Deliveries fell and the satellite shows less green canopy than in past years",
    "drop_canopy_normal": "Deliveries fell but the canopy looks normal: may be sold elsewhere, picked late, or a record gap. Ask, do not assume",
    "delivery_spike": "Deliveries rose much more than at other members",
    "above_plausible_yield": "Deliveries per registered tree are above good-practice yields: check the tree count and who delivered",
    "canopy_loss": "Canopy fell sharply this dry season while deliveries were not flagged: visit before the next harvest",
    "short_history": "Fewer than two past seasons of deliveries",
    "missing_delivery_record": "No delivery recorded this season",
    "plot_too_small": "Plot is too small for 10 m satellite pixels",
    "few_clear_pixels": "Too few cloud-free satellite pixels over the plot",
    "canopy_signal_unclear": "Satellite signal is between normal and loss",
}
NEXT_STEP = {
    "drop_with_canopy_loss": "visit",
    "canopy_loss": "visit",
    "drop_canopy_normal": "call_member",
    "delivery_spike": "call_member",
    "above_plausible_yield": "check_records",
}


def robust_z(values):
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], float)
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med))) * 1.4826
    return med, mad


def z(x, med, mad):
    if x is None or not np.isfinite(x) or mad <= 0:
        return None
    return (x - med) / mad


def classify(zd, zn, *, area_ha, clear_px, total_px, kg_missing, prior_n, kg_per_tree):
    """Decide status, reasons and abstentions for one plot from its two z-scores.

    zd: delivery z (None if not computable). zn: local canopy z (None if not computable).
    Returns (status, confidence, next_step, reasons, abstain).
    """
    reasons, abstain = [], []
    clear_frac = clear_px / max(1, total_px)
    ndvi_ok = True
    if area_ha < C.MIN_AREA_HA:
        abstain.append("plot_too_small"); ndvi_ok = False
    elif clear_px < C.MIN_CLEAR_PIXELS or clear_frac < C.MIN_CLEAR_FRACTION:
        abstain.append("few_clear_pixels"); ndvi_ok = False
    if kg_missing:
        abstain.append("missing_delivery_record")
    elif prior_n < C.MIN_PRIOR_SEASONS:
        abstain.append("short_history")
    delivery_ok = not any(a in abstain for a in ("missing_delivery_record", "short_history"))

    # Two independent signals may corroborate each other: a moderate delivery drop
    # counts when the canopy has also clearly fallen.
    strong_canopy_loss = ndvi_ok and zn is not None and zn <= -C.Z_FLAG
    drop_limit = C.Z_CORROBORATED if strong_canopy_loss else C.Z_FLAG
    if zd is not None and delivery_ok and zd <= -drop_limit:
        if not ndvi_ok or zn is None:
            reasons.append("delivery_drop")
        elif zn <= -2.0:
            reasons.append("drop_with_canopy_loss")
        elif zn > C.Z_CANOPY_NORMAL:
            reasons.append("drop_canopy_normal")
        else:
            reasons.append("delivery_drop"); abstain.append("canopy_signal_unclear")
    elif zd is not None and delivery_ok and zd >= C.Z_FLAG:
        reasons.append("delivery_spike")
    if kg_per_tree is not None and kg_per_tree > C.MAX_KG_PER_TREE:
        reasons.append("above_plausible_yield")
    if strong_canopy_loss and "drop_with_canopy_loss" not in reasons:
        reasons.append("canopy_loss")

    if abstain and (reasons or not delivery_ok or not ndvi_ok):
        status, confidence, next_step = "unsure", "low", "ask_officer"
    elif reasons:
        status, confidence = "outlier", "high"
        next_step = NEXT_STEP.get(reasons[0], "ask_officer")
    else:
        status, confidence, next_step = "normal", "high", "none"
    # A normal delivery pattern with unusable NDVI is still "normal" on deliveries,
    # but we say the canopy was not checked.
    if status == "normal" and not ndvi_ok:
        status, confidence, next_step = "unsure", "low", "ask_officer"
    return status, confidence, next_step, reasons, abstain


def plot_ndvi(poly_utm, rasters, transform, shape):
    px = ~geometry_mask([mapping(poly_utm)], out_shape=shape, transform=transform, all_touched=False)
    out = {}
    for s, arr in rasters.items():
        vals = arr[px]
        good = vals[np.isfinite(vals)]
        out[s] = {"median": float(np.median(good)) if good.size else None,
                  "clearPx": int(good.size), "totalPx": int(px.sum())}
    return out


def r(x, n=3):
    return None if x is None else round(float(x), n)


def main():
    reg = json.loads((C.DATA / "registry.geojson").read_text())
    rain = json.loads((C.DATA / "rainfall.json").read_text())
    sup_path = C.DATA / "season_support.json"
    sup = json.loads(sup_path.read_text()) if sup_path.exists() else None
    rasters = {}
    for s in C.COFFEE_YEARS:
        with rasterio.open(C.CACHE / f"ndvi_{s.replace('/', '-')}.tif") as src:
            rasters[s] = src.read(1)
            transform, shape, crs = src.transform, (src.height, src.width), src.crs
    to_utm = Transformer.from_crs(4326, C.UTM_EPSG, always_xy=True).transform

    rows = []
    for f in reg["features"]:
        p = f["properties"]
        poly = shp_transform(to_utm, shp_shape(f["geometry"]))
        nd = plot_ndvi(poly, rasters, transform, shape)
        dl = {d["season"]: d["kgCherry"] for d in p["deliveries"]}
        trees = p["treesRegistered"]
        cur_kg = dl.get(C.CURRENT_SEASON)
        prior_kg = [dl[s] for s in PRIOR if dl.get(s) is not None]
        cur_kpt = None if cur_kg is None else cur_kg / trees
        base_kpt = float(np.median(prior_kg)) / trees if prior_kg else None
        log_change = np.log(cur_kpt / base_kpt) if (cur_kpt and base_kpt) else None
        nd_cur = nd[C.CURRENT_SEASON]
        nd_prior = [nd[s]["median"] for s in PRIOR if nd[s]["median"] is not None]
        nd_base = float(np.median(nd_prior)) if nd_prior else None
        nd_change = (nd_cur["median"] - nd_base) if (nd_cur["median"] is not None and nd_base is not None) else None
        rows.append(dict(f=f, p=p, nd=nd, centre=(poly.centroid.x, poly.centroid.y), cur_kg=cur_kg, prior_n=len(prior_kg), cur_kpt=cur_kpt,
                         base_kpt=base_kpt, log_change=log_change, nd_cur=nd_cur, nd_base=nd_base,
                         nd_change=nd_change))

    # Peer statistics use only plots with enough data, so thin records cannot drag them.
    d_med, d_mad = robust_z([x["log_change"] for x in rows if x["prior_n"] >= C.MIN_PRIOR_SEASONS])
    # Canopy baseline is local: the median change of the nearest plots, so a broad
    # regional shift (a dry corner, a hillside) is not read as plot-level loss.
    usable = [i for i, x in enumerate(rows) if x["nd_change"] is not None and x["nd_cur"]["clearPx"] >= C.MIN_CLEAR_PIXELS]
    cen = np.array([x["centre"] for x in rows])
    for i, x in enumerate(rows):
        dist = np.hypot(*(cen[usable] - cen[i]).T)
        near = [usable[j] for j in np.argsort(dist) if usable[j] != i][:C.LOCAL_K]
        x["nd_local"] = float(np.median([rows[j]["nd_change"] for j in near]))
    resid = [x["nd_change"] - x["nd_local"] for x in rows if x["nd_change"] is not None and x["nd_cur"]["clearPx"] >= C.MIN_CLEAR_PIXELS]
    n_med, n_mad = 0.0, robust_z(resid)[1]

    out_plots, features = [], []
    for x in rows:
        p = x["p"]
        zd = z(x["log_change"], d_med, d_mad)
        zn = z(None if x["nd_change"] is None else x["nd_change"] - x["nd_local"], n_med, n_mad)
        status, confidence, next_step, reasons, abstain = classify(
            zd, zn, area_ha=p["areaHa"], clear_px=x["nd_cur"]["clearPx"], total_px=x["nd_cur"]["totalPx"],
            kg_missing=x["cur_kg"] is None, prior_n=x["prior_n"], kg_per_tree=x["cur_kpt"])

        scores = [abs(v) for v in (zd, zn) if v is not None]
        rec = {
            "plotId": p["plotId"], "memberId": p["memberId"], "plot": p["plot"],
            "status": status, "confidence": confidence, "reasons": reasons, "abstainReasons": abstain,
            "nextStep": next_step, "score": r(max(scores) if scores else None, 2),
            "metrics": {
                "kgCherry": x["cur_kg"], "kgPerTree": r(x["cur_kpt"], 2), "kgPerTreeBaseline": r(x["base_kpt"], 2),
                "changePct": None if x["log_change"] is None else round(100 * (np.exp(x["log_change"]) - 1), 1),
                "zDelivery": r(zd, 2), "priorSeasons": x["prior_n"],
                "ndvi": r(x["nd_cur"]["median"]), "ndviBaseline": r(x["nd_base"]),
                "ndviChange": r(x["nd_change"]), "ndviLocalChange": r(x["nd_local"]), "zNdvi": r(zn, 2),
                "clearPx": x["nd_cur"]["clearPx"], "totalPx": x["nd_cur"]["totalPx"],
            },
            "synthetic": True,
        }
        out_plots.append(rec)
        props = dict(p)
        props.update({"status": status, "reason": (reasons or abstain or [None])[0], "nextStep": next_step,
                      "ndviSeries": [{"season": s, **x["nd"][s]} for s in C.COFFEE_YEARS]})
        for item in props["ndviSeries"]:
            item["median"] = r(item["median"])
        features.append({"type": "Feature", "geometry": x["f"]["geometry"], "properties": props})

    rank = {"outlier": 0, "unsure": 1, "normal": 2}
    out_plots.sort(key=lambda o: (rank[o["status"]], -(o["score"] or 0)))

    coop_change = 100 * (np.exp(d_med) - 1)
    rc = rain["coffeeYears"][C.CURRENT_SEASON]
    area_wide = coop_change <= -10
    lon0, lat0, lon1, lat1 = C.BBOX
    counts = {k: sum(1 for o in out_plots if o["status"] == k) for k in rank}

    write_overlay(rasters, transform, crs)

    outliers = {
        "version": VERSION,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "season": C.CURRENT_SEASON,
        "area": {"name": C.AREA_NAME, "bbox": list(C.BBOX), "centre": [round((lon0 + lon1) / 2, 4), round((lat0 + lat1) / 2, 4)]},
        "synthetic": {"plots": True, "deliveries": True, "members": True, "ndvi": False, "rainfall": False},
        "method": {
            "model": "robust z-score (median and 1.4826 x MAD across members), no machine learning",
            "deliveryMetric": "log(kg cherry per registered tree this season / median of prior seasons)",
            "ndviMetric": "plot median dry-season NDVI this season minus median of prior seasons, minus the median of that change over the 12 nearest plots",
            "thresholds": {"zFlag": C.Z_FLAG, "zDropCorroborated": C.Z_CORROBORATED, "zCanopyLoss": -2.0, "zCanopyNormal": C.Z_CANOPY_NORMAL,
                           "minPriorSeasons": C.MIN_PRIOR_SEASONS, "minClearPixels": C.MIN_CLEAR_PIXELS,
                           "minClearFraction": C.MIN_CLEAR_FRACTION, "minAreaHa": C.MIN_AREA_HA,
                           "maxKgPerTree": C.MAX_KG_PER_TREE},
            "peerStats": {"deliveryMedianLog": r(d_med, 4), "deliveryMad": r(d_mad, 4),
                          "ndviLocalResidualMad": r(n_mad, 4), "localNeighbours": C.LOCAL_K},
        },
        "context": {
            "cooperativeMedianChangePct": round(float(coop_change), 1),
            "areaWideDrop": bool(area_wide),
            "rainfall": {"shortRainsAnomalyPct": rc["short_rains"]["anomalyPct"],
                         "longRainsAnomalyPct": rc["long_rains"]["anomalyPct"],
                         "coffeeYearTotalMm": rc["coffeeYearTotalMm"],
                         "climatology": rain["climatology"]["years"], "source": "NASA POWER PRECTOTCORR"},
            "ndviWindowRain": None if sup is None else {
                **sup["ndviWindowRain"][C.CURRENT_SEASON],
                "caveat": "The current NDVI window was much wetter than usual, so it is less comparable with drier prior windows. "
                          "Plots are scored against nearby plots, which cancels most of this, but treat small canopy changes with care."},
            "shortRains": None if sup is None else {
                "medianOnset": sup["short_rains"]["climatology1991to2020"]["medianDate"],
                "sdDays": sup["short_rains"]["climatology1991to2020"]["sdDays"],
                "shareOnsetBefore15Oct": sup["short_rains"]["shareOnsetBefore"]["15 Oct"],
                "onsetConfirmedThisYear": sup["thisYear"]["shortRainsOnsetConfirmed"],
                "dataEnd": sup["thisYear"]["dataEnd"], "source": "NASA POWER, simplified onset rule (assumption)"},
            "ndviSeasonMedians": {s: r(float(np.nanmedian(a))) for s, a in rasters.items()},
        },
        "overlay": {"image": "/geo/ndvi_change.png", "bounds": OVERLAY_BOUNDS,
                    "meaning": "NDVI change, this dry season minus median of prior three, relative to area median. Red is loss, green is gain. Real Sentinel-2 data."},
        "counts": counts,
        "legend": LEGEND,
        "nextSteps": {"visit": "Plan an officer visit", "call_member": "Call or ask the member at the factory",
                      "check_records": "Check the registry and delivery records", "ask_officer": "Not sure: officer decides",
                      "none": "No action"},
        "sources": [
            {"id": "s2", "name": "Sentinel-2 L2A (Copernicus), via Element 84 Earth Search STAC on AWS Open Data",
             "url": C.STAC_URL, "licence": "Copernicus Sentinel data terms (free, full and open)",
             "use": "Dry-season NDVI composites Jan 1 to Mar 15, 2023 to 2026, SCL mask keeps classes 4 and 5"},
            {"id": "power", "name": "NASA POWER daily, PRECTOTCORR", "url": C.POWER_URL,
             "licence": "NASA open data", "use": "Seasonal rainfall anomalies vs 1991 to 2020"},
            {"id": "nyeri_yield", "name": "Mugendi, Orero, Mwiti (2015), Asian Journal of Business and Management 3(6), citing MOALF 2014",
             "url": "https://ajouronline.com/index.php/AJBM/article/view/3270",
             "use": "Nyeri County average about 3.0 kg cherry per tree (2013/14), baseline for synthetic deliveries"},
            {"id": "coffee_yearbook", "name": "Coffee Directorate, Coffee Year Book 2022/23",
             "url": "https://www.kenyacoffee.co.ke/resources/2023/Coffee%20Book%20Year%202023-24-compressed.pdf",
             "use": "1,300 trees per ha for SL28 and SL34, used for synthetic tree counts"},
        ],
        "plots": out_plots,
    }
    C.OUT.mkdir(parents=True, exist_ok=True)
    (C.OUT / "outliers.json").write_text(json.dumps(outliers, indent=1))
    (C.OUT / "plots.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "synthetic": True, "season": C.CURRENT_SEASON,
         "note": "Synthetic plots and deliveries on real land. NDVI series are real Sentinel-2.",
         "features": features}, separators=(",", ":")))

    evaluate(out_plots)
    print(f"counts {counts}; cooperative median change {coop_change:.1f}%")


OVERLAY_BOUNDS = None


def write_overlay(rasters, transform, crs):
    """Real NDVI change as a small RGBA PNG in WGS84 for a map image overlay."""
    global OVERLAY_BOUNDS
    prior = np.nanmedian(np.stack([rasters[s] for s in PRIOR]), axis=0)
    rel = rasters[C.CURRENT_SEASON] - prior
    rel = (rel - np.nanmedian(rel)).astype("float32")
    h, w = rel.shape
    left, top = transform.c, transform.f
    right, bottom = left + w * transform.a, top + h * transform.e
    dst_t, dw, dh = calculate_default_transform(crs, "EPSG:4326", w, h, left, bottom, right, top)
    dst = np.full((dh, dw), np.nan, "float32")
    reproject(rel, dst, src_transform=transform, src_crs=crs, dst_transform=dst_t, dst_crs="EPSG:4326",
              resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
    v = np.clip(np.nan_to_num(dst) / 0.2, -1, 1)
    rgba = np.zeros((4, dh, dw), "uint8")
    loss, gain = v < 0, v > 0
    rgba[0] = np.where(loss, 215, np.where(gain, 40, 0))
    rgba[1] = np.where(loss, 48, np.where(gain, 150, 0))
    rgba[2] = np.where(loss, 39, np.where(gain, 70, 0))
    alpha = np.clip(np.abs(v) * 200, 0, 170)
    alpha[np.abs(v) < 0.25] = 0  # hide noise near zero
    alpha[np.isnan(dst)] = 0
    rgba[3] = alpha.astype("uint8")
    C.OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(C.OUT / "ndvi_change.png", "w", driver="PNG", width=dw, height=dh, count=4, dtype="uint8") as png:
        png.write(rgba)
    for extra in C.OUT.glob("ndvi_change.png.aux.xml"):
        extra.unlink()
    OVERLAY_BOUNDS = [[round(dst_t.f + dh * dst_t.e, 6), round(dst_t.c, 6)],
                      [round(dst_t.f, 6), round(dst_t.c + dw * dst_t.a, 6)]]  # [[south, west], [north, east]]


EXPECTED = {
    "decline_with_canopy_loss": ("outlier", "drop_with_canopy_loss"),
    "delivery_gap_canopy_ok": ("outlier", "drop_canopy_normal"),
    "over_delivery": ("outlier", "delivery_spike"),
    "canopy_loss_early": ("outlier", "canopy_loss"),
    "new_member": ("unsure", None),
    "tiny_plot": ("unsure", None),
    "missing_record": ("unsure", None),
    "normal": ("normal", None),
}


def evaluate(out_plots):
    truth = json.loads((C.DATA / "truth.json").read_text())["plots"]
    rows, hits = [], 0
    confusion: dict = {}
    for o in out_plots:
        sc = truth[o["plotId"]]
        exp_status, exp_reason = EXPECTED[sc]
        ok = o["status"] == exp_status and (exp_reason is None or exp_reason in o["reasons"])
        hits += ok
        key = f"{sc} -> {o['status']}"
        confusion[key] = confusion.get(key, 0) + 1
        if not ok:
            rows.append({"plotId": o["plotId"], "scenario": sc, "status": o["status"], "reasons": o["reasons"],
                         "abstain": o["abstainReasons"], "zDelivery": o["metrics"]["zDelivery"], "zNdvi": o["metrics"]["zNdvi"]})
    planted = [o for o in out_plots if truth[o["plotId"]] != "normal"]
    normals = [o for o in out_plots if truth[o["plotId"]] == "normal"]
    res = {
        "synthetic": True,
        "note": "Scores on planted synthetic scenarios. They show the logic works as designed, not that it works on real cooperatives.",
        "plots": len(out_plots), "matchedExpected": hits,
        "plantedCaught": sum(1 for o in planted if o["status"] == EXPECTED[truth[o["plotId"]]][0]),
        "planted": len(planted),
        "normalFlagged": sum(1 for o in normals if o["status"] != "normal"),
        "normal": len(normals),
        "confusion": dict(sorted(confusion.items())),
        "mismatches": rows,
    }
    (C.DATA / "eval.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
