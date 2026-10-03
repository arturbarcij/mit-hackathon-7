"""Build app/ml/manifest.csv from data_raw/.

Columns: path (relative to data_raw), source, original_label, label, split, dup_group.

Leakage control: perceptual hash (pHash, 64 bit, same algorithm as imagehash.phash). Two images are
near-duplicates when the Hamming distance is 6 or less between one image and any of the 8 flip or
90-degree-rotation variants of the other (JMuBEN and Uganda contain flipped and rotated copies).
Near-duplicates are grouped with union-find, and whole groups go to one split.
Train sets get a 70/15/15 split stratified by class; held-out sets get split=heldout_<name>.

Usage: python app/ml/build_manifest.py [--workers 4]
"""
import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.fftpack import dct

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data_raw"
OUT = Path(__file__).resolve().parent / "manifest.csv"
STATS = Path(__file__).resolve().parent / "manifest_stats.json"
CLASSES = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]
MAX_HAMMING = 6
IMG_EXT = (".jpg", ".jpeg", ".png")
SEED = 42


def images(d: Path):
    return sorted(p for p in d.rglob("*") if p.suffix.lower() in IMG_EXT and ".bak." not in p.name)


def collect():
    """Yield (abs path, source, original label, our label or None, held-out name or None)."""
    rows = []
    jm = {"Cerscospora": "cercospora", "Leaf rust": "rust", "Phoma": "phoma", "Healthy": "healthy", "Miner": "miner"}
    for ds in ("jmuben", "jmuben2"):
        for p in images(DATA_RAW / ds / "extracted"):
            orig = p.parent.name
            rows.append((p, ds, orig, jm.get(orig), None))

    bracol_dir = next((DATA_RAW / "bracol").rglob("dataset.csv"), None)
    if bracol_dir:
        leaf = bracol_dir.parent
        code = {"0": "healthy", "1": "miner", "2": "rust", "3": "phoma", "4": "cercospora"}
        for r in csv.DictReader(open(bracol_dir)):
            p = leaf / "images" / f"{r['id']}.jpg"
            if p.exists():
                rows.append((p, "bracol", f"predominant_stress={r['predominant_stress']}",
                             code.get(r["predominant_stress"]), None))

    for p in images(DATA_RAW / "plantdoc" / "images"):
        rows.append((p, "plantdoc", p.parent.name, "not_leaf", None))

    ug = {"Health leaves": "healthy", "leaf rust": "rust", "phoma": "phoma"}
    for p in images(DATA_RAW / "uganda" / "extracted"):
        rows.append((p, "uganda", p.parent.name, ug.get(p.parent.name), "uganda"))

    rocole_csv = next((DATA_RAW / "rocole").rglob("RoCoLE-csv.csv"), None)
    if rocole_csv:
        photos = {p.name: p for p in images(DATA_RAW / "rocole")}
        for name, orig in rocole_labels(rocole_csv).items():
            if name in photos:
                lab = "healthy" if orig == "healthy" else "rust" if orig.startswith("rust") else None
                rows.append((photos[name], "rocole", orig, lab, "rocole"))
    return rows


def rocole_labels(path: Path) -> dict[str, str]:
    """RoCoLe CSV holds one row per image with a JSON-ish label column; return {file name: class}."""
    out = {}
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("External ID") or r.get("filename") or "").strip()
            blob = r.get("Label") or ""
            m = re.search(r'"classification"\s*:\s*"([^"]+)"', blob)
            if name and m:
                out[name] = m.group(1).strip().lower().replace(" ", "_")
    return out


def phash_variants(path: str) -> list[int] | None:
    try:
        img = Image.open(path).convert("L").resize((32, 32), Image.Resampling.LANCZOS)
    except Exception:
        return None
    a = np.asarray(img, dtype=np.float64)
    out = []
    for k in range(4):
        r = np.rot90(a, k)
        for v in (r, r[:, ::-1]):
            d = dct(dct(v, axis=0), axis=1)[:8, :8]
            bits = (d > np.median(d)).flatten()
            out.append(int("".join("1" if b else "0" for b in bits), 2))
    return out


