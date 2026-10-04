"""Evidence integrity for the leaf model (W3, P1, D4): the numbers in EVALUATION.md are only
honest if the split is v1's, held-out sets never leak, calibration is sane, int8 matches PyTorch,
and the research queue chose before it looked at held-out data.

Pure Python. Reads app/ml and app/ml/research; writes nothing.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from qa.common import Result

HELDOUT = {"uganda", "rocole", "wild"}
POOL = ("train", "val", "test")
EXPECT = {"uganda": {"healthy", "rust", "phoma"}, "rocole": {"healthy", "rust"}}


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _sig(rows: list[dict]) -> dict:
    out = {}
    for s in POOL:
        paths = sorted(r["path"] for r in rows if r["split"] == s)
        out[s] = hashlib.sha256("\n".join(paths).encode("utf-8")).hexdigest()
    return out


def run(root: Path) -> list[Result]:
    ml = root / "ml"
    out: list[Result] = []
    man = ml / "manifest.csv"
    if not man.exists():
        return [Result("ml_integrity", "skip", "ml/manifest.csv missing")]
    rows = _rows(man)

    frozen = ml / "research" / "frozen.json"
    if frozen.exists():
        same = _sig(rows) == json.loads(frozen.read_text(encoding="utf-8"))["pool"]
        out.append(Result("ml_integrity:split_frozen", "pass" if same else "fail",
                          "ml/manifest.csv still has v1's train/val/test split" if same else
                          "ml/manifest.csv split differs from v1's frozen split: manifest.py was re-run, "
                          "so in-domain test may contain training images. Restore research/manifest_frozen.csv"))
    else:
        out.append(Result("ml_integrity:split_frozen", "warn", "no research/frozen.json: run `python research/data.py freeze`"))

    leak = [f"{r['source']} in {r['split']}: {r['path']}" for r in rows if r["source"] in HELDOUT and r["split"] in POOL]
    out.append(Result("ml_integrity:heldout_isolated", "fail" if leak else "pass",
                      f"{len(leak)} held-out rows in train/val/test" if leak else "no Uganda, RoCoLe or wild rows in train/val/test",
                      leak[:10]))

    by = defaultdict(set)
    for r in rows:
        if r["split"] in POOL and r.get("cluster_id"):
            by[r["split"]].add(r["cluster_id"])
    clash = []
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        n = len(by[a] & by[b])
        if n:
            clash.append(f"{a}/{b}: {n} near-duplicate clusters shared")
    out.append(Result("ml_integrity:no_near_duplicate_leak", "fail" if clash else "pass",
                      "; ".join(clash) if clash else "near-duplicate clusters never cross splits", clash))

    src = frozen.parent / "manifest_frozen.csv" if frozen.exists() else man
    hrows = _rows(src) if src.exists() else rows
    gaps, counts = [], {}
    for s, need in EXPECT.items():
        c = Counter(r["label"] for r in hrows if r["source"] == s)
        counts[s] = dict(c)
        missing = sorted(need - set(c))
        if missing:
            gaps.append(f"{s}: missing {', '.join(missing)} (have {dict(c) or 'nothing'})")
    out.append(Result("ml_integrity:heldout_complete", "warn" if gaps else "pass",
                      "held-out sets cover their shared classes" if not gaps else
                      "cross-domain results cannot speak for missing classes; say so in EVALUATION.md", gaps))

    cal = ml / "calibration.json"
    if cal.exists():
        c = json.loads(cal.read_text(encoding="utf-8"))
        thr, cov, T = c.get("threshold"), c.get("val_coverage"), c.get("temperature")
        bad = []
        if thr is None or thr >= 0.999:
            bad.append(f"threshold {thr}: the app would abstain on almost every leaf")
        if cov is None or cov < 0.30:
            bad.append(f"val coverage {cov}: below 30%")
        out.append(Result("ml_integrity:calibration", "fail" if bad else "pass",
                          "; ".join(bad) if bad else f"threshold {thr:.3f}, val coverage {cov:.1%}", bad))
        if T in (0.5, 3.0, 6.0):
            out.append(Result("ml_integrity:temperature_grid", "warn",
                              f"temperature {T} sits on the edge of the search grid; widen the grid"))
    else:
        out.append(Result("ml_integrity:calibration", "skip", "ml/calibration.json missing"))

    par = ml / "parity.json"
    if par.exists():
        p = json.loads(par.read_text(encoding="utf-8")).get("pt_vs_onnx_int8")
        out.append(Result("ml_integrity:int8_parity", "pass" if p is not None and p >= 0.95 else "fail",
                          f"int8 vs PyTorch top-1 agreement {p}" + ("" if p is not None and p >= 0.95 else " (needs 0.95)")))
    else:
        out.append(Result("ml_integrity:int8_parity", "skip", "ml/parity.json missing"))

    run_dir = ml / "research" / "overnight"
    sel, held, lock = run_dir / "selection.json", run_dir / "heldout.json", run_dir / "plan_lock.json"
    if sel.exists():
        s = json.loads(sel.read_text(encoding="utf-8"))
        bad = []
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8"))["plan_sha256"] != s.get("plan_sha256"):
            bad.append("selection used a different plan than the one pre-registered")
        if held.exists() and json.loads(held.read_text(encoding="utf-8")).get("scored_at", "") < s.get("selected_at", ""):
            bad.append("held-out sets were scored before the selection")
        out.append(Result("ml_integrity:preregistration", "fail" if bad else "pass",
                          "; ".join(bad) if bad else f"selection ({s.get('winner')}) made before held-out scoring, plan unchanged", bad))
    else:
        out.append(Result("ml_integrity:preregistration", "skip", "research queue has not selected yet"))
    return out
