"""Live data for the outlier map: NASA POWER rainfall and Sentinel-2 L2A NDVI.

Needs internet. Imports requests at call time and rasterio only for Sentinel-2,
so offline mode never needs either. Python 3.10+.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import numpy as np

import geo_core as core

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
STAC_URL = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-l2a"
MASK_SCL = {0, 1, 3, 8, 9, 10, 11}   # no data, saturated, cloud shadow, cloud medium/high, cirrus, snow
UA = {"User-Agent": "jani-hackathon-geo/1.0 (research prototype)"}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# NASA POWER rainfall
# ---------------------------------------------------------------------------
def fetch_power_daily(lon: float, lat: float, cache_dir: str, start: str = "19910101",
                      end: str | None = None) -> dict[dt.date, float | None]:
    import requests
    os.makedirs(cache_dir, exist_ok=True)
    end_date = dt.date.today() if end is None else dt.datetime.strptime(end, "%Y%m%d").date()
    cache = os.path.join(cache_dir, f"power_{lat:.4f}_{lon:.4f}_{start}_{end_date:%Y%m%d}.json")
    if os.path.exists(cache):
        raw = json.load(open(cache, encoding="utf-8"))
    else:
        raw, last_err = None, None
        for back in (0, 5, 10, 20, 40):   # POWER can refuse an end date past its latest data
            e = end_date - dt.timedelta(days=back)
            params = {"parameters": "PRECTOTCORR", "community": "AG", "longitude": round(lon, 4),
                      "latitude": round(lat, 4), "start": start, "end": f"{e:%Y%m%d}", "format": "JSON"}
            try:
                r = requests.get(POWER_URL, params=params, headers=UA, timeout=300)
                if r.status_code == 200:
                    raw = r.json()
                    break
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
            except Exception as ex:  # noqa: BLE001
                last_err = repr(ex)
            log(f"POWER retry ({last_err})")
        if raw is None:
            raise RuntimeError(f"NASA POWER failed: {last_err}")
        json.dump(raw, open(cache, "w", encoding="utf-8"))
    return parse_power(raw)


def parse_power(raw: dict) -> dict[dt.date, float | None]:
    fill = raw.get("header", {}).get("fill_value", -999.0)
    p = raw["properties"]["parameter"]["PRECTOTCORR"]
    out = {}
    for k, v in p.items():
        d = dt.datetime.strptime(k, "%Y%m%d").date()
        out[d] = None if v is None or v == fill or v < -900 else float(v)
    return out


def season_bounds(season: str) -> tuple[dt.date, dt.date]:
    y = int(season[:4])
    return dt.date(y, 10, 1), dt.date(y + 1, 9, 30)


def season_anomalies(days: dict[dt.date, float | None], seasons: list[str],
                     base_years: tuple[int, int] = (1991, 2020)) -> list[dict]:
    """Rainfall anomaly (%) of each Kenyan coffee season (Oct to Sep) against the
    1991 to 2020 mean of the same calendar days. A season that is not complete yet
    is compared over the days that have data."""
    rows = []
    for s in seasons:
        a, b = season_bounds(s)
        md, total, d = [], 0.0, a
        while d <= b:
            v = days.get(d)
            if v is not None and not (d.month == 2 and d.day == 29):
                md.append((d.month, d.day))
                total += v
            d += dt.timedelta(days=1)
        if len(md) < 60:
            rows.append({"season": s, "anomaly_pct": None, "days": len(md)})
            continue
        base_totals = []
        for y in range(base_years[0], base_years[1] + 1):
            vals = [days.get(dt.date(y, m, dd)) for m, dd in md]
            vals = [v for v in vals if v is not None]
            if len(vals) >= 0.9 * len(md):
                base_totals.append(sum(vals) * len(md) / len(vals))
        if not base_totals:
            rows.append({"season": s, "anomaly_pct": None, "days": len(md)})
            continue
        base = float(np.mean(base_totals))
        rows.append({"season": s, "anomaly_pct": round((total / base - 1.0) * 100.0, 1),
                     "days": len(md), "total_mm": round(total, 1), "baseline_mm": round(base, 1)})
    return rows


# ---------------------------------------------------------------------------
# STAC search and parsing
# ---------------------------------------------------------------------------
def period_dates(period: str) -> tuple[dt.date, dt.date]:
    y, w = period.split("-")
    y = int(y)
    if w == "JF":
        return dt.date(y, 1, 1), dt.date(y, 2, 28 + (1 if y % 4 == 0 else 0))
    return dt.date(y, 7, 1), dt.date(y, 9, 30)


def stac_search(bbox: list[float], start: dt.date, end: dt.date, cache_dir: str,
                max_cloud: float = 60.0) -> dict:
    import requests
    os.makedirs(cache_dir, exist_ok=True)
    cache = os.path.join(cache_dir, f"stac_{start:%Y%m%d}_{end:%Y%m%d}_{'_'.join(f'{v:.4f}' for v in bbox)}.json")
    if os.path.exists(cache):
        return json.load(open(cache, encoding="utf-8"))
    body = {"collections": [COLLECTION], "bbox": bbox,
            "datetime": f"{start:%Y-%m-%d}T00:00:00Z/{end:%Y-%m-%d}T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": max_cloud}}, "limit": 100}
    feats = fetch_all_pages(requests, STAC_URL, body)
    out = {"type": "FeatureCollection", "features": feats}
    json.dump(out, open(cache, "w", encoding="utf-8"))
    return out


def fetch_all_pages(requests, url: str, body: dict, max_pages: int = 30) -> list[dict]:
    """Follow STAC 'next' links (POST with a body, or GET)."""
    feats, method, req = [], "POST", dict(body)
    for _ in range(max_pages):
        if method == "POST":
            r = requests.post(url, json=req, headers=UA, timeout=120)
        else:
            r = requests.get(url, headers=UA, timeout=120)
        r.raise_for_status()
        fc = r.json()
        feats.extend(fc.get("features", []))
        nxt = next((ln for ln in fc.get("links", []) if ln.get("rel") == "next"), None)
        if not nxt or not fc.get("features"):
            break
        url = nxt["href"]
        method = str(nxt.get("method", "GET")).upper()
        if method == "POST":
            req = {**req, **(nxt.get("body") or {})}
    return feats


@dataclass
class Scene:
    id: str
    date: str          # YYYY-MM-DD (UTC sensing date)
    tile: str
    cloud: float
    hrefs: dict        # red, nir, scl
    scale: float
    offset: float


def _asset(assets: dict, *names):
    for n in names:
        if n in assets:
            return assets[n]
    return None


def parse_stac_items(fc: dict) -> list[Scene]:
    """Turn a STAC FeatureCollection into Scene records. Keeps one item per
    (tile, date): the reprocessed one when duplicates exist."""
    best: dict[tuple[str, str], tuple[str, Scene]] = {}
    for f in fc.get("features", []):
        props = f.get("properties", {})
        assets = f.get("assets", {})
        red = _asset(assets, "red", "B04")
        nir = _asset(assets, "nir", "B08")
        scl = _asset(assets, "scl", "SCL")
        if not (red and nir and scl):
            continue
        when = props.get("datetime", "")[:10]
        tile = props.get("grid:code") or "".join(str(props.get(k, "")) for k in
                                                ("mgrs:utm_zone", "mgrs:latitude_band", "mgrs:grid_square")) or f["id"].split("_")[1]
        bands = (red.get("raster:bands") or [{}])[0]
        scale = float(bands.get("scale", 0.0001))
        offset = float(bands.get("offset", 0.0))
        if props.get("earthsearch:boa_offset_applied") is True:
            offset = 0.0
        elif "offset" not in bands:
            pb = str(props.get("s2:processing_baseline", "00.00"))
            try:
                offset = -0.1 if float(pb) >= 4.0 else 0.0
            except ValueError:
                offset = 0.0
        sc = Scene(f["id"], when, str(tile), float(props.get("eo:cloud_cover", 100.0)),
                   {"red": red["href"], "nir": nir["href"], "scl": scl["href"]}, scale, offset)
        key = (sc.tile, sc.date)
        rank = f["id"]
        if key not in best or rank > best[key][0]:
            best[key] = (rank, sc)
    return sorted((v[1] for v in best.values()), key=lambda s: (s.date, s.tile))


def pick_dates(scenes: list[Scene], max_dates: int) -> list[str]:
    """Up to max_dates sensing dates with the lowest mean tile cloud cover."""
    by_date: dict[str, list[float]] = {}
    for s in scenes:
        by_date.setdefault(s.date, []).append(s.cloud)
    ranked = sorted(by_date, key=lambda d: (float(np.mean(by_date[d])), d))
    return sorted(ranked[:max_dates])


# ---------------------------------------------------------------------------
# Raster reading on a common grid
# ---------------------------------------------------------------------------
@dataclass
class Grid:
    crs: str
    transform: tuple   # a, b, c, d, e, f
    width: int
    height: int


def utm_epsg(lon: float, lat: float) -> int:
    zone = int((lon + 180) // 6) + 1
    return (32700 if lat < 0 else 32600) + zone


def make_grid(bbox: list[float], res: float = 10.0) -> Grid:
    from rasterio.warp import transform_bounds
    epsg = utm_epsg((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    xmin, ymin, xmax, ymax = transform_bounds("EPSG:4326", f"EPSG:{epsg}", *bbox, densify_pts=21)
    xmin, ymin = math.floor(xmin / res) * res, math.floor(ymin / res) * res
    xmax, ymax = math.ceil(xmax / res) * res, math.ceil(ymax / res) * res
    w, h = int(round((xmax - xmin) / res)), int(round((ymax - ymin) / res))
    return Grid(f"EPSG:{epsg}", (res, 0.0, xmin, 0.0, -res, ymax), w, h)


def gdal_env() -> dict:
    env = {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "AWS_NO_SIGN_REQUEST": "YES",
           "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.TIF,.tiff", "GDAL_HTTP_MAX_RETRY": "4",
           "GDAL_HTTP_RETRY_DELAY": "2", "VSI_CACHE": "TRUE"}
    if not os.environ.get("CURL_CA_BUNDLE"):
        try:
            import certifi
            env["CURL_CA_BUNDLE"] = certifi.where()
        except ImportError:
            pass
    return env


def read_on_grid(href: str, grid: Grid) -> np.ndarray:
    """Read one band onto the common grid (nearest neighbour). Only the blocks of the
    COG that overlap the grid are fetched. Outside the scene footprint the value is 0."""
    import rasterio
    from affine import Affine
    from rasterio.enums import Resampling
    from rasterio.vrt import WarpedVRT
    with rasterio.open(href) as src:
        with WarpedVRT(src, crs=grid.crs, transform=Affine(*grid.transform), width=grid.width,
                       height=grid.height, resampling=Resampling.nearest, src_nodata=0, nodata=0) as vrt:
            return vrt.read(1)


def load_scene(scene: Scene, grid: Grid, cache_dir: str) -> dict:
    """red, nir as uint16 DN and scl as uint8 on the grid, cached as npz."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{scene.id}_{grid.width}x{grid.height}.npz")
    if os.path.exists(path):
        z = np.load(path)
        return {k: z[k] for k in ("red", "nir", "scl")}
    import rasterio
    with rasterio.Env(**gdal_env()):
        arr = {k: read_on_grid(scene.hrefs[k], grid) for k in ("red", "nir", "scl")}
    arr = {"red": arr["red"].astype(np.uint16), "nir": arr["nir"].astype(np.uint16), "scl": arr["scl"].astype(np.uint8)}
    np.savez_compressed(path, **arr)
    return arr


