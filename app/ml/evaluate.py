"""Evaluate the shipped int8 ONNX model (leaf.onnx + model.json) exactly as the engine runs it.

Test sets (every metric in metrics.json sits under the name of its test set):
- in_domain_test: test split of JMuBEN, JMuBEN2, BRACOL and PlantDoc not_leaf (pHash-grouped, no leakage).
- heldout_uganda: Uganda set, healthy / rust / phoma, never trained on. Rows marked
  excluded_heldout_dup_of_train are a different split and are never loaded.
- heldout_rocole: RoCoLe (Ecuador Robusta), healthy and rust (rust levels mapped to rust), never trained on.
- rocole_red_spider_mite: RoCoLe red spider mite (out of scope): what the model predicts and how often it abstains.
- not_leaf_test: the not_leaf rows of the in-domain test split (PlantDoc non-coffee leaves).
Plus model bytes and single-thread onnxruntime CPU latency.

Writes metrics.json and figures/ (confusion matrices, accuracy vs coverage with the threshold marked).

Real run:   python app/ml/evaluate.py
Smoke run:  python app/ml/evaluate.py --model-dir /tmp/mlx/model --export-report /tmp/mlx/export_report.json \
              --calibration /tmp/mlx/calibration.json --max-per-class 30 --out /tmp/mlx/metrics.json --fig-dir /tmp/mlx/figures
"""
import argparse
import json
import os
import platform
import sys
import textwrap
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibrate import coverage_curve, ece  # noqa: E402
from export import engine_crop, open_rgb, ort_session, set_threads, sha256_file, softmax_t, to_tensor, load_split  # noqa: E402
from train import CLASSES, ML, ROOT  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support  # noqa: E402

SETS = {
    "in_domain_test": dict(split="test", labels=CLASSES,
                           desc="in-domain test split: JMuBEN, JMuBEN2, BRACOL, PlantDoc not_leaf (Kenya, Brazil; pHash-grouped)"),
    "heldout_uganda": dict(split="heldout_uganda", labels=CLASSES,
                           desc="Uganda held-out set (healthy, rust, phoma), never trained on; excluded_heldout_dup_of_train rows not used"),
    "heldout_rocole": dict(split="heldout_rocole", labels=CLASSES,
                           desc="RoCoLe held-out set (Ecuador Robusta; healthy, rust levels 1-4 mapped to rust), never trained on"),
    "rocole_red_spider_mite": dict(split="heldout_rocole", labels=["unmapped"],
                                   desc="RoCoLe red spider mite (no matching class; out of scope)"),
    # v2 (manifest_v2.csv)
    "heldout_uganda_test": dict(split="heldout_uganda_test", labels=CLASSES,
                                desc="Uganda test portion (35% of the Uganda set by duplicate group; healthy, rust, phoma); "
                                     "other Uganda groups were used for v2 training and calibration"),
    "synthetic_blank_pages": dict(split="test_synthetic_pages", labels=["not_leaf"],
                                  desc="SYNTHETIC exercise-book pages with no leaf (two thirds through the clutter generator: "
                                       "random pen strokes, rectangles, skin-tone blob); desired: not_leaf or abstain"),
}


def infer(sess, rows, data_root: Path):
    logits, keep = [], []
    for i, r in enumerate(rows):
        try:
            x = to_tensor(engine_crop(open_rgb(data_root / r["path"])))[None]
        except Exception as e:
            print(f"  skip unreadable {r['path']}: {e}")
            continue
        logits.append(sess.run(["logits"], {"input": x})[0][0])
        keep.append(r)
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(rows)}", flush=True)
    return np.array(logits).reshape(-1, len(CLASSES)), keep


def scores(logits, rows, temperature, threshold, desc, closed_set=True):
    p = softmax_t(logits, temperature)
    pred, conf = p.argmax(1), p.max(1)
    accepted = conf >= threshold
    out = {"test_set": desc, "n": int(len(rows)), "label_counts": dict(Counter(r["label"] for r in rows)),
           "source_counts": dict(Counter(r["source"] for r in rows)),
           "abstention_rate": float(1 - accepted.mean()) if len(rows) else None,
           "predicted_counts": {CLASSES[k]: int(v) for k, v in Counter(pred.tolist()).items()},
           "accepted_predicted_counts": {CLASSES[k]: int(v) for k, v in Counter(pred[accepted].tolist()).items()},
           "rate_abstain_or_not_leaf": float((~accepted | (pred == CLASSES.index("not_leaf"))).mean()) if len(rows) else None,
           "rate_predicted_not_leaf": float((pred == CLASSES.index("not_leaf")).mean()) if len(rows) else None,
           "rate_accepted_as_not_leaf": float((accepted & (pred == CLASSES.index("not_leaf"))).mean()) if len(rows) else None}
    if not closed_set or not len(rows):
        return out, p
    y = np.array([CLASSES.index(r["label"]) for r in rows])
    present = sorted(set(y.tolist()))
    correct = pred == y
    prec, rec, f1, sup = precision_recall_fscore_support(y, pred, labels=present, zero_division=0)
    out.update({
        "classes_scored": [CLASSES[c] for c in present],
        "accuracy": float(correct.mean()),
        "macro_f1": float(f1_score(y, pred, labels=present, average="macro", zero_division=0)),
        "per_class": {CLASSES[c]: {"precision": float(prec[i]), "recall": float(rec[i]), "f1": float(f1[i]), "n": int(sup[i])}
                      for i, c in enumerate(present)},
        "confusion": {"labels": CLASSES, "rows": "true", "cols": "predicted (argmax, before abstention)",
                      "matrix": confusion_matrix(y, pred, labels=list(range(len(CLASSES)))).tolist()},
        "selective": {"threshold": threshold, "coverage": float(accepted.mean()),
                      "accepted_accuracy": float(correct[accepted].mean()) if accepted.any() else None,
                      "n_accepted": int(accepted.sum())},
        "ece_15_bins": ece(conf, correct),
        "per_source_accuracy": {s: float(correct[[r["source"] == s for r in rows]].mean())
                                for s in sorted({r["source"] for r in rows})},
    })
    out["_curve"] = coverage_curve(conf, correct)
    return out, p


