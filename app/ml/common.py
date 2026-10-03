"""Shared constants for the Jani leaf classifier.

Heavy libraries (torch, timm, onnx, pillow, numpy) are imported inside the
functions that need them so this module imports with the Python 3.11 standard
library alone.
"""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
INPUT_SIZE = 224
ONNX_OPSET = 17
MAX_MODEL_BYTES = 5 * 1024 * 1024
SEED = 42
HAMMING_MAX = 6
SPLIT_FRACTIONS = {"train": 0.70, "val": 0.15, "test": 0.15}
SPLITS = ("train", "val", "test")
HELD_OUT_SPLIT = "heldout"
HELD_OUT_SOURCES = {"Uganda", "RoCoLe"}

MANIFEST_COLUMNS = [
    "path",
    "source",
    "original_label",
    "label",
    "split",
    "out_of_scope",
]

# BRACOL lists both names. Jani has one cercospora class. See README.md.
BROWN_LEAF_SPOT_ASSUMPTION = (
    "Assumption: BRACOL 'brown leaf spot' is mapped to cercospora. "
    "Coffee brown eye spot is caused by Cercospora coffeicola, and Jani has "
    "one cercospora class. BRACOL 'cercospora leaf spot' maps to that same "
    "class, so the two source labels are merged. BRACOL has no phoma class. "
    "DATASETS.md could not confirm this from the zip. Check the label file "
    "before trusting a metric that depends on it."
)

UGANDA_PREFIX_ASSUMPTION = (
    "Assumption: the Uganda record does not state which file-name prefix is "
    "which class. Counted prefixes match the stated class sizes, so "
    "manifest.py uses 1_ as healthy (counted 1179, stated 1179), 2300_ as "
    "phoma (counted 1110, stated 1110) and 1200_ as rust (counted 1033, "
    "stated coffee leaf rust 1023, ten extra files). A folder name or a label "
    "file wins over this prefix rule."
)

MITE_POLICY = (
    "RoCoLe red spider mite stays in original_label. The label column is "
    "not_leaf so it stays inside the six class names, and out_of_scope is "
    "red_spider_mite. Those rows are held out, they are not trained, and they "
    "are not counted as the not_leaf class. They are never labelled rust, "
    "even when a rust level is also present."
)

ML_DIR = Path(__file__).resolve().parent
APP_DIR = ML_DIR.parent
WORKSPACE_DIR = APP_DIR.parent
DATA_RAW = WORKSPACE_DIR / "data_raw"
PUBLIC_MODEL = APP_DIR / "public" / "model"
RUNS_DIR = ML_DIR / "runs"
MANIFEST_PATH = ML_DIR / "manifest.csv"
METRICS_PATH = ML_DIR / "metrics.json"
DATASETS_PATH = ML_DIR / "datasets.json"
PARITY_DIR = ML_DIR / "parity_samples"
DOCS_DIR = APP_DIR / "docs"

MODEL_CARD_KEYS = (
    "version",
    "labels",
    "input",
    "temperature",
    "threshold",
    "sha256",
    "bytes",
)
INPUT_KEYS = ("size", "resize", "mean", "std", "layout", "range")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def softmax(logits: list[float], temperature: float = 1.0) -> list[float]:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    scaled = [value / temperature for value in logits]
    peak = max(scaled)
    exps = [math.exp(value - peak) for value in scaled]
    total = sum(exps)
    return [value / total for value in exps]


