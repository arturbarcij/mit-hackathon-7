"""Print one-image logits and try safer quant recipes."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch

from common import ML, ROOT, SEED
from export import load_best, preprocess_numpy, pt_logits, quantize, export_onnx, parity
from train import load_manifest
import random

from onnxruntime.quantization import QuantFormat, QuantType, quantize_static, CalibrationDataReader, CalibrationMethod


def show(name, arr):
    print(f"{name}: shape={arr.shape} min={arr.min():.4f} max={arr.max():.4f} argmax={int(arr.argmax())} {np.round(arr, 3)}")


def main():
    model, cal = load_best()
    rows = load_manifest({"test"})
    p = ROOT / rows[0]["path"]
    print("image", p)
    a = pt_logits(model, p)
    show("pt", a)

    fp32 = ML / "export" / "leaf_fp32.onnx"
    int8 = ML / "export" / "leaf_int8.onnx"
    for path, tag in [(fp32, "fp32"), (int8, "int8")]:
        if not path.exists():
            continue
        m = onnx.load(str(path))
        print(tag, "ir", m.ir_version, "inputs", [(i.name, i.type.tensor_type.elem_type) for i in m.graph.input],
              "outputs", [o.name for o in m.graph.output])
        sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        print(tag, "sess in", [(i.name, i.shape, i.type) for i in sess.get_inputs()])
        inp = preprocess_numpy(p)
        out = sess.run(None, {sess.get_inputs()[0].name: inp})[0][0]
        show(tag, out)


if __name__ == "__main__":
    main()
