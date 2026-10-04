"""Frozen split and held-out rows for the research harness.

v1 was trained on the split in ml/manifest.csv. manifest.py cannot regenerate that split
(it iterates a set of strings, and string hashing is randomised per process), so this module
copies it once into research/manifest_frozen.csv and never changes its train/val/test rows.
Held-out rows (Uganda, RoCoLe, wild) are rebuilt from what is on disk and merged in without
touching the pool.

  python research/data.py freeze                       # copy ml/manifest.csv once
  python research/data.py merge                        # refresh held-out rows in the frozen file
  python research/data.py merge --write-ml-manifest    # also update ml/manifest.csv (pool unchanged)
  python research/data.py counts

Pure Python (manifest.py is imported only by `merge`, for its Uganda and RoCoLe label mapping).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ML = HERE.parent
if str(ML) not in sys.path:
    sys.path.insert(0, str(ML))

from common import LABELS, RAW, ROOT  # noqa: E402  (common.py is plain pathlib)

FROZEN = HERE / "manifest_frozen.csv"
FROZEN_META = HERE / "frozen.json"
FIELDS = ["path", "source", "original_label", "label", "split", "phash", "cluster_id", "synthetic"]
HELDOUT_SOURCES = ("uganda", "rocole", "wild")
POOL_SPLITS = ("train", "val", "test")
WILD_CSV = ROOT / "kb" / "research" / "wild_set.csv"
WILD_TAXA = {"hemileia": "rust", "cercospora": "cercospora", "leucoptera": "miner", "phoma": "phoma"}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    tmp.replace(path)


def split_hash(rows: list[dict], split: str) -> str:
    paths = sorted(r["path"] for r in rows if r.get("split") == split)
    return hashlib.sha256("\n".join(paths).encode("utf-8")).hexdigest()


def pool_signature(rows: list[dict]) -> dict:
    return {s: split_hash(rows, s) for s in POOL_SPLITS}


def is_heldout(r: dict) -> bool:
    return r.get("source") in HELDOUT_SOURCES or str(r.get("split", "")).startswith("heldout")


def freeze() -> dict:
    """Copy ml/manifest.csv once. Later calls only report drift."""
    src = ML / "manifest.csv"
    if not src.exists():
        raise SystemExit("ml/manifest.csv missing: run manifest.py once (v1's split) before the research queue")
    cur = read_csv(src)
    if not FROZEN.exists():
        shutil.copy2(src, FROZEN)
        meta = {
            "frozen_at": datetime.now().isoformat(timespec="seconds"),
            "source_file": "app/ml/manifest.csv",
            "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "pool": pool_signature(cur),
            "counts": dict(Counter(r["split"] for r in cur)),
            "note": "v1's split. Never regenerate; held-out rows may be refreshed by `data.py merge`.",
        }
        FROZEN_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return {**meta, "drift": False}
    meta = json.loads(FROZEN_META.read_text(encoding="utf-8"))
    drift = pool_signature(cur) != meta["pool"]
    return {**meta, "drift": drift}


def read_frozen() -> list[dict]:
    if not FROZEN.exists():
        raise SystemExit("research/manifest_frozen.csv missing: run `python research/data.py freeze`")
    return read_csv(FROZEN)


def pool_rows(rows: list[dict], splits: set[str]) -> list[dict]:
    out = []
    for r in rows:
        if r["split"] in splits and r["label"] in LABELS and not is_heldout(r):
            out.append(r)
    return out


def existing(rows: list[dict]) -> list[dict]:
    return [r for r in rows if (ROOT / r["path"]).exists()]


def small(rows: list[dict], per_group: int, seed: int) -> list[dict]:
    """Tiny stratified subset for smoke runs: per (label, is_bracol) group."""
    rng = random.Random(seed)
    groups: dict[tuple[str, bool], list[dict]] = {}
    for r in rows:
        groups.setdefault((r["label"], r["source"] == "bracol"), []).append(r)
    out = []
    for key in sorted(groups):
        g = groups[key][:]
        rng.shuffle(g)
        out.extend(existing(g[: per_group * 3])[:per_group])
    return out


def _wild_rows() -> list[dict]:
    if not WILD_CSV.exists():
        return []
    rows = []
    for w in read_csv(WILD_CSV):
        rel = (w.get("local_file") or "").replace("\\", "/")
        if not rel or not (ROOT / rel).exists():
            continue
        hint = (w.get("label_hint") or "").lower()
        taxon = (w.get("taxon") or "").lower()
        label = next((lab for key, lab in WILD_TAXA.items() if key in taxon or key in hint), None)
        if label is None and hint.startswith("healthy"):
            label = "healthy"
        if label is None:
            continue
        rows.append({"path": rel, "source": "wild", "original_label": w.get("label_hint", ""),
                     "label": label, "split": "heldout_wild", "phash": "", "cluster_id": "", "synthetic": "0"})
    return rows


def fresh_heldout_rows() -> list[dict]:
    """Uganda and RoCoLe rows from manifest.py's own label mapping, plus labelled wild photos."""
    import manifest  # ml/manifest.py; imports PIL, imagehash, tqdm (all in the jani env)

    rows = []
    for r in manifest.collect_rows():
        if r["source"] in ("uganda", "rocole"):
            rows.append({"path": r["path"], "source": r["source"], "original_label": r["original_label"],
                         "label": r["label"], "split": f"heldout_{r['source']}", "phash": "",
                         "cluster_id": "", "synthetic": r.get("synthetic", "0")})
    return rows + _wild_rows()


def merge_heldout(write_ml_manifest: bool = False, fresh: list[dict] | None = None) -> dict:
    frozen = read_frozen()
    before = pool_signature(frozen)
    keep = [r for r in frozen if not is_heldout(r)]
    fresh = fresh_heldout_rows() if fresh is None else fresh
    merged = keep + fresh
    after = pool_signature(merged)
    if before != after:
        raise SystemExit("BUG: merging held-out rows changed the pool split; nothing written")
    write_csv(FROZEN, merged)
    out = {"heldout": {s: dict(Counter(r["label"] for r in fresh if r["source"] == s)) for s in HELDOUT_SOURCES},
           "pool_unchanged": True, "ml_manifest_written": False}
    if write_ml_manifest:
        cur = read_csv(ML / "manifest.csv")
        if pool_signature(cur) != before:
            raise SystemExit("ml/manifest.csv no longer has v1's split (manifest.py re-run?); not overwriting it")
        write_csv(ML / "manifest.csv", merged)
        out["ml_manifest_written"] = True
    return out


def counts() -> dict:
    rows = read_frozen()
    c = Counter((r["split"], r["source"]) for r in rows)
    return {f"{k[0]}/{k[1]}": v for k, v in sorted(c.items())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["freeze", "merge", "counts"])
    ap.add_argument("--write-ml-manifest", action="store_true")
    a = ap.parse_args()
    if a.cmd == "freeze":
        print(json.dumps(freeze(), indent=2))
    elif a.cmd == "merge":
        freeze()
        print(json.dumps(merge_heldout(a.write_ml_manifest), indent=2))
    else:
        print(json.dumps(counts(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