def choose_threshold(
    confidences: list[float],
    correct: list[bool],
    target: float = 0.95,
) -> dict:
    """Pick the lowest confidence cut whose accepted accuracy is at least target.

    Acceptance is confidence >= threshold. Among cuts that meet the target,
    the one with the highest coverage is kept. If none meet it, the cut with
    the best accuracy is returned and target_met is false. No figure is invented
    for an empty list.
    """
    if len(confidences) != len(correct):
        raise ValueError("confidences and correct must be the same length")
    n = len(confidences)
    if n == 0:
        return {
            "threshold": None,
            "coverage": 0.0,
            "accuracy": None,
            "target_met": False,
            "target": target,
            "n": 0,
            "n_accepted": 0,
        }
    distinct = sorted(set(confidences), reverse=True)
    meeting = None
    best = None
    for threshold in distinct:
        accepted = [i for i in range(n) if confidences[i] >= threshold]
        n_accepted = len(accepted)
        accuracy = sum(1 for i in accepted if correct[i]) / n_accepted
        coverage = n_accepted / n
        candidate = {
            "threshold": float(threshold),
            "coverage": coverage,
            "accuracy": accuracy,
            "target_met": accuracy >= target,
            "target": target,
            "n": n,
            "n_accepted": n_accepted,
        }
        if accuracy >= target:
            meeting = candidate
        if best is None or (accuracy, coverage) > (best["accuracy"], best["coverage"]):
            best = candidate
    return meeting if meeting is not None else best


def validate_model_card(card: dict) -> list[str]:
    """Return a list of problems. An empty list means the card matches the schema."""
    errors: list[str] = []
    if set(card) != set(MODEL_CARD_KEYS):
        errors.append(
            "model.json keys must be exactly "
            + ", ".join(MODEL_CARD_KEYS)
        )
        return errors
    version = card["version"]
    if not isinstance(version, str) or re.fullmatch(r"v\d+-\d{4}-\d{2}-\d{2}", version) is None:
        errors.append("version must look like v1-2026-10-04")
    if card["labels"] != LABELS:
        errors.append("labels must be the six fixed class names in order")
    spec = card["input"]
    if not isinstance(spec, dict) or set(spec) != set(INPUT_KEYS):
        errors.append("input keys must be size, resize, mean, std, layout, range")
    else:
        if spec["size"] != INPUT_SIZE:
            errors.append("input.size must be 224")
        if spec["resize"] != "shorter_side_then_center_crop":
            errors.append("input.resize must be shorter_side_then_center_crop")
        if spec["layout"] != "NCHW":
            errors.append("input.layout must be NCHW")
        if spec["range"] != "0-1":
            errors.append("input.range must be 0-1")
        if not _close_list(spec["mean"], MEAN) or not _close_list(spec["std"], STD):
            errors.append("input mean or std does not match ImageNet values")
    temperature = card["temperature"]
    threshold = card["threshold"]
    if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
        errors.append("temperature must be a number")
    elif not 0 < float(temperature) <= 100:
        errors.append("temperature must be in (0, 100]")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        errors.append("threshold must be a number")
    elif not 0 <= float(threshold) <= 1:
        errors.append("threshold must be in [0, 1]")
    sha = card["sha256"]
    if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{64}", sha) is None:
        errors.append("sha256 must be 64 lowercase hex characters")
    size = card["bytes"]
    if not isinstance(size, int) or isinstance(size, bool):
        errors.append("bytes must be an integer")
    elif not 1 <= size <= MAX_MODEL_BYTES:
        errors.append(f"bytes must be between 1 and {MAX_MODEL_BYTES}")
    return errors


def _close_list(left, right, tol: float = 1e-9) -> bool:
    if not isinstance(left, list) or len(left) != len(right):
        return False
    return all(isinstance(a, (int, float)) and abs(float(a) - float(b)) <= tol for a, b in zip(left, right))


