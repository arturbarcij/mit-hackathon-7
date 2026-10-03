"""Build per-season Sentinel-2 NDVI median composites over the AOI.

Source: Sentinel-2 L2A COGs listed by Element 84 Earth Search (STAC), AWS open
data. Pixels are kept only where the Scene Classification Layer (SCL) says
vegetation or bare soil. Output: one float32 GeoTIFF per season in cache/, plus
a per-season scene log in data/ndvi_scenes.json.
"""
import json
import os

import numpy as np
import rasterio
from pyproj import Transformer
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.windows import from_bounds

import config as C

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")


def utm_grid():
    """AOI bounds in UTM, snapped outward to 20 m so 10 m and 20 m bands align."""
    t = Transformer.from_crs(4326, C.UTM_EPSG, always_xy=True)
    xs, ys = zip(*[t.transform(x, y) for x in (C.BBOX[0], C.BBOX[2]) for y in (C.BBOX[1], C.BBOX[3])])
    snap = 20.0
    x0, x1 = np.floor(min(xs) / snap) * snap, np.ceil(max(xs) / snap) * snap
    y0, y1 = np.floor(min(ys) / snap) * snap, np.ceil(max(ys) / snap) * snap
    w, h = int((x1 - x0) / 10), int((y1 - y0) / 10)
    return (x0, y0, x1, y1), from_origin(x0, y1, 10, 10), (h, w)


def read_band(href, bounds, shape, scale=1.0, offset=0.0, resampling=Resampling.nearest):
    with rasterio.open(href) as src:
        win = from_bounds(*bounds, transform=src.transform)
        arr = src.read(1, window=win, out_shape=shape, resampling=resampling, boundless=True, fill_value=0)
    return arr


def band_meta(asset):
    rb = (asset.extra_fields.get("raster:bands") or [{}])[0]
    return rb.get("scale", 1.0), rb.get("offset", 0.0), rb.get("nodata", 0)


def composite(client, season, start, end, bounds, shape):
    items = list(client.search(
        collections=[C.S2_COLLECTION], bbox=C.BBOX, datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": 90 if season.startswith("wet") else C.SCENE_CLOUD_MAX}},
    ).items())
    items = [i for i in items if f"_{C.S2_TILE}_" in i.id]
    stack, log = [], []
    for it in sorted(items, key=lambda i: i.datetime):
        try:
            scl = read_band(it.assets["scl"].href, bounds, shape)
            clear = np.isin(scl, C.SCL_CLEAR)
            if clear.mean() < 0.05:
                log.append({"id": it.id, "date": it.datetime.date().isoformat(), "clear": round(float(clear.mean()), 3), "used": False})
                continue
            rs, ro, rn = band_meta(it.assets["red"])
            ns, no, nn = band_meta(it.assets["nir"])
            red_dn = read_band(it.assets["red"].href, bounds, shape)
            nir_dn = read_band(it.assets["nir"].href, bounds, shape)
            # Earth Search usually removes BOA_ADD_OFFSET (1000 DN) before publishing,
            # but the flag and the -0.1 in raster:bands are not always consistent
            # (some 2025 items say False with offset-free pixels). If the darkest clear
            # red pixels sit below 1000 DN, the offset is not in the data.
            land = clear & (red_dn > 0)
            dark = np.percentile(red_dn[land], 1) if land.any() else 0
            offset_in_data = (not it.properties.get("earthsearch:boa_offset_applied")) and dark >= 1000
            if not offset_in_data:
                ro = no = 0.0
            valid = clear & (red_dn != rn) & (nir_dn != nn)
            red = np.clip(red_dn * rs + ro, 1e-4, None)
            nir = np.clip(nir_dn * ns + no, 1e-4, None)
            ndvi = np.where(valid, (nir - red) / (nir + red), np.nan).astype("float32")
            stack.append(ndvi)
            log.append({"id": it.id, "date": it.datetime.date().isoformat(),
                        "sceneCloud": it.properties.get("eo:cloud_cover"),
                        "baseline": it.properties.get("s2:processing_baseline"),
                        "offsetApplied": bool(offset_in_data),
                        "clear": round(float(valid.mean()), 3), "used": True})
            print(f"  {season} {it.id} clear={valid.mean():.2f}")
        except Exception as e:  # network hiccup on one scene should not kill the season
            log.append({"id": it.id, "error": str(e)[:200], "used": False})
            print(f"  {season} {it.id} FAILED {e}")
    if not stack:
        raise RuntimeError(f"no usable scenes for {season}")
    arr = np.stack(stack)
    with np.errstate(all="ignore"):
        med = np.nanmedian(arr, axis=0).astype("float32")
    nobs = np.sum(~np.isnan(arr), axis=0).astype("uint8")
    return med, nobs, log


def main():
    C.CACHE.mkdir(exist_ok=True)
    C.DATA.mkdir(exist_ok=True)
    bounds, transform, shape = utm_grid()
    client = Client.open(C.STAC_URL)
    scenes = {}
    jobs = {**C.DRY_SEASONS, **C.EXTRA_COMPOSITES}
    for season, (start, end) in jobs.items():
        med, nobs, log = composite(client, season, start, end, bounds, shape)
        scenes[season] = {"window": f"{start}/{end}", "scenesUsed": sum(1 for l in log if l.get("used")), "scenes": log}
        path = C.CACHE / f"ndvi_{season.replace('/', '-')}.tif"
        prof = dict(driver="GTiff", height=shape[0], width=shape[1], count=2, dtype="float32",
                    crs=f"EPSG:{C.UTM_EPSG}", transform=transform, nodata=np.nan, compress="deflate")
        with rasterio.open(path, "w", **prof) as dst:
            dst.write(med, 1)
            dst.write(nobs.astype("float32"), 2)
            dst.set_band_description(1, "ndvi_median")
            dst.set_band_description(2, "clear_observations")
        print(f"{season}: {scenes[season]['scenesUsed']} scenes, median NDVI {np.nanmedian(med):.3f}, "
              f"no-data pixels {np.isnan(med).mean():.1%} -> {path.name}")
    (C.DATA / "ndvi_scenes.json").write_text(json.dumps(
        {"source": "Sentinel-2 L2A, Element 84 Earth Search STAC (AWS open data)", "stac": C.STAC_URL,
         "tile": C.S2_TILE, "sclKept": list(C.SCL_CLEAR), "gridEpsg": C.UTM_EPSG, "gridBounds": bounds,
         "pixelM": 10, "seasons": scenes}, indent=1))


if __name__ == "__main__":
    main()
