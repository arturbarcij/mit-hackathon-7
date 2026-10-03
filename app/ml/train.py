"""Train the Jani leaf classifier (timm mobilenetv3_small_100, 224x224, 6 classes).

Reads app/ml/manifest.csv (paths relative to data_raw/). Runs on CPU or GPU.
Logs to app/ml/runs/<timestamp>/: config.json (exact command), metrics.csv, metrics.jsonl,
best.pt and last.pt (git-ignored), val_confusion.json, train.log.

Smoke test:  python app/ml/train.py --epochs 1 --max-train-per-class 50 --max-val-per-class 20
"""
import argparse
import csv
import io
import json
import math
import os
import random
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import timm
import torch
import torch.nn as nn
from PIL import Image, ImageFilter
from sklearn.metrics import confusion_matrix, f1_score
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms as T

ML = Path(__file__).resolve().parent
ROOT = ML.parents[1]
CLASSES = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
SIZE = 224


class RandomJpeg:
    """Re-encode as JPEG at a random quality, like a cheap phone camera or a messaging app."""

    def __init__(self, p=0.5, quality=(25, 90)):
        self.p, self.quality = p, quality

    def __call__(self, img):
        if random.random() > self.p:
            return img
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=random.randint(*self.quality))
        buf.seek(0)
        return Image.open(buf).convert("RGB")


class RandomBlur:
    def __init__(self, p=0.3, radius=(0.1, 1.5)):
        self.p, self.radius = p, radius

    def __call__(self, img):
        if random.random() > self.p:
            return img
        return img.filter(ImageFilter.GaussianBlur(random.uniform(*self.radius)))


