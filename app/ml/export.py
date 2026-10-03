#!/usr/bin/env python3
"""Export a trained checkpoint to ONNX and, when checks pass, publish it.

Opset 17, input name "input", output name "logits", static shape [1, 3, 224, 224].
Static int8 quantisation (QDQ) with about 200 calibration images. Hard cap 5 MB.
public/model/leaf.onnx and public/model/model.json are written only when a
checkpoint exists and the export passes the shape, size, calibration and parity
checks. If no checkpoint exists, this script exits 0 and writes neither file.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
from pathlib import Path

from common import (
    INPUT_SIZE,
    LABELS,
    MANIFEST_PATH,
    MAX_MODEL_BYTES,
    ONNX_OPSET,
    PARITY_DIR,
    PUBLIC_MODEL,
    SEED,
    image_path,
    is_trainable,
    latest_best_checkpoint,
    load_manifest,
    sha256_file,
    softmax,
    to_nchw,
    validate_model_card,
)


def _load_torch_checkpoint(path: Path):
    import torch

    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def _build(arch: str):
    import timm

    model = timm.create_model(arch, pretrained=False, num_classes=len(LABELS))
    model.eval()
    return model


def _export_fp32(model, dest: Path) -> None:
    import torch

    dest.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros(1, 3, INPUT_SIZE, INPUT_SIZE)
    kwargs = dict(
        export_params=True,
        opset_version=ONNX_OPSET,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes=None,
    )
    try:
        torch.onnx.export(model, dummy, str(dest), dynamo=False, **kwargs)
    except TypeError:
        torch.onnx.export(model, dummy, str(dest), **kwargs)


def _assert_onnx_contract(path: Path) -> None:
    import onnx

    model = onnx.load(str(path))
    if len(model.graph.input) != 1 or model.graph.input[0].name != "input":
        raise SystemExit(f"{path} input must be named 'input'")
    dims = [dim.dim_value for dim in model.graph.input[0].type.tensor_type.shape.dim]
    if dims != [1, 3, INPUT_SIZE, INPUT_SIZE]:
        raise SystemExit(f"{path} input shape is {dims}, expected static [1, 3, 224, 224]")
    if len(model.graph.output) < 1 or model.graph.output[0].name != "logits":
        raise SystemExit(f"{path} output must be named 'logits'")


def _calibration_batches(rows: list[dict], limit: int = 200):
    from PIL import Image

    rng = random.Random(SEED)
    pool = [row for row in rows if is_trainable(row) and image_path(row).is_file()]
    rng.shuffle(pool)
    chosen = pool[:limit]
    batches = []
    for row in chosen:
        with Image.open(image_path(row)) as image:
            batches.append(to_nchw(image))
    return batches


def _quantise(fp32_path: Path, int8_path: Path, batches) -> None:
    from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static

    class Reader(CalibrationDataReader):
        def __init__(self, arrays):
            self.batches = arrays
            self.index = 0

        def get_next(self):
            if self.index >= len(self.batches):
                return None
            batch = self.batches[self.index]
            self.index += 1
            return {"input": batch}

        def rewind(self):
            self.index = 0

    reader = Reader(batches)
    quantize_static(
        model_input=str(fp32_path),
        model_output=str(int8_path),
        calibration_data_reader=reader,
        quant_format=QuantFormat.QDQ,
        activation_type=QuantType.QInt8,
        weight_type=QuantType.QInt8,
    )


def _session(path: Path):
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    return ort.InferenceSession(str(path), sess_options=options, providers=["CPUExecutionProvider"])


def _top1_torch(model, batch) -> int:
    import torch

    with torch.no_grad():
        logits = model(torch.from_numpy(batch))
    return int(logits.argmax(dim=1)[0])


def _top1_onnx(session, batch) -> tuple[int, list[float]]:
    logits = session.run(["logits"], {"input": batch})[0][0]
    values = [float(value) for value in logits]
    return max(range(len(values)), key=lambda index: values[index]), values


def _predict_rows(model, fp32_session, int8_session, rows: list[dict]) -> list[dict]:
    from PIL import Image

    reports = []
    try:
        from tqdm import tqdm

        iterator = tqdm(rows, desc="parity")
    except ImportError:
        iterator = rows
    for row in iterator:
        path = image_path(row)
        if not path.is_file():
            continue
        with Image.open(path) as image:
            batch = to_nchw(image)
        torch_top = _top1_torch(model, batch)
        fp32_top, _fp32_logits = _top1_onnx(fp32_session, batch)
        int8_top, int8_logits = _top1_onnx(int8_session, batch)
        reports.append(
            {
                "path": row["path"],
                "label": row["label"],
                "split": row["split"],
                "torch": torch_top,
                "onnx_fp32": fp32_top,
                "onnx_int8": int8_top,
                "int8_logits": int8_logits,
            }
        )
    return reports


def _agreement(reports: list[dict]) -> dict:
    n = len(reports)
    if n == 0:
        return {"n": 0, "three_way": None, "torch_fp32": None, "torch_int8": None, "fp32_int8": None}
    three = sum(1 for row in reports if row["torch"] == row["onnx_fp32"] == row["onnx_int8"])
    torch_fp32 = sum(1 for row in reports if row["torch"] == row["onnx_fp32"])
    torch_int8 = sum(1 for row in reports if row["torch"] == row["onnx_int8"])
    fp32_int8 = sum(1 for row in reports if row["onnx_fp32"] == row["onnx_int8"])
    return {
        "n": n,
        "three_way": three / n,
        "torch_fp32": torch_fp32 / n,
        "torch_int8": torch_int8 / n,
        "fp32_int8": fp32_int8 / n,
    }


def _write_parity_samples(reports: list[dict], temperature: float, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for child in dest.iterdir():
        if child.is_file():
            child.unlink()
    chosen = reports[:10]
    index = []
    for number, row in enumerate(chosen):
        source = image_path({"path": row["path"]})
        filename = f"{number:02d}{source.suffix.lower()}"
        shutil.copy2(source, dest / filename)
        probabilities = softmax(row["int8_logits"], temperature)
        payload = {
            "file": filename,
            "source_path": row["path"],
            "label": row["label"],
            "split": row["split"],
            "temperature": temperature,
            "logits": row["int8_logits"],
            "probs": {LABELS[i]: probabilities[i] for i in range(len(LABELS))},
            "top1": LABELS[int(max(range(len(probabilities)), key=lambda i: probabilities[i]))],
            "preprocess": {
                "resize": "shorter_side_then_center_crop",
                "filter": "bilinear",
                "size": INPUT_SIZE,
                "range": "0-1",
                "mean": [0.485, 0.456, 0.406],
                "std": [0.229, 0.224, 0.225],
                "layout": "NCHW",
                "probs": "softmax of int8 logits divided by temperature",
            },
        }
        (dest / f"{number:02d}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        index.append({"file": filename, "json": f"{number:02d}.json", "top1": payload["top1"]})
    (dest / "index.json").write_text(
        json.dumps({"n": len(index), "samples": index}, indent=2) + "\n",
        encoding="utf-8",
    )


def _version_from_run(run_dir: Path) -> str:
    stamp = run_dir.name
    if len(stamp) >= 8 and stamp[:8].isdigit():
        return f"v1-{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"
    raise SystemExit(f"Run directory name {stamp} is not a timestamp, so no version was invented")


def _read_calibration(run_dir: Path) -> dict | None:
    path = run_dir / "calibration.json"
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _publish(int8_path: Path, card: dict) -> None:
    PUBLIC_MODEL.mkdir(parents=True, exist_ok=True)
    tmp_onnx = PUBLIC_MODEL / ".leaf.onnx.partial"
    tmp_json = PUBLIC_MODEL / ".model.json.partial"
    shutil.copyfile(int8_path, tmp_onnx)
    tmp_json.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_onnx, PUBLIC_MODEL / "leaf.onnx")
    os.replace(tmp_json, PUBLIC_MODEL / "model.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export best.pt to int8 ONNX when a real checkpoint exists.")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    checkpoint = args.checkpoint if args.checkpoint else latest_best_checkpoint()
    if checkpoint is None or not checkpoint.is_file():
        print(
            "No checkpoint found under app/ml/runs. Nothing was exported. "
            "leaf.onnx and model.json were not written."
        )
        return 0

    try:
        import torch  # noqa: F401
    except ImportError:
        print("Checkpoint exists but torch is not installed. Nothing was published.")
        return 1

    run_dir = checkpoint.parent
    bundle = _load_torch_checkpoint(checkpoint)
    arch = bundle.get("arch", "mobilenetv3_small_100")
    model = _build(arch)
    model.load_state_dict(bundle["state_dict"])
    model.eval()

    if not args.manifest.is_file():
        print(f"Checkpoint found but {args.manifest} is missing. Refusing to export without labels. Nothing was published.")
        return 1
    rows = load_manifest(args.manifest)
    calibration = _read_calibration(run_dir)
    if not calibration or not calibration.get("temperature") or calibration.get("threshold") is None:
        print(
            "Checkpoint found but calibration.json has no fitted temperature and threshold. "
            "Refusing to write model.json with placeholder values. Nothing was published."
        )
        return 1
    temperature = float(calibration["temperature"])
    threshold = float(calibration["threshold"])

    batches = _calibration_batches(rows, limit=200)
    if len(batches) < 1:
        print("No trainable images were available for static quantisation. Nothing was published.")
        return 1
    print(f"Static int8 calibration images: {len(batches)} (target about 200).")

    fp32_path = run_dir / "leaf_fp32.onnx"
    int8_path = run_dir / "leaf_int8.onnx"
    _export_fp32(model, fp32_path)
    _assert_onnx_contract(fp32_path)
    _quantise(fp32_path, int8_path, batches)
    _assert_onnx_contract(int8_path)

    test_rows = [
        row
        for row in rows
        if row.get("split") == "test" and (row.get("out_of_scope") or "") == "" and row.get("source") not in {"Uganda", "RoCoLe"}
    ]
    rng = random.Random(SEED)
    rng.shuffle(test_rows)
    parity_rows = test_rows[:50]
    fp32_session = _session(fp32_path)
    int8_session = _session(int8_path)
    reports = _predict_rows(model, fp32_session, int8_session, parity_rows)
    agreement = _agreement(reports)
    (run_dir / "parity_report.json").write_text(json.dumps(agreement, indent=2) + "\n", encoding="utf-8")
    print(
        "Parity top-1 agreement "
        f"(n={agreement['n']}): three-way {agreement['three_way']}, "
        f"torch vs fp32 {agreement['torch_fp32']}, torch vs int8 {agreement['torch_int8']}."
    )
    if reports:
        _write_parity_samples(reports, temperature, PARITY_DIR)
        print(f"Wrote parity samples under {PARITY_DIR}")

    size = int8_path.stat().st_size
    problems = []
    if size > MAX_MODEL_BYTES:
        problems.append(
            f"Quantised model is {size} bytes, over the 5 MB cap ({MAX_MODEL_BYTES}). "
            "Retrain with --arch mobilenetv3_small_050 and export again."
        )
    if agreement["n"] < 50:
        problems.append(
            f"Parity used {agreement['n']} test images. The bar is 50, so the model was not published."
        )
    elif agreement["three_way"] is None or agreement["three_way"] < 0.95:
        problems.append(
            f"Three-way top-1 agreement is {agreement['three_way']}, below 0.95. The model was not published."
        )
    if problems:
        for problem in problems:
            print(problem)
        print("public/model/leaf.onnx and public/model/model.json were not written.")
        return 1

    card = {
        "version": _version_from_run(run_dir),
        "labels": list(LABELS),
        "input": {
            "size": INPUT_SIZE,
            "resize": "shorter_side_then_center_crop",
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
            "layout": "NCHW",
            "range": "0-1",
        },
        "temperature": temperature,
        "threshold": threshold,
        "sha256": sha256_file(int8_path),
        "bytes": size,
    }
    errors = validate_model_card(card)
    if errors:
        print("model.json failed its schema check and was not written: " + "; ".join(errors))
        return 1
    _publish(int8_path, card)
    print(f"Published {PUBLIC_MODEL / 'leaf.onnx'} ({size} bytes) and {PUBLIC_MODEL / 'model.json'}.")
    if not calibration.get("target_met", False):
        print(
            "Warning: the validation threshold did not reach 95 percent accuracy on accepted images. "
            "The written threshold is the fitted value, not a placeholder. See calibration.json."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