def detect_offset(arr: dict, meta_offset: float) -> float:
    """Reflectance offset for this scene. Since processing baseline 04.00 (25 Jan 2022) L2A DNs
    carry +1000 unless the provider already removed it. Metadata on this point has varied, so
    decide from the data: if the 1st percentile of red DN over clear pixels is at least 900,
    the +1000 is still in the DNs (dense vegetation has red reflectance far below 0.09)."""
    ok = (arr["red"] > 0) & ~np.isin(arr["scl"], list(MASK_SCL))
    if ok.sum() < 500:
        return meta_offset
    p1 = float(np.percentile(arr["red"][ok], 1))
    return -0.1 if p1 >= 900 else 0.0


def ndvi_and_clear(arr: dict, scale: float, offset: float) -> tuple[np.ndarray, np.ndarray]:
    red = arr["red"].astype(np.float32)
    nir = arr["nir"].astype(np.float32)
    valid = (arr["red"] > 0) & (arr["nir"] > 0)
    r = red * scale + offset
    n = nir * scale + offset
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = (n - r) / (n + r)
    clear = valid & ~np.isin(arr["scl"], list(MASK_SCL)) & np.isfinite(ndvi) & (n + r > 0)
    ndvi = np.where(clear, np.clip(ndvi, -1, 1), np.nan).astype(np.float32)
    return ndvi, clear


