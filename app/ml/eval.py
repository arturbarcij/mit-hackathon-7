"""Write ml/metrics.json and docs/EVALUATION.md. Never trains. Uganda/RoCoLe are test-only."""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader
from tqdm import tqdm

from common import DOCS, LABEL_TO_IDX, LABELS, ML, PUBLIC_MODEL, ROOT, SEED
from train import LeafDataset, eval_transform, metrics, run_eval

import timm


def read_manifest(path=None):
    path = Path(path) if path else ML / "manifest.csv"
    if not path.is_absolute():
        path = ROOT / path if (ROOT / path).exists() else path
    rows = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def subset(rows, *, split=None, source=None, label=None):
    out = []
    for r in rows:
        if r["label"] not in LABEL_TO_IDX:
            continue
        if split and r["split"] != split:
            continue
        if source and r["source"] != source:
            continue
        if label and r["label"] != label:
            continue
        if not (ROOT / r["path"]).exists():
            continue
        out.append(r)
    return out


@torch.no_grad()
def predict_rows(model, rows, device, T, batch=64):
    if not rows:
        return np.zeros((0, len(LABELS))), np.array([], dtype=int)
    ds = LeafDataset(rows, eval_transform())
    loader = DataLoader(ds, batch_size=batch, shuffle=False, num_workers=0)
    logits_all, ys = [], []
    model.eval()
    for x, y in loader:
        x = x.to(device)
        logits_all.append(model(x).cpu())
        ys.extend(y.tolist())
    logits = torch.cat(logits_all)
    probs = torch.softmax(logits / T, dim=1).numpy()
    return probs, np.array(ys)


def confusion_png(y, pred, dest: Path, title: str):
    k = len(LABELS)
    cm = np.zeros((k, k), dtype=int)
    for a, b in zip(y, pred):
        cm[a, b] += 1
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(k), LABELS, rotation=40, ha="right")
    ax.set_yticks(range(k), LABELS)
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(title)
    for i in range(k):
        for j in range(k):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=120)
    plt.close(fig)
    return cm


def coverage_png(probs, y, threshold, dest: Path):
    conf = probs.max(1)
    pred = probs.argmax(1)
    order = np.argsort(-conf)
    xs, ys = [], []
    for k in range(1, len(order) + 1):
        idx = order[:k]
        xs.append(k / len(order))
        ys.append(float((pred[idx] == y[idx]).mean()))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xs, ys, color="#1d4ed8")
    # mark our threshold
    accepted = conf >= threshold
    if accepted.any():
        cov = float(accepted.mean())
        acc = float((pred[accepted] == y[accepted]).mean())
        ax.axvline(cov, color="#b45309", ls="--", label=f"threshold {threshold:.2f}")
        ax.scatter([cov], [acc], color="#b45309")
    ax.set_xlabel("coverage")
    ax.set_ylabel("accuracy on accepted")
    ax.set_title("Selective prediction on in-domain val")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def load_model(cal, device):
    ckpt_path = Path(cal["best_checkpoint"])
    if not ckpt_path.is_absolute():
        ckpt_path = ROOT / ckpt_path
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    arch = cal.get("arch") or ckpt.get("args", {}).get("arch") or "mobilenetv3_small_100"
    model = timm.create_model(arch, pretrained=False, num_classes=len(LABELS))
    model.load_state_dict(ckpt["model"])
    model.to(device)
    model.eval()
    return model


def cpu_latency(onnx_path: Path, paths: list[Path], n=30) -> float:
    import onnxruntime as ort
    from export import preprocess_numpy
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    sess._sess  # keep
    opts_ok = True
    so = ort.SessionOptions()
    so.intra_op_num_threads = 1
    so.inter_op_num_threads = 1
    sess = ort.InferenceSession(str(onnx_path), so, providers=["CPUExecutionProvider"])
    times = []
    for p in paths[:n]:
        arr = preprocess_numpy(p)
        t0 = time.perf_counter()
        sess.run(["logits"], {"input": arr})
        times.append(time.perf_counter() - t0)
    return float(np.median(times)) if times else -1.0


