"""Export the trained classifier to int8 ONNX for the browser engine, with parity checks and parity samples.

Steps:
1. PyTorch checkpoint -> ONNX fp32 (opset 17, static [1,3,224,224], input `input`, output `logits`).
2. Static int8 QDQ quantisation (onnxruntime quantize_static) on about 200 train images. With --quant auto,
   if its top-1 agreement with PyTorch is below 95%, fall back to int8 weight-only QDQ (float activations).
3. Parity on 50 test images: PyTorch fp32 vs ONNX fp32 vs ONNX int8 top-1 agreement. Fails below 95% or over 5 MB.
4. Writes <out-dir>/leaf.onnx and <out-dir>/model.json (temperature and threshold from calibration.json,
   sha256 and bytes of leaf.onnx), and <parity-dir>/ with 10 test JPEGs plus expected.json computed from the
   int8 model with the engine's preprocessing.

Preprocessing here is a copy of the engine (app/src/engine/preprocess.ts, source.ts): decode with EXIF
orientation applied, limit the longer side to 1600 px, take the centre square of the shorter side and resize it
to 224 in one step, RGB 0-1, ImageNet mean and std, NCHW. calibrate.py and evaluate.py import it from here.

Real run:   python app/ml/export.py --ckpt app/ml/runs/<run>/best.pt
Smoke run:  python app/ml/export.py --ckpt app/ml/runs/smoke/best.pt --calibration /tmp/mlx/calibration.json \
              --out-dir /tmp/mlx/model --parity-dir /tmp/mlx/parity_samples --report /tmp/mlx/export_report.json --force
"""
import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import CLASSES, MEAN, ML, ROOT, SIZE, STD  # noqa: E402

MAX_DECODE_SIDE = 1600
# Engine quality gate (app/src/engine/quality.ts).
BLUR_MAX, BRIGHTNESS_MIN, MIN_SIDE, ANALYSIS_SIDE, REBLUR_WINDOW = 0.6, 45, 224, 256, 9


def set_threads(n: int):
    import torch
    torch.set_num_threads(n)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass


def ort_session(path, threads: int = 1):
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.inter_op_num_threads = 1
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(str(path), so, providers=["CPUExecutionProvider"])


