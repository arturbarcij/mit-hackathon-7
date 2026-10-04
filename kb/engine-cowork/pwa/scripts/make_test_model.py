"""Make a representative test model for the PWA offline proof.

Untrained timm mobilenetv3_small_100 with 6 classes, input "input" (1x3x224x224),
output "logits" (1x6), opset 17. Exported with torch, then statically quantised with
onnxruntime (QDQ, uint8 activations, int8 weights, random calibration data) so that the
file size is representative of the real leaf.onnx.

Usage: python3 scripts/make_test_model.py public/model
Writes leaf.onnx (int8), leaf_fp32.onnx (kept out of public/ by default), model.json, sizes.json.
"""
import json
import os
import sys

import numpy as np
import onnx
import timm
import torch
from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static
from onnxruntime.quantization.shape_inference import quant_pre_process

out_dir = sys.argv[1] if len(sys.argv) > 1 else "public/model"
work_dir = sys.argv[2] if len(sys.argv) > 2 else "_work/model"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(work_dir, exist_ok=True)

LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]

torch.manual_seed(0)
model = timm.create_model("mobilenetv3_small_100", pretrained=False, num_classes=len(LABELS)).eval()

fp32_path = os.path.join(work_dir, "leaf_fp32.onnx")
dummy = torch.randn(1, 3, 224, 224)
torch.onnx.export(
    model,
    dummy,
    fp32_path,
    input_names=["input"],
    output_names=["logits"],
    opset_version=17,
    dynamo=False,
    do_constant_folding=True,
)
onnx.checker.check_model(onnx.load(fp32_path))

# Recommended pre-processing before static quantisation (shape inference + optimisation).
pre_path = os.path.join(work_dir, "leaf_fp32_pre.onnx")
quant_pre_process(fp32_path, pre_path)


class RandomReader(CalibrationDataReader):
    def __init__(self, n=8):
        rng = np.random.default_rng(0)
        self.items = iter([{"input": rng.standard_normal((1, 3, 224, 224)).astype(np.float32)} for _ in range(n)])

    def get_next(self):
        return next(self.items, None)


int8_path = os.path.join(out_dir, "leaf.onnx")
quantize_static(
    pre_path,
    int8_path,
    RandomReader(),
    quant_format=QuantFormat.QDQ,
    activation_type=QuantType.QUInt8,
    weight_type=QuantType.QInt8,
    per_channel=True,
)

# Sanity run with onnxruntime (CPU) so we know the expected argmax for the fixed LCG input used in the page.
import onnxruntime as ort

n = 3 * 224 * 224
data = np.empty(n, dtype=np.float32)
s = 12345
for i in range(n):
    s = (s * 1103515245 + 12345) & 0x7FFFFFFF
    data[i] = (s / 0x7FFFFFFF) * 2 - 1
sess = ort.InferenceSession(int8_path, providers=["CPUExecutionProvider"])
logits = sess.run(["logits"], {"input": data.reshape(1, 3, 224, 224)})[0]
argmax = int(np.argmax(logits))

meta = {
    "version": "test-mnv3s-int8-0.0.1",
    "arch": "mobilenetv3_small_100",
    "trained": False,
    "labels": LABELS,
    "input": {"name": "input", "shape": [1, 3, 224, 224], "layout": "NCHW", "resize_shorter": 256, "center_crop": 224,
              "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
    "output": {"name": "logits", "shape": [1, len(LABELS)]},
    "temperature": 1.0,
    "threshold": 0.6,
    "opset": 17,
    "quantisation": "static QDQ, QUInt8 activations, QInt8 weights, per channel, random calibration",
    "expected_argmax_for_lcg_input": argmax,
}
with open(os.path.join(out_dir, "model.json"), "w") as f:
    json.dump(meta, f, indent=2)

sizes = {
    "fp32_bytes": os.path.getsize(fp32_path),
    "int8_bytes": os.path.getsize(int8_path),
    "params": sum(p.numel() for p in model.parameters()),
    "expected_argmax_for_lcg_input": argmax,
    "logits": [float(x) for x in logits.ravel()],
}
with open(os.path.join(work_dir, "sizes.json"), "w") as f:
    json.dump(sizes, f, indent=2)
print(json.dumps(sizes, indent=2))
