"""Synthetic cooperative registry: plots, deliveries and planted scenarios.

SYNTHETIC. Every member, plot polygon, tree count and delivery here is made up
with a fixed seed. Only the land under the polygons (Sentinel-2) and the
rainfall (NASA POWER) are real. Plots for the canopy-loss scenarios are placed
on patches where the real dry-season NDVI fell; we do not know why it fell
(stumping, pruning, felling, disease or a new building are all possible).
"""
import json

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import geometry_mask
from scipy.ndimage import uniform_filter
from shapely.geometry import Polygon, mapping
from shapely.ops import transform as shp_transform

import config as C

N_PLOTS = 80
# Synthetic cooperative-wide multiplier per coffee year (weather, prices, labour).
# Assumption, loosely following the real rainfall pattern: poor 2022 short rains,
# very wet 2023/24, normal 2024/25, below-normal 2025 short rains.
AREA_FACTOR = {"2022/23": 0.85, "2023/24": 1.05, "2024/25": 1.00, "2025/26": 0.85}
NOISE_SD = 0.15  # lognormal noise on each delivery (assumption)

SCENARIOS = {
    # name: (count, delivery multiplier in current season, placement)
    "decline_with_canopy_loss": (4, 0.45, "loss_patch"),
    "delivery_gap_canopy_ok":   (4, 0.40, "stable"),
    "over_delivery":            (2, 2.30, "stable"),
    "canopy_loss_early":        (2, 1.00, "loss_patch"),
    "new_member":               (2, 1.00, "stable"),
    "tiny_plot":                (2, 0.50, "stable"),
    "missing_record":           (1, None, "stable"),
}
NOOR = ("OCC0412", 2)  # contract example member; her plot gets the canopy-loss decline


def load_ndvi():
    arrs, nobs = {}, {}
    for s in C.COFFEE_YEARS:
        with rasterio.open(C.CACHE / f"ndvi_{s.replace('/', '-')}.tif") as src:
            arrs[s] = src.read(1)
            nobs[s] = src.read(2)
            transform, shape = src.transform, (src.height, src.width)
    return arrs, nobs, transform, shape


def rect(cx, cy, area_m2, aspect, angle, rng):
    w = np.sqrt(area_m2 * aspect)
    h = area_m2 / w
    pts = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]])
    pts += rng.normal(0, 0.06 * min(w, h), pts.shape)  # irregular, like real plots
    ca, sa = np.cos(angle), np.sin(angle)
    rot = pts @ np.array([[ca, sa], [-sa, ca]])
    return Polygon(rot + [cx, cy])


def plot_pixels(poly, transform, shape):
    return ~geometry_mask([mapping(poly)], out_shape=shape, transform=transform, all_touched=False)