def plot_confusion(m, title, path):
    m = np.array(m)
    keep = [i for i in range(len(CLASSES)) if m[i].sum() > 0]
    sub = m[keep]
    norm = sub / np.maximum(sub.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(7, 0.6 * len(keep) + 2))
    ax.imshow(norm, cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(CLASSES)), CLASSES, rotation=30, ha="right")
    ax.set_yticks(range(len(keep)), [CLASSES[i] for i in keep])
    for i in range(len(keep)):
        for j in range(len(CLASSES)):
            ax.text(j, i, f"{sub[i, j]}\n{norm[i, j]:.0%}", ha="center", va="center", fontsize=7,
                    color="white" if norm[i, j] > 0.6 else "black")
    ax.set_xlabel("predicted (argmax, before abstention)")
    ax.set_ylabel("true")
    ax.set_title("\n".join(textwrap.wrap(title, 70)), fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_coverage(curves, threshold, title, path):
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for name, (t, cov, acc) in curves.items():
        line, = ax.plot(cov, acc, label=name)
        k = np.nonzero(t >= threshold)[0]
        if len(k):
            ax.plot(cov[k[-1]], acc[k[-1]], "o", color=line.get_color())
            ax.annotate(f"{cov[k[-1]]:.0%} cov, {acc[k[-1]]:.1%} acc", (cov[k[-1]], acc[k[-1]]), fontsize=7,
                        xytext=(5, -12), textcoords="offset points")
    ax.axhline(0.95, color="grey", ls=":", lw=1)
    ax.set_xlabel("coverage (share of images not abstained)")
    ax.set_ylabel("accuracy on accepted images")
    ax.set_xlim(0, 1.02)
    ax.set_title(f"{title}\ndots: shipped threshold {threshold:.3f}", fontsize=9)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def latency(sess, sample_path: Path, runs: int):
    img = open_rgb(sample_path)
    t_pre = []
    for _ in range(20):
        t0 = time.perf_counter()
        x = to_tensor(engine_crop(open_rgb(sample_path)))[None]
        t_pre.append((time.perf_counter() - t0) * 1000)
    for _ in range(10):
        sess.run(["logits"], {"input": x})
    t = []
    for _ in range(runs):
        t0 = time.perf_counter()
        sess.run(["logits"], {"input": x})
        t.append((time.perf_counter() - t0) * 1000)
    t = np.array(t)
    return {"runs": runs, "threads": 1, "inference_ms": {"mean": float(t.mean()), "median": float(np.median(t)),
                                                        "p90": float(np.percentile(t, 90))},
            "decode_and_preprocess_ms_median": float(np.median(t_pre)), "sample_image_size": list(img.size),
            "machine": {"platform": platform.platform(), "processor": platform.processor() or platform.machine(),
                        "cpu_count": os.cpu_count(), "loadavg_1m_at_start": os.getloadavg()[0]},
            "note": "onnxruntime CPU in Python, not onnxruntime-web on a phone; inference only unless stated"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default=str(ROOT / "app" / "public" / "model"))
    ap.add_argument("--calibration", default=str(ML / "calibration.json"))
    ap.add_argument("--export-report", default=str(ML / "export_report.json"))
    ap.add_argument("--manifest", default=str(ML / "manifest.csv"))
    ap.add_argument("--data-root", default=str(ROOT / "data_raw"))
    ap.add_argument("--sets", nargs="*", default=list(SETS))
    ap.add_argument("--max-per-class", type=int, default=0, help="0 = all images")
    ap.add_argument("--latency-runs", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(ML / "metrics.json"))
    ap.add_argument("--fig-dir", default=str(ML / "figures"))
    a = ap.parse_args()

    set_threads(1)
    model_dir, data_root, manifest = Path(a.model_dir), Path(a.data_root), Path(a.manifest)
    cfg = json.loads((model_dir / "model.json").read_text())
    onnx_path = model_dir / "leaf.onnx"
    nbytes, digest = onnx_path.stat().st_size, sha256_file(onnx_path)
    if cfg.get("bytes") != nbytes or cfg.get("sha256") != digest:
        raise SystemExit(f"model.json bytes/sha256 do not match leaf.onnx ({nbytes}, {digest}); re-run export.py")
    if cfg["labels"] != CLASSES:
        raise SystemExit(f"model.json labels {cfg['labels']} differ from {CLASSES}")
    temperature, threshold = float(cfg["temperature"]), float(cfg["threshold"])
    sess = ort_session(onnx_path, 1)
    fig_dir = Path(a.fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)

    metrics = {
        "model": {"version": cfg["version"], "file": "leaf.onnx", "bytes": nbytes, "sha256": digest,
                  "temperature": temperature, "threshold": threshold, "arch": cfg.get("arch")},
        "command": " ".join([os.path.basename(sys.executable)] + sys.argv),
        "inference": "int8 ONNX via onnxruntime CPU, 1 thread, engine preprocessing; no quality gate applied",
        "sample_cap_per_class": a.max_per_class or None,
        "test_sets": {},
    }
    curves, examples = {}, []
    for name in a.sets:
        spec = SETS[name]
        rows = load_split(manifest, spec["split"], a.max_per_class, a.seed, labels=spec["labels"])
        assert all(r["split"] != "excluded_heldout_dup_of_train" for r in rows)
        print(f"{name}: {len(rows)} images")
        logits, rows = infer(sess, rows, data_root)
        closed = spec["labels"] == CLASSES
        s, p = scores(logits, rows, temperature, threshold, spec["desc"], closed_set=closed)
        if "_curve" in s:
            curves[name] = s.pop("_curve")
        metrics["test_sets"][name] = s
        if closed:
            plot_confusion(s["confusion"]["matrix"], f"{name}: {spec['desc']}\n(n={s['n']}, int8 ONNX)",
                           fig_dir / f"confusion_{name}.png")
        if name == "in_domain_test":
            nl = [i for i, r in enumerate(rows) if r["label"] == "not_leaf"]
            if nl:
                metrics["test_sets"]["not_leaf_test"], _ = scores(
                    logits[nl], [rows[i] for i in nl], temperature, threshold,
                    "not_leaf rows of the in-domain test split (PlantDoc non-coffee leaves)", closed_set=False)
            rng = np.random.default_rng(a.seed)
            conf = p.max(1)
            acc_i = [i for i in np.nonzero(conf >= threshold)[0]]
            abs_i = [i for i in np.nonzero(conf < threshold)[0]]
            pick = list(rng.permutation(acc_i)[:3]) + list(rng.permutation(abs_i)[:2])
            for i in pick:
                top3 = np.argsort(-p[i])[:3]
                examples.append({"test_set": "in_domain_test", "path": rows[i]["path"], "true": rows[i]["label"],
                                 "top3": [[CLASSES[k], float(p[i, k])] for k in top3],
                                 "accepted": bool(conf[i] >= threshold)})
    if "rocole_red_spider_mite" in metrics["test_sets"]:
        metrics["test_sets"]["rocole_red_spider_mite"]["note"] = (
            "No class fits red spider mite. Desired behaviour is abstention or not_leaf; any accepted disease label is a wrong answer.")
    metrics["worked_examples"] = examples
    if curves:
        plot_coverage(curves, threshold, "Accuracy vs coverage (int8 ONNX, calibrated)", fig_dir / "accuracy_vs_coverage.png")
        metrics["figures"] = sorted(str(p.name) for p in fig_dir.glob("*.png"))

    cal_path = Path(a.calibration)
    if cal_path.exists():
        cal = json.loads(cal_path.read_text())
        metrics["calibration"] = {k: cal.get(k) for k in ("test_set", "n", "temperature", "threshold", "chosen", "targets",
                                                          "nll", "ece_15_bins", "checkpoint_sha256")}
        metrics["calibration"]["note"] = "fitted on PyTorch fp32 val logits; the shipped model is int8"
    rep = Path(a.export_report)
    if rep.exists():
        r = json.loads(rep.read_text())
        metrics["export"] = {"bytes": r.get("bytes"), "parity": r.get("parity"), "failures": r.get("failures"),
                             "quantisation": r.get("quantisation"), "opset": r.get("opset")}

    sample = next((r for r in load_split(manifest, "test", 0, a.seed, sources=["bracol"])), None)
    if sample:
        metrics["latency"] = latency(sess, data_root / sample["path"], a.latency_runs)
        metrics["latency"]["sample_source"] = "BRACOL test photo"

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(metrics, indent=2))
    brief = {k: {kk: v.get(kk) for kk in ("n", "accuracy", "macro_f1", "abstention_rate", "rate_abstain_or_not_leaf", "selective")}
             for k, v in metrics["test_sets"].items()}
    print(json.dumps({"model": metrics["model"], "test_sets": brief, "latency": metrics.get("latency", {}).get("inference_ms")}, indent=2))
    print(f"wrote {a.out} and figures in {fig_dir}")


if __name__ == "__main__":
    main()
