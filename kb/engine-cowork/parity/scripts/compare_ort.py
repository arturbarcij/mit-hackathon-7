"""Reference logits: PyTorch, onnxruntime fp32 and int8 on the fixture tensors.

Usage: python compare_ort.py <fixtures_dir> <model_dir> <out_json>
Writes per fixture logits for pytorch, ort_fp32, ort_int8 (using the PNG expected tensor),
plus Python side CPU latency.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import timm
import torch

LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]


def main():
    fix = Path(sys.argv[1])
    mdir = Path(sys.argv[2])
    out = Path(sys.argv[3])
    meta = json.loads((fix / "fixtures.json").read_text())
    model = timm.create_model("mobilenetv3_small_100", pretrained=False, num_classes=len(LABELS))
    model.load_state_dict(torch.load(mdir / "test_model.pt", map_location="cpu"))
    model.eval()
    so = ort.SessionOptions()
    so.intra_op_num_threads = 1
    so.inter_op_num_threads = 1
    s32 = ort.InferenceSession(str(mdir / "test_fp32.onnx"), so, providers=["CPUExecutionProvider"])
    s8 = ort.InferenceSession(str(mdir / "test_int8.onnx"), so, providers=["CPUExecutionProvider"])
    rows = []
    lat32, lat8 = [], []
    for f in meta["fixtures"]:
        x = np.fromfile(fix / (f["png"] + ".bin"), dtype=np.float32).reshape(1, 3, 224, 224)
        with torch.no_grad():
            pt = model(torch.from_numpy(x)).numpy()[0]
        t = time.perf_counter(); o32 = s32.run(["logits"], {"input": x})[0][0]; lat32.append((time.perf_counter() - t) * 1e3)
        t = time.perf_counter(); o8 = s8.run(["logits"], {"input": x})[0][0]; lat8.append((time.perf_counter() - t) * 1e3)
        rows.append({
            "name": f["name"], "tensor": f["png"] + ".bin",
            "pytorch": pt.tolist(), "ort_fp32": o32.tolist(), "ort_int8": o8.tolist(),
            "pt_vs_ort_fp32_max_abs": float(np.abs(pt - o32).max()),
            "pt_vs_ort_int8_max_abs": float(np.abs(pt - o8).max()),
            "top1": {"pytorch": int(pt.argmax()), "ort_fp32": int(o32.argmax()), "ort_int8": int(o8.argmax())},
        })
    n = len(rows)
    summary = {
        "onnxruntime": ort.__version__, "torch": torch.__version__, "timm": timm.__version__,
        "n": n,
        "pt_vs_ort_fp32_max_abs": max(r["pt_vs_ort_fp32_max_abs"] for r in rows),
        "pt_vs_ort_int8_max_abs": max(r["pt_vs_ort_int8_max_abs"] for r in rows),
        "top1_pt_vs_ort_fp32": sum(r["top1"]["pytorch"] == r["top1"]["ort_fp32"] for r in rows) / n,
        "top1_pt_vs_ort_int8": sum(r["top1"]["pytorch"] == r["top1"]["ort_int8"] for r in rows) / n,
        "python_ort_fp32_ms_median_1thread": float(np.median(lat32[1:])),
        "python_ort_int8_ms_median_1thread": float(np.median(lat8[1:])),
        "per_image": rows,
    }
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "per_image"}, indent=2))


if __name__ == "__main__":
    main()
