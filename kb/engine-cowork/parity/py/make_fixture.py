"""Fixture model, exported exactly like app/ml/export.py, with seeded random weights.

timm mobilenetv3_small_100(num_classes=6, pretrained=False), torch.manual_seed(42),
ONNX opset 17, dynamo=False, input 'input' [1,3,224,224], output 'logits'.
Static int8 QDQ (activations QUInt8, weights QInt8) calibrated on ~50 tensors
written by preprocess.ts (tools/write_calib.mjs).
Then Python onnxruntime reference logits on the torchvision tensors (work/*.tensor).
"""
from __future__ import annotations

import collections
import json
import time
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort

HERE = Path(__file__).resolve().parents[1]
WORK = HERE / "work"
FIX = HERE / "fixtures" / "model"
FIX.mkdir(parents=True, exist_ok=True)
LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]


def export_fp32(dest: Path) -> dict:
    import torch
    import timm

    torch.manual_seed(42)
    model = timm.create_model("mobilenetv3_small_100", pretrained=False, num_classes=len(LABELS))
    model.eval()
    dummy = torch.zeros(1, 3, 224, 224)
    torch.onnx.export(model, dummy, str(dest), input_names=["input"], output_names=["logits"],
                      opset_version=17, dynamo=False)
    # PyTorch logits on the torchvision tensors, for the record
    pt = {}
    with torch.no_grad():
        for p in sorted(WORK.glob("*.tensor")):
            x = torch.from_numpy(np.fromfile(p, dtype=np.float32).reshape(1, 3, 224, 224))
            pt[p.stem] = model(x).numpy()[0].tolist()
    return {"torch": torch.__version__, "timm": timm.__version__, "params": sum(p.numel() for p in model.parameters()), "pt_logits": pt}


def quantize(fp32: Path, int8: Path) -> int:
    from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static

    files = sorted((WORK / "calib").glob("*.f32"))

    class Reader(CalibrationDataReader):
        def __init__(self):
            self.i = 0

        def get_next(self):
            if self.i >= len(files):
                return None
            arr = np.fromfile(files[self.i], dtype=np.float32).reshape(1, 3, 224, 224)
            self.i += 1
            return {"input": arr}

    # Same settings as app/ml/export.py quantize(): quant_pre_process, per-channel, MinMax.
    from onnxruntime.quantization import CalibrationMethod
    from onnxruntime.quantization.preprocess import quant_pre_process
    prep = fp32.with_name(fp32.stem + "_prep.onnx")
    quant_pre_process(str(fp32), str(prep))
    quantize_static(model_input=str(prep), model_output=str(int8), calibration_data_reader=Reader(),
                    quant_format=QuantFormat.QDQ, per_channel=True, reduce_range=False,
                    calibrate_method=CalibrationMethod.MinMax,
                    activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8,
                    extra_options={"ActivationSymmetric": False, "WeightSymmetric": True})
    prep.unlink()
    return len(files)


def to_fp16(fp32: Path, fp16: Path):
    # Same fallback as export.py when int8 parity < 0.95 (this is what ships today).
    from onnxruntime.transformers.float16 import convert_float_to_float16
    onnx.save(convert_float_to_float16(onnx.load(str(fp32)), keep_io_types=True), str(fp16))


def ops(path: Path) -> dict:
    m = onnx.load(str(path))
    c = collections.Counter(n.op_type for n in m.graph.node)
    return {"opset": [(o.domain or "ai.onnx", o.version) for o in m.opset_import], "ops": dict(sorted(c.items()))}


def ort_ref(path: Path) -> dict:
    so = ort.SessionOptions()
    so.intra_op_num_threads = 1
    s = ort.InferenceSession(str(path), so, providers=["CPUExecutionProvider"])
    out = {}
    times = []
    for p in sorted(WORK.glob("*.tensor")):
        x = np.fromfile(p, dtype=np.float32).reshape(1, 3, 224, 224)
        t0 = time.perf_counter()
        out[p.stem] = s.run(["logits"], {"input": x})[0][0].tolist()
        times.append((time.perf_counter() - t0) * 1000)
    return {"logits": out, "median_ms_1thread": float(np.median(times[1:]))}


def main():
    fp32 = FIX / "fixture_fp32.onnx"
    int8 = FIX / "fixture_int8.onnx"
    info = export_fp32(fp32)
    ncal = quantize(fp32, int8)
    fp16 = FIX / "fixture_fp16.onnx"
    to_fp16(fp32, fp16)
    res = {
        "torch": info["torch"], "timm": info["timm"], "params": info["params"],
        "onnxruntime": ort.__version__, "onnx": onnx.__version__,
        "calibration_tensors": ncal,
        "fp32_bytes": fp32.stat().st_size, "int8_bytes": int8.stat().st_size,
        "fp16_bytes": fp16.stat().st_size,
        "fp32_ops": ops(fp32), "int8_ops": ops(int8), "fp16_ops": ops(fp16),
    }
    r32 = ort_ref(fp32)
    r8 = ort_ref(int8)
    r16 = ort_ref(fp16)
    res["py_ort_fp16_median_ms"] = r16["median_ms_1thread"]
    res["py_ort_fp32_median_ms"] = r32["median_ms_1thread"]
    res["py_ort_int8_median_ms"] = r8["median_ms_1thread"]
    pt = info["pt_logits"]
    res["pt_vs_ort_fp32_max_logit_diff"] = max(float(np.max(np.abs(np.array(pt[k]) - np.array(r32["logits"][k])))) for k in pt)
    (WORK / "py_ref.json").write_text(json.dumps({"fp32": r32["logits"], "int8": r8["logits"], "fp16": r16["logits"], "pt": pt}))
    (HERE / "logs" / "fixture_model.json").write_text(json.dumps(res, indent=1))
    def agree(a, b):
        return sum(int(np.argmax(a[k]) == np.argmax(b[k])) for k in a), len(a)
    res["py_top1_agree_pt_vs_int8"] = agree(pt, r8["logits"])
    res["py_top1_agree_pt_vs_fp16"] = agree(pt, r16["logits"])
    res["py_max_logit_diff_pt_vs_int8"] = max(float(np.max(np.abs(np.array(pt[k]) - np.array(r8["logits"][k])))) for k in pt)
    res["py_max_logit_diff_pt_vs_fp16"] = max(float(np.max(np.abs(np.array(pt[k]) - np.array(r16["logits"][k])))) for k in pt)
    (HERE / "logs" / "fixture_model.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if not k.endswith("_ops")}, indent=1))


if __name__ == "__main__":
    main()