def shorter_side_center_crop(image, size: int = INPUT_SIZE):
    """Resize so the shorter side is `size`, then centre-crop. Bilinear."""
    from PIL import Image

    img = image.convert("RGB")
    width, height = img.size
    if width < 1 or height < 1:
        raise ValueError("image has no pixels")
    if width < height:
        new_w = size
        new_h = max(size, int(round(height * (size / width))))
    else:
        new_h = size
        new_w = max(size, int(round(width * (size / height))))
    img = img.resize((new_w, new_h), Image.BILINEAR)
    left = max(0, (img.size[0] - size) // 2)
    top = max(0, (img.size[1] - size) // 2)
    return img.crop((left, top, left + size, top + size))


def to_nchw(image, size: int = INPUT_SIZE):
    """Return float32 NCHW normalised with ImageNet mean and std. Range before norm is 0-1."""
    import numpy as np

    crop = shorter_side_center_crop(image, size)
    array = np.asarray(crop).astype("float32") / 255.0
    mean = np.asarray(MEAN, dtype="float32")
    std = np.asarray(STD, dtype="float32")
    array = (array - mean) / std
    array = np.transpose(array, (2, 0, 1))
    return array[None, ...]


def load_manifest(path: Path | None = None) -> list[dict]:
    import csv

    path = path or MANIFEST_PATH
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in MANIFEST_COLUMNS if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"manifest is missing columns: {', '.join(missing)}")
        return list(reader)


def image_path(row: dict) -> Path:
    raw = Path(row["path"])
    if raw.is_file():
        return raw
    return DATA_RAW / row["path"]


def is_held_out_source(source: str) -> bool:
    return source in HELD_OUT_SOURCES


def is_trainable(row: dict) -> bool:
    return (
        row.get("split") == "train"
        and (row.get("out_of_scope") or "") == ""
        and row.get("label") in LABELS
        and not is_held_out_source(row.get("source", ""))
    )


def assert_not_under_docs(path: Path) -> None:
    resolved = path.resolve()
    docs = DOCS_DIR.resolve()
    if resolved == docs or docs in resolved.parents:
        raise SystemExit(f"Refusing to write under {docs}: {resolved}")


def band_keys(value: int, n_bands: int, n_bits: int = 64) -> list[int]:
    keys = [0] * n_bands
    shifts = [0] * n_bands
    for bit in range(n_bits):
        band = bit % n_bands
        if (value >> bit) & 1:
            keys[band] |= 1 << shifts[band]
        shifts[band] += 1
    return keys


def latest_best_checkpoint() -> Path | None:
    """Lexicographically latest runs/<timestamp>/best.pt, or None."""
    if not RUNS_DIR.is_dir():
        return None
    found = sorted(path for path in RUNS_DIR.glob("*/best.pt") if path.is_file())
    return found[-1] if found else None


def cluster_hashes(hashes: list[int | None], max_dist: int = HAMMING_MAX) -> list[int]:
    """Cluster integer perceptual hashes. Hamming distance <= max_dist shares a cluster.

    Uses max_dist + 1 bands. Two codes within that distance must share a band,
    so the search is exact for the radius, not a sample. None stays a singleton
    until the caller unions it for another reason.
    """
    n = len(hashes)
    parent = list(range(n))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        ra, rb = find(left), find(right)
        if ra != rb:
            parent[rb] = ra

    by_hash: dict[int, list[int]] = {}
    for index, value in enumerate(hashes):
        if value is None:
            continue
        by_hash.setdefault(int(value), []).append(index)
    reps: list[tuple[int, int]] = []
    for value, members in by_hash.items():
        for member in members[1:]:
            union(members[0], member)
        reps.append((members[0], value))

    n_bands = max_dist + 1
    buckets: list[dict[int, list[tuple[int, int]]]] = [dict() for _ in range(n_bands)]
    for index, value in reps:
        for band, key in enumerate(band_keys(value, n_bands)):
            buckets[band].setdefault(key, []).append((index, value))
    for band in range(n_bands):
        for group in buckets[band].values():
            if len(group) < 2:
                continue
            for a in range(len(group)):
                ia, ha = group[a]
                for b in range(a + 1, len(group)):
                    ib, hb = group[b]
                    if (ha ^ hb).bit_count() <= max_dist:
                        union(ia, ib)
    return [find(i) for i in range(n)]
