"""Export leaf.onnx (fp32 then static int8 QDQ), parity test, model.json, parity samples."""
from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from tqdm import tqdm

from common import (
    IMAGENET_MEAN,
    IMAGENET_STD,
    INPUT_SIZE,
    LABEL_TO_IDX,
    LABELS,
    ML,
    PUBLIC_MODEL,
    ROOT,
    SEED,
)
from train import eval_transform, load_manifest

import timm


def preprocess_numpy(path: Path) -> np.ndarray:
    tfm = eval_transform()
    with Image.open(path) as im:
        x = tfm(im.convert("RGB"))
    return x.unsqueeze(0).numpy().astype(np.float32)


def resolve(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def load_best(cal_path=None):
    cal_file = resolve(cal_path) if cal_path else ML / "calibration.json"
    if cal_file.is_dir():
        cal_file = cal_file / "calibration.json"
    cal = json.loads(cal_file.read_text(encoding="utf-8"))
    ckpt_path = resolve(cal["best_checkpoint"])
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    arch = cal.get("arch") or ckpt.get("args", {}).get("arch") or "mobilenetv3_small_100"
    model = timm.create_model(arch, pretrained=False, num_classes=len(LABELS))
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, cal


def export_onnx(model, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros(1, 3, INPUT_SIZE, INPUT_SIZE)
    torch.onnx.export(
        model,
        dummy,
        str(dest),
        input_names=["input"],
        output_names=["logits"],
        opset_version=17,
        dynamo=False,
    )
    print(f"wrote {dest} {dest.stat().st_size} bytes", flush=True)


def quantize(fp32: Path, int8: Path, cal_paths: list[Path]):
    from onnxruntime.quantization import (
        CalibrationDataReader,
        CalibrationMethod,
        QuantFormat,
        QuantType,
        quantize_dynamic,
        quantize_static,
    )
    try:
        from onnxruntime.quantization.preprocess import quant_pre_process
    except ImportError:
        from onnxruntime.quantization.shape_inference import quant_pre_process

    class Reader(CalibrationDataReader):
        def __init__(self, paths):
            self.paths = list(paths)
            self.i = 0

        def get_next(self):
            if self.i >= len(self.paths):
                return None
            arr = preprocess_numpy(self.paths[self.i])
            self.i += 1
            return {"input": arr}

        def rewind(self):
            self.i = 0

    prepared = fp32.with_name(fp32.stem + "_prep.onnx")
    try:
        quant_pre_process(str(fp32), str(prepared))
        src = prepared
        print(f"quant pre-process -> {prepared}", flush=True)
    except Exception as e:
        print(f"quant pre-process skipped: {e}", flush=True)
        src = fp32

    reader = Reader([p for p in cal_paths if p.exists()][:200])
    try:
        quantize_static(
            model_input=str(src),
            model_output=str(int8),
            calibration_data_reader=reader,
            quant_format=QuantFormat.QDQ,
            per_channel=True,
            reduce_range=False,
            calibrate_method=CalibrationMethod.MinMax,
            activation_type=QuantType.QUInt8,
            weight_type=QuantType.QInt8,
            extra_options={"ActivationSymmetric": False, "WeightSymmetric": True},
        )
    except Exception as e:
        print(f"static quant failed ({e}); trying dynamic weight-only", flush=True)
        quantize_dynamic(str(src), str(int8), weight_type=QuantType.QInt8, per_channel=True)
    print(f"wrote {int8} {int8.stat().st_size} bytes", flush=True)


def ort_logits(session, path: Path) -> np.ndarray:
    return session.run(["logits"], {"input": preprocess_numpy(path)})[0][0]


@torch.no_grad()
def pt_logits(model, path: Path) -> np.ndarray:
    x = torch.from_numpy(preprocess_numpy(path))
    return model(x).numpy()[0]


def parity(model, onnx_fp32, onnx_int8, paths: list[Path]) -> dict:
    import onnxruntime as ort
    s32 = ort.InferenceSession(str(onnx_fp32), providers=["CPUExecutionProvider"])
    s8 = ort.InferenceSession(str(onnx_int8), providers=["CPUExecutionProvider"])
    agree_32 = agree_8 = agree_both = 0
    for p in tqdm(paths, desc="parity"):
        a = pt_logits(model, p).argmax()
        b = ort_logits(s32, p).argmax()
        c = ort_logits(s8, p).argmax()
        agree_32 += int(a == b)
        agree_8 += int(a == c)
        agree_both += int(a == b == c)
    n = len(paths)
    return {
        "n": n,
        "pt_vs_onnx_fp32": agree_32 / n,
        "pt_vs_onnx_int8": agree_8 / n,
        "all_three": agree_both / n,
    }


def write_parity_samples(model, cal, paths: list[Path], out: Path):
    out.mkdir(parents=True, exist_ok=True)
    T = cal["temperature"]
    expected = []
    for i, p in enumerate(paths[:10]):
        dest = out / f"{i:02d}_{p.suffix.lower() and p.name}"
        # keep a short safe name
        dest = out / f"{i:02d}.jpg"
        with Image.open(p) as im:
            im.convert("RGB").save(dest, quality=90)
        logits = pt_logits(model, p) / T
        e = np.exp(logits - logits.max())
        probs = e / e.sum()
        expected.append({
            "file": dest.name,
            "source_path": str(p.relative_to(ROOT).as_posix()) if p.is_relative_to(ROOT) else str(p),
            "probs": {LABELS[j]: float(probs[j]) for j in range(len(LABELS))},
            "label": LABELS[int(probs.argmax())],
            "confidence": float(probs.max()),
        })
    (out / "expected.json").write_text(
        json.dumps({
            "preprocess": {
                "size": INPUT_SIZE,
                "resize": "shorter_side_then_center_crop",
                "mean": list(IMAGENET_MEAN),
                "std": list(IMAGENET_STD),
                "layout": "NCHW",
                "range": "0-1",
            },
            "temperature": T,
            "samples": expected,
        }, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="Run dir or calibration.json for this candidate")
    ap.add_argument("--out", default=None, help="Write onnx/model.json here; skip public/model if set")
    ap.add_argument("--manifest", default=None)
    args = ap.parse_args()

    model, cal = load_best(args.run)
    rng = random.Random(SEED)
    train_rows = load_manifest({"train"}, args.manifest)
    test_rows = load_manifest({"test"}, args.manifest)
    cal_paths = [ROOT / r["path"] for r in train_rows]
    rng.shuffle(cal_paths)
    test_paths = [ROOT / r["path"] for r in test_rows]
    rng.shuffle(test_paths)
    test_paths = [p for p in test_paths if p.exists()][:50]
    if len(test_paths) < 10:
        raise SystemExit("not enough test images for parity")

    out_dir = resolve(args.out) if args.out else ML / "export"
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir
    fp32 = tmp / "leaf_fp32.onnx"
    int8 = tmp / "leaf_int8.onnx"
    export_onnx(model, fp32)
    quantize(fp32, int8, [p for p in cal_paths if p.exists()][:200])

    size = int8.stat().st_size
    print(f"int8 bytes={size} cap=5242880", flush=True)
    if size > 5 * 1024 * 1024:
        print("WARN int8 over 5 MB; try mobilenetv3_small_050 next", flush=True)

    par = parity(model, fp32, int8, test_paths)
    print("parity", par, flush=True)
    if par["pt_vs_onnx_int8"] < 0.95:
        print("full static quant broken on MobileNetV3 h-swish; Conv-only dynamic", flush=True)
        from onnxruntime.quantization import QuantType, quantize_dynamic
        quantize_dynamic(
            str(fp32), str(int8),
            weight_type=QuantType.QInt8,
            per_channel=False,
            extra_options={"MatMulConstBOnly": True},
            op_types_to_quantize=["Conv"],
        )
        print(f"conv-only int8 bytes={int8.stat().st_size}", flush=True)
        par = parity(model, fp32, int8, test_paths)
        print("parity conv-only", par, flush=True)
    if par["pt_vs_onnx_int8"] < 0.95:
        print("int8 still bad; shipping float16 under 5 MB instead", flush=True)
        import onnx
        from onnxruntime.transformers.float16 import convert_float_to_float16
        m16 = convert_float_to_float16(onnx.load(str(fp32)), keep_io_types=True)
        onnx.save(m16, int8)
        print(f"fp16 bytes={int8.stat().st_size}", flush=True)
        par = parity(model, fp32, int8, test_paths)
        print("parity fp16", par, flush=True)
        par["format"] = "fp16"
    else:
        par["format"] = "int8"
    (tmp / "parity.json").write_text(json.dumps(par, indent=2), encoding="utf-8")
    if not args.out:
        (ML / "parity.json").write_text(json.dumps(par, indent=2), encoding="utf-8")
    if par["pt_vs_onnx_int8"] < 0.95:
        print("FAIL parity below 95 percent; not shipping to public/", flush=True)
        if args.out:
            # Sweep still keeps the artefact and the parity numbers.
            print(f"candidate artefacts in {tmp}", flush=True)
            return 0
        return 1

    dest_dir = out_dir if args.out else PUBLIC_MODEL
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "leaf.onnx"
    shutil.copy2(int8, dest)
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    model_json = {
        "version": "v1-2026-10-04",
        "labels": LABELS,
        "input": {
            "size": INPUT_SIZE,
            "resize": "shorter_side_then_center_crop",
            "mean": list(IMAGENET_MEAN),
            "std": list(IMAGENET_STD),
            "layout": "NCHW",
            "range": "0-1",
        },
        "temperature": cal["temperature"],
        "threshold": cal["threshold"],
        "sha256": sha,
        "bytes": dest.stat().st_size,
        "quantization": par.get("format", "int8"),
        "arch": cal.get("arch", "mobilenetv3_small_100"),
    }
    (dest_dir / "model.json").write_text(json.dumps(model_json, indent=2), encoding="utf-8")
    samples_dir = (out_dir / "parity_samples") if args.out else ML / "parity_samples"
    write_parity_samples(model, cal, test_paths, samples_dir)
    print(f"shipped {dest} sha256={sha} bytes={dest.stat().st_size}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
