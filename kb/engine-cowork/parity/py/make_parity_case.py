"""Builds a check_parity.mjs test case in the exact layout and expected.json format of
app/ml/export.py write_parity_samples, from a given ONNX model.
Difference from export.py (deliberate, see PARITY.md Request ml-1): probs are computed
from the SAVED q90 jpg with the SHIPPED onnx (Python onnxruntime), not PyTorch on the source.
Usage: python3 py/make_parity_case.py model.onnx temperature out_dir img1.jpg [img2.jpg ...]"""
import hashlib, json, shutil, sys
from pathlib import Path
import numpy as np
import onnxruntime as ort
from PIL import Image
from torchvision import transforms

LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
tfm = transforms.Compose([transforms.Resize(224), transforms.CenterCrop(224), transforms.ToTensor(), transforms.Normalize(MEAN, STD)])

model, T, out = Path(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3])
imgs = [Path(p) for p in sys.argv[4:]]
mdir, sdir = out / "public" / "model", out / "ml" / "parity_samples"
mdir.mkdir(parents=True, exist_ok=True); sdir.mkdir(parents=True, exist_ok=True)
shutil.copy2(model, mdir / "leaf.onnx")
data = (mdir / "leaf.onnx").read_bytes()
pre = {"size": 224, "resize": "shorter_side_then_center_crop", "mean": list(MEAN), "std": list(STD), "layout": "NCHW", "range": "0-1"}
(mdir / "model.json").write_text(json.dumps({"version": "fixture", "labels": LABELS, "input": pre, "temperature": T, "threshold": 0.5,
    "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "quantization": "int8", "arch": "mobilenetv3_small_100"}, indent=2))
so = ort.SessionOptions(); so.intra_op_num_threads = 1
s = ort.InferenceSession(str(mdir / "leaf.onnx"), so, providers=["CPUExecutionProvider"])
samples = []
for i, p in enumerate(imgs):
    dest = sdir / f"{i:02d}.jpg"
    with Image.open(p) as im:
        im.convert("RGB").save(dest, quality=90)
    with Image.open(dest) as im:  # reopen the saved file: expected must describe the bytes we ship
        x = tfm(im.convert("RGB")).unsqueeze(0).numpy().astype(np.float32)
    logits = s.run(["logits"], {"input": x})[0][0] / T
    e = np.exp(logits - logits.max()); probs = e / e.sum()
    samples.append({"file": dest.name, "source_path": f"kb/engine-cowork/parity/images/{p.name}",
                    "probs": {LABELS[j]: float(probs[j]) for j in range(6)}, "label": LABELS[int(probs.argmax())], "confidence": float(probs.max())})
(sdir / "expected.json").write_text(json.dumps({"preprocess": pre, "temperature": T, "samples": samples}, indent=2))
print("wrote", out, len(samples), "samples")
