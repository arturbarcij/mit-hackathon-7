"""Unit tests for the geo decision rules. Run: python3 -m pytest test_geo.py -q

These pin the behaviour described in kb/geo/CONTRACT.md. They use hand-made z-scores,
no network and no rasters.
"""
import json
import numpy as np

import config as C
import outliers as O
import visit_plan as V

OK = dict(area_ha=0.4, clear_px=40, total_px=40, kg_missing=False, prior_n=3, kg_per_tree=3.0)


def cls(zd, zn, **kw):
    status, conf, step, reasons, abstain = O.classify(zd, zn, **{**OK, **kw})
    return status, reasons, abstain, step


def test_robust_z_ignores_outliers():
    med, mad = O.robust_z([0.0, 0.1, -0.1, 0.05, -0.05, 5.0])
    assert abs(med) < 0.1 and mad < 0.2


def test_normal_plot():
    assert cls(0.2, -0.3)[:2] == ("normal", [])


def test_delivery_drop_with_canopy_loss_is_visit():
    status, reasons, _, step = cls(-3.5, -4.0)
    assert status == "outlier" and reasons[0] == "drop_with_canopy_loss" and step == "visit"


def test_delivery_drop_with_normal_canopy_is_a_call_not_an_accusation():
    status, reasons, _, step = cls(-3.5, 0.2)
    assert status == "outlier" and reasons == ["drop_canopy_normal"] and step == "call_member"


def test_borderline_canopy_abstains():
    status, reasons, abstain, step = cls(-3.5, -1.8)
    assert status == "unsure" and "canopy_signal_unclear" in abstain and step == "ask_officer"


def test_two_signals_corroborate_a_moderate_drop():
    assert cls(-2.4, -6.0)[1][0] == "drop_with_canopy_loss"
    assert cls(-2.4, 0.0)[0] == "normal"           # moderate drop alone is not enough


def test_canopy_loss_alone_is_flagged_for_a_visit():
    status, reasons, _, step = cls(0.0, -4.0)
    assert status == "outlier" and reasons == ["canopy_loss"] and step == "visit"


def test_spike_and_implausible_yield():
    assert cls(3.4, 0.0)[1] == ["delivery_spike"]
    s, r, _, step = cls(0.0, 0.0, kg_per_tree=12.0)
    assert r == ["above_plausible_yield"] and step == "check_records"


def test_short_history_missing_record_small_plot_abstain():
    s, r, a, step = cls(-5.0, -5.0, prior_n=1)
    assert s == "unsure" and "short_history" in a and "delivery_drop" not in r and step == "ask_officer"
    s, r, a, _ = cls(None, -0.1, kg_missing=True, prior_n=3)
    assert s == "unsure" and a == ["missing_delivery_record"]
    s, r, a, _ = cls(-4.0, None, area_ha=0.06)
    assert s == "unsure" and "plot_too_small" in a


def test_unreadable_canopy_never_reads_as_normal():
    s, _, a, _ = cls(0.1, None, clear_px=C.MIN_CLEAR_PIXELS - 1, total_px=40)
    assert s == "unsure" and a == ["few_clear_pixels"]
    s, _, a, _ = cls(0.1, 0.0, clear_px=12, total_px=40)    # under half the plot clear
    assert s == "unsure" and a == ["few_clear_pixels"]


def test_status_and_confidence_agree():
    for zd in (None, -4, 0, 4):
        for zn in (None, -5, -1.8, 0, 3):
            s, conf, step, r, a = O.classify(zd, zn, **OK)
            assert (conf == "low") == (s == "unsure")
            assert s != "outlier" or r
            assert s != "normal" or step == "none"


def test_every_code_has_a_legend_entry():
    codes = {"drop_with_canopy_loss", "drop_canopy_normal", "delivery_drop", "delivery_spike", "above_plausible_yield",
             "canopy_loss", "short_history", "missing_delivery_record", "plot_too_small", "few_clear_pixels", "canopy_signal_unclear"}
    assert codes <= set(O.LEGEND)


