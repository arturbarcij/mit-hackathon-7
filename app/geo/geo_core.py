"""Core of the Jani outlier map: area, synthetic plots, synthetic deliveries,
synthetic NDVI and rainfall (offline mode), and the outlier model.

Pure numpy. No network. Python 3.10+.

Everything synthetic is labelled synthetic in the outputs. The model follows
kb/agents/geo.md section "The outlier model".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# Area (real place, approximate choice)
# ---------------------------------------------------------------------------
# A 6 x 6 km box south-east of Othaya town, Nyeri County, Kenya. Chosen by hand
# from general knowledge of the Othaya coffee belt; approximate, not checked
# against a land-cover map. The west edge sits just east of Othaya town centre
# (about -0.547, 36.943) so the town core is outside the box.
AREA_NAME = "Nyeri reference area (Othaya, approximate)"
CENTRE_LON = 36.975
CENTRE_LAT = -0.555
HALF_SIDE_KM = 3.0
KM_PER_DEG_LAT = 110.574
KM_PER_DEG_LON_EQ = 111.320


def km_per_deg_lon(lat: float = CENTRE_LAT) -> float:
    return KM_PER_DEG_LON_EQ * math.cos(math.radians(lat))


def area_bbox() -> list[float]:
    dlat = HALF_SIDE_KM / KM_PER_DEG_LAT
    dlon = HALF_SIDE_KM / km_per_deg_lon()
    return [round(CENTRE_LON - dlon, 5), round(CENTRE_LAT - dlat, 5),
            round(CENTRE_LON + dlon, 5), round(CENTRE_LAT + dlat, 5)]


def area_json() -> dict:
    return {
        "name": AREA_NAME,
        "bbox": area_bbox(),
        "centre": [CENTRE_LON, CENTRE_LAT],
        "size_km": [2 * HALF_SIDE_KM, 2 * HALF_SIDE_KM],
        "crs": "EPSG:4326, bbox order [west, south, east, north]",
        "notes": (
            "Real place, approximate choice: a 6 x 6 km box south-east of Othaya town in "
            "Nyeri County, Kenya, in the coffee-growing belt on the eastern slopes of the "
            "Aberdares. Chosen by hand, not checked against a land-cover map. Othaya town "
            "centre (about -0.547, 36.943) lies just west of the box. Plot shapes inside it "
            "are synthetic."
        ),
    }


# ---------------------------------------------------------------------------
# Plots, members, scenarios
# ---------------------------------------------------------------------------
SEASONS = ["2021/22", "2022/23", "2023/24", "2024/25", "2025/26"]
LATEST = SEASONS[-1]
DROUGHT_SEASON = "2022/23"
NDVI_YEARS = [2022, 2023, 2024, 2025, 2026]
# Dry-season composites; the long and short rains are too cloudy.
NDVI_PERIODS = [f"{y}-{w}" for y in NDVI_YEARS for w in ("JF", "JAS")]
LATEST_NDVI_PERIOD = "2026-JAS"

FIXED_MEMBERS = {
    "P01": "OCC0118", "P02": "OCC0233", "P03": "OCC0307", "P04": "OCC0521",
    "P05": "OCC0642", "P06": "OCC0719", "P07": "OCC0412", "P08": "OCC0855",
    "P09": "OCC0903", "P10": "OCC0977", "P11": "OCC1004", "P12": "OCC1088",
}
REFERRAL_SEEDED = set(FIXED_MEMBERS)

CANOPY_LOSS = ["P07", "P05", "P11", "P15"]          # P07 is Noor's plot
OTHER_CAUSE = ["P04", "P20"]
NOT_ENOUGH = ["P30", "P31", "P32"]
CORNER_CLUSTER = ["P33", "P34", "P35", "P36", "P37", "P38"]

PLANTED = {
    **{p: "canopy_loss_check_leaves" for p in CANOPY_LOSS},
    **{p: "drop_other_cause_ask_officer" for p in OTHER_CAUSE},
    **{p: "not_enough_data" for p in NOT_ENOUGH},
    **{p: "area_wide_weather" for p in CORNER_CLUSTER},
}

# Cluster layout in km from the south-west corner of the box: (name, centre, radius, n)
# Five farm clusters, roughly one per coffee factory catchment. Synthetic.
CLUSTERS = [
    ("A", (1.3, 4.6), 0.75, 8),
    ("B", (4.4, 4.7), 0.75, 8),
    ("C", (2.9, 2.9), 0.80, 9),
    ("D", (1.2, 1.3), 0.70, 9),
    ("E", (5.25, 0.75), 0.45, 6),   # corner cluster
]

# Offline id assignment per cluster (fixed so the demo is stable).
OFFLINE_ASSIGNMENT = {
    "A": ["P05", "P04", "P30", "P01", "P02", "P03", "P06", "P08"],
    "B": ["P11", "P09", "P10", "P12", "P13", "P14", "P16", "P17"],
    "C": ["P07", "P31", "P18", "P19", "P21", "P22", "P23", "P24", "P25"],
    "D": ["P15", "P20", "P32", "P26", "P27", "P28", "P29", "P39", "P40"],
    "E": CORNER_CLUSTER,
}


def member_id(plot_id: str) -> str:
    if plot_id in FIXED_MEMBERS:
        return FIXED_MEMBERS[plot_id]
    n = int(plot_id[1:])
    return f"OCC{1100 + 37 * n:04d}"   # synthetic, deterministic, never collides with fixed ids


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def km_to_lonlat(x_km: float, y_km: float, bbox: list[float]) -> tuple[float, float]:
    return bbox[0] + x_km / km_per_deg_lon(), bbox[1] + y_km / KM_PER_DEG_LAT


def lonlat_to_km(lon: float, lat: float, bbox: list[float]) -> tuple[float, float]:
    return (lon - bbox[0]) * km_per_deg_lon(), (lat - bbox[1]) * KM_PER_DEG_LAT


def shoelace_area(xy: np.ndarray) -> float:
    x, y = xy[:, 0], xy[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def polygon_area_ha(ring_lonlat: list[list[float]]) -> float:
    lat0 = float(np.mean([p[1] for p in ring_lonlat]))
    xy = np.array([[p[0] * km_per_deg_lon(lat0) * 1000.0, p[1] * KM_PER_DEG_LAT * 1000.0]
                   for p in ring_lonlat])
    return shoelace_area(xy) / 1e4


def make_polygon(rng: np.random.Generator, lon: float, lat: float, area_ha: float) -> list[list[float]]:
    """Simple 5 to 7 vertex star-convex polygon of the given area around (lon, lat).
    Returns a closed ring of [lon, lat] rounded to 5 decimals."""
    n = int(rng.integers(5, 8))
    step = 2 * math.pi / n
    ang = np.arange(n) * step + rng.uniform(-0.25, 0.25, n) * step + rng.uniform(0, 2 * math.pi)
    rad = 1.0 + rng.uniform(-0.2, 0.2, n)
    xy = np.c_[rad * np.cos(ang), rad * np.sin(ang)]
    scale = math.sqrt(area_ha * 1e4 / shoelace_area(xy))
    xy *= scale  # metres
    ring = [[round(lon + dx / (km_per_deg_lon(lat) * 1000.0), 5),
             round(lat + dy / (KM_PER_DEG_LAT * 1000.0), 5)] for dx, dy in xy]
    ring.append(ring[0])
    return ring


def plot_radius_m(area_ha: float) -> float:
    return math.sqrt(area_ha * 1e4 / math.pi) * 1.25


@dataclass
class Slot:
    cluster: str
    lon: float
    lat: float
    area_ha: float
    ring: list
    stats: dict = field(default_factory=dict)  # filled in live mode (NDVI per slot)


def generate_slots(rng: np.random.Generator, bbox: list[float], accept=None,
                   max_tries: int = 600) -> list[Slot]:
    """Place 40 synthetic plots in the cluster layout. `accept(ring) -> float score in [0,1]`
    is used in live mode to keep plots on vegetated pixels (score >= 0.8 accepted; otherwise the
    best of max_tries is kept)."""
    slots: list[Slot] = []
    margin_km = 0.15
    for name, (cx, cy), radius, n in CLUSTERS:
        for _ in range(n):
            area = float(np.round(rng.uniform(0.5, 2.5), 2))
            best = None
            for t in range(max_tries):
                r = radius * math.sqrt(rng.uniform(0, 1))
                a = rng.uniform(0, 2 * math.pi)
                x, y = cx + r * math.cos(a), cy + r * math.sin(a)
                if not (margin_km < x < 2 * HALF_SIDE_KM - margin_km and margin_km < y < 2 * HALF_SIDE_KM - margin_km):
                    continue
                lon, lat = km_to_lonlat(x, y, bbox)
                ok = True
                for s in slots:
                    sx, sy = lonlat_to_km(s.lon, s.lat, bbox)
                    if math.hypot(sx - x, sy - y) * 1000 < plot_radius_m(area) + plot_radius_m(s.area_ha) + 30:
                        ok = False
                        break
                if not ok:
                    continue
                ring = make_polygon(rng, lon, lat, area)
                score = 1.0 if accept is None else float(accept(ring))
                if best is None or score > best[0]:
                    best = (score, lon, lat, ring)
                if score >= 0.8:
                    break
            if best is None:
                raise RuntimeError(f"could not place a plot in cluster {name}")
            _, lon, lat, ring = best
            slots.append(Slot(name, round(lon, 5), round(lat, 5), round(polygon_area_ha(ring), 2), ring))
    return slots


def ring_centroid(ring: list[list[float]]) -> list[float]:
    pts = np.array(ring[:-1])
    return [round(float(pts[:, 0].mean()), 5), round(float(pts[:, 1].mean()), 5)]


def polygon_mask(ring_xy: np.ndarray, transform: tuple, shape: tuple[int, int]) -> np.ndarray:
    """Boolean mask of raster cells whose centres fall inside the polygon.
    ring_xy: (n, 2) polygon in the raster CRS; transform: affine (a, b, c, d, e, f) as in
    rasterio (x = a*col + b*row + c, y = d*col + e*row + f). Pure numpy ray casting."""
    a, b, c, d, e, f = transform[:6]
    h, w = shape
    cols, rows = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
    px = a * cols + b * rows + c
    py = d * cols + e * rows + f
    poly = np.asarray(ring_xy, dtype=float)
    if np.allclose(poly[0], poly[-1]):
        poly = poly[:-1]
    inside = np.zeros(shape, dtype=bool)
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = (yi > py) != (yj > py)
        with np.errstate(divide="ignore", invalid="ignore"):
            xcross = (xj - xi) * (py - yi) / (yj - yi) + xi
        inside ^= cond & (px < xcross)
        j = i
    return inside


def zonal_mean(values: np.ndarray, clear: np.ndarray, mask: np.ndarray,
               min_clear_frac: float = 0.5, min_pixels: int = 3) -> float | None:
    """Mean of clear pixels inside the mask, or None if too few clear pixels."""
    n = int(mask.sum())
    if n == 0:
        return None
    sel = mask & clear & np.isfinite(values)
    k = int(sel.sum())
    if k < max(min_pixels, min_clear_frac * n):
        return None
    return float(values[sel].mean())


# ---------------------------------------------------------------------------
# Synthetic deliveries, NDVI, rainfall
# ---------------------------------------------------------------------------
BASE_YIELD_CLEAN_KG_HA = 414.7   # KNBS 2025 Table 5.1.2, co-operatives 2023/24 (EVIDENCE E3)
CHERRY_TO_CLEAN = 6.0            # assumption: kg cherry per kg clean coffee, not verified for Nyeri
SEASON_FACTOR = {"2021/22": 1.00, "2022/23": 0.70, "2023/24": 1.05, "2024/25": 1.00, "2025/26": 1.00}
SYNTHETIC_RAIN = {"2021/22": -15.0, "2022/23": -31.0, "2023/24": 38.0, "2024/25": -6.0, "2025/26": -24.0}


def synthetic_deliveries(rng: np.random.Generator, ids: list[str], area: dict[str, float]) -> dict[str, dict[str, int | None]]:
    out = {}
    for pid in ids:
        plot_factor = float(np.exp(rng.normal(0, 0.25)))
        drought_hit = 1.0 if rng.uniform() < 0.85 else 0.5   # most plots took the full 2022/23 dip
        hist: dict[str, int | None] = {}
        for s in SEASONS:
            f = SEASON_FACTOR[s]
            if s == DROUGHT_SEASON:
                f = 1.0 - (1.0 - f) * drought_hit
            if s == LATEST:
                if pid in CANOPY_LOSS:
                    f *= 0.55
                elif pid in OTHER_CAUSE:
                    f *= 0.57
                elif pid in CORNER_CLUSTER:
                    f *= 0.68
            noise = float(np.exp(rng.normal(0, 0.07)))
            kg = area[pid] * BASE_YIELD_CLEAN_KG_HA * CHERRY_TO_CLEAN * plot_factor * f * noise
            hist[s] = int(round(kg))
        if pid in NOT_ENOUGH:   # new members: joined in 2024/25
            for s in SEASONS[:-2]:
                hist[s] = None
        out[pid] = hist
    return out


def synthetic_ndvi(rng: np.random.Generator, ids: list[str]) -> dict[str, dict[str, tuple[float, int]]]:
    """Per plot per period: (composite NDVI, clear observations). Synthetic."""
    low_obs = set(rng.choice([p for p in ids if p not in PLANTED], 3, replace=False).tolist())
    out = {}
    for pid in ids:
        base = rng.normal(0.70, 0.04)
        series = {}
        for per in NDVI_PERIODS:
            v = base + rng.normal(0, 0.02)
            if per.endswith("JF"):
                v -= 0.04
            if per == "2023-JF":          # after the failed 2022 short rains
                v -= 0.07
            if pid in CANOPY_LOSS:
                if per == "2026-JAS":
                    v -= 0.12
                elif per == "2026-JF":
                    v -= 0.04
            if pid in CORNER_CLUSTER and per == "2026-JAS":
                v -= 0.03
            obs = int(rng.integers(6, 15)) if per.endswith("JAS") else int(rng.integers(7, 17))
            if pid in low_obs and per == LATEST_NDVI_PERIOD:
                obs = int(rng.integers(3, 6))
            series[per] = (round(float(np.clip(v, -1, 1)), 3), obs)
        out[pid] = series
    return out


def ndvi_change_from_series(series: dict[str, tuple[float | None, int]]) -> tuple[float | None, int | None]:
    """Latest Jul-Sep composite minus the plot's own median of earlier Jul-Sep composites."""
    latest, obs = series.get(LATEST_NDVI_PERIOD, (None, 0))
    earlier = [series[p][0] for p in NDVI_PERIODS
               if p.endswith("JAS") and p != LATEST_NDVI_PERIOD and p in series and series[p][0] is not None]
    if latest is None or not earlier:
        return None, obs
    return round(latest - float(np.median(earlier)), 3), obs