def open_rgb(path) -> Image.Image:
    """Decode like createImageBitmap: EXIF orientation applied, longer side limited to 1600 px."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_DECODE_SIDE:
        s = MAX_DECODE_SIDE / max(w, h)
        img = img.resize((round(w * s), round(h * s)), Image.BICUBIC)
    return img


def engine_crop(img: Image.Image, size: int = SIZE, resize_to: int | None = None) -> Image.Image:
    """preprocess.ts cropRegion + drawRegion: centre square of the shorter side, resized to size x size."""
    w, h = img.size
    shorter = min(w, h)
    side = shorter * size / resize_to if resize_to and resize_to > size else shorter
    sx, sy = (w - side) / 2, (h - side) / 2
    # Chrome's canvas downscale behaves like a box filter; PIL BILINEAR moved an ambiguous parity sample by 0.05.
    flt = Image.BOX if side > size else Image.BILINEAR
    return img.resize((size, size), flt, box=(sx, sy, sx + side, sy + side))


def to_tensor(crop: Image.Image, mean=MEAN, std=STD) -> np.ndarray:
    """preprocess.ts rgbaToTensor: RGB 0-1, (x - mean) / std, CHW float32."""
    x = np.asarray(crop, dtype=np.float32) / 255.0
    x = (x - np.array(mean, np.float32)) / np.array(std, np.float32)
    return np.ascontiguousarray(x.transpose(2, 0, 1))


def engine_tensor(path) -> np.ndarray:
    return to_tensor(engine_crop(open_rgb(path)))


def _moving_average(a: np.ndarray, window: int, axis: int) -> np.ndarray:
    half = (window - 1) // 2
    pad = [(0, 0), (0, 0)]
    pad[axis] = (half, half)
    p = np.pad(a, pad, mode="reflect")
    c = np.cumsum(p, axis=axis, dtype=np.float64)
    c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
    n = a.shape[axis]
    return (np.take(c, range(window, window + n), axis=axis) - np.take(c, range(0, n), axis=axis)) / window


def engine_quality(img: Image.Image) -> dict:
    """Python port of quality.ts checkQuality (canvas downscale replaced by PIL bilinear, so values are close, not exact)."""
    w0, h0 = img.size
    s = min(1.0, ANALYSIS_SIDE / max(w0, h0))
    w, h = max(1, round(w0 * s)), max(1, round(h0 * s))
    small = np.asarray(img.resize((w, h), Image.BILINEAR), dtype=np.float64)
    grey = 0.299 * small[..., 0] + 0.587 * small[..., 1] + 0.114 * small[..., 2]
    brightness = float(grey.mean())
    bx = _moving_average(grey, REBLUR_WINDOW, 1)
    by = _moving_average(grey, REBLUR_WINDOW, 0)
    dh, dv = np.abs(np.diff(grey, axis=1)), np.abs(np.diff(grey, axis=0))
    lost_h = np.maximum(0, dh - np.abs(np.diff(bx, axis=1))).sum()
    lost_v = np.maximum(0, dv - np.abs(np.diff(by, axis=0))).sum()
    oh, ov = dh.sum(), dv.sum()
    blur = 1.0 if oh == 0 or ov == 0 else float(max((oh - lost_h) / oh, (ov - lost_v) / ov))
    reason = None
    if min(w0, h0) < MIN_SIDE:
        reason = "too_small"
    elif brightness < BRIGHTNESS_MIN:
        reason = "dark"
    elif blur > BLUR_MAX:
        reason = "blurry"
    return {"ok": reason is None, "reason": reason, "blur": blur, "brightness": brightness}


def softmax_t(logits: np.ndarray, t: float) -> np.ndarray:
    """scoring.ts calibratedSoftmax."""
    t = t if t > 0 and np.isfinite(t) else 1.0
    z = np.asarray(logits, np.float64) / t
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def load_split(manifest: Path, split: str, cap: int = 0, seed: int = 42, labels=None, sources=None) -> list[dict]:
    """Rows of one split, shuffled with the seed; cap = max rows per label (0 = all)."""
    rows = [r for r in csv.DictReader(open(manifest)) if r["split"] == split]
    if labels is not None:
        rows = [r for r in rows if r["label"] in labels]
    if sources is not None:
        rows = [r for r in rows if r["source"] in sources]
    rng = random.Random(seed)
    rng.shuffle(rows)
    if cap:
        n, kept = Counter(), []
        for r in rows:
            if n[r["label"]] < cap:
                kept.append(r)
                n[r["label"]] += 1
        rows = kept
    return rows


def load_model(ckpt_path):
    import timm
    import torch
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    if ckpt.get("classes", CLASSES) != CLASSES:
        raise SystemExit(f"checkpoint classes {ckpt.get('classes')} differ from {CLASSES}")
    model = timm.create_model(ckpt["arch"], pretrained=False, num_classes=len(CLASSES))
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, ckpt


class EngineImages:
    """Map-style dataset of engine-preprocessed tensors, usable with a torch DataLoader."""

    def __init__(self, rows, data_root: Path):
        self.rows, self.root = rows, Path(data_root)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        y = CLASSES.index(r["label"]) if r["label"] in CLASSES else -1
        return engine_tensor(self.root / r["path"]), y


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def balanced(rows: list[dict], n: int) -> list[dict]:
    """Round-robin over labels so n rows cover every label as evenly as the data allows."""
    by = defaultdict(list)
    for r in rows:
        by[r["label"]].append(r)
    out, i = [], 0
    while len(out) < n and any(i < len(v) for v in by.values()):
        for lab in CLASSES:
            if i < len(by[lab]) and len(out) < n:
                out.append(by[lab][i])
        i += 1
    return out


def export_fp32(model, path: Path, opset: int):
    import torch
    dummy = torch.zeros(1, 3, SIZE, SIZE)
    with torch.no_grad():
        torch.onnx.export(model, (dummy,), str(path), input_names=["input"], output_names=["logits"],
                          opset_version=opset, do_constant_folding=True, dynamo=False)
    import onnx
    m = onnx.load(str(path))
    onnx.checker.check_model(m)
    return m


def quantise(fp32: Path, out: Path, calib_rows, data_root: Path, work: Path):
    from onnxruntime.quantization import CalibrationDataReader, CalibrationMethod, QuantFormat, QuantType, quantize_static
    from onnxruntime.quantization.shape_inference import quant_pre_process

    prep = work / "leaf.prep.onnx"
    try:
        quant_pre_process(str(fp32), str(prep), skip_symbolic_shape=True)
    except Exception as e:  # pre-processing is an optimisation; quantising the raw graph still works
        print(f"quant_pre_process failed ({e}); quantising the fp32 graph directly")
        shutil.copy(fp32, prep)

    class Reader(CalibrationDataReader):
        def __init__(self):
            self.it = iter(calib_rows)

        def get_next(self):
            r = next(self.it, None)
            return None if r is None else {"input": engine_tensor(data_root / r["path"])[None]}

    quantize_static(str(prep), str(out), Reader(), quant_format=QuantFormat.QDQ, per_channel=True,
                    activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8,
                    calibrate_method=CalibrationMethod.MinMax)


def quantise_weights_only(fp32: Path, out: Path):
    """int8 weights (symmetric, per output channel) feeding DequantizeLinear; activations stay float.
    Used when static activation quantisation loses too much: MobileNetV3's early depthwise and
    squeeze-excite activations have outlier channels that per-tensor uint8 ranges cannot hold."""
    import onnx
    from onnx import helper, numpy_helper

    m = onnx.load(str(fp32))
    g = m.graph
    inits = {i.name: i for i in g.initializer}
    dq_nodes = []
    for n in g.node:
        if n.op_type not in ("Conv", "Gemm") or len(n.input) < 2 or n.input[1] not in inits:
            continue
        axis = 0
        if n.op_type == "Gemm" and not next((a.i for a in n.attribute if a.name == "transB"), 0):
            axis = 1
        name = n.input[1]
        w = numpy_helper.to_array(inits[name]).astype(np.float32)
        scale = np.maximum(np.abs(w).max(axis=tuple(i for i in range(w.ndim) if i != axis)), 1e-12) / 127.0
        shape = [1] * w.ndim
        shape[axis] = -1
        q = np.clip(np.round(w / scale.reshape(shape)), -127, 127).astype(np.int8)
        g.initializer.remove(inits[name])
        g.initializer.extend([numpy_helper.from_array(q, f"{name}_q"),
                              numpy_helper.from_array(scale.astype(np.float32), f"{name}_scale"),
                              numpy_helper.from_array(np.zeros(scale.shape, np.int8), f"{name}_zp")])
        dq_nodes.append(helper.make_node("DequantizeLinear", [f"{name}_q", f"{name}_scale", f"{name}_zp"], [name],
                                         name=f"{name}_DequantizeLinear", axis=axis))
    nodes = dq_nodes + list(g.node)
    del g.node[:]
    g.node.extend(nodes)
    onnx.checker.check_model(m)
    onnx.save(m, str(out))


def reference_logits(model, sess_fp32, rows, data_root: Path):
    """PyTorch and ONNX fp32 logits on engine-preprocessed tensors, plus PyTorch on train.eval_tf tensors."""
    import torch
    from train import eval_tf

    tv = eval_tf()
    xs, pt, f32, pt_tv, ys = [], [], [], [], []
    with torch.no_grad():
        for r in rows:
            img = open_rgb(data_root / r["path"])
            x = to_tensor(engine_crop(img))[None]
            xs.append(x)
            pt.append(model(torch.from_numpy(x)).numpy()[0])
            pt_tv.append(model(tv(img)[None]).numpy()[0])
            f32.append(sess_fp32.run(["logits"], {"input": x})[0][0])
            ys.append(CLASSES.index(r["label"]))
    return xs, np.array(pt), np.array(f32), np.array(pt_tv), np.array(ys)


def parity(ref, sess_int8, temperature: float) -> dict:
    xs, pt, f32, pt_tv, ys = ref
    i8 = np.array([sess_int8.run(["logits"], {"input": x})[0][0] for x in xs])
    agree = lambda a, b: float((a.argmax(1) == b.argmax(1)).mean())
    pdiff = lambda a, b: float(np.abs(softmax_t(a, temperature) - softmax_t(b, temperature)).max())
    return {
        "test_set": "in-domain test split, class-balanced sample",
        "n": int(len(ys)),
        "label_counts": dict(Counter(CLASSES[y] for y in ys)),
        "top1_agreement": {"pytorch_vs_onnx_fp32": agree(pt, f32), "pytorch_vs_onnx_int8": agree(pt, i8),
                           "onnx_fp32_vs_onnx_int8": agree(f32, i8),
                           "pytorch_engine_preproc_vs_pytorch_train_eval_tf": agree(pt, pt_tv)},
        "max_abs_prob_diff_after_temperature": {"pytorch_vs_onnx_fp32": pdiff(pt, f32), "pytorch_vs_onnx_int8": pdiff(pt, i8)},
        "relative_logit_error_int8": float(np.abs(i8 - f32).mean() / max(np.abs(f32).mean(), 1e-12)),
        "accuracy_on_sample": {"pytorch": float((pt.argmax(1) == ys).mean()), "onnx_int8": float((i8.argmax(1) == ys).mean())},
    }


PARITY_PLAN = ["healthy", "rust", "rust", "cercospora", "cercospora", "phoma", "phoma", "miner", "miner", "not_leaf"]
# Indices in PARITY_PLAN saved at a larger size so the engine's resize path is exercised as well.
PARITY_LARGE = {2, 8, 9}


def resave(src: Path, dst: Path, shorter: int):
    """Re-encode without EXIF or ICC so browser and PIL decode the same pixels.
    Shorter side 224 with an even margin makes the engine crop a pure pixel copy (no resampling)."""
    img = open_rgb(src)
    w, h = img.size
    s = shorter / min(w, h)
    nw, nh = max(shorter, round(w * s)), max(shorter, round(h * s))
    if shorter == SIZE:
        nw += (nw - SIZE) % 2
        nh += (nh - SIZE) % 2
    img.resize((nw, nh), Image.BICUBIC).save(dst, "JPEG", quality=92, optimize=True)


def make_parity_samples(rows, data_root: Path, parity_dir: Path, sess, temperature, threshold, seed) -> dict:
    """10 test images that pass the engine quality gate with margin; expected probs from the int8 model."""
    if parity_dir.exists():
        shutil.rmtree(parity_dir)
    parity_dir.mkdir(parents=True)
    by = defaultdict(list)
    for r in rows:
        by[r["label"]].append(r)
    rng = random.Random(seed)
    for v in by.values():
        rng.shuffle(v)
    used, expected, meta = set(), {}, {}
    for i, lab in enumerate(PARITY_PLAN):
        for r in by.get(lab, []):
            if r["path"] in used:
                continue
            src = data_root / r["path"]
            try:
                img = open_rgb(src)
            except Exception:
                continue
            if min(img.size) < 256:
                continue
            name = f"{i:02d}_{lab}.jpg"
            dst = parity_dir / name
            resave(src, dst, 448 if i in PARITY_LARGE else SIZE)
            saved = open_rgb(dst)
            q = engine_quality(saved)
            if not (q["ok"] and q["blur"] <= BLUR_MAX - 0.1 and q["brightness"] >= BRIGHTNESS_MIN + 15):
                dst.unlink()
                continue
            used.add(r["path"])
            logits = sess.run(["logits"], {"input": to_tensor(engine_crop(saved))[None]})[0][0]
            p = softmax_t(logits, temperature)
            top = int(p.argmax())
            abstained = not (p[top] >= threshold)
            expected[name] = {"label": "unsure" if abstained else CLASSES[top], "top": CLASSES[top],
                              "confidence": float(p[top]), "abstained": abstained,
                              "probs": {c: float(p[k]) for k, c in enumerate(CLASSES)}, "true_label": lab}
            meta[name] = {"source_path": r["path"], "source": r["source"], "true_label": lab,
                          "size": list(saved.size), "file_bytes": dst.stat().st_size,
                          "engine_quality_python_port": {k: q[k] for k in ("blur", "brightness")},
                          "resize_path": "pixel copy" if i not in PARITY_LARGE else "engine resizes 448 -> 224"}
            break
        else:
            print(f"WARNING: no test image for parity class {lab} passed the quality gate")
    (parity_dir / "expected.json").write_text(json.dumps(expected, indent=2))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--calibration", default=str(ML / "calibration.json"))
    ap.add_argument("--manifest", default=str(ML / "manifest.csv"))
    ap.add_argument("--data-root", default=str(ROOT / "data_raw"))
    ap.add_argument("--out-dir", default=str(ROOT / "app" / "public" / "model"))
    ap.add_argument("--parity-dir", default=str(ML / "parity_samples"))
    ap.add_argument("--report", default=str(ML / "export_report.json"))
    ap.add_argument("--version", default=f"v1-{datetime.now().strftime('%Y-%m-%d')}")
    ap.add_argument("--opset", type=int, default=17)
    ap.add_argument("--n-calib", type=int, default=200)
    ap.add_argument("--n-parity", type=int, default=50)
    ap.add_argument("--max-mb", type=float, default=5.0)
    ap.add_argument("--min-agreement", type=float, default=0.95)
    ap.add_argument("--quant", choices=["auto", "static", "weight_only"], default="auto",
                    help="auto: static QDQ, falling back to weight-only int8 if top-1 agreement is below --min-agreement")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--force", action="store_true", help="write outputs even if a check fails (smoke tests only)")
    a = ap.parse_args()

    set_threads(a.threads)
    data_root, manifest = Path(a.data_root), Path(a.manifest)
    cal = json.loads(Path(a.calibration).read_text())
    temperature, threshold = float(cal["temperature"]), float(cal["threshold"])

    model, ckpt = load_model(a.ckpt)
    work = Path(tempfile.mkdtemp(prefix="jani-export-"))
    fp32, int8 = work / "leaf.fp32.onnx", work / "leaf.int8.onnx"
    print(f"exporting {ckpt['arch']} (epoch {ckpt.get('epoch')}) to {fp32}")
    export_fp32(model, fp32, a.opset)

    s32 = ort_session(fp32, a.threads)
    test_rows = load_split(manifest, "test", 0, a.seed, labels=CLASSES)
    ref = reference_logits(model, s32, balanced(test_rows, a.n_parity), data_root)
    calib_rows = balanced(load_split(manifest, "train", 0, a.seed, labels=CLASSES), a.n_calib)
    methods = {
        "static": "static int8 QDQ (quantize_static), per-channel int8 weights, uint8 activations, MinMax, "
                  f"{len(calib_rows)} train calibration images",
        "weight_only": "int8 weight-only QDQ: per-channel symmetric int8 Conv/Gemm weights with DequantizeLinear, float activations",
    }
    candidates = {}
    for method in (["static", "weight_only"] if a.quant == "auto" else [a.quant]):
        path = work / f"leaf.{method}.onnx"
        if method == "static":
            print(f"static quantisation with {len(calib_rows)} train images {dict(Counter(r['label'] for r in calib_rows))}")
            quantise(fp32, path, calib_rows, data_root, work)
        else:
            quantise_weights_only(fp32, path)
        s8 = ort_session(path, a.threads)
        for s in (s32, s8):
            i, o = s.get_inputs()[0], s.get_outputs()[0]
            assert i.name == "input" and list(i.shape) == [1, 3, SIZE, SIZE], (i.name, i.shape)
            assert o.name == "logits" and list(o.shape) == [1, len(CLASSES)], (o.name, o.shape)
        candidates[method] = {"path": path, "bytes": path.stat().st_size, "parity": parity(ref, s8, temperature)}
        agree8 = candidates[method]["parity"]["top1_agreement"]["pytorch_vs_onnx_int8"]
        print(f"{method}: {candidates[method]['bytes']} bytes, top-1 agreement with PyTorch {agree8:.3f}")
        if agree8 >= a.min_agreement:
            break
    method = next((m for m, c in candidates.items()
                   if c["parity"]["top1_agreement"]["pytorch_vs_onnx_int8"] >= a.min_agreement), list(candidates)[-1])
    int8, par, size8 = candidates[method]["path"], candidates[method]["parity"], candidates[method]["bytes"]
    report = {
        "checkpoint": str(a.ckpt), "arch": ckpt["arch"], "epoch": ckpt.get("epoch"),
        "command": " ".join([os.path.basename(sys.executable)] + sys.argv),
        "opset": a.opset, "quantisation": methods[method], "quantisation_method": method,
        "bytes": {"onnx_fp32": fp32.stat().st_size, "onnx_int8": size8},
        "parity": par, "temperature": temperature, "threshold": threshold,
        "candidates": {m: {"bytes": c["bytes"], "top1_agreement": c["parity"]["top1_agreement"],
                           "relative_logit_error_int8": c["parity"]["relative_logit_error_int8"]}
                       for m, c in candidates.items()},
    }
    failures = []
    if size8 > a.max_mb * 1e6:
        failures.append(f"int8 model is {size8 / 1e6:.2f} MB, over the {a.max_mb} MB cap")
    for k in ("pytorch_vs_onnx_fp32", "pytorch_vs_onnx_int8"):
        if par["top1_agreement"][k] < a.min_agreement:
            failures.append(f"top-1 agreement {k} = {par['top1_agreement'][k]:.3f}, below {a.min_agreement}")
    if not cal.get("chosen", {}).get("reached", False):
        failures.append(f"calibration did not reach its accepted-accuracy target; threshold {threshold} is a fallback")
    report["failures"] = failures
    print(json.dumps({k: report[k] for k in ("bytes", "parity", "failures")}, indent=2))
    if failures and not a.force:
        Path(a.report).write_text(json.dumps(report, indent=2))
        raise SystemExit("EXPORT FAILED, nothing written to the model folder:\n  " + "\n  ".join(failures))
    if failures:
        print("WARNING: checks failed but --force was given:\n  " + "\n  ".join(failures))

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(int8, out / "leaf.onnx")
    model_json = {
        "version": a.version,
        "labels": CLASSES,
        "input": {"size": SIZE, "resize": "shorter_side_then_center_crop", "mean": MEAN, "std": STD,
                  "layout": "NCHW", "range": "0-1"},
        "temperature": temperature,
        "threshold": threshold,
        "sha256": sha256_file(out / "leaf.onnx"),
        "bytes": (out / "leaf.onnx").stat().st_size,
        "arch": ckpt["arch"],
        "quantisation": "int8 static QDQ" if method == "static" else "int8 weight-only QDQ",
        "threshold_target_val_accuracy": cal.get("chosen", {}).get("target"),
    }
    (out / "model.json").write_text(json.dumps(model_json, indent=2) + "\n")

    sess = ort_session(out / "leaf.onnx", a.threads)
    gate_rows = [r for r in test_rows if r["source"] in ("bracol", "plantdoc")]
    meta = make_parity_samples(gate_rows, data_root, Path(a.parity_dir), sess, temperature, threshold, a.seed)
    (Path(a.parity_dir) / "samples.json").write_text(json.dumps(
        {"model_sha256": model_json["sha256"], "model_version": a.version, "temperature": temperature,
         "threshold": threshold, "note": "expected.json probs are after temperature, from the int8 ONNX model "
         "with the engine preprocessing; images re-encoded without EXIF or ICC.", "samples": meta}, indent=2))
    report["model_json"] = model_json
    report["parity_samples"] = {"dir": str(a.parity_dir), "n": len(meta)}
    Path(a.report).write_text(json.dumps(report, indent=2))
    shutil.rmtree(work, ignore_errors=True)
    print(f"wrote {out / 'leaf.onnx'} ({model_json['bytes']} bytes), {out / 'model.json'}, {len(meta)} parity samples in {a.parity_dir}")


if __name__ == "__main__":
    main()