def find(parent, i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def to_signs(hs: list[int]):
    import torch
    bits = [[(h >> (63 - k)) & 1 for k in range(64)] for h in hs]
    return torch.tensor(bits, dtype=torch.float32) * 2 - 1


def group(hashes: list[list[int]], chunk: int = 256) -> tuple[list[int], int]:
    """Union-find over near-duplicates. With +-1 bit vectors, Hamming = (64 - dot) / 2, so a matrix
    product compares every image with all 8 variants of every other image at once."""
    import torch
    torch.set_num_threads(4)
    n = len(hashes)
    query = to_signs([h[0] for h in hashes])
    db = to_signs([h for hs in hashes for h in hs])
    owner = torch.arange(n).repeat_interleave(8)
    min_dot = 64 - 2 * MAX_HAMMING
    parent = list(range(n))
    pairs = 0
    for s in range(0, n, chunk):
        hit = (query[s:s + chunk] @ db.T) >= min_dot
        qi, dj = hit.nonzero(as_tuple=True)
        qi = qi + s
        oj = owner[dj]
        keep = qi != oj
        for i, j in set(zip(qi[keep].tolist(), oj[keep].tolist())):
            pairs += 1
            ri, rj = find(parent, i), find(parent, j)
            if ri != rj:
                parent[rj] = ri
    return [find(parent, i) for i in range(n)], pairs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    rows = collect()
    print(f"collected {len(rows)} images")
    cache_file = DATA_RAW / "phash_cache.json"
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    todo = [str(r[0]) for r in rows if str(r[0]) not in cache]
    with ProcessPoolExecutor(a.workers) as ex:
        for p, h in zip(todo, ex.map(phash_variants, todo, chunksize=256)):
            cache[p] = h
    cache_file.write_text(json.dumps(cache))
    hashes = [cache[str(r[0])] for r in rows]
    print("hashed")
    keep = [i for i, h in enumerate(hashes) if h is not None]
    unreadable = len(rows) - len(keep)
    rows = [rows[i] for i in keep]
    hashes = [hashes[i] for i in keep]

    roots, pairs = group(hashes)
    print(f"{pairs} near-duplicate pairs")
    members = defaultdict(list)
    for i, r in enumerate(roots):
        members[r].append(i)
    dup_groups = {r: m for r, m in members.items() if len(m) > 1}

    is_train = [r[4] is None for r in rows]
    stats = {"unreadable": unreadable, "max_hamming": MAX_HAMMING, "near_duplicate_pairs": pairs}
    stats["dup_groups_train"] = sum(1 for m in dup_groups.values() if all(is_train[i] for i in m))
    stats["dup_images_train"] = sum(len(m) for m in dup_groups.values() if all(is_train[i] for i in m))
    stats["dup_groups_heldout_only"] = sum(1 for m in dup_groups.values() if not any(is_train[i] for i in m))
    mixed = [m for m in dup_groups.values() if any(is_train[i] for i in m) and not all(is_train[i] for i in m)]
    stats["dup_groups_spanning_train_and_heldout"] = len(mixed)
    stats["heldout_images_duplicating_train"] = sum(1 for m in mixed for i in m if not is_train[i])
    stats["largest_groups"] = sorted((len(m) for m in dup_groups.values()), reverse=True)[:10]
    label_conflict = [m for m in dup_groups.values() if len({rows[i][3] for i in m}) > 1]
    stats["dup_groups_with_conflicting_labels"] = len(label_conflict)

    # Split train groups 70/15/15 per class (group class = majority label), greedily by image count.
    split = [None] * len(rows)
    rng = random.Random(SEED)
    train_groups = defaultdict(list)
    for r, m in members.items():
        tm = [i for i in m if is_train[i] and rows[i][3] is not None]
        if tm:
            cls = Counter(rows[i][3] for i in tm).most_common(1)[0][0]
            train_groups[cls].append(tm)
    for cls, groups in train_groups.items():
        rng.shuffle(groups)
        groups.sort(key=len, reverse=True)  # place big groups first so they land in train
        total = sum(len(g) for g in groups)
        target = {"train": 0.70 * total, "val": 0.15 * total, "test": 0.15 * total}
        filled = {"train": 0, "val": 0, "test": 0}
        for g in groups:
            s = max(target, key=lambda k: (target[k] - filled[k]) / target[k])
            for i in g:
                split[i] = s
            filled[s] += len(g)
    overlap = {i for m in mixed for i in m if not is_train[i]}
    for i, r in enumerate(rows):
        if i in overlap:
            split[i] = "excluded_heldout_dup_of_train"  # e.g. Uganda phoma images copied from JMuBEN
        elif r[4] is not None:
            split[i] = f"heldout_{r[4]}"
        elif split[i] is None:
            split[i] = "excluded"  # train-set image whose label we do not use (e.g. BRACOL mixed stress)

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "source", "original_label", "label", "split", "dup_group"])
        for i, r in enumerate(rows):
            g = roots[i] if roots[i] in dup_groups else ""
            w.writerow([r[0].relative_to(DATA_RAW).as_posix(), r[1], r[2], r[3] or "unmapped", split[i], g])

    counts = Counter((split[i], rows[i][3] or "unmapped") for i in range(len(rows)))
    table = {s: {c: counts.get((s, c), 0) for c in CLASSES + ["unmapped"]} for s in sorted({k[0] for k in counts})}
    stats["counts"] = table
    stats["by_source"] = dict(Counter(r[1] for r in rows))
    STATS.write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