# ---------------------------------------------------------------------------
# Outlier model
# ---------------------------------------------------------------------------
THRESHOLDS = {
    "gap_z": -2.0,
    "ndvi_z": -1.5,
    "peer_change_weather_pct": -15.0,
    "rain_anomaly_weather_pct": -20.0,
    "min_seasons": 3,
    "min_peers": 5,
    "n_peers": 8,
    "peer_radius_km": 2.0,
    "min_clear_obs": 6,
    "near_threshold_margin": 0.3,
}

REASONS = ["not_enough_data", "area_wide_weather", "drop_check_leaves_or_ask",
           "canopy_loss_check_leaves", "drop_other_cause_ask_officer", "in_line_with_peers"]

NUDGE = {
    "canopy_loss_check_leaves": "nudge_leaf_check",
    "drop_check_leaves_or_ask": "nudge_leaf_check",
    "drop_other_cause_ask_officer": "nudge_officer_visit",
    "area_wide_weather": "nudge_weather_everyone",
    "in_line_with_peers": None,
    "not_enough_data": None,
}


def robust_z(x) -> np.ndarray:
    """(x - median) / (1.4826 * MAD), NaN-aware. Falls back to the mean absolute
    deviation, then to 1, when the MAD is zero."""
    x = np.asarray(x, dtype=float)
    ok = np.isfinite(x)
    z = np.full(x.shape, np.nan)
    if not ok.any():
        return z
    med = np.median(x[ok])
    dev = np.abs(x[ok] - med)
    scale = 1.4826 * np.median(dev)
    if scale < 1e-12:
        scale = 1.2533 * dev.mean()
    if scale < 1e-12:
        scale = 1.0
    z[ok] = (x[ok] - med) / scale
    return z