def train_tf():
    return T.Compose([
        T.RandomResizedCrop(SIZE, scale=(0.5, 1.0), ratio=(0.75, 1.33)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(),
        T.RandomRotation(25, fill=255),
        T.ColorJitter(brightness=0.35, contrast=0.3, saturation=0.3, hue=0.04),
        RandomBlur(),
        RandomJpeg(),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])


def eval_tf():
    # Must match model.json "shorter_side_then_center_crop" (the engine reproduces this in the browser).
    return T.Compose([T.Resize(SIZE), T.CenterCrop(SIZE), T.ToTensor(), T.Normalize(MEAN, STD)])


class Leaves(Dataset):
    def __init__(self, rows, data_root: Path, tf):
        self.rows, self.root, self.tf = rows, data_root, tf

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        path, label = self.rows[i]
        img = Image.open(self.root / path).convert("RGB")
        return self.tf(img), label


def load_rows(manifest: Path, split: str, cap: int, seed: int):
    rows = [r for r in csv.DictReader(open(manifest)) if r["split"] == split and r["label"] in CLASSES]
    rng = random.Random(seed)
    rng.shuffle(rows)
    if cap:
        kept, n = [], Counter()
        for r in rows:
            if n[r["label"]] < cap:
                kept.append(r)
                n[r["label"]] += 1
        rows = kept
    return [(r["path"], CLASSES.index(r["label"])) for r in rows]


def pick_device(name: str) -> torch.device:
    if name != "auto":
        return torch.device(name)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def seed_all(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def worker_init(wid):
    s = torch.initial_seed() % 2**32
    random.seed(s)
    np.random.seed(s)


def evaluate(model, loader, device):
    model.eval()
    loss_fn = nn.CrossEntropyLoss(reduction="sum")
    total, loss, ys, ps = 0, 0.0, [], []
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            loss += loss_fn(out, y).item()
            total += len(y)
            ys += y.tolist()
            ps += out.argmax(1).tolist()
    ys, ps = np.array(ys), np.array(ps)
    present = sorted(set(ys.tolist()))
    recall = {CLASSES[c]: float((ps[ys == c] == c).mean()) for c in present}
    return {
        "loss": loss / max(total, 1),
        "acc": float((ys == ps).mean()) if total else 0.0,
        "macro_f1": float(f1_score(ys, ps, labels=present, average="macro")) if total else 0.0,
        "recall": recall,
        "confusion": confusion_matrix(ys, ps, labels=list(range(len(CLASSES)))).tolist(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(ML / "manifest.csv"))
    ap.add_argument("--data-root", default=str(ROOT / "data_raw"))
    ap.add_argument("--model", default="mobilenetv3_small_100")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=None, help="default 1e-3 frozen, 5e-4 full fine-tune")
    ap.add_argument("--weight-decay", type=float, default=0.02)
    ap.add_argument("--freeze-backbone", action="store_true", help="train only conv_head and classifier")
    ap.add_argument("--max-train-per-class", type=int, default=0, help="0 = all")
    ap.add_argument("--max-val-per-class", type=int, default=500, help="0 = all")
    ap.add_argument("--samples-per-epoch", type=int, default=0,
                    help="class-balanced draws per epoch; 0 = number of (capped) train images")
    ap.add_argument("--patience", type=int, default=2, help="early stop after this many epochs without val loss improvement")
    ap.add_argument("--num-workers", type=int, default=None, help="default: 3 on CPU, 4 on GPU")
    ap.add_argument("--threads", type=int, default=None, help="torch CPU threads (default: all cores)")
    ap.add_argument("--max-steps", type=int, default=0, help="stop each epoch after this many steps (timing only)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    seed_all(a.seed)
    device = pick_device(a.device)
    if a.threads:
        torch.set_num_threads(a.threads)
    workers = a.num_workers if a.num_workers is not None else (4 if device.type == "cuda" else 3)
    lr = a.lr or (1e-3 if a.freeze_backbone else 5e-4)

    run = Path(a.out) if a.out else ML / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S")
    run.mkdir(parents=True, exist_ok=True)
    log_f = open(run / "train.log", "a")

    def log(msg):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        log_f.write(line + "\n")
        log_f.flush()

    data_root = Path(a.data_root)
    train_rows = load_rows(Path(a.manifest), "train", a.max_train_per_class, a.seed)
    val_rows = load_rows(Path(a.manifest), "val", a.max_val_per_class, a.seed)
    counts = Counter(CLASSES[y] for _, y in train_rows)
    val_counts = Counter(CLASSES[y] for _, y in val_rows)
    samples = a.samples_per_epoch or len(train_rows)

    config = {
        "command": " ".join([os.path.basename(sys.executable)] + sys.argv),
        "args": vars(a), "device": str(device), "lr": lr, "num_workers": workers,
        "torch_threads": torch.get_num_threads(), "classes": CLASSES,
        "train_counts": dict(counts), "val_counts": dict(val_counts), "samples_per_epoch": samples,
        "input": {"size": SIZE, "resize": "shorter_side_then_center_crop", "mean": MEAN, "std": STD,
                  "layout": "NCHW", "range": "0-1"},
        "torch": torch.__version__, "timm": timm.__version__,
    }
    (run / "config.json").write_text(json.dumps(config, indent=2))
    log(f"run dir {run}")
    log(f"device {device}, threads {torch.get_num_threads()}, workers {workers}, lr {lr}")
    log(f"train {len(train_rows)} {dict(counts)}; val {len(val_rows)} {dict(val_counts)}; draws/epoch {samples}")

    class_w = {c: 1.0 / n for c, n in counts.items()}
    weights = torch.tensor([class_w[CLASSES[y]] for _, y in train_rows], dtype=torch.double)
    gen = torch.Generator().manual_seed(a.seed)
    sampler = WeightedRandomSampler(weights, samples, replacement=True, generator=gen)
    pin = device.type == "cuda"
    train_dl = DataLoader(Leaves(train_rows, data_root, train_tf()), batch_size=a.batch_size, sampler=sampler,
                          num_workers=workers, pin_memory=pin, drop_last=True, worker_init_fn=worker_init,
                          persistent_workers=workers > 0)
    val_dl = DataLoader(Leaves(val_rows, data_root, eval_tf()), batch_size=a.batch_size * 2, shuffle=False,
                        num_workers=workers, pin_memory=pin)

    model = timm.create_model(a.model, pretrained=True, num_classes=len(CLASSES))
    head_names = ("conv_head", "classifier")
    if a.freeze_backbone:
        for n, p in model.named_parameters():
            p.requires_grad = n.startswith(head_names)
    model.to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    log(f"trainable params {sum(p.numel() for p in params):,} of {sum(p.numel() for p in model.parameters()):,}")

    opt = torch.optim.AdamW(params, lr=lr, weight_decay=a.weight_decay)
    steps_per_epoch = min(len(train_dl), a.max_steps) if a.max_steps else len(train_dl)
    total_steps = steps_per_epoch * a.epochs
    warmup = max(1, int(0.03 * total_steps))

    def lr_at(step):
        if step < warmup:
            return (step + 1) / warmup
        t = (step - warmup) / max(1, total_steps - warmup)
        return 0.5 * (1 + math.cos(math.pi * t))

    sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_at)
    loss_fn = nn.CrossEntropyLoss()

    best, bad, step = float("inf"), 0, 0
    fields = ["epoch", "train_loss", "train_acc", "val_loss", "val_acc", "val_macro_f1", "lr", "epoch_s", "img_per_s"]
    with open(run / "metrics.csv", "w", newline="") as f:
        csv.writer(f).writerow(fields + [f"val_recall_{c}" for c in CLASSES])

    for epoch in range(1, a.epochs + 1):
        model.train()
        if a.freeze_backbone:
            for n, m in model.named_modules():
                if not n.startswith(head_names) and isinstance(m, nn.BatchNorm2d):
                    m.eval()
        t0, seen, correct, run_loss = time.time(), 0, 0, 0.0
        for i, (x, y) in enumerate(train_dl):
            if a.max_steps and i >= a.max_steps:
                break
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            out = model(x)
            loss = loss_fn(out, y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            step += 1
            seen += len(y)
            correct += (out.argmax(1) == y).sum().item()
            run_loss += loss.item() * len(y)
            if (i + 1) % 50 == 0:
                el = time.time() - t0
                log(f"epoch {epoch} step {i + 1}/{steps_per_epoch} loss {run_loss / seen:.4f} "
                    f"acc {correct / seen:.3f} {seen / el:.1f} img/s, epoch ETA {(steps_per_epoch - i - 1) * el / (i + 1) / 60:.1f} min")
        train_s = time.time() - t0
        v = evaluate(model, val_dl, device)
        epoch_s = time.time() - t0
        row = {"epoch": epoch, "train_loss": run_loss / max(seen, 1), "train_acc": correct / max(seen, 1),
               "val_loss": v["loss"], "val_acc": v["acc"], "val_macro_f1": v["macro_f1"],
               "lr": opt.param_groups[0]["lr"], "epoch_s": round(epoch_s, 1), "img_per_s": round(seen / train_s, 1)}
        with open(run / "metrics.csv", "a", newline="") as f:
            csv.writer(f).writerow([row[k] for k in fields] + [v["recall"].get(c, "") for c in CLASSES])
        with open(run / "metrics.jsonl", "a") as f:
            f.write(json.dumps({**row, "val_recall": v["recall"], "val_confusion": v["confusion"]}) + "\n")
        log(f"epoch {epoch} done in {epoch_s / 60:.1f} min: train loss {row['train_loss']:.4f} acc {row['train_acc']:.3f} | "
            f"val loss {v['loss']:.4f} acc {v['acc']:.3f} macro F1 {v['macro_f1']:.3f} | recall {v['recall']}")
        ckpt = {"model": model.state_dict(), "arch": a.model, "classes": CLASSES, "epoch": epoch, "val": v,
                "config": config}
        torch.save(ckpt, run / "last.pt")
        if v["loss"] < best:
            best, bad = v["loss"], 0
            torch.save(ckpt, run / "best.pt")
            (run / "val_confusion.json").write_text(json.dumps(
                {"epoch": epoch, "labels": CLASSES, "matrix": v["confusion"], "val_counts": dict(val_counts)}, indent=2))
            log(f"new best val loss {best:.4f}, saved best.pt")
        else:
            bad += 1
            if bad >= a.patience:
                log(f"early stop: val loss has not improved for {bad} epochs")
                break
    log(f"finished; best val loss {best:.4f}")
    (run / "DONE").write_text("ok\n")


if __name__ == "__main__":
    main()