def main():
    rng = np.random.default_rng(C.SEED)
    ndvi, _, transform, shape = load_ndvi()
    prior = np.nanmedian(np.stack([ndvi[s] for s in C.COFFEE_YEARS if s != C.CURRENT_SEASON]), axis=0)
    cur = ndvi[C.CURRENT_SEASON]
    change = cur - prior
    rel = change - np.nanmedian(change)
    smooth = uniform_filter(np.nan_to_num(rel), size=5)
    # Coffee is evergreen: keep land that is green in the wet season too and whose NDVI
    # barely moves between dry (2025) and wet (2025) seasons. Annual crops and bare
    # fields swing more. This is a plausibility filter, not a coffee map.
    with rasterio.open(C.CACHE / "ndvi_wet-2025.tif") as src:
        wet = src.read(1)
    perennial = (wet >= 0.60) & (np.abs(ndvi["2024/25"] - wet) <= 0.15)
    vegetated = (prior >= 0.55) & (prior <= 0.88) & perennial

    x0, y1 = transform.c, transform.f
    x1, y0 = x0 + shape[1] * 10, y1 - shape[0] * 10
    margin = 120
    placed: list[Polygon] = []

    def free(poly):
        buf = poly.buffer(12)
        return all(not buf.intersects(p) for p in placed)

    def try_place(cx, cy, area_ha, need):
        for _ in range(40):
            poly = rect(cx, cy, area_ha * 1e4, rng.uniform(0.6, 2.2), rng.uniform(0, np.pi), rng)
            if not free(poly):
                cx += rng.normal(0, 25); cy += rng.normal(0, 25)
                continue
            px = plot_pixels(poly, transform, shape)
            if px.sum() == 0:
                continue
            if need == "loss_patch":
                ok = np.nanmedian(rel[px]) <= -0.12 and vegetated[px].mean() >= 0.7
            elif need == "tiny":
                ok = vegetated[px].mean() >= 0.7
            else:
                ok = vegetated[px].mean() >= 0.8 and abs(np.nanmedian(rel[px])) <= 0.06
            if ok:
                return poly
            return None
        return None

    plan = []
    for name, (n, mult, where) in SCENARIOS.items():
        plan += [(name, mult, where)] * n
    plan += [("normal", 1.0, "stable")] * (N_PLOTS - len(plan))

    # Candidate centres for loss patches: strongest real relative NDVI declines.
    order = np.argsort(smooth, axis=None)
    loss_centres = []
    for idx in order[:4000]:
        r, c = np.unravel_index(idx, shape)
        if not vegetated[r, c] or smooth[r, c] > -0.12:
            continue
        x, y = x0 + (c + 0.5) * 10, y1 - (r + 0.5) * 10
        if not (x0 + margin < x < x1 - margin and y0 + margin < y < y1 - margin):
            continue
        if all(np.hypot(x - a, y - b) > 150 for a, b in loss_centres):
            loss_centres.append((x, y))

    plots = []
    li = 0
    for name, mult, where in plan:
        poly = None
        for attempt in range(3000):
            if where == "loss_patch":
                if li >= len(loss_centres):
                    break
                cx, cy = loss_centres[li]; li += 1
                area = rng.uniform(0.15, 0.35)
                poly = try_place(cx, cy, area, "loss_patch")
            else:
                cx, cy = rng.uniform(x0 + margin, x1 - margin), rng.uniform(y0 + margin, y1 - margin)
                area = rng.uniform(0.05, 0.08) if name == "tiny_plot" else float(np.clip(rng.lognormal(np.log(0.45), 0.5), 0.15, 1.5))
                poly = try_place(cx, cy, area, "tiny" if name == "tiny_plot" else "stable")
            if poly is not None:
                break
        if poly is None:
            raise RuntimeError(f"could not place a plot for scenario {name}")
        placed.append(poly)
        plots.append({"scenario": name, "mult": mult, "poly": poly})

    # Members: most have one coffee plot, some two. Noor is OCC0412 plot 2.
    member_ids = [f"OCC{n:04d}" for n in rng.choice(np.arange(100, 999), size=70, replace=False) if n != 412]
    rng.shuffle(plots)
    noor_idx = next(i for i, p in enumerate(plots) if p["scenario"] == "decline_with_canopy_loss")
    plots.insert(0, plots.pop(noor_idx))
    assigned, mi = [], 0
    for i, p in enumerate(plots):
        if i == 0:
            p["member"], p["plot"] = NOOR
            continue
        if i == 1:
            p["member"], p["plot"] = NOOR[0], 1
            continue
        m = member_ids[mi % len(member_ids)]
        n_existing = sum(1 for q in assigned if q == m)
        p["member"], p["plot"] = m, n_existing + 1
        assigned.append(m)
        if rng.random() > 0.15:
            mi += 1
    # Noor's plot 1 must be an ordinary plot, so swap scenario if needed.
    if plots[1]["scenario"] != "normal":
        j = next(i for i, p in enumerate(plots) if i > 1 and p["scenario"] == "normal")
        for k in ("scenario", "mult", "poly"):
            plots[1][k], plots[j][k] = plots[j][k], plots[1][k]

    to_wgs = Transformer.from_crs(C.UTM_EPSG, 4326, always_xy=True).transform
    features, truth = [], {}
    for p in plots:
        area_ha = p["poly"].area / 1e4
        trees = int(round(area_ha * C.TREES_PER_HA * rng.uniform(0.6, 1.0)))
        base = float(np.clip(rng.lognormal(np.log(C.BASE_KG_PER_TREE), 0.3), 1.0, 7.0))
        seasons = C.COFFEE_YEARS[-2:] if p["scenario"] == "new_member" else C.COFFEE_YEARS
        deliveries = []
        for s in C.COFFEE_YEARS:
            if s not in seasons:
                continue
            kg = trees * base * AREA_FACTOR[s] * rng.lognormal(0, NOISE_SD)
            if s == C.CURRENT_SEASON and (p["member"], p["plot"]) == NOOR:
                kg = trees * base * AREA_FACTOR[s] * 0.40   # scripted demo plot: a clear, noise-free drop
            elif s == C.CURRENT_SEASON:
                if p["mult"] is None:
                    deliveries.append({"season": s, "kgCherry": None})
                    continue
                kg *= p["mult"]
            deliveries.append({"season": s, "kgCherry": int(round(kg))})
        plot_id = f"{p['member']}-{p['plot']}"
        geom = shp_transform(to_wgs, p["poly"])
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[round(x, 6), round(y, 6)] for x, y in geom.exterior.coords]]},
            "properties": {
                "plotId": plot_id, "memberId": p["member"], "plot": p["plot"],
                "areaHa": round(area_ha, 3), "treesRegistered": trees,
                "deliveries": deliveries, "synthetic": True,
            },
        })
        truth[plot_id] = p["scenario"]

    reg = {"type": "FeatureCollection", "synthetic": True, "features": features,
           "note": "Synthetic registry for the demo. Not real farmers or plots."}
    C.DATA.mkdir(exist_ok=True)
    (C.DATA / "registry.geojson").write_text(json.dumps(reg))
    (C.DATA / "truth.json").write_text(json.dumps(
        {"synthetic": True, "note": "Planted scenarios, used only to evaluate the outlier model.",
         "areaFactor": AREA_FACTOR, "noiseSd": NOISE_SD,
         "scenarios": {k: {"count": v[0], "currentSeasonMultiplier": v[1], "placement": v[2]} for k, v in SCENARIOS.items()},
         "plots": truth}, indent=1))
    counts = {}
    for v in truth.values():
        counts[v] = counts.get(v, 0) + 1
    print(f"{len(features)} plots, {len({f['properties']['memberId'] for f in features})} members, "
          f"{len(loss_centres)} real NDVI-loss centres found; scenarios {counts}")


if __name__ == "__main__":
    main()