def own_change_pct(hist: dict[str, int | None]) -> tuple[float | None, int]:
    vals = [(s, hist.get(s)) for s in SEASONS]
    have = [v for _, v in vals if v is not None]
    latest = hist.get(LATEST)
    prev = [v for s, v in vals if s != LATEST and v is not None]
    if latest is None or not prev:
        return None, len(have)
    med = float(np.median(prev))
    if med <= 0:
        return None, len(have)
    return (latest - med) / med * 100.0, len(have)


def pairwise_km(lonlat: np.ndarray) -> np.ndarray:
    lat0 = float(np.mean(lonlat[:, 1]))
    x = lonlat[:, 0] * km_per_deg_lon(lat0)
    y = lonlat[:, 1] * KM_PER_DEG_LAT
    return np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])


def classify(n_seasons, n_peers, peer_change, rain, gap_z, ndvi_z, ndvi_available, t=THRESHOLDS) -> str:
    """Reason code, first match wins (kb/agents/geo.md)."""
    if n_seasons < t["min_seasons"] or n_peers < t["min_peers"]:
        return "not_enough_data"
    if peer_change is not None and rain is not None and peer_change < t["peer_change_weather_pct"] \
            and rain < t["rain_anomaly_weather_pct"]:
        return "area_wide_weather"
    if gap_z is not None and gap_z < t["gap_z"]:
        if not ndvi_available or ndvi_z is None:
            return "drop_check_leaves_or_ask"
        if ndvi_z < t["ndvi_z"]:
            return "canopy_loss_check_leaves"
        return "drop_other_cause_ask_officer"
    return "in_line_with_peers"


