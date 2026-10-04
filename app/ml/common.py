"""Shared paths, labels and preprocessing for the Jani leaf model."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ML = ROOT / "app" / "ml"
RAW = ROOT / "data_raw"
PUBLIC_MODEL = ROOT / "app" / "public" / "model"
DOCS = ROOT / "app" / "docs"

LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]
LABEL_TO_IDX = {n: i for i, n in enumerate(LABELS)}
SEED = 42

# ImageNet, 0-1 range, NCHW. Engine must match this exactly.
INPUT_SIZE = 224
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# After near-duplicate grouping, cap the two oversized JMuBEN2 classes.
CAP_AFTER_DEDUPE = {"healthy": 9000, "miner": 9000}

# Held-out sets are never used for train or val.
HELDOUT_SOURCES = {"uganda", "rocole"}
