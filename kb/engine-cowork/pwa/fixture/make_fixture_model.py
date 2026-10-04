"""Build a tiny seeded ONNX fixture for the offline PWA proof.

NOT the leaf model. Conv(3->8, 3x3, stride 2) -> Relu -> GlobalAveragePool -> Flatten -> Gemm(8->6).
Input `input` [1,3,224,224] float32, output `logits` [1,6].
Usage: python make_fixture_model.py <mirror>/public/model  (mirror only; ml owns the real public/model)
"""
import hashlib, json, sys
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

out = Path(sys.argv[1] if len(sys.argv) > 1 else "public/model")
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261004)
W = rng.standard_normal((8, 3, 3, 3)).astype(np.float32) * 0.1
B = np.zeros(8, np.float32)
G = rng.standard_normal((6, 8)).astype(np.float32) * 0.1
GB = np.zeros(6, np.float32)
nodes = [
    helper.make_node("Conv", ["input", "W", "B"], ["c"], kernel_shape=[3, 3], strides=[2, 2], pads=[1, 1, 1, 1]),
    helper.make_node("Relu", ["c"], ["r"]),
    helper.make_node("GlobalAveragePool", ["r"], ["g"]),
    helper.make_node("Flatten", ["g"], ["f"], axis=1),
    helper.make_node("Gemm", ["f", "G", "GB"], ["logits"], transB=1),
]
graph = helper.make_graph(
    nodes, "jani_fixture",
    [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, 224, 224])],
    [helper.make_tensor_value_info("logits", TensorProto.FLOAT, [1, 6])],
    [numpy_helper.from_array(W, "W"), numpy_helper.from_array(B, "B"),
     numpy_helper.from_array(G, "G"), numpy_helper.from_array(GB, "GB")],
)
model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)], producer_name="jani-fixture")
model.ir_version = 8
onnx.checker.check_model(model)
p = out / "fixture.onnx"
onnx.save(model, p)
data = p.read_bytes()
meta = {
    "version": "fixture-not-a-real-model",
    "note": "Tiny random fixture for the offline PWA proof. Not the leaf model. Never show its output to a farmer.",
    "file": "fixture.onnx",
    "labels": ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"],
    "input": {"name": "input", "shape": [1, 3, 224, 224], "dtype": "float32"},
    "output": {"name": "logits", "shape": [1, 6]},
    "temperature": 1.0,
    "threshold": 0.5,
    "sha256": hashlib.sha256(data).hexdigest(),
    "bytes": len(data),
}
(out / "model.json").write_text(json.dumps(meta, indent=2) + "\n")
print(p, len(data), meta["sha256"])
