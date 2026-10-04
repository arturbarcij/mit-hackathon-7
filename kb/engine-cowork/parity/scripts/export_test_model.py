"""Export an untrained mobilenetv3_small_100 (6 classes) to ONNX fp32 and static int8 QDQ,
the same way app/ml/export.py does, with random calibration data.

Usage: python export_test_model.py <out_dir>
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import timm
import torch
from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static

LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]
INPUT_SIZE = 224
SEED = 42


class RandomReader(CalibrationDataReader):
    def __init__(self, n=32):
        self.rng = np.random.default_rng(SEED)
        self.n = n
        self.i = 0

    def get_next(self):
        if self.i >= self.n:
            return None
        self.i += 1
        # roughly the range of normalised ImageNet pixels
        return {"input": self.rng.normal(0.0, 1.0, (1, 3, INPUT_SIZE, INPUT_SIZE)).astype(np.float32)}


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED)
    model = timm.create_model("mobilenetv3_small_100", pretrained=False, num_classes=len(LABELS))
    model.eval()
    torch.save(model.state_dict(), out / "test_model.pt")
    fp32 = out / "test_fp32.onnx"
    int8 = out / "test_int8.onnx"
    dummy = torch.zeros(1, 3, INPUT_SIZE, INPUT_SIZE)
    torch.onnx.export(model, dummy, str(fp32), input_names=["input"], output_names=["logits"],
                      opset_version=17, dynamo=False)
    print(f"wrote {fp32} {fp32.stat().st_size} bytes")
    quantize_static(model_input=str(fp32), model_output=str(int8), calibration_data_reader=RandomReader(),
                    quant_format=QuantFormat.QDQ, activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8)
    print(f"wrote {int8} {int8.stat().st_size} bytes")


if __name__ == "__main__":
    main()
