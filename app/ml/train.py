"""Train the Jani leaf classifier (timm mobilenetv3_small_100, 224x224, 6 classes).

Reads app/ml/manifest.csv (paths relative to data_raw/). Runs on CPU or GPU.
Logs to app/ml/runs/<timestamp>/: config.json (exact command), metrics.csv, metrics.jsonl,
best.pt and last.pt (git-ignored), val_confusion.json, train.log.

Smoke test:  python app/ml/train.py --epochs 1 --max-train-per-class 50 --max-val-per-class 20

v2 options (defaults keep v1 behaviour): --train-splits / --val-splits take several manifest splits;
--composite-p pastes coffee crops onto synthetic exercise-book pages (synth.py), --field-bg-p of those onto
crops of PlantDoc field photos instead; --synthetic-not-leaf adds generated blank pages with clutter to
not_leaf; --plantdoc-crop-p shows PlantDoc not_leaf images as close-up crops; --not-leaf-share fixes the
not_leaf share of each batch; --init starts from a checkpoint; --select mean_f1 picks the best epoch on
the mean macro F1 over the val splits.
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


def post_tf():
    """Phone-camera augmentations for images that are already a full scene (composites, synthetic pages)."""
    return T.Compose([
        T.RandomResizedCrop(SIZE, scale=(0.7, 1.0), ratio=(0.8, 1.25)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(),
        T.RandomRotation(8),
        T.ColorJitter(brightness=0.35, contrast=0.3, saturation=0.3, hue=0.04),
        RandomBlur(),
        RandomJpeg(),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])


COFFEE_SOURCES = ("jmuben", "jmuben2", "bracol")
SYNTH = "SYNTHETIC_PAGE"


def open_small(path, min_side: int = 512) -> Image.Image:
    """Decode a JPEG at reduced scale (DCT draft mode) when it is much larger than needed."""
    img = Image.open(path)
    if img.format == "JPEG":
        img.draft("RGB", (min_side, min_side))
    return img.convert("RGB")


class TrainLeaves(Dataset):
    """Training images with v2 protocol compositing. Rows are (path, label, source); path SYNTH = generated page."""

    def __init__(self, rows, data_root: Path, composite_p=0.0, field_bg_p=0.0, plantdoc_crop_p=0.0, field_bgs=()):
        self.rows, self.root = rows, data_root
        self.composite_p, self.field_bg_p, self.plantdoc_crop_p = composite_p, field_bg_p, plantdoc_crop_p
        self.field_bgs = list(field_bgs)
        self.tf, self.post = train_tf(), post_tf()

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        import synth
        path, label, source = self.rows[i]
        rng = random.Random(random.getrandbits(32))
        if path == SYNTH:
            return self.post(synth.blank_page(rng)), label
        img = open_small(self.root / path)
        if source in COFFEE_SOURCES and rng.random() < self.composite_p:
            bg = None
            if self.field_bgs and rng.random() < self.field_bg_p:
                bg = synth.random_crop(open_small(self.root / rng.choice(self.field_bgs)), rng, 0.3, 0.9)
            return self.post(synth.composite_leaf(img, source, rng, bg)), label
        if source == "plantdoc" and rng.random() < self.plantdoc_crop_p:
            return self.post(synth.random_crop(img, rng)), label
        return self.tf(img), label


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


def load_rows(manifest: Path, split: str, cap: int, seed: int, with_source: bool = False, uncapped=()):
    rows = [r for r in csv.DictReader(open(manifest)) if r["split"] == split and r["label"] in CLASSES]
    rng = random.Random(seed)
    rng.shuffle(rows)
    if cap:
        kept, n = [], Counter()
        for r in rows:
            if r["source"] in uncapped:
                kept.append(r)
            elif n[r["label"]] < cap:
                kept.append(r)
                n[r["label"]] += 1
        rows = kept
    if with_source:
        return [(r["path"], CLASSES.index(r["label"]), r["source"]) for r in rows]
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
    ap.add_argument("--init", default=None, help="start from this checkpoint instead of ImageNet weights")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=None, help="default 1e-3 frozen, 5e-4 full fine-tune")
    ap.add_argument("--weight-decay", type=float, default=0.02)
    ap.add_argument("--freeze-backbone", action="store_true", help="train only conv_head and classifier")
    ap.add_argument("--train-splits", nargs="+", default=["train"])
    ap.add_argument("--val-splits", nargs="+", default=["val"])
    ap.add_argument("--max-train-per-class", type=int, default=0,
                    help="cap per class on the first train split (in-domain); 0 = all. Other splits are not capped")
    ap.add_argument("--uncapped-sources", nargs="*", default=[], help="sources exempt from --max-train-per-class")
    ap.add_argument("--max-val-per-class", type=int, default=500, help="per val split; 0 = all")
    ap.add_argument("--samples-per-epoch", type=int, default=0,
                    help="class-balanced draws per epoch; 0 = number of (capped) train images")
    ap.add_argument("--composite-p", type=float, default=0.0, help="probability of pasting a coffee crop onto a page")
    ap.add_argument("--field-bg-p", type=float, default=0.0, help="share of composites on a PlantDoc field crop instead")
    ap.add_argument("--plantdoc-crop-p", type=float, default=0.0, help="probability of a close-up crop for PlantDoc")
    ap.add_argument("--synthetic-not-leaf", type=int, default=0, help="virtual blank-page not_leaf items")
    ap.add_argument("--not-leaf-share", type=float, default=0.0, help="share of draws that are not_leaf; 0 = equal classes")
    ap.add_argument("--source-weight", nargs="*", default=[], help="source=weight within its class, e.g. uganda=2")
    ap.add_argument("--select", choices=["loss", "mean_f1"], default="loss",
                    help="best epoch: lowest val loss (first val split) or highest mean macro F1 over val splits")
    ap.add_argument("--patience", type=int, default=2, help="early stop after this many epochs without improvement")
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

    data_root, manifest = Path(a.data_root), Path(a.manifest)
    train_rows = []
    for k, sp in enumerate(a.train_splits):
        train_rows += load_rows(manifest, sp, a.max_train_per_class if k == 0 else 0, a.seed, with_source=True,
                                uncapped=a.uncapped_sources)
    train_rows += [(SYNTH, CLASSES.index("not_leaf"), "synthetic_page")] * a.synthetic_not_leaf
    val_sets = {sp: load_rows(manifest, sp, a.max_val_per_class, a.seed) for sp in a.val_splits}
    counts = Counter(CLASSES[y] for _, y, _ in train_rows)
    by_source = Counter((CLASSES[y], src) for _, y, src in train_rows)
    val_counts = {sp: dict(Counter(CLASSES[y] for _, y in rows)) for sp, rows in val_sets.items()}
    samples = a.samples_per_epoch or len(train_rows)
    field_bgs = [p for p, y, src in train_rows if src == "plantdoc"]

    config = {
        "command": " ".join([os.path.basename(sys.executable)] + sys.argv),
        "args": vars(a), "device": str(device), "lr": lr, "num_workers": workers,
        "torch_threads": torch.get_num_threads(), "classes": CLASSES,
        "train_counts": dict(counts), "train_counts_by_source": {f"{c}/{s}": n for (c, s), n in sorted(by_source.items())},
        "val_counts": val_counts if len(val_sets) > 1 else val_counts[a.val_splits[0]], "samples_per_epoch": samples,
        "input": {"size": SIZE, "resize": "shorter_side_then_center_crop", "mean": MEAN, "std": STD,
                  "layout": "NCHW", "range": "0-1"},
        "torch": torch.__version__, "timm": timm.__version__,
    }
    (run / "config.json").write_text(json.dumps(config, indent=2))
    log(f"run dir {run}")
    log(f"device {device}, threads {torch.get_num_threads()}, workers {workers}, lr {lr}")
    log(f"train {len(train_rows)} {dict(counts)}; draws/epoch {samples}")
    log(f"train by source {config['train_counts_by_source']}")
    log(f"val {val_counts}")

    # Sampling weights: each class gets an equal share of draws (not_leaf gets --not-leaf-share if set);
    # inside a class, rows are weighted by --source-weight (default 1).
    src_w = {k: float(v) for k, v in (x.split("=") for x in a.source_weight)}
    row_w = [src_w.get(src, 1.0) for _, _, src in train_rows]
    class_mass = Counter()
    for (_, y, _), w in zip(train_rows, row_w):
        class_mass[y] += w
    nl = CLASSES.index("not_leaf")
    present = sorted(class_mass)
    if a.not_leaf_share and nl in class_mass:
        share = {c: (a.not_leaf_share if c == nl else (1 - a.not_leaf_share) / (len(present) - 1)) for c in present}
    else:
        share = {c: 1 / len(present) for c in present}
    weights = torch.tensor([share[y] * w / class_mass[y] for (_, y, _), w in zip(train_rows, row_w)], dtype=torch.double)
    gen = torch.Generator().manual_seed(a.seed)
    sampler = WeightedRandomSampler(weights, samples, replacement=True, generator=gen)
    pin = device.type == "cuda"
    train_ds = TrainLeaves(train_rows, data_root, a.composite_p, a.field_bg_p, a.plantdoc_crop_p, field_bgs)
    train_dl = DataLoader(train_ds, batch_size=a.batch_size, sampler=sampler,
                          num_workers=workers, pin_memory=pin, drop_last=True, worker_init_fn=worker_init,
                          persistent_workers=workers > 0)
    val_dls = {sp: DataLoader(Leaves(rows, data_root, eval_tf()), batch_size=a.batch_size * 2, shuffle=False,
                              num_workers=workers, pin_memory=pin) for sp, rows in val_sets.items()}

    model = timm.create_model(a.model, pretrained=a.init is None, num_classes=len(CLASSES))
    if a.init:
        init = torch.load(a.init, map_location="cpu", weights_only=False)
        assert init.get("classes", CLASSES) == CLASSES and init.get("arch", a.model) == a.model
        model.load_state_dict(init["model"])
        log(f"initialised from {a.init} (epoch {init.get('epoch')})")
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

    multi = len(val_sets) > 1
    best, bad, step = (float("inf") if a.select == "loss" else -1.0), 0, 0
    fields = ["epoch", "train_loss", "train_acc"]
    for sp in val_sets:
        pre = f"{sp}_" if multi else "val_"
        fields += [f"{pre}loss", f"{pre}acc", f"{pre}macro_f1"] if multi else ["val_loss", "val_acc", "val_macro_f1"]
    fields += (["select_score"] if multi else []) + ["lr", "epoch_s", "img_per_s"]
    recall_fields = [f"{(sp + '_') if multi else 'val_'}recall_{c}" for sp in val_sets for c in CLASSES]
    with open(run / "metrics.csv", "w", newline="") as f:
        csv.writer(f).writerow(fields + recall_fields)

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
        vs = {sp: evaluate(model, dl, device) for sp, dl in val_dls.items()}
        epoch_s = time.time() - t0
        first = vs[a.val_splits[0]]
        score = float(np.mean([v["macro_f1"] for v in vs.values()]))
        row = {"epoch": epoch, "train_loss": run_loss / max(seen, 1), "train_acc": correct / max(seen, 1),
               "lr": opt.param_groups[0]["lr"], "epoch_s": round(epoch_s, 1), "img_per_s": round(seen / train_s, 1)}
        for sp, v in vs.items():
            pre = f"{sp}_" if multi else "val_"
            row.update({f"{pre}loss": v["loss"], f"{pre}acc": v["acc"], f"{pre}macro_f1": v["macro_f1"]})
        if multi:
            row["select_score"] = score
        with open(run / "metrics.csv", "a", newline="") as f:
            csv.writer(f).writerow([row[k] for k in fields] +
                                   [vs[sp]["recall"].get(c, "") for sp in val_sets for c in CLASSES])
        with open(run / "metrics.jsonl", "a") as f:
            extra = ({"val": {sp: {k: v[k] for k in ("recall", "confusion")} for sp, v in vs.items()}} if multi
                     else {"val_recall": first["recall"], "val_confusion": first["confusion"]})
            f.write(json.dumps({**row, **extra}) + "\n")
        log(f"epoch {epoch} done in {epoch_s / 60:.1f} min: train loss {row['train_loss']:.4f} acc {row['train_acc']:.3f}")
        for sp, v in vs.items():
            log(f"  {sp}: loss {v['loss']:.4f} acc {v['acc']:.3f} macro F1 {v['macro_f1']:.3f} | recall {v['recall']}")
        if multi:
            log(f"  mean macro F1 {score:.4f}")
        ckpt = {"model": model.state_dict(), "arch": a.model, "classes": CLASSES, "epoch": epoch,
                "val": first if not multi else vs, "config": config}
        torch.save(ckpt, run / "last.pt")
        metric = first["loss"] if a.select == "loss" else score
        improved = metric < best if a.select == "loss" else metric > best
        if improved:
            best, bad = metric, 0
            torch.save(ckpt, run / "best.pt")
            (run / "val_confusion.json").write_text(json.dumps(
                {"epoch": epoch, "labels": CLASSES, "val_counts": val_counts,
                 **({"matrix": first["confusion"]} if not multi else {"matrix": {sp: v["confusion"] for sp, v in vs.items()}})},
                indent=2))
            log(f"new best ({a.select}) {best:.4f} at epoch {epoch}, saved best.pt")
        else:
            bad += 1
            if bad >= a.patience:
                log(f"early stop: {a.select} has not improved for {bad} epochs")
                break
    log(f"finished; best {a.select} {best:.4f}")
    (run / "DONE").write_text("ok\n")


if __name__ == "__main__":
    main()