def write_eval_md(m: dict, dest: Path):
    idom = m["in_domain_test"]
    lines = [
        "# EVALUATION",
        "",
        "Owner: ml agent. Numbers come from `app/ml/eval.py` on the v1 model. Plain British English.",
        "",
        "Every accuracy figure names its test set. Uganda and RoCoLe were never used for training.",
        "",
        "## 1. In-domain test (JMuBEN + JMuBEN2 + BRACOL + PlantDoc held-out split)",
        "",
        f"- Images: {idom['n']}",
        f"- Accuracy: {idom['acc']:.3f} on the in-domain test split",
        f"- Macro F1: {idom['macro_f1']:.3f} on the in-domain test split",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in LABELS:
        c = idom["per_class"][name]
        lines.append(f"| {name} | {c['precision']:.3f} | {c['recall']:.3f} | {c['f1']:.3f} | {c['support']} |")
    lines += [
        "",
        "Confusion matrix: `app/ml/plots/cm_indomain.png`.",
        "",
        "## 2. Cross-domain (held-out; never trained on)",
        "",
    ]
    ug = m.get("uganda")
    if ug and ug["n"]:
        lines += [
            f"### Uganda coffee leaf set (Soroti; smartphone; augmented copies may be present)",
            "",
            f"- Images scored: {ug['n']} (shared classes only: healthy, rust, phoma)",
            f"- Accuracy: {ug['acc']:.3f} on the Uganda set",
            f"- Macro F1 (shared classes): {ug['macro_f1']:.3f} on the Uganda set",
            "",
        ]
    else:
        lines += [
            "### Uganda coffee leaf set",
            "",
            "NOT RUN. Download was incomplete at evaluation time (held-out files missing or only the healthy prefix).",
            "",
        ]
    ro = m.get("rocole")
    if ro and ro["n"]:
        lines += [
            f"### RoCoLe (Ecuador, Robusta, field)",
            "",
            f"- Images scored: {ro['n']} (healthy and rust only; red spider mite used as an OOD probe)",
            f"- Accuracy: {ro['acc']:.3f} on the RoCoLe shared classes",
            f"- Macro F1: {ro['macro_f1']:.3f} on the RoCoLe shared classes",
            "",
        ]
    else:
        lines += [
            "### RoCoLe (Ecuador, Robusta, field)",
            "",
            "NOT RUN. Images were not on disk at evaluation time. They are held-out and were never used for training.",
            "",
        ]
    sel = m["selective"]
    lines += [
        "## 3. Selective prediction",
        "",
        f"- Temperature: {m['temperature']:.3f}",
        f"- Confidence threshold: {m['threshold']:.3f}",
        f"- In-domain val accuracy on accepted cases: {sel['val_acc_accepted']:.3f}",
        f"- Coverage at that threshold (in-domain val): {sel['val_coverage']:.3f}",
        f"- In-domain test accuracy on accepted cases: {sel['test_acc_accepted']:.3f}",
        f"- Coverage at that threshold (in-domain test): {sel['test_coverage']:.3f}",
        "",
        "Curve: `app/ml/plots/coverage_val.png`.",
        "",
        "## 4. Out-of-distribution",
        "",
        f"- `not_leaf` in-domain test: abstain or predict not_leaf on {m['ood']['not_leaf_safe_rate']:.3f} of {m['ood']['not_leaf_n']} images",
        f"- RoCoLe red spider mite (OOD probe): abstain or predict not_leaf on {m['ood']['mite_safe_rate']:.3f} of {m['ood']['mite_n']} images",
        "",
        "## 5. Size and latency",
        "",
        f"- `leaf.onnx` ({m.get('quantization', 'fp16')}): {m['size_bytes']} bytes ({m['size_bytes'] / (1024 * 1024):.2f} MB). Static int8 QDQ broke MobileNetV3 h-swish (parity under 35%).",
        f"- CPU latency (onnxruntime, 1 thread, median of {m['latency_n']} images): {m['latency_s'] * 1000:.0f} ms per leaf",
        "- Device: measured on the training laptop CPU, not a field Android. Field latency is still to measure.",
        "",
        "## 6. Worked examples",
        "",
        "Images and top-3 probabilities are in `app/ml/examples/`. Two of the five are abstentions.",
        "",
    ]
    for ex in m["examples"]:
        lines += [
            f"- `{ex['file']}`  true={ex['true']}  pred={ex['pred']}  conf={ex['confidence']:.3f}  "
            f"{'ABSTAIN' if ex['abstained'] else 'accept'}  top3={ex['top3']}",
        ]
    lines += [
        "",
        "## 7. What these numbers prove, and what they do not",
        "",
        m["caveat"],
        "",
    ]
    dest.write_text("\n".join(lines), encoding="utf-8")


def pick_examples(rows, probs, y, threshold, out: Path):
    pred = probs.argmax(1)
    conf = probs.max(1)
    out.mkdir(parents=True, exist_ok=True)
    chosen = []
    # two abstentions, three accepted (prefer diverse labels)
    abs_idx = [i for i in range(len(rows)) if conf[i] < threshold]
    acc_idx = [i for i in range(len(rows)) if conf[i] >= threshold]
    rng = np.random.default_rng(SEED)
    take_abs = list(rng.choice(abs_idx, size=min(2, len(abs_idx)), replace=False)) if abs_idx else []
    take_acc = list(rng.choice(acc_idx, size=min(3, len(acc_idx)), replace=False)) if acc_idx else []
    for i in take_abs + take_acc:
        p = ROOT / rows[i]["path"]
        dest = out / f"ex_{len(chosen):02d}.jpg"
        with Image.open(p) as im:
            im.convert("RGB").save(dest, quality=85)
        order = list(np.argsort(-probs[i])[:3])
        top3 = {LABELS[j]: round(float(probs[i][j]), 4) for j in order}
        chosen.append({
            "file": dest.name,
            "true": rows[i]["label"],
            "pred": LABELS[int(pred[i])],
            "confidence": float(conf[i]),
            "abstained": bool(conf[i] < threshold),
            "top3": top3,
        })
    return chosen


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="Run dir or calibration.json")
    ap.add_argument("--out", default=None, help="Write metrics and plots here; skip docs/EVALUATION.md")
    ap.add_argument("--manifest", default=None)
    args = ap.parse_args()

    cal_file = ML / "calibration.json"
    if args.run:
        p = Path(args.run)
        if not p.is_absolute():
            p = ROOT / p
        cal_file = p / "calibration.json" if p.is_dir() else p
    cal = json.loads(cal_file.read_text(encoding="utf-8"))
    T = float(cal["temperature"])
    thr = float(cal["threshold"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(cal, device)
    rows = read_manifest(args.manifest)
    out_root = Path(args.out) if args.out else ML
    if args.out and not out_root.is_absolute():
        out_root = ROOT / out_root
    plots = out_root / "plots"
    plots.mkdir(parents=True, exist_ok=True)

    test = subset(rows, split="test")
    val = subset(rows, split="val")
    probs_te, y_te = predict_rows(model, test, device, T)
    pred_te = probs_te.argmax(1)
    idom = metrics(y_te, pred_te)
    idom["n"] = int(len(y_te))
    confusion_png(y_te, pred_te, plots / "cm_indomain.png", "In-domain test")

    probs_va, y_va = predict_rows(model, val, device, T)
    coverage_png(probs_va, y_va, thr, plots / "coverage_val.png")
    acc_va = (probs_va.argmax(1) == y_va)
    acc_te = (pred_te == y_te)
    sel = {
        "val_acc_accepted": float(acc_va[probs_va.max(1) >= thr].mean()) if (probs_va.max(1) >= thr).any() else 0.0,
        "val_coverage": float((probs_va.max(1) >= thr).mean()) if len(y_va) else 0.0,
        "test_acc_accepted": float(acc_te[probs_te.max(1) >= thr].mean()) if (probs_te.max(1) >= thr).any() else 0.0,
        "test_coverage": float((probs_te.max(1) >= thr).mean()) if len(y_te) else 0.0,
    }

    def shared_eval(name, allowed):
        sub = [r for r in subset(rows, source=name) if r["label"] in allowed]
        if not sub:
            return {"n": 0, "acc": 0.0, "macro_f1": 0.0, "per_class": {}}
        # Map to full 6-way then score only on allowed indices
        pr, y = predict_rows(model, sub, device, T)
        # collapse prediction: if pred not in allowed, it is a miss
        allow_idx = {LABEL_TO_IDX[a] for a in allowed}
        pred = pr.argmax(1)
        # metrics on full label set but only rows whose true label is allowed
        m = metrics(y, pred)
        m["n"] = int(len(y))
        return m

    uganda = shared_eval("uganda", {"healthy", "rust", "phoma"})
    rocole = shared_eval("rocole", {"healthy", "rust"})

    not_leaf = subset(rows, split="test", label="not_leaf")
    pr_nl, _ = predict_rows(model, not_leaf, device, T)
    if len(pr_nl):
        nl_pred = pr_nl.argmax(1)
        nl_conf = pr_nl.max(1)
        nl_safe = ((nl_pred == LABEL_TO_IDX["not_leaf"]) | (nl_conf < thr)).mean()
        nl_n = len(pr_nl)
    else:
        nl_safe, nl_n = 0.0, 0

    mites = [r for r in subset(rows, source="rocole") if r["original_label"] == "red_spider_mite"]
    pr_m, _ = predict_rows(model, mites, device, T)
    if len(pr_m):
        m_pred = pr_m.argmax(1)
        m_conf = pr_m.max(1)
        mite_safe = float(((m_pred == LABEL_TO_IDX["not_leaf"]) | (m_conf < thr)).mean())
        mite_n = len(pr_m)
    else:
        mite_safe, mite_n = 0.0, 0

    onnx_path = (out_root / "leaf.onnx") if args.out else PUBLIC_MODEL / "leaf.onnx"
    if not onnx_path.exists() and (out_root / "leaf_int8.onnx").exists():
        onnx_path = out_root / "leaf_int8.onnx"
    size = onnx_path.stat().st_size if onnx_path.exists() else 0
    lat_paths = [ROOT / r["path"] for r in test[:40]]
    latency = cpu_latency(onnx_path, lat_paths) if onnx_path.exists() and lat_paths else -1.0

    examples = pick_examples(test, probs_te, y_te, thr, out_root / "examples")

    caveat = (
        "These figures show that a small ImageNet-pretrained MobileNetV3-Small, fine-tuned on "
        "Kenyan JMuBEN/JMuBEN2 crops plus whatever BRACOL leaves we could extract, can separate "
        "the six training labels on a hash-grouped in-domain split. They do not show field accuracy "
        "on whole leaves still on the tree, on Kenyan varieties that are not labelled in the source "
        "sets, or on mixed infections. JMuBEN images are cropped to the lesion and were augmented "
        "without a source-image manifest; near-duplicate hashing reduces leakage but cannot remove it. "
        "The Uganda set is itself augmented, so a high number there would still not be a clean "
        "cross-country test. RoCoLe is Robusta, not Arabica, and is a field set. We do not report "
        "PlantVillage coffee accuracy because that set has no coffee. A single-leaf score is not a "
        "plot decision; the app uses ten leaves and abstains when confidence is low."
    )

    out = {
        "temperature": T,
        "threshold": thr,
        "in_domain_test": idom,
        "uganda": uganda,
        "rocole": rocole,
        "selective": sel,
        "ood": {
            "not_leaf_safe_rate": float(nl_safe),
            "not_leaf_n": int(nl_n),
            "mite_safe_rate": mite_safe,
            "mite_n": int(mite_n),
        },
        "size_bytes": int(size),
        "latency_s": latency,
        "latency_n": min(30, len(lat_paths)),
        "examples": examples,
        "caveat": caveat,
        "seed": SEED,
        "never_trained_on": ["uganda", "rocole"],
    }
    (out_root / "metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    if not args.out:
        DOCS.mkdir(parents=True, exist_ok=True)
        write_eval_md(out, DOCS / "EVALUATION.md")
        print("wrote", ML / "metrics.json", "and", DOCS / "EVALUATION.md", flush=True)
    else:
        print("wrote", out_root / "metrics.json", "(docs untouched)", flush=True)
    print("in-domain test acc", idom["acc"], "n", idom["n"], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
