#!/usr/bin/env python3
"""Train the Jani leaf classifier.

Model: timm mobilenetv3_small_100, 224 input, ImageNet pretrained weights.
Augmentations simulate a cheap phone camera. Sampling is class-balanced.
Optimiser is AdamW with a cosine schedule. Training stops early when
validation loss rises.

Writes app/ml/runs/<timestamp>/. Refuses to start when manifest.csv is missing.
CPU is a fallback when CUDA is not visible. Parsing this file does not need a GPU.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shlex
import sys
import time
from collections import Counter
from pathlib import Path

from common import (
    DATA_RAW,
    INPUT_SIZE,
    LABELS,
    MANIFEST_PATH,
    MEAN,
    RUNS_DIR,
    SEED,
    STD,
    choose_threshold,
    image_path,
    is_trainable,
    load_manifest,
    softmax,
    to_nchw,
)

AUGMENTATIONS = [
    "random resized crop to 224 (scale 0.7 to 1.0)",
    "horizontal flip",
    "vertical flip",
    "rotation up to 15 degrees",
    "colour jitter",
    "mild gaussian blur (p=0.3, kernel 3)",
    "JPEG compression quality 40 to 95 (p=0.5)",
]


class JpegCompression:
    """Random in-memory JPEG round trip. Applied to a PIL image."""

    def __init__(self, quality_min: int = 40, quality_max: int = 95, probability: float = 0.5):
        self.quality_min = quality_min
        self.quality_max = quality_max
        self.probability = probability

    def __call__(self, image):
        import io
        import random as py_random

        from PIL import Image

        if py_random.random() > self.probability:
            return image
        quality = py_random.randint(self.quality_min, self.quality_max)
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        return Image.open(buffer).convert("RGB")


def fit_temperature(logits: list[list[float]], labels: list[int], steps: int = 200) -> float:
    """Fit a single temperature on validation logits. Requires torch at call time."""
    import torch

    inputs = torch.tensor(logits, dtype=torch.float32)
    targets = torch.tensor(labels, dtype=torch.long)
    log_t = torch.nn.Parameter(torch.zeros(1))
    optimiser = torch.optim.Adam([log_t], lr=0.05)
    loss_fn = torch.nn.CrossEntropyLoss()
    for _ in range(steps):
        optimiser.zero_grad()
        temperature = log_t.exp().clamp(min=1e-3, max=100.0)
        loss = loss_fn(inputs / temperature, targets)
        loss.backward()
        optimiser.step()
    return float(log_t.detach().exp().clamp(min=1e-3, max=100.0))


def seed_all(seed: int) -> None:
    import torch

    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def trainable_rows(rows: list[dict], split: str) -> list[dict]:
    kept = []
    for row in rows:
        if split == "train":
            if is_trainable(row):
                kept.append(row)
        elif row.get("split") == split and (row.get("out_of_scope") or "") == "" and row.get("label") in LABELS:
            if row.get("source") in {"Uganda", "RoCoLe"}:
                continue
            kept.append(row)
    return kept


def build_transforms(train: bool):
    from torchvision import transforms

    if not train:
        return None
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(
                INPUT_SIZE,
                scale=(0.7, 1.0),
                interpolation=transforms.InterpolationMode.BILINEAR,
            ),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.25, contrast=0.25, saturation=0.25, hue=0.02),
            transforms.RandomApply(
                [transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0))],
                p=0.3,
            ),
            JpegCompression(),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ]
    )


class LeafSet:
    """Picklable dataset so Windows can use more than one loader worker."""

    def __init__(self, items: list[dict], train: bool):
        self.items = items
        self.train = train
        self.transform = None

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int):
        import torch
        from PIL import Image

        if self.train and self.transform is None:
            self.transform = build_transforms(True)
        row = self.items[index]
        path = image_path(row)
        with Image.open(path) as image:
            rgb = image.convert("RGB")
        if self.transform is None:
            tensor = torch.from_numpy(to_nchw(rgb)[0])
        else:
            tensor = self.transform(rgb)
        return tensor, LABELS.index(row["label"])


def make_loader(rows: list[dict], train: bool, batch_size: int, workers: int, device_type: str):
    import torch
    from torch.utils.data import DataLoader, WeightedRandomSampler

    dataset = LeafSet(rows, train)
    sampler = None
    shuffle = False
    if train:
        counts = Counter(row["label"] for row in rows)
        weights = [1.0 / counts[row["label"]] for row in rows]
        generator = torch.Generator()
        generator.manual_seed(SEED)
        sampler = WeightedRandomSampler(
            weights,
            num_samples=len(weights),
            replacement=True,
            generator=generator,
        )
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        sampler=sampler,
        num_workers=workers,
        pin_memory=device_type == "cuda",
    )
    return loader


def macro_f1(truth: list[int], predicted: list[int], n_classes: int) -> float:
    scores = []
    for class_index in range(n_classes):
        tp = sum(1 for left, right in zip(truth, predicted) if left == class_index and right == class_index)
        fp = sum(1 for left, right in zip(truth, predicted) if left != class_index and right == class_index)
        fn = sum(1 for left, right in zip(truth, predicted) if left == class_index and right != class_index)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall))
    return sum(scores) / n_classes


def run_epoch(model, loader, device, optimiser, criterion, train: bool):
    import torch

    model.train(train)
    total_loss = 0.0
    seen = 0
    truth: list[int] = []
    predicted: list[int] = []
    context = torch.enable_grad() if train else torch.no_grad()
    with context:
        for inputs, targets in loader:
            inputs = inputs.to(device)
            targets = targets.to(device)
            if train:
                optimiser.zero_grad(set_to_none=True)
            logits = model(inputs)
            loss = criterion(logits, targets)
            if train:
                loss.backward()
                optimiser.step()
            batch = targets.shape[0]
            total_loss += float(loss.item()) * batch
            seen += batch
            guess = logits.argmax(dim=1)
            truth.extend(int(value) for value in targets.detach().cpu())
            predicted.extend(int(value) for value in guess.detach().cpu())
    if seen == 0:
        return {"loss": None, "accuracy": None, "macro_f1": None}
    correct = sum(1 for left, right in zip(truth, predicted) if left == right)
    return {
        "loss": total_loss / seen,
        "accuracy": correct / seen,
        "macro_f1": macro_f1(truth, predicted, len(LABELS)),
    }


def collect_logits(model, loader, device):
    import torch

    model.eval()
    logits_out: list[list[float]] = []
    labels_out: list[int] = []
    with torch.no_grad():
        for inputs, targets in loader:
            inputs = inputs.to(device)
            logits = model(inputs).detach().cpu()
            for row, target in zip(logits, targets):
                logits_out.append([float(value) for value in row])
                labels_out.append(int(target))
    return logits_out, labels_out


def calibrate(model, loader, device) -> dict:
    logits, labels = collect_logits(model, loader, device)
    if not logits:
        return {"temperature": None, "threshold": None, "target_met": False, "n_val": 0}
    temperature = fit_temperature(logits, labels)
    confidences = []
    correct = []
    for row, label in zip(logits, labels):
        probabilities = softmax(row, temperature)
        guess = max(range(len(probabilities)), key=lambda index: probabilities[index])
        confidences.append(probabilities[guess])
        correct.append(guess == label)
    chosen = choose_threshold(confidences, correct, target=0.95)
    chosen["temperature"] = temperature
    chosen["n_val"] = len(labels)
    return chosen


def build_model(arch: str, pretrained: bool):
    import timm

    return timm.create_model(arch, pretrained=pretrained, num_classes=len(LABELS))


def freeze_backbone(model) -> None:
    for parameter in model.parameters():
        parameter.requires_grad = False
    for parameter in model.get_classifier().parameters():
        parameter.requires_grad = True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train the Jani MobileNetV3 leaf classifier.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--arch", default="mobilenetv3_small_100")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--patience", type=int, default=1, help="Stop after this many epochs of rising val loss.")
    parser.add_argument("--workers", type=int, default=0, help="Data loader workers. 0 is the safe default on Windows.")
    parser.add_argument("--freeze-backbone", action="store_true")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    if not args.manifest.is_file():
        print(
            f"Refusing to train: {args.manifest} is missing. "
            "Run download.py and then manifest.py. No run directory was created."
        )
        return 1

    try:
        import torch
    except ImportError:
        print("Refusing to train: torch is not installed. Create the jani conda env first. No metrics were written.")
        return 1

    rows = load_manifest(args.manifest)
    train_rows = trainable_rows(rows, "train")
    val_rows = trainable_rows(rows, "val")
    if not train_rows or not val_rows:
        print(
            f"Refusing to train: need train and val rows in {args.manifest}. "
            f"Found train={len(train_rows)} val={len(val_rows)}. "
            "Held-out Uganda and RoCoLe rows are ignored. No run was started."
        )
        return 1
    missing = [row["path"] for row in train_rows[:20] if not image_path(row).is_file()]
    if missing:
        print(f"Refusing to train: manifest paths are missing under {DATA_RAW}, for example {missing[0]}")
        return 1

    seed_all(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cpu":
        print(
            "CPU fallback: no CUDA device is visible, so this run uses the CPU. "
            "It is the same script and will be much slower. On the Acer Nitro, check nvidia-smi "
            "and install the cu121 wheel if the GPU should be used."
        )
    else:
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")

    learning_rate = args.lr if args.lr is not None else (1e-3 if args.freeze_backbone else 3e-4)
    model = build_model(args.arch, pretrained=True)
    if args.freeze_backbone:
        freeze_backbone(model)
        print("Backbone frozen. Only the classifier head will train.")
    model.to(device)

    train_loader = make_loader(train_rows, True, args.batch_size, args.workers, device.type)
    val_loader = make_loader(val_rows, False, args.batch_size, args.workers, device.type)
    optimiser = torch.optim.AdamW(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=learning_rate,
        weight_decay=0.01,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimiser, T_max=max(args.epochs, 1))
    criterion = torch.nn.CrossEntropyLoss()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    command = " ".join(shlex.quote(part) for part in sys.argv)
    (run_dir / "command.txt").write_text(command + "\n", encoding="utf-8")
    config = {
        "arch": args.arch,
        "pretrained": "imagenet",
        "input_size": INPUT_SIZE,
        "mean": MEAN,
        "std": STD,
        "resize_eval": "shorter_side_then_center_crop",
        "augmentations": AUGMENTATIONS,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": learning_rate,
        "weight_decay": 0.01,
        "optimizer": "AdamW",
        "schedule": "cosine",
        "patience": args.patience,
        "seed": args.seed,
        "freeze_backbone": args.freeze_backbone,
        "labels": LABELS,
        "device": device.type,
        "n_train": len(train_rows),
        "n_val": len(val_rows),
        "command": command,
    }
    (run_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    metrics_path = run_dir / "metrics.csv"
    with open(metrics_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["epoch", "train_loss", "val_loss", "val_accuracy", "val_macro_f1", "lr"],
            lineterminator="\n",
        )
        writer.writeheader()

    best_loss = None
    bad_epochs = 0
    best_epoch = 0
    for epoch in range(1, args.epochs + 1):
        train_stats = run_epoch(model, train_loader, device, optimiser, criterion, train=True)
        val_stats = run_epoch(model, val_loader, device, None, criterion, train=False)
        scheduler.step()
        current_lr = optimiser.param_groups[0]["lr"]
        print(
            f"epoch {epoch}: train_loss={train_stats['loss']:.4f} "
            f"val_loss={val_stats['loss']:.4f} val_acc={val_stats['accuracy']:.4f} "
            f"val_macro_f1={val_stats['macro_f1']:.4f}"
        )
        with open(metrics_path, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["epoch", "train_loss", "val_loss", "val_accuracy", "val_macro_f1", "lr"],
                lineterminator="\n",
            )
            writer.writerow(
                {
                    "epoch": epoch,
                    "train_loss": train_stats["loss"],
                    "val_loss": val_stats["loss"],
                    "val_accuracy": val_stats["accuracy"],
                    "val_macro_f1": val_stats["macro_f1"],
                    "lr": current_lr,
                }
            )
        payload = {
            "arch": args.arch,
            "labels": LABELS,
            "state_dict": model.state_dict(),
            "epoch": epoch,
            "val_loss": val_stats["loss"],
            "seed": args.seed,
        }
        torch.save(payload, run_dir / "last.pt")
        improved = best_loss is None or val_stats["loss"] < best_loss
        if improved:
            best_loss = val_stats["loss"]
            best_epoch = epoch
            bad_epochs = 0
            torch.save(payload, run_dir / "best.pt")
        else:
            bad_epochs += 1
            if bad_epochs >= args.patience:
                print(
                    f"Early stop: validation loss rose for {bad_epochs} epoch(s). "
                    f"Best epoch was {best_epoch} with val_loss={best_loss:.4f}."
                )
                break

    try:
        best = torch.load(run_dir / "best.pt", map_location=device, weights_only=False)
    except TypeError:
        best = torch.load(run_dir / "best.pt", map_location=device)
    model.load_state_dict(best["state_dict"])
    calibration = calibrate(model, val_loader, device)
    (run_dir / "calibration.json").write_text(json.dumps(calibration, indent=2) + "\n", encoding="utf-8")
    if calibration.get("temperature") is None:
        print("Calibration did not run because the validation loader was empty.")
    else:
        print(
            f"Temperature {calibration['temperature']:.4f}. "
            f"Threshold {calibration['threshold']}. "
            f"Val accuracy on accepted images {calibration['accuracy']}. "
            f"Coverage {calibration['coverage']}. "
            f"Target met: {calibration['target_met']}."
        )
    print(f"Run directory: {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
