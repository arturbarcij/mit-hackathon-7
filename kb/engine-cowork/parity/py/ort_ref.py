"""Python onnxruntime reference: logits for every <workdir>/*.tensor (torchvision tensors).
Usage: python3 py/ort_ref.py model.onnx workdir out.json"""
import json, sys, time
from pathlib import Path
import numpy as np
import onnxruntime as ort

model, work, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
so = ort.SessionOptions()
so.intra_op_num_threads = 1
s = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"])
res, times = {}, []
for p in sorted(work.glob("*.tensor")):
    x = np.fromfile(p, dtype=np.float32).reshape(1, 3, 224, 224)
    t0 = time.perf_counter()
    res[p.stem] = s.run(["logits"], {"input": x})[0][0].tolist()
    times.append((time.perf_counter() - t0) * 1000)
Path(out).write_text(json.dumps({"onnxruntime": ort.__version__, "median_ms_1thread": float(np.median(times)), "logits": res}))
print(model, len(res), "median ms", round(float(np.median(times)), 2))
