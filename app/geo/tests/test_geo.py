"""Tests for the geo layer. No network: STAC and NASA POWER are mocked, rasters are
written locally. Run from the repo root: python -m pytest app/geo/tests -q"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import geo_core as core  # noqa: E402
import geo_live as live  # noqa: E402


# --- robust z -----------------------------------------------------------------
def test_robust_z_median_and_mad():
    x = np.array([1.0, 2.0, 3.0, 4.0, 100.0])
    z = core.robust_z(x)
    # median 3, MAD 1 -> scale 1.4826
    assert z[2] == pytest.approx(0.0)
    assert z[0] == pytest.approx(-2 / 1.4826)
    assert z[4] == pytest.approx(97 / 1.4826)


def test_robust_z_nan_and_zero_mad():
    z = core.robust_z([np.nan, 5.0, 5.0, 5.0, 6.0])
    assert np.isnan(z[0])
    assert np.all(np.isfinite(z[1:]))   # MAD is 0, falls back to mean absolute deviation
    assert z[1] == pytest.approx(0.0)
    assert np.all(np.isnan(core.robust_z([np.nan, np.nan])))


def test_robust_z_is_robust_to_outliers():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, 200)
    x[:5] = -50
    z = core.robust_z(x)
    assert np.all(z[:5] < -20)
    assert abs(np.median(z[5:])) < 0.3


# --- own change ---------------------------------------------------------------
def test_own_change_vs_own_median():
    hist = {"2021/22": 100, "2022/23": 70, "2023/24": 110, "2024/25": 100, "2025/26": 60}
    oc, n = core.own_change_pct(hist)
    assert n == 5
    assert oc == pytest.approx(-40.0)   # median of 100, 70, 110, 100 = 100


def test_own_change_short_history():
    hist = {s: None for s in core.SEASONS}
    hist["2025/26"] = 50
    assert core.own_change_pct(hist) == (None, 1)


# --- reason ordering ----------------------------------------------------------
@pytest.mark.parametrize("kw,expected", [
    (dict(n_seasons=2, n_peers=8, peer_change=-30, rain=-30, gap_z=-5, ndvi_z=-5, ndvi_available=True), "not_enough_data"),
    (dict(n_seasons=5, n_peers=4, peer_change=0, rain=0, gap_z=-5, ndvi_z=-5, ndvi_available=True), "not_enough_data"),
    (dict(n_seasons=5, n_peers=8, peer_change=-30, rain=-25, gap_z=-5, ndvi_z=-5, ndvi_available=True), "area_wide_weather"),
    (dict(n_seasons=5, n_peers=8, peer_change=-30, rain=-10, gap_z=-5, ndvi_z=-5, ndvi_available=True), "canopy_loss_check_leaves"),
    (dict(n_seasons=5, n_peers=8, peer_change=-30, rain=None, gap_z=0, ndvi_z=0, ndvi_available=True), "in_line_with_peers"),
    (dict(n_seasons=5, n_peers=8, peer_change=0, rain=-30, gap_z=-2.5, ndvi_z=-1.6, ndvi_available=True), "canopy_loss_check_leaves"),
    (dict(n_seasons=5, n_peers=8, peer_change=0, rain=-30, gap_z=-2.5, ndvi_z=-1.4, ndvi_available=True), "drop_other_cause_ask_officer"),
    (dict(n_seasons=5, n_peers=8, peer_change=0, rain=0, gap_z=-2.5, ndvi_z=None, ndvi_available=False), "drop_check_leaves_or_ask"),
    (dict(n_seasons=5, n_peers=8, peer_change=0, rain=0, gap_z=-1.9, ndvi_z=-4, ndvi_available=True), "in_line_with_peers"),
])
def test_classify_first_match_wins(kw, expected):
    assert core.classify(**kw) == expected


def test_confidence_rules():
    assert core.confidence("in_line_with_peers", 0.0, 0.0, 5, True) == "low"     # few clear obs
    assert core.confidence("in_line_with_peers", 0.0, 0.0, 9, True) == "high"
    assert core.confidence("in_line_with_peers", -1.8, 0.0, 9, True) == "low"    # near gap threshold
    assert core.confidence("canopy_loss_check_leaves", -3.0, -1.6, 9, True) == "low"   # near NDVI threshold
    assert core.confidence("in_line_with_peers", 1.0, -1.5, 9, True) == "high"   # NDVI threshold irrelevant
    assert core.confidence("not_enough_data", None, None, 9, True) == "low"
    assert core.confidence("in_line_with_peers", 0.0, None, None, False) == "high"  # no NDVI layer at all


# --- full model on a toy layout ------------------------------------------------
def _toy_plots(drop_id=None, ndvi_drop=False, short_id=None, n=20, seed=1):
    rng = np.random.default_rng(seed)
    plots = []
    for i in range(n):
        pid = f"T{i:02d}"
        lon = 36.95 + (i % 5) * 0.004
        lat = -0.55 + (i // 5) * 0.004
        hist = {s: int(1000 * (0.7 if s == "2022/23" else 1.0) * math.exp(rng.normal(0, 0.05))) for s in core.SEASONS}
        nd = float(rng.normal(0, 0.01))
        if pid == drop_id:
            hist["2025/26"] = int(hist["2025/26"] * 0.55)
            if ndvi_drop:
                nd -= 0.12
        if pid == short_id:
            for s in core.SEASONS[:-2]:
                hist[s] = None
        plots.append({"plot_id": pid, "centroid": [lon, lat], "area_ha": 1.0, "history": hist,
                      "ndvi_change": nd, "clear_obs": 10})
    return plots


def test_model_flags_canopy_loss_and_other_cause():
    res = {r["plot_id"]: r for r in core.run_model(_toy_plots("T07", True, "T12"), -5.0, True)}
    assert res["T07"]["reason"] == "canopy_loss_check_leaves"
    assert res["T12"]["reason"] == "not_enough_data"
    assert sum(r["reason"] == "in_line_with_peers" for r in res.values()) == 18
    res = {r["plot_id"]: r for r in core.run_model(_toy_plots("T07", False), -5.0, True)}
    assert res["T07"]["reason"] == "drop_other_cause_ask_officer"
    res = {r["plot_id"]: r for r in core.run_model(_toy_plots("T07", True), -5.0, False)}
    assert res["T07"]["reason"] == "drop_check_leaves_or_ask"
    assert res["T07"]["ndvi_change"] is None


def test_peers_limited_to_radius_and_eight():
    plots = _toy_plots()
    plots[0]["centroid"] = [37.2, -0.3]   # far away: no peers within 2 km
    res = core.run_model(plots, 0.0, True)
    assert res[0]["n_peers"] == 0 and res[0]["reason"] == "not_enough_data"
    assert max(r["n_peers"] for r in res) == 8


def test_area_wide_weather_when_peers_dropped_and_rain_low():
    plots = _toy_plots()
    for p in plots:
        p["history"]["2025/26"] = int(p["history"]["2025/26"] * 0.7)
    res = core.run_model(plots, -24.0, True)
    assert all(r["reason"] == "area_wide_weather" for r in res)
    res = core.run_model(plots, -5.0, True)
    assert all(r["reason"] == "in_line_with_peers" for r in res)


# --- zonal mean with a synthetic raster ---------------------------------------
def test_polygon_mask_and_zonal_mean():
    transform = (10.0, 0.0, 0.0, 0.0, -10.0, 100.0)   # 10 x 10 cells of 10 m, origin top-left (0, 100)
    ring = np.array([[20, 80], [60, 80], [60, 40], [20, 40], [20, 80]], dtype=float)   # 4 x 4 cells
    m = core.polygon_mask(ring, transform, (10, 10))
    assert m.sum() == 16
    assert m[2:6, 2:6].all()
    vals = np.zeros((10, 10), dtype=float)
    vals[2:6, 2:6] = 0.8
    vals[2, 2] = 0.0
    clear = np.ones((10, 10), dtype=bool)
    clear[2, 2] = False                                    # cloudy pixel is ignored
    assert core.zonal_mean(vals, clear, m) == pytest.approx(0.8)
    clear[2:6, 2:5] = False                                # only 4 of 16 clear: below 50 percent
    assert core.zonal_mean(vals, clear, m) is None


def test_polygon_area_and_shape():
    rng = np.random.default_rng(3)
    for a in (0.5, 1.3, 2.5):
        ring = core.make_polygon(rng, 36.97, -0.55, a)
        assert 6 <= len(ring) <= 8 and ring[0] == ring[-1]
        assert core.polygon_area_ha(ring) == pytest.approx(a, abs=0.02)


# --- STAC parsing (mocked response) -------------------------------------------
def _item(iid, date, cloud, tile="37MBV", offset=-0.1, applied=None, baseline="05.09", with_scl=True):
    props = {"datetime": f"{date}T07:55:00.123Z", "eo:cloud_cover": cloud, "grid:code": f"MGRS-{tile}",
             "s2:processing_baseline": baseline}
    if applied is not None:
        props["earthsearch:boa_offset_applied"] = applied
    band = {"nodata": 0, "data_type": "uint16", "scale": 0.0001}
    if offset is not None:
        band["offset"] = offset
    assets = {"red": {"href": f"https://x/{iid}/B04.tif", "raster:bands": [band]},
              "nir": {"href": f"https://x/{iid}/B08.tif", "raster:bands": [band]}}
    if with_scl:
        assets["scl"] = {"href": f"https://x/{iid}/SCL.tif"}
    return {"type": "Feature", "id": iid, "properties": props, "assets": assets}


def test_parse_stac_items():
    fc = {"type": "FeatureCollection", "features": [
        _item("S2A_37MBV_20260705_0_L2A", "2026-07-05", 12.0),
        _item("S2A_37MBV_20260705_1_L2A", "2026-07-05", 11.0),         # reprocessed duplicate wins
        _item("S2A_37MCV_20260705_0_L2A", "2026-07-05", 30.0, tile="37MCV"),
        _item("S2B_37MBV_20260710_0_L2A", "2026-07-10", 50.0, applied=True),
        _item("S2B_37MBV_20260715_0_L2A", "2026-07-15", 5.0, offset=None, baseline="05.11"),
        _item("S2B_37MBV_20220115_0_L2A", "2022-01-15", 5.0, offset=None, baseline="03.01"),
        _item("S2B_37MBV_20260720_0_L2A", "2026-07-20", 5.0, with_scl=False),   # dropped
    ]}
    sc = live.parse_stac_items(fc)
    ids = [s.id for s in sc]
    assert "S2A_37MBV_20260705_0_L2A" not in ids and "S2A_37MBV_20260705_1_L2A" in ids
    assert "S2B_37MBV_20260720_0_L2A" not in ids
    assert len(sc) == 5
    by = {s.id: s for s in sc}
    assert by["S2A_37MBV_20260705_1_L2A"].offset == pytest.approx(-0.1)
    assert by["S2B_37MBV_20260710_0_L2A"].offset == 0.0
    assert by["S2B_37MBV_20260715_0_L2A"].offset == pytest.approx(-0.1)
    assert by["S2B_37MBV_20220115_0_L2A"].offset == 0.0
    assert by["S2A_37MCV_20260705_0_L2A"].tile == "MGRS-37MCV"
    assert set(by["S2A_37MBV_20260705_1_L2A"].hrefs) == {"red", "nir", "scl"}
    # two tiles on one date count as one date
    assert live.pick_dates(sc, 2) == ["2022-01-15", "2026-07-15"]
    assert "2026-07-10" not in live.pick_dates(sc, 3)   # cloudiest date is dropped first


def test_stac_pagination_follows_next(monkeypatch):
    pages = [
        {"features": [_item("A_37MBV_20260701_0_L2A", "2026-07-01", 1.0)],
         "links": [{"rel": "next", "href": "https://stac/search", "method": "POST", "body": {"next": "tok1"}}]},
        {"features": [_item("A_37MBV_20260702_0_L2A", "2026-07-02", 1.0)], "links": []},
    ]
    sent = []

    class R:
        def __init__(self, d):
            self.d = d

        def raise_for_status(self):
            pass

        def json(self):
            return self.d

    fake = SimpleNamespace(post=lambda url, json=None, headers=None, timeout=None: (sent.append(json), R(pages[len(sent) - 1]))[1],
                           get=None)
    feats = live.fetch_all_pages(fake, "https://stac/search", {"collections": ["sentinel-2-l2a"]})
    assert len(feats) == 2
    assert sent[1]["next"] == "tok1" and sent[1]["collections"] == ["sentinel-2-l2a"]


def test_detect_offset():
    scl = np.full((40, 40), 4, dtype=np.uint8)
    red = np.full((40, 40), 1350, dtype=np.uint16)
    assert live.detect_offset({"red": red, "scl": scl}, 0.0) == pytest.approx(-0.1)
    red = np.full((40, 40), 350, dtype=np.uint16)
    assert live.detect_offset({"red": red, "scl": scl}, -0.1) == 0.0


def test_ndvi_and_clear_masks_scl():
    red = np.array([[400, 400, 0]], dtype=np.uint16)
    nir = np.array([[3000, 3000, 3000]], dtype=np.uint16)
    scl = np.array([[4, 9, 4]], dtype=np.uint8)
    nd, cl = live.ndvi_and_clear({"red": red, "nir": nir, "scl": scl}, 0.0001, 0.0)
    assert cl.tolist() == [[True, False, False]]
    assert nd[0, 0] == pytest.approx((0.3 - 0.04) / 0.34, abs=1e-4)
    assert np.isnan(nd[0, 1]) and np.isnan(nd[0, 2])


def test_merge_same_date():
    a = (np.array([[0.5, np.nan]]), np.array([[True, False]]))
    b = (np.array([[0.1, 0.7]]), np.array([[True, True]]))
    nd, cl = live.merge_same_date([a, b])
    assert nd.tolist()[0][0] == 0.5 and nd.tolist()[0][1] == pytest.approx(0.7) and cl.all()


# --- rainfall -----------------------------------------------------------------
def _days(mm_base=3.0, latest_factor=1.0):
    d, out = dt.date(1991, 1, 1), {}
    while d <= dt.date(2026, 9, 25):
        v = mm_base
        if d >= dt.date(2025, 10, 1):
            v *= latest_factor
        out[d] = v
        d += dt.timedelta(days=1)
    return out


def test_season_anomalies():
    rows = live.season_anomalies(_days(3.0, 0.76), core.SEASONS)
    by = {r["season"]: r for r in rows}
    assert by["2024/25"]["anomaly_pct"] == pytest.approx(0.0)
    assert by["2025/26"]["anomaly_pct"] == pytest.approx(-24.0)
    assert by["2025/26"]["days"] < 365          # partial season compared over the same days


def test_parse_power():
    raw = {"header": {"fill_value": -999.0},
           "properties": {"parameter": {"PRECTOTCORR": {"20260101": 2.5, "20260102": -999.0}}}}
    d = live.parse_power(raw)
    assert d[dt.date(2026, 1, 1)] == 2.5 and d[dt.date(2026, 1, 2)] is None


# --- offline end to end -------------------------------------------------------
def _run_build(tmp_path, mode="offline", **kw):
    import build_geo
    args = SimpleNamespace(mode=mode, seed=7, out=str(tmp_path / "geo"), cache=str(tmp_path / "cache"),
                           max_dates=10, workers=2, skip_s2=False, skip_rain=False)
    for k, v in kw.items():
        setattr(args, k, v)
    return build_geo.build(args)


def test_offline_build_and_validate(tmp_path):
    out = _run_build(tmp_path)
    import validate
    assert validate.main(["--dir", str(tmp_path / "geo")]) == 0
    assert out["ndvi_source"] == "synthetic" and out["rainfall"]["synthetic"] is True
    assert out["counts"]["canopy_loss_check_leaves"] == 4
    assert os.path.getsize(tmp_path / "geo" / "plots.geojson") < 20_000
    by = {p["plot_id"]: p for p in out["plots"]}
    assert by["P07"]["member_id"] == "OCC0412" and by["P07"]["sms_nudge_id"] == "nudge_leaf_check"


def test_live_mode_falls_back_when_offline(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("no network in tests")
    monkeypatch.setattr(live, "fetch_power_daily", boom)
    monkeypatch.setattr(live, "stac_search", boom)
    out = _run_build(tmp_path, mode="live")
    assert out["ndvi_source"] == "unavailable"
    assert out["rainfall"]["season_anomaly_pct"] is None
    reasons = {p["plot_id"]: p["reason"] for p in out["plots"]}
    for pid in core.CANOPY_LOSS + core.OTHER_CAUSE:
        assert reasons[pid] == "drop_check_leaves_or_ask"
    assert all(p["ndvi_change"] is None for p in out["plots"])
    import validate
    assert validate.main(["--dir", str(tmp_path / "geo")]) == 0


# --- live mode against local rasters (rasterio needed, no network) -------------
def _write_tile(path, epsg, bounds, arr, res=10.0):
    import rasterio
    from rasterio.transform import from_origin
    xmin, ymin, xmax, ymax = bounds
    h, w = arr.shape
    with rasterio.open(path, "w", driver="GTiff", width=w, height=h, count=1, dtype=arr.dtype,
                       crs=f"EPSG:{epsg}", transform=from_origin(xmin, ymax, res, res), nodata=0,
                       tiled=True, blockxsize=256, blockysize=256, compress="deflate") as dst:
        dst.write(arr, 1)


def test_live_pipeline_with_local_rasters(tmp_path, monkeypatch):
    pytest.importorskip("rasterio")
    from rasterio.warp import transform_bounds
    bbox = core.area_bbox()
    # Tile 1 in UTM 37S covers the west 65 percent; tile 2 in UTM 36S covers the east 65 percent:
    # the box crosses two tiles in two different CRSs.
    w, s, e, n = bbox
    split1 = w + 0.65 * (e - w)
    split2 = w + 0.35 * (e - w)
    tiles = {}
    for name, epsg, bb in (("t1", 32737, (w - 0.01, s - 0.01, split1, n + 0.01)),
                           ("t2", 32736, (split2, s - 0.01, e + 0.01, n + 0.01))):
        xmin, ymin, xmax, ymax = transform_bounds("EPSG:4326", f"EPSG:{epsg}", *bb)
        xmin, ymin, xmax, ymax = (math.floor(xmin / 10) * 10, math.floor(ymin / 10) * 10,
                                  math.ceil(xmax / 10) * 10, math.ceil(ymax / 10) * 10)
        wpx, hpx = int((xmax - xmin) / 10), int((ymax - ymin) / 10)
        # pixel lon/lat for planting patterns
        from rasterio.warp import transform as wt
        cols, rows = np.meshgrid(np.arange(wpx) + 0.5, np.arange(hpx) + 0.5)
        lon, lat = wt(f"EPSG:{epsg}", "EPSG:4326", (xmin + cols * 10).ravel().tolist(), (ymax - rows * 10).ravel().tolist())
        lon, lat = np.array(lon).reshape(hpx, wpx), np.array(lat).reshape(hpx, wpx)
        xk, yk = core.lonlat_to_km(lon, lat, bbox)
        bare = (xk > 3.6) & (xk < 4.4) & (yk > 1.8) & (yk < 2.6)            # a non-vegetated block
        bx, by = np.floor(xk / 0.25).astype(int), np.floor(yk / 0.25).astype(int)
        thin = ((bx * 7919 + by * 104729) % 5) == 0                         # canopy thinning in 2026, 1 block in 5
        red = np.where(bare, 1200, 350).astype(np.uint16)                   # harmonised DNs (no +1000)
        nir_v = np.where(bare, 1500, 3000).astype(np.uint16)
        nir_thin = np.where(thin & ~bare, 1900, nir_v).astype(np.uint16)
        scl = np.where(bare, 5, 4).astype(np.uint8)
        scl_cloud = scl.copy()
        scl_cloud[: hpx // 3] = 9
        for tag, arr in (("red", red), ("nir", nir_v), ("nirthin", nir_thin), ("scl", scl), ("sclcloud", scl_cloud)):
            p = str(tmp_path / f"{name}_{tag}.tif")
            _write_tile(p, epsg, (xmin, ymin, xmax, ymax), arr)
            tiles[(name, tag)] = p

    def fake_stac(bb, a, b, cache_dir, max_cloud=60.0):
        feats = []
        for k in range(7):
            d = a + dt.timedelta(days=5 * k)
            if d > b:
                break
            latest = d.year == 2026 and d.month >= 7
            for name, tile in (("t1", "37MBV"), ("t2", "36MZV")):
                it = _item(f"S2A_{tile}_{d:%Y%m%d}_0_L2A", d.isoformat(), 10.0 + k, tile=tile)
                it["assets"]["red"]["href"] = tiles[(name, "red")]
                it["assets"]["nir"]["href"] = tiles[(name, "nirthin" if latest else "nir")]
                it["assets"]["scl"]["href"] = tiles[(name, "sclcloud" if k == 0 else "scl")]
                feats.append(it)
        return {"type": "FeatureCollection", "features": feats}

    monkeypatch.setattr(live, "stac_search", fake_stac)
    monkeypatch.setattr(live, "fetch_power_daily", lambda lon, lat, cache: _days(3.0, 0.9))
    out = _run_build(tmp_path, mode="live", max_dates=7)
    assert out["ndvi_source"] == "sentinel-2"
    assert out["rainfall"]["season_anomaly_pct"] == pytest.approx(-10.0)
    assert "Copernicus" in out["attribution"]
    by = {p["plot_id"]: p for p in out["plots"]}
    # canopy-loss plots were placed where the (test) NDVI dropped and are flagged red
    for pid in core.CANOPY_LOSS:
        assert by[pid]["ndvi_change"] < -0.05, (pid, by[pid]["ndvi_change"])
        assert by[pid]["reason"] == "canopy_loss_check_leaves"
    for pid in core.OTHER_CAUSE:
        assert by[pid]["reason"] == "drop_other_cause_ask_officer"
    # rain was only 10 percent low: the corner cluster is not blue
    assert all(by[p]["reason"] != "area_wide_weather" for p in core.CORNER_CLUSTER)
    assert all(p["clear_obs"] >= 6 for p in out["plots"])
    import validate
    assert validate.main(["--dir", str(tmp_path / "geo"), "--strict"]) == 0