def confidence(reason, gap_z, ndvi_z, clear_obs, ndvi_available, t=THRESHOLDS) -> str:
    if reason == "not_enough_data":
        return "low"
    m = t["near_threshold_margin"]
    if ndvi_available and (clear_obs is None or clear_obs < t["min_clear_obs"]):
        return "low"
    if gap_z is not None and abs(gap_z - t["gap_z"]) < m:
        return "low"
    # The NDVI threshold only matters when the delivery gap is (nearly) past its threshold.
    if ndvi_available and gap_z is not None and gap_z < t["gap_z"] + m and ndvi_z is not None \
            and abs(ndvi_z - t["ndvi_z"]) < m:
        return "low"
    return "high"


def run_model(plots: list[dict], rain_anomaly: float | None, ndvi_available: bool,
              t=THRESHOLDS) -> list[dict]:
    """plots: dicts with plot_id, centroid [lon, lat], history {season: kg|None},
    ndvi_change (float|None), clear_obs (int|None). Returns one result dict per plot."""
    n = len(plots)
    ll = np.array([p["centroid"] for p in plots], dtype=float)
    dist = pairwise_km(ll)
    own, nseas = [], []
    for p in plots:
        oc, ns = own_change_pct(p["history"])
        own.append(oc)
        nseas.append(ns)
    valid = np.array([o is not None and s >= t["min_seasons"] for o, s in zip(own, nseas)])
    own_arr = np.array([np.nan if o is None else o for o in own])
    ndvi_arr = np.array([np.nan if p.get("ndvi_change") is None else p["ndvi_change"] for p in plots])

    peers_idx = []
    for i in range(n):
        cand = [j for j in np.argsort(dist[i]) if j != i and valid[j] and dist[i, j] <= t["peer_radius_km"]]
        peers_idx.append(cand[: t["n_peers"]])

    peer_change = np.full(n, np.nan)
    gap = np.full(n, np.nan)
    ndvi_gap = np.full(n, np.nan)
    for i in range(n):
        pj = peers_idx[i]
        if pj:
            peer_change[i] = float(np.median(own_arr[pj]))
            if np.isfinite(own_arr[i]):
                gap[i] = own_arr[i] - peer_change[i]
            pv = ndvi_arr[pj]
            pv = pv[np.isfinite(pv)]
            if np.isfinite(ndvi_arr[i]) and pv.size:
                ndvi_gap[i] = ndvi_arr[i] - float(np.median(pv))
    eligible = valid & np.array([len(p) >= t["min_peers"] for p in peers_idx])
    gap_z = np.full(n, np.nan)
    ndvi_z = np.full(n, np.nan)
    if eligible.any():
        gap_z[eligible] = robust_z(gap[eligible])
        nd_ok = eligible & np.isfinite(ndvi_gap)
        if nd_ok.any():
            ndvi_z[nd_ok] = robust_z(ndvi_gap[nd_ok])

    def f(v, nd=1):
        return None if v is None or not np.isfinite(v) else round(float(v), nd)

    results = []
    for i, p in enumerate(plots):
        gz, nz = f(gap_z[i], 2), f(ndvi_z[i], 2)
        has_ndvi = ndvi_available and np.isfinite(ndvi_arr[i])
        reason = classify(nseas[i], len(peers_idx[i]), f(peer_change[i]), rain_anomaly, gz, nz, has_ndvi, t)
        conf = confidence(reason, gz, nz, p.get("clear_obs"), ndvi_available, t)
        results.append({
            "plot_id": p["plot_id"],
            "own_change_pct": f(own_arr[i]),
            "peer_change_pct": f(peer_change[i]),
            "gap_z": gz,
            "ndvi_change": f(ndvi_arr[i], 3) if ndvi_available else None,
            "ndvi_z": nz if ndvi_available else None,
            "clear_obs": p.get("clear_obs") if ndvi_available else None,
            "n_seasons": nseas[i],
            "n_peers": len(peers_idx[i]),
            "peer_ids": [plots[j]["plot_id"] for j in peers_idx[i]],
            "reason": reason,
            "confidence": conf,
            "sms_nudge_id": NUDGE[reason],
        })
    return results


def peer_median_history(plots: list[dict], results: list[dict]) -> dict[str, list[dict]]:
    """Per plot: median kg/ha of its peers per season, scaled to this plot's area (kg)."""
    by_id = {p["plot_id"]: p for p in plots}
    out = {}
    for r in results:
        p = by_id[r["plot_id"]]
        rows = []
        for s in SEASONS:
            vals = [by_id[q]["history"].get(s) / by_id[q]["area_ha"] for q in r["peer_ids"]
                    if by_id[q]["history"].get(s) is not None]
            rows.append({"season": s, "kg": int(round(float(np.median(vals)) * p["area_ha"])) if vals else None})
        out[r["plot_id"]] = rows
    return out
