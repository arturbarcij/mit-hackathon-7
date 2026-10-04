"""Train mobilenetv3_small_100 and calibrate temperature plus abstention threshold.

Usage:
  python train.py
  python train.py --head-only          # freeze backbone (00:30 fallback)
  python train.py --epochs 8 --batch 64
Never reads Uganda or RoCoLe rows as train or val (manifest already excludes them).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from tqdm import tqdm

from common import IMAGENET_MEAN, IMAGENET_STD, INPUT_SIZE, LABEL_TO_IDX, LABELS, ML, ROOT, SEED

try:
    import timm
except ImportError as e:
    raise SystemExit("timm missing in this env") from e


class RandomJPEG:
    def __init__(self, p=0.4, qmin=35, qmax=90):
        self.p, self.qmin, self.qmax = p, qmin, qmax

    def __call__(self, img):
        if random.random() > self.p:
            return img
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=random.randint(self.qmin, self.qmax))
        buf.seek(0)
        return Image.open(buf).convert("RGB")


class RandomMildBlur:
    def __init__(self, p=0.3):
        self.p = p

    def __call__(self, img):
        if random.random() > self.p:
            return img
        return img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.4, 1.6)))


def eval_transform():
    # shorter side to 224, then centre crop. Matches model.json.
    return transforms.Compose([
        transforms.Resize(INPUT_SIZE),
        transforms.CenterCrop(INPUT_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


class RandomSheetPaste:
    """Paste the leaf onto a plain exercise-book page. Simulates the capture protocol."""

    def __init__(self, p=0.85):
        self.p = p

    def __call__(self, img):
        if random.random() > self.p:
            return img
        img = img.convert("RGB")
        side = random.randint(280, 400)
        paper = np.array([
            random.uniform(228, 255),
            random.uniform(224, 252),
            random.uniform(210, 242),
        ], dtype=np.float32)
        canvas = np.ones((side, side, 3), dtype=np.float32) * paper
        # faint ruled lines
        if random.random() < 0.5:
            step = random.randint(14, 22)
            for y in range(step, side, step):
                canvas[y : y + 1, :, :] -= np.array([28, 14, 8], dtype=np.float32)
        scale = random.uniform(0.42, 0.82)
        nw = max(8, int(img.width * scale * side / max(img.width, img.height)))
        nh = max(8, int(img.height * scale * side / max(img.width, img.height)))
        leaf = img.resize((nw, nh), Image.BILINEAR)
        if random.random() < 0.5:
            # mild perspective
            dx = int(nw * random.uniform(-0.08, 0.08))
            dy = int(nh * random.uniform(-0.08, 0.08))
            coeffs = (1, dx / max(nh, 1), 0, dy / max(nw, 1), 1, 0)
            leaf = leaf.transform((nw, nh), Image.AFFINE, coeffs, Image.BILINEAR)
        x0 = random.randint(0, max(0, side - nw))
        y0 = random.randint(0, max(0, side - nh))
        # soft shadow under the leaf
        shadow = np.zeros((side, side), dtype=np.float32)
        yy, xx = np.ogrid[:side, :side]
        shadow += np.exp(-(((yy - (y0 + nh * 0.55)) ** 2 + (xx - (x0 + nw * 0.55)) ** 2) / (2 * (0.28 * side) ** 2)))
        canvas -= shadow[..., None] * random.uniform(12, 28)
        arr = np.clip(canvas, 0, 255).astype("uint8")
        out = Image.fromarray(arr)
        out.paste(leaf, (x0, y0))
        return out


def train_transform(aug: str = "v1"):
    jitter = (0.4, 0.4, 0.3, 0.08) if aug == "sheet" else (0.25, 0.25, 0.2, 0.05)
    steps = []
    if aug == "sheet":
        steps.append(RandomSheetPaste())
    steps.extend([
        transforms.RandomResizedCrop(INPUT_SIZE, scale=(0.6, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(25),
        transforms.ColorJitter(*jitter),
        RandomMildBlur(),
        RandomJPEG(),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    return transforms.Compose(steps)


class LeafDataset(Dataset):
    def __init__(self, rows, tfm):
        self.rows = rows
        self.tfm = tfm

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        path = ROOT / r["path"]
        with Image.open(path) as im:
            im = im.convert("RGB")
            x = self.tfm(im)
        return x, LABEL_TO_IDX[r["label"]]


def load_manifest(splits, path=None):
    path = Path(path) if path else ML / "manifest.csv"
    rows = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["split"] in splits and r["label"] in LABEL_TO_IDX:
                if r["source"] in {"uganda", "rocole"}:
                    continue
                rows.append(r)
    return rows


def metrics(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    acc = float((y == p).mean()) if len(y) else 0.0
    f1s = []
    per = {}
    for i, name in enumerate(LABELS):
        tp = int(((y == i) & (p == i)).sum())
        fp = int(((y != i) & (p == i)).sum())
        fn = int(((y == i) & (p != i)).sum())
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        per[name] = {"precision": prec, "recall": rec, "f1": f1, "support": int((y == i).sum())}
        f1s.append(f1)
    return {"acc": acc, "macro_f1": float(np.mean(f1s)), "per_class": per}


@torch.no_grad()
def run_eval(model, loader, device):
    model.eval()
    ys, ps, logits_all = [], [], []
    loss_sum, n = 0.0, 0
    for x, y in loader:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)
        logits = model(x)
        loss_sum += F.cross_entropy(logits, y, reduction="sum").item()
        n += y.size(0)
        pred = logits.argmax(1)
        ys.extend(y.cpu().tolist())
        ps.extend(pred.cpu().tolist())
        logits_all.append(logits.cpu())
    out = metrics(ys, ps)
    out["loss"] = loss_sum / max(n, 1)
    out["logits"] = torch.cat(logits_all) if logits_all else torch.empty(0, len(LABELS))
    out["y"] = np.array(ys)
    return out


def calibrate(logits, y):
    """Temperature scaling, then the lowest threshold that still keeps 95% acc on accepted.

    Walk from most to least confident and keep the largest accepted set whose
    accuracy stays at or above 0.95. Do not stop at the first single correct image.
    """
    y_t = torch.tensor(y, dtype=torch.long)
    best_t, best_nll = 1.0, 1e9
    for t in np.linspace(0.5, 8.0, 76):
        nll = F.cross_entropy(logits / t, y_t).item()
        if nll < best_nll:
            best_nll, best_t = nll, float(t)
    probs = torch.softmax(logits / best_t, dim=1).numpy()
    conf = probs.max(1)
    pred = probs.argmax(1)
    order = np.argsort(-conf)
    chosen = {"threshold": 1.0, "acc": 0.0, "coverage": 0.0}
    at_95 = None
    for k in range(1, len(order) + 1):
        idx = order[:k]
        acc = float((pred[idx] == y[idx]).mean())
        cov = k / len(order)
        if acc >= 0.95:
            at_95 = {"threshold": float(conf[idx].min()), "acc": acc, "coverage": cov}
        if acc >= chosen["acc"] and cov >= 0.30:
            chosen = {"threshold": float(conf[idx].min()), "acc": acc, "coverage": cov}
    if at_95 is not None:
        chosen = at_95
    return best_t, chosen, probs


def set_seed(s):
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch", type=int, default=96)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--head-only", action="store_true")
    ap.add_argument("--patience", type=int, default=2)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--arch", default="mobilenetv3_small_100")
    ap.add_argument("--aug", choices=["v1", "sheet"], default="v1")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--run-dir", default=None, help="Write this run here instead of ml/runs/<stamp>")
    ap.add_argument("--no-global", action="store_true", help="Do not write ml/calibration.json")
    args = ap.parse_args()

    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if args.run_dir:
        run = Path(args.run_dir)
        if not run.is_absolute():
            run = ROOT / run
    else:
        run = ML / "runs" / stamp
    run.mkdir(parents=True, exist_ok=True)
    cmd = " ".join(sys.argv)
    (run / "command.txt").write_text(cmd + f"\nseed={SEED}\ndevice={device}\n", encoding="utf-8")
    print(f"run {run}  device={device}  head_only={args.head_only}", flush=True)

    train_rows = load_manifest({"train"}, args.manifest)
    val_rows = load_manifest({"val"}, args.manifest)
    print("train", Counter(r["label"] for r in train_rows), flush=True)
    print("val  ", Counter(r["label"] for r in val_rows), flush=True)
    print(f"arch={args.arch} aug={args.aug} no_global={args.no_global}", flush=True)
    if not train_rows or not val_rows:
        raise SystemExit("manifest empty; run python manifest.py first")

    train_ds = LeafDataset(train_rows, train_transform(args.aug))
    val_ds = LeafDataset(val_rows, eval_transform())
    counts = Counter(LABEL_TO_IDX[r["label"]] for r in train_rows)
    w_class = {i: 1.0 / max(counts[i], 1) for i in range(len(LABELS))}
    weights = [w_class[LABEL_TO_IDX[r["label"]]] for r in train_rows]
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)
    train_loader = DataLoader(
        train_ds, batch_size=args.batch, sampler=sampler,
        num_workers=args.workers, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=args.workers, pin_memory=True)

    model = timm.create_model(args.arch, pretrained=True, num_classes=len(LABELS))
    if args.head_only:
        for p in model.parameters():
            p.requires_grad = False
        for p in model.get_classifier().parameters():
            p.requires_grad = True
        print("backbone frozen; training classifier only", flush=True)
    model.to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")

    best_loss, bad, best_path = 1e9, 0, run / "best.pt"
    log_f = (run / "metrics.csv").open("w", newline="", encoding="utf-8")
    log_w = csv.DictWriter(log_f, fieldnames=["epoch", "train_loss", "val_loss", "val_acc", "val_macro_f1", "seconds"])
    log_w.writeheader()

    t0 = time.time()
    for epoch in range(1, args.epochs + 1):
        model.train()
        loss_sum, n = 0.0, 0
        for x, y in tqdm(train_loader, desc=f"epoch {epoch}"):
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                logits = model(x)
                loss = F.cross_entropy(logits, y)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            loss_sum += loss.item() * y.size(0)
            n += y.size(0)
        sched.step()
        ev = run_eval(model, val_loader, device)
        row = {
            "epoch": epoch,
            "train_loss": round(loss_sum / max(n, 1), 4),
            "val_loss": round(ev["loss"], 4),
            "val_acc": round(ev["acc"], 4),
            "val_macro_f1": round(ev["macro_f1"], 4),
            "seconds": int(time.time() - t0),
        }
        log_w.writerow(row)
        log_f.flush()
        print(row, flush=True)
        if ev["loss"] < best_loss - 1e-4:
            best_loss = ev["loss"]
            bad = 0
            torch.save({
                "model": model.state_dict(),
                "epoch": epoch,
                "val": {k: ev[k] for k in ("acc", "macro_f1", "loss", "per_class")},
                "args": vars(args),
                "head_only": args.head_only,
                "labels": LABELS,
            }, best_path)
        else:
            bad += 1
            if bad >= args.patience:
                print(f"early stop at epoch {epoch} (val loss rose)", flush=True)
                break

    log_f.close()
    if not best_path.exists():
        torch.save({"model": model.state_dict(), "epoch": 0, "labels": LABELS, "head_only": args.head_only}, best_path)

    ckpt = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model"])
    ev = run_eval(model, val_loader, device)
    temperature, thresh, _ = calibrate(ev["logits"], ev["y"])
    pred = ev["logits"].argmax(1).numpy()
    bracol_idx = [i for i, r in enumerate(val_rows) if r["source"] == "bracol"]
    bracol_f1 = metrics(ev["y"][bracol_idx], pred[bracol_idx])["macro_f1"] if bracol_idx else None
    cal = {
        "temperature": temperature,
        "threshold": thresh["threshold"],
        "val_selective_acc": thresh["acc"],
        "val_coverage": thresh["coverage"],
        "val_acc": ev["acc"],
        "val_macro_f1": ev["macro_f1"],
        "val_loss": ev["loss"],
        "bracol_val_macro_f1": bracol_f1,
        "arch": args.arch,
        "aug": args.aug,
        "head_only": args.head_only,
        "run": str(run.relative_to(ROOT).as_posix()) if run.is_relative_to(ROOT) else str(run),
        "best_checkpoint": str(best_path.relative_to(ROOT).as_posix()) if best_path.is_relative_to(ROOT) else str(best_path),
        "command": cmd,
        "seed": SEED,
    }
    (run / "calibration.json").write_text(json.dumps(cal, indent=2), encoding="utf-8")
    if not args.no_global:
        (ML / "calibration.json").write_text(json.dumps(cal, indent=2), encoding="utf-8")
    print("calibration", cal, flush=True)
    print(f"DONE {run}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
