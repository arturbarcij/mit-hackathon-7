"""Temperature scaling and abstention threshold on the val split. Writes calibration.json.

Logits come from the PyTorch checkpoint with the engine's preprocessing (export.engine_tensor).
The temperature minimises val negative log-likelihood. The chosen threshold is the lowest calibrated top-class
probability at which accuracy on accepted val images is at least --target (default 0.95), which gives the
highest coverage that meets the target. Thresholds for 0.98 and 0.99 are reported too.

With --splits A B (v2: val and uganda_calib), logits from all splits are pooled for the temperature, and the
threshold must reach the target on every split separately (the highest of the per-split thresholds). If that is
impossible at --target, --fallback-target is tried and the result says so ("fallback_used").

Real run:   python app/ml/calibrate.py --ckpt app/ml/runs/<run>/best.pt
v2 run:     python app/ml/calibrate.py --ckpt <best.pt> --manifest app/ml/manifest_v2.csv --splits val uganda_calib --fallback-target 0.90
Smoke run:  python app/ml/calibrate.py --ckpt app/ml/runs/smoke/best.pt --max-per-class 30 --out /tmp/mlx/calibration.json
"""
import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export import EngineImages, load_model, load_split, set_threads, sha256_file, softmax_t  # noqa: E402
from train import CLASSES, ML, ROOT  # noqa: E402


def collect_logits(model, rows, data_root, batch_size, workers):
    import torch
    from torch.utils.data import DataLoader

    dl = DataLoader(EngineImages(rows, data_root), batch_size=batch_size, shuffle=False, num_workers=workers)
    out, ys = [], []
    with torch.no_grad():
        for i, (x, y) in enumerate(dl):
            out.append(model(x).numpy())
            ys.append(y.numpy())
            if (i + 1) % 50 == 0:
                print(f"  {(i + 1) * batch_size}/{len(rows)} images", flush=True)
    return np.concatenate(out), np.concatenate(ys)


def nll(logits, y, t):
    p = softmax_t(logits, t)
    return float(-np.log(np.clip(p[np.arange(len(y)), y], 1e-12, None)).mean())


def fit_temperature(logits, y) -> float:
    """Minimise NLL over log T: coarse grid, then golden-section refinement (1-D and convex in practice)."""
    grid = np.linspace(np.log(0.05), np.log(20), 200)
    k = int(np.argmin([nll(logits, y, np.exp(g)) for g in grid]))
    lo, hi = grid[max(k - 1, 0)], grid[min(k + 1, len(grid) - 1)]
    g = (np.sqrt(5) - 1) / 2
    for _ in range(60):
        a, b = hi - g * (hi - lo), lo + g * (hi - lo)
        if nll(logits, y, np.exp(a)) < nll(logits, y, np.exp(b)):
            hi = b
        else:
            lo = a
    return float(np.exp((lo + hi) / 2))


def ece(conf, correct, bins=15) -> float:
    edges = np.linspace(0, 1, bins + 1)
    e = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            e += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(e)


def coverage_curve(conf, correct):
    """For each distinct confidence value t (descending): coverage and accuracy of {conf >= t}."""
    order = np.argsort(-conf, kind="stable")
    c, ok = conf[order], correct[order].astype(np.float64)
    cum = np.cumsum(ok)
    last = np.r_[c[1:] != c[:-1], True]  # last index of each tie group
    idx = np.nonzero(last)[0]
    n = np.arange(1, len(c) + 1)[idx]
    return c[idx], n / len(c), cum[idx] / n


