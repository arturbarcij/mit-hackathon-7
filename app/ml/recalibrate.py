"""Recompute temperature and threshold from the saved best checkpoint. Does not train."""
from __future__ import annotations

import json
import sys

import torch
from torch.utils.data import DataLoader

from common import LABELS, ML, ROOT, SEED
from train import LeafDataset, calibrate, eval_transform, load_manifest, run_eval, set_seed

import timm


def main() -> int:
    set_seed(SEED)
    cal_path = ML / "calibration.json"
    old = json.loads(cal_path.read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(ROOT / old["best_checkpoint"], map_location=device, weights_only=False)
    model = timm.create_model("mobilenetv3_small_100", pretrained=False, num_classes=len(LABELS))
    model.load_state_dict(ckpt["model"])
    model.to(device)
    val = load_manifest({"val"})
    loader = DataLoader(LeafDataset(val, eval_transform()), batch_size=96, shuffle=False, num_workers=0)
    ev = run_eval(model, loader, device)
    temperature, thresh, _ = calibrate(ev["logits"], ev["y"])
    old.update({
        "temperature": temperature,
        "threshold": thresh["threshold"],
        "val_selective_acc": thresh["acc"],
        "val_coverage": thresh["coverage"],
        "val_acc": ev["acc"],
        "val_macro_f1": ev["macro_f1"],
        "val_loss": ev["loss"],
    })
    text = json.dumps(old, indent=2)
    cal_path.write_text(text, encoding="utf-8")
    (ROOT / old["run"] / "calibration.json").write_text(text, encoding="utf-8")
    print(old, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
