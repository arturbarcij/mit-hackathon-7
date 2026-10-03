"""Builds a tiny stand-in ONNX model for engine tests. NOT a coffee model.

Input  : "input"  float32 [1,3,224,224]  (same contract as the real model)
Output : "logits" float32 [1,6]          (healthy, rust, cercospora, phoma, miner, not_leaf)
Logits come from the per-channel mean of the normalised image, so green-dominant images read as
healthy, red-dominant as rust and blue-dominant as cercospora. Grey images give equal logits.

Run: python3 tests/fixtures/make_fixture_model.py   (needs onnx, numpy, onnxruntime)
"""
import json
import pathlib

import numpy as np
import onnx
import onnxruntime as ort
from onnx import TensorProto, helper, numpy_helper

out = pathlib.Path(__file__).parent / "model"
out.mkdir(exist_ok=True)

K = 3.0
W = np.zeros((3, 6), dtype=np.float32)
W[:, 0] = np.array([-1, 2, -1]) * K   # healthy: green
W[:, 1] = np.array([2, -1, -1]) * K   # rust: red
W[:, 2] = np.array([-1, -1, 2]) * K   # cercospora: blue
B = np.zeros((6,), dtype=np.float32)

inp = helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, 224, 224])
outp = helper.make_tensor_value_info("logits", TensorProto.FLOAT, [1, 6])
nodes = [
    helper.make_node("GlobalAveragePool", ["input"], ["pooled"]),
    helper.make_node("Flatten", ["pooled"], ["flat"], axis=1),
    helper.make_node("Gemm", ["flat", "W", "B"], ["logits"]),
]
graph = helper.make_graph(
    nodes, "fixture", [inp], [outp],
    initializer=[numpy_helper.from_array(W, "W"), numpy_helper.from_array(B, "B")],
)
model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
model.ir_version = 9
onnx.checker.check_model(model)
onnx.save(model, out / "leaf.onnx")

cfg = {
    "version": "fixture-not-a-coffee-model",
    "labels": ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"],
    "input": {"size": 224, "resize": "shorter_side_then_center_crop", "mean": [0.485, 0.456, 0.406],
               "std": [0.229, 0.224, 0.225], "layout": "NCHW", "range": "0-1"},
    "temperature": 1.0,
    "threshold": 0.6,
    "sha256": "",
    "bytes": 0,
}
(out / "model.json").write_text(json.dumps(cfg, indent=2))

# Reference logits from onnxruntime (Python) for a fixed pseudo-random tensor.
# x[c, i] = sin(0.0001 * (i + 1) * (c + 1)) + [0.5, -0.2, 0.9][c], computed in float64 then cast to float32,
# so the browser test can rebuild the exact same tensor with Math.sin.
idx = np.arange(224 * 224, dtype=np.float64) + 1
x = np.stack([np.sin(0.0001 * idx * (c + 1)) + [0.5, -0.2, 0.9][c] for c in range(3)]).astype(np.float32)
x = x.reshape(1, 3, 224, 224)
sess = ort.InferenceSession(str(out / "leaf.onnx"), providers=["CPUExecutionProvider"])
logits = sess.run(["logits"], {"input": x})[0][0].tolist()
(out / "expected.json").write_text(json.dumps({"formula": "sin(0.0001*(i+1)*(c+1)) + [0.5,-0.2,0.9][c]", "logits": logits}, indent=2))
print("wrote", out, "logits", logits)