def threshold_for(conf, correct, target) -> dict:
    t, cov, acc = coverage_curve(conf, correct)
    ok = np.nonzero(acc >= target)[0]
    if len(ok) == 0:
        return {"target": target, "reached": False, "threshold": None, "coverage": 0.0, "accepted_accuracy": None,
                "n_accepted": 0}
    k = ok[-1]
    return {"target": target, "reached": True, "threshold": float(t[k]), "coverage": float(cov[k]),
            "accepted_accuracy": float(acc[k]), "n_accepted": int(round(cov[k] * len(conf)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--manifest", default=str(ML / "manifest.csv"))
    ap.add_argument("--data-root", default=str(ROOT / "data_raw"))
    ap.add_argument("--split", default="val")
    ap.add_argument("--splits", nargs="*", default=None, help="several splits, pooled; overrides --split")
    ap.add_argument("--fallback-target", type=float, default=None,
                    help="if --target cannot be met on every split, use this target instead and say so")
    ap.add_argument("--max-per-class", type=int, default=0, help="0 = whole val split")
    ap.add_argument("--target", type=float, default=0.95, help="accepted-val accuracy the shipped threshold must reach")
    ap.add_argument("--report-targets", type=float, nargs="*", default=[0.95, 0.98, 0.99])
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(ML / "calibration.json"))
    a = ap.parse_args()

    set_threads(a.threads)
    splits = a.splits or [a.split]
    rows = []
    for sp in splits:
        rows += load_split(Path(a.manifest), sp, a.max_per_class, a.seed, labels=CLASSES)
    part = np.array([r["split"] for r in rows])
    counts = Counter(r["label"] for r in rows)
    print(f"{splits}: {len(rows)} images {dict(counts)}")
    model, ckpt = load_model(a.ckpt)
    logits, y = collect_logits(model, rows, Path(a.data_root), a.batch_size, a.workers)

    t = fit_temperature(logits, y)
    p1, pt = softmax_t(logits, 1.0), softmax_t(logits, t)
    pred, conf1, conf = pt.argmax(1), p1.max(1), pt.max(1)
    correct = pred == y
    def joint(target):
        """Threshold meeting the target on the pooled set and on every split separately."""
        res = {"pooled": threshold_for(conf, correct, target)}
        if len(splits) > 1:
            for sp in splits:
                m = part == sp
                res[sp] = threshold_for(conf[m], correct[m], target)
        reached = all(r["reached"] for r in res.values())
        out = dict(res["pooled"])
        out.update({"reached": reached, "per_split": res})
        if reached:
            out["threshold"] = max(r["threshold"] for r in res.values())
            out["threshold_set_on"] = sorted(
                name for name, r in res.items() if r.get("threshold") == out["threshold"]
            )
        return out

    all_targets = sorted(set(a.report_targets) | {a.target} | ({a.fallback_target} if a.fallback_target else set()))
    targets = {f"{x:.2f}": joint(x) for x in all_targets}
    chosen = dict(targets[f"{a.target:.2f}"])
    chosen["fallback_used"] = False
    if not chosen["reached"] and a.fallback_target:
        print(f"WARNING: accepted accuracy {a.target} is NOT reachable on every split; using fallback target {a.fallback_target}")
        chosen = dict(targets[f"{a.fallback_target:.2f}"])
        chosen.update({"fallback_used": True, "original_target": a.target})
    if chosen["reached"]:
        threshold = chosen["threshold"]
    else:
        threshold = 1.0
        print(f"WARNING: accepted accuracy never reaches {chosen['target']}; threshold falls back to 1.0 (abstain on almost everything)")
    accepted = conf >= threshold
    # The shipped threshold is the strictest split. Coverage on `chosen` must be
    # measured there, not at the lower pooled-only threshold.
    if chosen.get("reached") and len(conf):
        chosen["coverage"] = float(accepted.mean())
        chosen["n_accepted"] = int(accepted.sum())
        chosen["accepted_accuracy"] = float(correct[accepted].mean()) if accepted.any() else None
        chosen["coverage_note"] = (
            "coverage and accepted_accuracy are on the pooled set at the shipped threshold, "
            "the highest threshold that still meets the target on every split"
        )
    per_split = {}
    for sp in splits:
        m = part == sp
        per_split[sp] = {"n": int(m.sum()), "accuracy": float(correct[m].mean()),
                         "coverage_at_threshold": float(accepted[m].mean()),
                         "accepted_accuracy": float(correct[m & accepted].mean()) if (m & accepted).any() else None,
                         "nll_after": nll(logits[m], y[m], t), "ece_15_bins_after": ece(conf[m], correct[m])}

    per_class = {}
    for k, c in enumerate(CLASSES):
        m = y == k
        if m.any():
            per_class[c] = {"n": int(m.sum()), "accuracy": float(correct[m].mean()),
                            "coverage_at_threshold": float(accepted[m].mean()),
                            "accepted_accuracy": float(correct[m & accepted].mean()) if (m & accepted).any() else None}
    tc, cov, acc = coverage_curve(conf, correct)
    step = max(1, len(tc) // 200)
    result = {
        "test_set": (f"{a.split} split (JMuBEN, JMuBEN2, BRACOL, PlantDoc not_leaf)" if len(splits) == 1 and splits[0] == "val"
                     else f"pooled splits {splits} of {Path(a.manifest).name}")
                    + (f", at most {a.max_per_class} images per class" if a.max_per_class else ", all images"),
        "splits": splits,
        "checkpoint": str(a.ckpt), "checkpoint_sha256": sha256_file(a.ckpt), "arch": ckpt["arch"], "epoch": ckpt.get("epoch"),
        "command": " ".join([os.path.basename(sys.executable)] + sys.argv),
        "preprocessing": "engine (export.engine_tensor): centre square of shorter side resized to 224, ImageNet mean/std",
        "n": int(len(y)), "counts": dict(counts),
        "temperature": t,
        "threshold": float(threshold),
        "chosen": {**chosen, "threshold_used": float(threshold)},
        "targets": targets,
        "accuracy_all": float(correct.mean()),
        "nll": {"before": nll(logits, y, 1.0), "after": nll(logits, y, t)},
        "ece_15_bins": {"before": ece(conf1, p1.argmax(1) == y), "after": ece(conf, correct)},
        "per_class_at_threshold": per_class,
        "per_split_at_threshold": per_split,
        "curve": {"threshold": tc[::step].tolist(), "coverage": cov[::step].tolist(), "accuracy": acc[::step].tolist()},
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ("test_set", "n", "temperature", "threshold", "chosen", "accuracy_all", "nll",
                                             "ece_15_bins", "per_split_at_threshold")}, indent=2))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
