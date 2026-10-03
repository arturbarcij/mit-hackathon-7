#!/usr/bin/env python3
"""Evaluate a real checkpoint and print the EVALUATION.md text.

Writes app/ml/metrics.json only when a checkpoint can be scored.
Does not edit app/docs/EVALUATION.md. If no checkpoint exists, prints a
notice and exits 0 without inventing accuracy figures.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from common import (
    DOCS_DIR,
    HELD_OUT_SOURCES,
    LABELS,
    MANIFEST_PATH,
    METRICS_PATH,
    PUBLIC_MODEL,
    image_path,
    latest_best_checkpoint,
    load_manifest,
    softmax,
    to_nchw,
)

SHARED_UGANDA = ["healthy", "rust", "phoma"]
SHARED_ROCOLE = ["healthy", "rust"]


def _load_checkpoint(path: Path):
    import torch

    try:
        bundle = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        bundle = torch.load(path, map_location="cpu")
    import timm

    model = timm.create_model(bundle.get("arch", "mobilenetv3_small_100"), pretrained=False, num_classes=len(LABELS))
    model.load_state_dict(bundle["state_dict"])
    model.eval()
    return model


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _score_rows(model, rows: list[dict]) -> list[dict]:
    import torch
    from PIL import Image

    scored = []
    try:
        from tqdm import tqdm

        iterator = tqdm(rows, desc="eval")
    except ImportError:
        iterator = rows
    with torch.no_grad():
        for row in iterator:
            path = image_path(row)
            if not path.is_file():
                continue
            with Image.open(path) as image:
                batch = to_nchw(image)
            logits = model(torch.from_numpy(batch))[0]
            values = [float(value) for value in logits]
            scored.append({**row, "logits": values})
    return scored


def _with_probs(scored: list[dict], temperature: float | None) -> list[dict]:
    if temperature is None or temperature <= 0:
        return scored
    for row in scored:
        probabilities = softmax(row["logits"], temperature)
        order = sorted(range(len(probabilities)), key=lambda index: probabilities[index], reverse=True)
        row["probs"] = {LABELS[index]: probabilities[index] for index in range(len(LABELS))}
        row["top1"] = LABELS[order[0]]
        row["confidence"] = probabilities[order[0]]
        row["top3"] = [{"label": LABELS[index], "prob": probabilities[index]} for index in order[:3]]
    return scored


def _empty_block(note: str) -> dict:
    return {
        "n": 0,
        "accuracy": None,
        "macro_f1": None,
        "per_class": {},
        "confusion_matrix": None,
        "note": note,
    }


def _classification_block(rows: list[dict], label_names: list[str]) -> dict:
    usable = [row for row in rows if row.get("top1") in label_names and row.get("label") in label_names]
    if not usable:
        return _empty_block("no images")
    index = {label: position for position, label in enumerate(label_names)}
    truth = [index[row["label"]] for row in usable]
    pred = [index[row["top1"]] for row in usable]
    try:
        from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support

        labels = list(range(len(label_names)))
        accuracy = float(accuracy_score(truth, pred))
        macro = float(f1_score(truth, pred, labels=labels, average="macro", zero_division=0))
        precision, recall, _f1, support = precision_recall_fscore_support(
            truth, pred, labels=labels, zero_division=0
        )
        matrix = confusion_matrix(truth, pred, labels=labels).tolist()
        backend = "sklearn"
    except ImportError:
        accuracy = sum(1 for left, right in zip(truth, pred) if left == right) / len(truth)
        precision = []
        recall = []
        support = []
        f1s = []
        matrix = [[0 for _ in label_names] for _ in label_names]
        for class_index, _name in enumerate(label_names):
            tp = sum(1 for left, right in zip(truth, pred) if left == class_index and right == class_index)
            fp = sum(1 for left, right in zip(truth, pred) if left != class_index and right == class_index)
            fn = sum(1 for left, right in zip(truth, pred) if left == class_index and right != class_index)
            prec = tp / (tp + fp) if tp + fp else 0.0
            rec = tp / (tp + fn) if tp + fn else 0.0
            precision.append(prec)
            recall.append(rec)
            support.append(sum(1 for left in truth if left == class_index))
            f1s.append(0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec))
            for left, right in zip(truth, pred):
                if left == class_index:
                    matrix[class_index][right] += 1
        macro = sum(f1s) / len(label_names)
        backend = "python"
    per_class = {}
    try:
        import pandas as pd

        frame = pd.DataFrame(
            {
                "label": label_names,
                "precision": [float(value) for value in precision],
                "recall": [float(value) for value in recall],
                "support": [int(value) for value in support],
            }
        )
        for record in frame.to_dict(orient="records"):
            per_class[str(record["label"])] = {
                "precision": float(record["precision"]),
                "recall": float(record["recall"]),
                "support": int(record["support"]),
            }
    except ImportError:
        for name, prec, rec, supp in zip(label_names, precision, recall, support):
            per_class[name] = {"precision": float(prec), "recall": float(rec), "support": int(supp)}
    return {
        "n": len(usable),
        "accuracy": accuracy,
        "macro_f1": macro,
        "per_class": per_class,
        "confusion_matrix": {"labels": label_names, "matrix": matrix},
        "metric_backend": backend,
        "note": "",
    }


def _selective(rows: list[dict], threshold: float | None) -> dict:
    usable = [row for row in rows if "confidence" in row]
    if not usable:
        return {"threshold": threshold, "coverage": None, "accuracy_on_accepted": None, "curve": [], "note": "no images"}
    ordered = sorted(usable, key=lambda row: row["confidence"], reverse=True)
    curve = []
    steps = 20
    for step in range(1, steps + 1):
        k = max(1, int(round(len(ordered) * step / steps)))
        chunk = ordered[:k]
        correct = sum(1 for row in chunk if row["top1"] == row["label"])
        curve.append({"coverage": k / len(ordered), "accuracy": correct / k})
    if threshold is None:
        return {
            "threshold": None,
            "coverage": None,
            "accuracy_on_accepted": None,
            "curve": curve,
            "note": "no fitted threshold, so accepted accuracy is not reported",
        }
    accepted = [row for row in usable if row["confidence"] >= threshold]
    if not accepted:
        accuracy = None
        coverage = 0.0
    else:
        accuracy = sum(1 for row in accepted if row["top1"] == row["label"]) / len(accepted)
        coverage = len(accepted) / len(usable)
    return {
        "threshold": threshold,
        "coverage": coverage,
        "accuracy_on_accepted": accuracy,
        "n": len(usable),
        "n_accepted": len(accepted),
        "curve": curve,
        "note": "in-domain test split; threshold was chosen on validation",
    }


def _ood(rows: list[dict], threshold: float | None, want_not_leaf: bool) -> dict:
    if want_not_leaf:
        chosen = [
            row
            for row in rows
            if row.get("label") == "not_leaf" and (row.get("out_of_scope") or "") == "" and row.get("split") == "test"
        ]
    else:
        chosen = [row for row in rows if row.get("out_of_scope") == "red_spider_mite"]
    if not chosen or any("confidence" not in row for row in chosen):
        return {"n": len(chosen), "abstention_rate": None, "predicted_not_leaf_rate": None, "abstain_or_not_leaf_rate": None}
    if threshold is None:
        return {
            "n": len(chosen),
            "abstention_rate": None,
            "predicted_not_leaf_rate": sum(1 for row in chosen if row["top1"] == "not_leaf") / len(chosen),
            "abstain_or_not_leaf_rate": None,
            "note": "threshold was not fitted, so abstention is not reported",
        }
    abstain = sum(1 for row in chosen if row["confidence"] < threshold)
    not_leaf = sum(1 for row in chosen if row["top1"] == "not_leaf")
    either = sum(1 for row in chosen if row["confidence"] < threshold or row["top1"] == "not_leaf")
    n = len(chosen)
    return {
        "n": n,
        "abstention_rate": abstain / n,
        "predicted_not_leaf_rate": not_leaf / n,
        "abstain_or_not_leaf_rate": either / n,
    }


def _examples(rows: list[dict], threshold: float | None) -> list[dict]:
    usable = [row for row in rows if "top3" in row and row.get("split") == "test" and row.get("source") not in HELD_OUT_SOURCES]
    if threshold is None:
        return []
    abstained = sorted(
        [row for row in usable if row["confidence"] < threshold],
        key=lambda row: row["confidence"],
    )
    accepted = [row for row in usable if row["confidence"] >= threshold]
    picked = []
    seen_labels = set()
    for row in accepted:
        if row["top1"] in seen_labels:
            continue
        picked.append(row)
        seen_labels.add(row["top1"])
        if len(picked) == 3:
            break
    for row in accepted:
        if len(picked) >= 3:
            break
        if row not in picked:
            picked.append(row)
    picked.extend(abstained[:2])
    examples = []
    for row in picked:
        examples.append(
            {
                "path": row["path"],
                "true_label": row["label"],
                "source": row["source"],
                "top3": row["top3"],
                "confidence": row["confidence"],
                "decision": "abstained" if row["confidence"] < threshold else "accepted",
            }
        )
    return examples


def _fmt_block(block: dict, name: str) -> str:
    if block.get("n", 0) == 0 or block.get("accuracy") is None:
        return f"{name}: no images in this run, so no accuracy is reported."
    return (
        f"On {name} (n={block['n']}), accuracy is {block['accuracy']:.3f} "
        f"and macro F1 is {block['macro_f1']:.3f}."
    )


def _limits(in_domain: dict, uganda: dict, rocole: dict, selective: dict) -> str:
    parts = [
        _fmt_block(in_domain, "the in-domain test split (JMuBEN, JMuBEN2, BRACOL and PlantDoc after near-duplicate clustering)"),
        "That split is not a Kenya field test.",
        _fmt_block(uganda, "the Uganda held-out set, scored only on healthy, rust and phoma"),
        _fmt_block(rocole, "the RoCoLe held-out set, scored only on healthy and rust, with red spider mite excluded"),
        "Uganda images are small, compressed and partly augmented, and the prefix-to-class map is inferred where no label file is present.",
        "RoCoLe is one Robusta farm in Ecuador. Its images stay together by plant, four per plant when the file names say so.",
        "BRACOL brown leaf spot is merged into cercospora by assumption, and BRACOL has no phoma class.",
        "These figures do not measure PlantVillage, berries, nutrient deficiency, or a Kenyan phone photo test.",
    ]
    if selective.get("accuracy_on_accepted") is None:
        parts.append("Selective prediction is not reported because no threshold was fitted.")
    else:
        parts.append(
            "On the in-domain test split, accuracy on images accepted at the validation threshold "
            f"is {selective['accuracy_on_accepted']:.3f} at coverage {selective['coverage']:.3f}."
        )
    return " ".join(parts)


def _markdown(metrics: dict) -> str:
    lines = [
        "# Evaluation",
        "",
        "Figures below come from ml/metrics.json for this checkpoint. Each accuracy names its test set.",
        "",
        "## 1. In-domain test",
        "",
        _fmt_block(metrics["in_domain_test"], "the in-domain test split"),
        "",
        "## 2. Uganda and RoCoLe",
        "",
        _fmt_block(metrics["uganda"], "the Uganda held-out set (healthy, rust, phoma)"),
        _fmt_block(metrics["rocole"], "the RoCoLe held-out set (healthy and rust only)"),
        "",
        "## 3. Selective prediction",
        "",
    ]
    selective = metrics["selective_prediction"]
    if selective.get("accuracy_on_accepted") is None:
        lines.append("No accepted-accuracy figure is reported. " + selective.get("note", ""))
    else:
        lines.append(
            "On the in-domain test split, accuracy on accepted images is "
            f"{selective['accuracy_on_accepted']:.3f} at coverage {selective['coverage']:.3f}. "
            f"The validation threshold is {selective['threshold']}."
        )
    lines.extend(["", "## 4. Out of distribution", ""])
    for name, block in (("not_leaf test images", metrics["ood"]["not_leaf"]), ("RoCoLe red spider mite", metrics["ood"]["red_spider_mite"])):
        if block.get("abstention_rate") is None and block.get("predicted_not_leaf_rate") is None:
            lines.append(f"{name}: n={block.get('n', 0)}. No rate is reported.")
        else:
            lines.append(
                f"{name}: n={block.get('n', 0)}, abstention rate {block.get('abstention_rate')}, "
                f"predicted not_leaf rate {block.get('predicted_not_leaf_rate')}, "
                f"abstain or not_leaf rate {block.get('abstain_or_not_leaf_rate')}."
            )
    lines.extend(["", "## 5. Size and CPU latency", ""])
    lines.append(
        f"Shipped model size: {metrics['size_bytes'] if metrics['size_bytes'] is not None else 'not available'}. "
        f"CPU latency per image, one thread: {metrics['cpu_latency_ms'] if metrics['cpu_latency_ms'] is not None else 'not available'}."
    )
    if metrics.get("latency_note"):
        lines.append(metrics["latency_note"])
    lines.extend(["", "## 6. Worked examples", ""])
    if not metrics["examples"]:
        lines.append("No worked examples are listed. Two abstentions were not invented.")
    else:
        abstained = sum(1 for example in metrics["examples"] if example["decision"] == "abstained")
        lines.append(f"Examples below include {abstained} abstention(s). Missing abstentions were not invented.")
        for example in metrics["examples"]:
            top = ", ".join(f"{item['label']} {item['prob']:.3f}" for item in example["top3"])
            lines.append(
                f"- {example['path']} true {example['true_label']}, {example['decision']}, top3: {top}."
            )
    lines.extend(["", "## 7. What this proves", "", metrics["limits"], ""])
    return "\n".join(lines)


def _save_plots(metrics: dict, plot_dir: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        metrics["plots"] = None
        metrics["plots_note"] = "matplotlib is not installed, so no plots were written"
        return
    plot_dir.mkdir(parents=True, exist_ok=True)
    matrix = metrics["in_domain_test"].get("confusion_matrix")
    written = []
    if matrix and matrix.get("matrix"):
        figure, axis = plt.subplots(figsize=(6, 5))
        axis.imshow(matrix["matrix"])
        axis.set_xticks(range(len(matrix["labels"])))
        axis.set_yticks(range(len(matrix["labels"])))
        axis.set_xticklabels(matrix["labels"], rotation=45, ha="right")
        axis.set_yticklabels(matrix["labels"])
        axis.set_title("In-domain test confusion")
        figure.tight_layout()
        path = plot_dir / "confusion_in_domain.png"
        figure.savefig(path)
        plt.close(figure)
        written.append(str(path))
    curve = metrics["selective_prediction"].get("curve") or []
    if curve:
        figure, axis = plt.subplots(figsize=(6, 4))
        axis.plot([point["coverage"] for point in curve], [point["accuracy"] for point in curve])
        if metrics["selective_prediction"].get("coverage") is not None:
            axis.scatter(
                [metrics["selective_prediction"]["coverage"]],
                [metrics["selective_prediction"]["accuracy_on_accepted"]],
            )
        axis.set_xlabel("Coverage")
        axis.set_ylabel("Accuracy on accepted images")
        axis.set_title("In-domain test selective prediction")
        figure.tight_layout()
        path = plot_dir / "selective_prediction.png"
        figure.savefig(path)
        plt.close(figure)
        written.append(str(path))
    metrics["plots"] = written


def _latency_ms(onnx_path: Path) -> tuple[float | None, str]:
    if not onnx_path.is_file():
        return None, "leaf.onnx is not present, so CPU latency is not reported."
    try:
        import numpy as np
        import onnxruntime as ort
    except ImportError:
        return None, "onnxruntime is not installed, so CPU latency is not reported."
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(onnx_path), sess_options=options, providers=["CPUExecutionProvider"])
    batch = np.zeros((1, 3, 224, 224), dtype="float32")
    for _ in range(5):
        session.run(["logits"], {"input": batch})
    started = time.perf_counter()
    repeats = 20
    for _ in range(repeats):
        session.run(["logits"], {"input": batch})
    elapsed = time.perf_counter() - started
    return (elapsed / repeats) * 1000.0, "CPU latency is the mean of 20 runs after 5 warm-up runs, one thread, on a zero tensor of shape [1, 3, 224, 224]."


def _missing_checkpoint_message() -> str:
    return "\n".join(
        [
            "No model has been trained in this checkout. Metrics are not available.",
            "",
            "This script would write app/ml/metrics.json and print the text for docs/EVALUATION.md.",
            "It does not edit app/docs/EVALUATION.md.",
            "",
            "Sections that would be filled from a real checkpoint:",
            "1. In-domain test (manifest split test, excluding Uganda and RoCoLe): accuracy, macro F1, per-class precision and recall, confusion matrix.",
            "2. Uganda and RoCoLe held-out results on the classes those sets share with the model.",
            "3. Selective prediction: accuracy against coverage, with the validation threshold marked.",
            "4. Out of distribution: abstention rate on not_leaf and on RoCoLe red spider mite.",
            "5. File size in bytes and CPU latency per image (onnxruntime, one thread).",
            "6. Five worked examples, including two abstentions.",
            "7. A paragraph on what the figures prove and what they do not.",
            "",
            "No accuracy figure is printed because no checkpoint exists.",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a checkpoint. Does not invent metrics.")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--metrics", type=Path, default=METRICS_PATH)
    args = parser.parse_args(argv)

    if DOCS_DIR in args.metrics.resolve().parents or args.metrics.resolve() == DOCS_DIR:
        print("Refusing to write under app/docs.")
        return 1

    checkpoint = args.checkpoint if args.checkpoint else latest_best_checkpoint()
    if checkpoint is None or not checkpoint.is_file():
        print(_missing_checkpoint_message())
        return 0

    if not args.manifest.is_file():
        print(f"Checkpoint found but {args.manifest} is missing. Refusing to invent metrics.")
        return 1
    try:
        import torch  # noqa: F401
    except ImportError:
        print("Checkpoint found but torch is not installed. Refusing to invent metrics.")
        return 1

    rows = load_manifest(args.manifest)
    calibration = _read_json(checkpoint.parent / "calibration.json") or {}
    temperature = calibration.get("temperature")
    threshold = calibration.get("threshold")
    temperature_f = float(temperature) if isinstance(temperature, (int, float)) else None
    threshold_f = float(threshold) if isinstance(threshold, (int, float)) else None

    model = _load_checkpoint(checkpoint)
    in_domain_rows = [
        row
        for row in rows
        if row.get("split") == "test"
        and (row.get("out_of_scope") or "") == ""
        and row.get("source") not in HELD_OUT_SOURCES
    ]
    uganda_rows = [
        row
        for row in rows
        if row.get("source") == "Uganda" and row.get("split") == "heldout" and (row.get("out_of_scope") or "") == ""
    ]
    rocole_rows = [
        row
        for row in rows
        if row.get("source") == "RoCoLe"
        and (row.get("out_of_scope") or "") == ""
        and row.get("label") in SHARED_ROCOLE
    ]
    mite_rows = [row for row in rows if row.get("out_of_scope") == "red_spider_mite"]
    needed = in_domain_rows + uganda_rows + rocole_rows + mite_rows
    scored = _with_probs(_score_rows(model, needed), temperature_f)
    by_path = {row["path"]: row for row in scored}

    def take(selected: list[dict]) -> list[dict]:
        return [by_path[row["path"]] for row in selected if row["path"] in by_path]

    in_domain = _classification_block(take(in_domain_rows), LABELS)
    in_domain["test_set"] = "manifest split=test, sources other than Uganda and RoCoLe, out_of_scope empty"
    uganda = _classification_block(take(uganda_rows), SHARED_UGANDA)
    uganda["test_set"] = "Uganda held-out, shared classes healthy rust phoma"
    rocole = _classification_block(take(rocole_rows), SHARED_ROCOLE)
    rocole["test_set"] = "RoCoLe held-out, healthy and rust only, red spider mite excluded"
    selective = _selective(take(in_domain_rows), threshold_f)
    ood = {
        "not_leaf": _ood(scored, threshold_f, want_not_leaf=True),
        "red_spider_mite": _ood(scored, threshold_f, want_not_leaf=False),
    }
    examples = _examples(scored, threshold_f)
    onnx_path = PUBLIC_MODEL / "leaf.onnx"
    if not onnx_path.is_file():
        candidate = checkpoint.parent / "leaf_int8.onnx"
        onnx_path = candidate if candidate.is_file() else onnx_path
    size = onnx_path.stat().st_size if onnx_path.is_file() else None
    latency, latency_note = _latency_ms(onnx_path) if onnx_path.is_file() else (None, "leaf.onnx is not present, so CPU latency is not reported.")
    metrics = {
        "status": "computed",
        "checkpoint": str(checkpoint),
        "temperature": temperature_f,
        "threshold": threshold_f,
        "in_domain_test": in_domain,
        "uganda": uganda,
        "rocole": rocole,
        "selective_prediction": selective,
        "ood": ood,
        "size_bytes": size,
        "cpu_latency_ms": latency,
        "latency_note": latency_note,
        "examples": examples,
        "limits": _limits(in_domain, uganda, rocole, selective),
    }
    _save_plots(metrics, METRICS_PATH.parent / "plots")
    if DOCS_DIR in args.metrics.resolve().parents:
        print("Refusing to write metrics under app/docs.")
        return 1
    args.metrics.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(_markdown(metrics))
    print(f"Wrote {args.metrics}")
    print("app/docs/EVALUATION.md was not modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