def merge_same_date(layers: list[tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray]:
    """Two MGRS tiles on the same date: take the first clear value per pixel."""
    ndvi, clear = layers[0][0].copy(), layers[0][1].copy()
    for nd, cl in layers[1:]:
        take = ~clear & cl
        ndvi[take] = nd[take]
        clear |= cl
    return ndvi, clear


def fetch_ndvi_stack(bbox: list[float], cache_dir: str, max_dates: int = 10, workers: int = 6,
                     max_cloud: float = 60.0) -> tuple[Grid, dict[str, list[tuple[str, np.ndarray, np.ndarray]]]]:
    """Returns the grid and, per period, a list of (date, ndvi, clear) on that grid."""
    grid = make_grid(bbox)
    log(f"grid {grid.crs} {grid.width} x {grid.height} px at 10 m")
    jobs: dict[str, list[Scene]] = {}
    for per in core.NDVI_PERIODS:
        a, b = period_dates(per)
        if a > dt.date.today():
            continue
        scenes = parse_stac_items(stac_search(bbox, a, min(b, dt.date.today()), os.path.join(cache_dir, "stac"), max_cloud))
        keep = set(pick_dates(scenes, max_dates))
        jobs[per] = [s for s in scenes if s.date in keep]
        log(f"{per}: {len(scenes)} items, using {len(jobs[per])} items on {len(keep)} dates "
            f"(tiles {sorted({s.tile for s in jobs[per]})})")
    flat = [(per, s) for per, ss in jobs.items() for s in ss]
    log(f"reading {len(flat)} scenes (red, nir, scl windows only); cached under {cache_dir}")
    loaded: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut = {ex.submit(load_scene, s, grid, os.path.join(cache_dir, "scenes")): s for _, s in flat}
        for i, f in enumerate(as_completed(fut), 1):
            s = fut[f]
            try:
                loaded[s.id] = f.result()
            except Exception as e:  # noqa: BLE001
                log(f"  skip {s.id}: {e!r}")
            if i % 10 == 0 or i == len(flat):
                log(f"  {i}/{len(flat)} scenes")
    out: dict[str, list] = {}
    offsets: dict[float, int] = {}
    for per, ss in jobs.items():
        by_date: dict[str, list] = {}
        for s in ss:
            if s.id in loaded:
                off = detect_offset(loaded[s.id], s.offset)
                offsets[off] = offsets.get(off, 0) + 1
                by_date.setdefault(s.date, []).append(ndvi_and_clear(loaded[s.id], s.scale, off))
        out[per] = [(d, *merge_same_date(layers)) for d, layers in sorted(by_date.items())]
    log(f"reflectance offsets used (offset: scenes): {offsets}")
    for per, rows in out.items():
        log(f"  {per}: {len(rows)} dates read")
    return grid, out


def ring_to_grid_xy(ring: list[list[float]], grid: Grid) -> np.ndarray:
    from rasterio.warp import transform as wtransform
    xs, ys = wtransform("EPSG:4326", grid.crs, [p[0] for p in ring], [p[1] for p in ring])
    return np.c_[xs, ys]


def local_mask(ring: list[list[float]], grid: Grid) -> tuple[slice, slice, np.ndarray]:
    """Polygon mask on the small window of the grid that holds the polygon (north-up grid)."""
    xy = ring_to_grid_xy(ring, grid)
    a, _, c, _, e, f = grid.transform[:6]
    c0 = max(int(math.floor((xy[:, 0].min() - c) / a)) - 1, 0)
    c1 = min(int(math.ceil((xy[:, 0].max() - c) / a)) + 1, grid.width)
    r0 = max(int(math.floor((xy[:, 1].max() - f) / e)) - 1, 0)
    r1 = min(int(math.ceil((xy[:, 1].min() - f) / e)) + 1, grid.height)
    if c1 <= c0 or r1 <= r0:
        return slice(0, 0), slice(0, 0), np.zeros((0, 0), dtype=bool)
    sub = (a, 0.0, c + c0 * a, 0.0, e, f + r0 * e)
    return slice(r0, r1), slice(c0, c1), core.polygon_mask(xy, sub, (r1 - r0, c1 - c0))


def plot_ndvi_series(ring: list[list[float]], grid: Grid, stack: dict) -> dict[str, tuple[float | None, int]]:
    """Per period: (median of per-date plot means over clear pixels, number of clear dates)."""
    rs, cs, mask = local_mask(ring, grid)
    series = {}
    for per in core.NDVI_PERIODS:
        vals = []
        for _, ndvi, clear in stack.get(per, []):
            v = core.zonal_mean(ndvi[rs, cs], clear[rs, cs], mask) if mask.size else None
            if v is not None:
                vals.append(v)
        series[per] = (round(float(np.median(vals)), 3) if vals else None, len(vals))
    return series


def vegetation_scorer(grid: Grid, stack: dict, threshold: float = 0.5):
    """Score = share of a polygon's pixels whose median dry-season (Jul to Sep) NDVI is at
    least `threshold`. Used to keep synthetic plots on vegetated pixels."""
    layers = [nd for per, rows in stack.items() if per.endswith("JAS") for _, nd, _ in rows]
    if not layers:
        layers = [nd for rows in stack.values() for _, nd, _ in rows]
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.nanmedian(np.stack(layers), axis=0)
    veg = np.nan_to_num(med, nan=0.0) >= threshold
    log(f"vegetated share of the box (median Jul to Sep NDVI >= {threshold}): {veg.mean():.0%}")

    def score(ring):
        rs, cs, m = local_mask(ring, grid)
        return float(veg[rs, cs][m].mean()) if m.any() else 0.0
    return score