def test_thresholds_are_consistent():
    assert C.Z_CORROBORATED < C.Z_FLAG
    assert C.MIN_CLEAR_PIXELS <= round(C.MIN_AREA_HA * 100)    # 0.10 ha is about 10 pixels
    assert -C.Z_FLAG < C.Z_CANOPY_NORMAL < 0


def _outlier(zn=None, zd=None, change=None, status="normal", abstain=()):
    return {"plotId": "X-1", "status": status, "abstainReasons": list(abstain), "nextStep": "none",
            "metrics": {"zNdvi": zn, "zDelivery": zd, "changePct": change, "ndvi": 0.4, "ndviBaseline": 0.8}}


def test_visit_points_and_tiers():
    pts, sig = V.score_plot(_outlier(zn=-5, zd=-4, change=-60), None)
    assert pts == V.WEIGHTS["canopy_strong"] + V.WEIGHTS["delivery_drop"] >= V.TIER_A
    assert {s for s, _ in sig} == {"satellite", "deliveries"}
    ref = {"answer_id": "rust_high_pre_rains", "counts": {"rust": 6}, "uncertain": 1}
    pts2, sig2 = V.score_plot(_outlier(), ref)
    assert pts2 == V.WEIGHTS["leaf_rust_high"] >= V.TIER_A and sig2[0][0] == "leaf_check"
    assert V.score_plot(_outlier(), None)[0] == 0


def test_thin_data_gives_no_phantom_signal():
    pts, sig = V.score_plot(_outlier(zn=-6, zd=-6, change=-70, status="unsure", abstain=["few_clear_pixels", "short_history"]), None)
    assert pts == 0 or all(s != "satellite" for s, _ in sig)
    assert all(s != "deliveries" for s, _ in sig)


def test_route_is_not_worse_than_input_order():
    pts = [(37.06, -0.47), (37.08, -0.44), (37.05, -0.45), (37.07, -0.46)]
    order = V.best_tour(pts)
    assert sorted(order) == [0, 1, 2, 3]
    assert V.tour_km(pts, order) <= V.tour_km(pts, [0, 1, 2, 3]) + 1e-9


def test_referral_sms_format_and_answers():
    rng = np.random.default_rng(1)
    plots = [{"plotId": f"OCC{i:04d}-1", "memberId": f"OCC{i:04d}", "plot": 1,
              "status": ["outlier", "unsure", "normal"][i % 3]} for i in range(40)] + [
        {"plotId": "OCC0412-2", "memberId": "OCC0412", "plot": 2, "status": "outlier"},
        {"plotId": "OCC0412-1", "memberId": "OCC0412", "plot": 1, "status": "normal"}]
    refs = V.make_referrals(plots, rng)
    assert len(refs) == V.N_REFERRALS
    for r in refs:
        assert V.SMS_RE.match(r["sms"]) and len(r["sms"]) <= 160 and r["sms"].isascii()
        assert sum(r["counts"].values()) + r["uncertain"] == 10
        assert r["answer_id"] != "healthy_all"
    noor = next(r for r in refs if r["geoPlotId"] == "OCC0412-2")
    assert noor["answer_id"] == "rust_high_pre_rains" and "R:6" in noor["sms"]


def _keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _keys(v)


def test_committed_outputs_have_no_personal_fields_or_em_dashes():
    personal = {"phone", "msisdn", "email", "fullName", "firstName", "surname", "memberName"}
    for name in ("plots.geojson", "outliers.json", "visit_plan.json", "referrals_seed.json"):
        text = (C.OUT / name).read_text()
        assert "\u2014" not in text, name
        assert not personal & set(_keys(json.loads(text))), name
    for f in json.loads((C.OUT / "plots.geojson").read_text())["features"]:
        assert "name" not in f["properties"]
