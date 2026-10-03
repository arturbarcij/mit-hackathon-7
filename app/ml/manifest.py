#!/usr/bin/env python3
"""Build app/ml/manifest.csv from data_raw.

Columns: path, source, original_label, label, split, out_of_scope.
Labels: healthy, rust, cercospora, phoma, miner, not_leaf.

Uganda and RoCoLe are always split heldout. Near-duplicate perceptual hashes
(Hamming distance 6 or less) stay in the same split, as do the four RoCoLe
images of one plant. This script does nothing on import.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import (
    BROWN_LEAF_SPOT_ASSUMPTION,
    DATA_RAW,
    HAMMING_MAX,
    HELD_OUT_SOURCES,
    HELD_OUT_SPLIT,
    LABELS,
    MANIFEST_COLUMNS,
    MANIFEST_PATH,
    MITE_POLICY,
    SEED,
    SPLIT_FRACTIONS,
    SPLITS,
    UGANDA_PREFIX_ASSUMPTION,
    choose_threshold,
    cluster_hashes,
    softmax,
    validate_model_card,
)

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
SKIP_DIR_NAMES = {
    "train",
    "test",
    "val",
    "validation",
    "images",
    "image",
    "dataset",
    "extracted",
    "files",
    "__macosx",
}
SOURCE_DIRS = [
    ("JMuBEN", DATA_RAW / "train" / "jmuben"),
    ("JMuBEN2", DATA_RAW / "train" / "jmuben2"),
    ("BRACOL", DATA_RAW / "train" / "bracol"),
    ("PlantDoc", DATA_RAW / "negatives" / "plantdoc"),
    ("backgrounds", DATA_RAW / "negatives" / "backgrounds"),
    ("Uganda", DATA_RAW / "heldout" / "uganda"),
    ("RoCoLe", DATA_RAW / "heldout" / "rocole"),
]
ALIASES = {
    "healthy": "healthy",
    "healthy leaf": "healthy",
    "rust": "rust",
    "leaf rust": "rust",
    "coffee leaf rust": "rust",
    "clr": "rust",
    "cercospora": "cercospora",
    "cerscospora": "cercospora",
    "cercospora leaf spot": "cercospora",
    "brown leaf spot": "cercospora",
    "brown eye spot": "cercospora",
    "brown eyespot": "cercospora",
    "phoma": "phoma",
    "phoma leaf spot": "phoma",
    "miner": "miner",
    "leaf miner": "miner",
    "leafminer": "miner",
}
PLANT_RE = re.compile(r"C(\d+)P(\d+)", re.IGNORECASE)
NEGATIVE_TEXT = {"0", "no", "false", "absent", "none", "n", "nan", ""}


def norm_key(text: str) -> str:
    cleaned = text.lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def alias(text: str) -> str | None:
    return ALIASES.get(norm_key(text))


def uganda_prefix_label(filename: str) -> str | None:
    """Inferred prefix map. Folder names and label files are preferred by the caller."""
    if filename.startswith("2300_") or filename.startswith("2300-"):
        return "phoma"
    if filename.startswith("1200_") or filename.startswith("1200-"):
        return "rust"
    if filename.startswith("1_") or filename.startswith("1-"):
        return "healthy"
    return None


def plant_id_from_name(filename: str) -> str:
    match = PLANT_RE.search(filename)
    if not match:
        return ""
    return f"C{int(match.group(1))}P{int(match.group(2))}"


def _truthy(value: object) -> bool:
    text = str(value).strip().lower()
    return text not in NEGATIVE_TEXT


def classify_rocole(raw_label: str, mite: bool, rust_level: int | None) -> dict | None:
    """Map one RoCoLe image. Mite rows are never rust."""
    if mite:
        original = raw_label.strip() or "red spider mite"
        if rust_level is not None and "rust" not in original.lower():
            original = f"{original}; rust level {rust_level}"
        return {
            "original_label": original,
            "label": "not_leaf",
            "out_of_scope": "red_spider_mite",
        }
    if rust_level is not None and rust_level >= 1:
        return {
            "original_label": raw_label.strip() or f"rust level {rust_level}",
            "label": "rust",
            "out_of_scope": "",
        }
    mapped = alias(raw_label) if raw_label else None
    if rust_level == 0 or mapped == "healthy":
        return {
            "original_label": raw_label.strip() or "healthy",
            "label": "healthy",
            "out_of_scope": "",
        }
    if mapped in {"healthy", "rust"}:
        return {"original_label": raw_label.strip(), "label": mapped, "out_of_scope": ""}
    return None


def _parse_level(text: str) -> int | None:
    stripped = text.strip().lower()
    if stripped.isdigit():
        number = int(stripped)
        if 0 <= number <= 4:
            return number
    match = re.search(r"\b([0-4])\b", stripped)
    if match and any(token in stripped for token in ("rust", "level", "sever")):
        return int(match.group(1))
    return None


def rocole_from_row(row: dict) -> dict | None:
    raw_parts = []
    mite = False
    rust_level = None
    label_text = ""
    for key, value in row.items():
        key_n = norm_key(str(key))
        value_s = str(value).strip()
        if key_n in {"filename", "file", "image", "img", "name", "path"}:
            continue
        raw_parts.append(f"{key}={value_s}")
        if "mite" in key_n or "spider" in key_n:
            if _truthy(value_s) and "no " not in value_s and value_s.lower() not in NEGATIVE_TEXT:
                mite = True
        if "mite" in value_s.lower() or "red spider" in value_s.lower():
            mite = True
        if any(token in key_n for token in ("rust", "sever", "level")):
            parsed = _parse_level(value_s)
            if parsed is not None:
                rust_level = parsed if rust_level is None else max(rust_level, parsed)
        if key_n in {"label", "class", "classes", "state", "condition", "diagnosis"}:
            label_text = value_s
    if not mite and label_text and ("mite" in label_text.lower() or "spider" in label_text.lower()):
        mite = True
    original = label_text or "; ".join(raw_parts)
    return classify_rocole(original, mite, rust_level)


def classes_from_table_row(row: dict) -> list[str]:
    """Read a BRACOL-style row. Multi-hot headers win over free text."""
    from_headers = []
    for key, value in row.items():
        mapped = alias(str(key))
        if mapped and _truthy(value):
            from_headers.append(mapped)
    if from_headers:
        return list(dict.fromkeys(from_headers))
    found = []
    for value in row.values():
        mapped = alias(str(value))
        if mapped:
            found.append(mapped)
    return list(dict.fromkeys(found))


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        return list(csv.DictReader(handle, dialect=dialect))


def _read_xlsx(path: Path) -> list[dict]:
    import xml.etree.ElementTree as ET
    import zipfile

    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    tag = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", ns):
                texts = [node.text or "" for node in item.iter(f"{tag}t")]
                shared.append("".join(texts))
        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in archive.namelist():
            sheets = [name for name in archive.namelist() if name.startswith("xl/worksheets/sheet")]
            if not sheets:
                return []
            sheet_name = sheets[0]
        root = ET.fromstring(archive.read(sheet_name))
        grid = []
        for row in root.findall("m:sheetData/m:row", ns):
            cells: dict[int, str] = {}
            for cell in row.findall("m:c", ns):
                ref = cell.attrib.get("r", "")
                letters = "".join(ch for ch in ref if ch.isalpha())
                index = 0
                for ch in letters:
                    index = index * 26 + (ord(ch.upper()) - 64)
                index = max(0, index - 1)
                node = cell.find("m:v", ns)
                if node is None or node.text is None:
                    cells[index] = ""
                    continue
                if cell.attrib.get("t") == "s":
                    cells[index] = shared[int(node.text)]
                else:
                    cells[index] = node.text
            width = max(cells) + 1 if cells else 0
            grid.append([cells.get(i, "") for i in range(width)])
    if not grid:
        return []
    header = [norm_key(str(cell)) or f"col{i}" for i, cell in enumerate(grid[0])]
    rows = []
    for values in grid[1:]:
        rows.append({header[i]: values[i] if i < len(values) else "" for i in range(len(header))})
    return rows


def load_tables(root: Path) -> dict[str, dict]:
    """Map lowercase basename to a row dict. CSV is preferred to xlsx."""
    if not root.exists():
        return {}
    indexed: dict[str, dict] = {}
    tables = sorted(root.rglob("*.csv")) + sorted(root.rglob("*.xlsx"))
    for path in tables:
        if path.name.startswith("."):
            continue
        try:
            if path.suffix.lower() == ".csv":
                try:
                    import pandas as pd

                    frame = pd.read_csv(path)
                    rows = frame.fillna("").astype(str).to_dict(orient="records")
                except ImportError:
                    rows = _read_csv(path)
            else:
                rows = _read_xlsx(path)
        except (OSError, ValueError, KeyError) as exc:
            print(f"Could not read label file {path}: {exc}", file=sys.stderr)
            continue
        if not rows:
            continue
        print(f"Label file {path}: {len(rows)} rows, columns {list(rows[0].keys())[:12]}")
        for row in rows:
            for key, value in row.items():
                key_n = norm_key(str(key))
                if key_n not in {"filename", "file", "image", "img", "name", "path", "image name"}:
                    continue
                base = Path(str(value)).name.lower()
                if base:
                    indexed[base] = {str(k): v for k, v in row.items()}
    return indexed


def _folder_label(path: Path, source_root: Path) -> str:
    for parent in path.parents:
        if parent == source_root or parent == source_root.parent:
            break
        if parent.name.lower() in SKIP_DIR_NAMES or parent.name.startswith("."):
            continue
        return parent.name
    return path.parent.name


def _iter_images(root: Path) -> list[Path]:
    found = []
    if not root.exists():
        return found
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXT:
            continue
        if any(part.startswith(".") or part.lower() == "__macosx" for part in path.parts):
            continue
        found.append(path)
    return found


def label_image(source: str, path: Path, source_root: Path, tables: dict[str, dict]) -> dict | None:
    filename = path.name
    table_row = tables.get(filename.lower())
    folder = _folder_label(path, source_root)
    plant_id = plant_id_from_name(filename) if source == "RoCoLe" else ""

    if source in {"PlantDoc", "backgrounds"}:
        return {
            "original_label": folder,
            "label": "not_leaf",
            "out_of_scope": "",
            "plant_id": "",
        }

    if source == "RoCoLe":
        if table_row is not None:
            mapped = rocole_from_row(table_row)
            if mapped is None:
                return None
            mapped["plant_id"] = plant_id
            return mapped
        folder_mite = "mite" in folder.lower() or "spider" in folder.lower()
        mapped = classify_rocole(folder, folder_mite, None)
        if mapped is None:
            mapped_folder = alias(folder)
            if mapped_folder in {"healthy", "rust"}:
                mapped = {"original_label": folder, "label": mapped_folder, "out_of_scope": ""}
            else:
                return None
        mapped["plant_id"] = plant_id
        return mapped

    if table_row is not None:
        classes = classes_from_table_row(table_row)
        original = folder
        for key, value in table_row.items():
            if norm_key(str(key)) in {"label", "class", "classes", "diagnosis", "symptom"}:
                original = str(value).strip() or folder
                break
        if len(classes) > 1:
            return {"skip": "multi_label"}
        if len(classes) == 1:
            return {
                "original_label": original,
                "label": classes[0],
                "out_of_scope": "",
                "plant_id": "",
            }

    if source == "Uganda":
        from_folder = alias(folder)
        if from_folder:
            return {"original_label": folder, "label": from_folder, "out_of_scope": "", "plant_id": ""}
        from_prefix = uganda_prefix_label(filename)
        if from_prefix:
            return {
                "original_label": filename,
                "label": from_prefix,
                "out_of_scope": "",
                "plant_id": "",
            }
        return None

    mapped = alias(folder)
    if mapped is None:
        return None
    return {"original_label": folder, "label": mapped, "out_of_scope": "", "plant_id": ""}


def phash_int(path: Path) -> int:
    import imagehash
    from PIL import Image

    with Image.open(path) as image:
        hashed = imagehash.phash(image.convert("RGB"))
    return int(str(hashed), 16)


def collect_rows() -> tuple[list[dict], dict]:
    rows = []
    stats = Counter()
    brown_seen = False
    for source, root in SOURCE_DIRS:
        images = _iter_images(root)
        if not images:
            continue
        tables = load_tables(root)
        print(f"{source}: {len(images)} images under {root}")
        try:
            from tqdm import tqdm

            iterator = tqdm(images, desc=f"hash {source}")
        except ImportError:
            iterator = images
        for path in iterator:
            labelled = label_image(source, path, root, tables)
            if labelled is None:
                stats["skipped_unmapped"] += 1
                continue
            if labelled.get("skip"):
                stats[labelled["skip"]] += 1
                continue
            if norm_key(labelled["original_label"]) == "brown leaf spot" or alias(labelled["original_label"]) == "cercospora" and "brown leaf spot" in norm_key(labelled["original_label"]):
                brown_seen = True
            if "brown leaf spot" in norm_key(str(labelled["original_label"])):
                brown_seen = True
            try:
                hashed = phash_int(path)
            except (OSError, ValueError) as exc:
                print(f"Unreadable image {path}: {exc}", file=sys.stderr)
                stats["unreadable"] += 1
                continue
            relative = path.resolve().relative_to(DATA_RAW.resolve()).as_posix()
            rows.append(
                {
                    "path": relative,
                    "source": source,
                    "original_label": labelled["original_label"],
                    "label": labelled["label"],
                    "out_of_scope": labelled["out_of_scope"],
                    "plant_id": labelled.get("plant_id") or "",
                    "hash": hashed,
                }
            )
            stats["kept"] += 1
    stats["brown_leaf_spot_seen"] = int(brown_seen)
    return rows, stats


def assign_splits(rows: list[dict], seed: int = SEED, max_dist: int = HAMMING_MAX) -> dict:
    """Set row['split']. Held-out sources force the whole near-duplicate cluster to heldout."""
    n = len(rows)
    if n == 0:
        return {"n": 0, "duplicate_clusters": 0, "duplicate_images": 0, "label_clashes": 0, "train_images_held_out": 0}

    hashes = [row.get("hash") for row in rows]
    roots = cluster_hashes(hashes, max_dist=max_dist)
    parent = list(roots)

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        ra, rb = find(left), find(right)
        if ra != rb:
            parent[rb] = ra

    plants: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        if row["source"] == "RoCoLe" and row.get("plant_id"):
            plants[row["plant_id"]].append(index)
    for members in plants.values():
        for member in members[1:]:
            union(members[0], member)

    clusters: dict[int, list[int]] = defaultdict(list)
    for index in range(n):
        clusters[find(index)].append(index)

    free: list[list[int]] = []
    held_roots = []
    clash_images = 0
    for root, members in clusters.items():
        labels = [rows[i]["label"] for i in members if rows[i]["label"] in LABELS]
        if len(set(labels)) > 1:
            for index in members:
                if rows[index]["out_of_scope"] == "":
                    rows[index]["out_of_scope"] = "label_clash"
                    clash_images += 1
        if any(rows[i]["source"] in HELD_OUT_SOURCES for i in members):
            held_roots.append(root)
        else:
            free.append(members)

    def majority(members: list[int]) -> str:
        counts = Counter(rows[i]["label"] for i in members)
        best = None
        best_n = -1
        for label in LABELS:
            if counts.get(label, 0) > best_n:
                best_n = counts[label]
                best = label
        return best or "not_leaf"

    grouped: dict[str, list[list[int]]] = {label: [] for label in LABELS}
    for members in free:
        grouped[majority(members)].append(members)

    assignment = {root: HELD_OUT_SPLIT for root in held_roots}
    for label, groups in grouped.items():
        if not groups:
            continue
        rng = random.Random(f"{seed}:{label}")
        rng.shuffle(groups)
        groups.sort(key=len, reverse=True)
        total = sum(len(group) for group in groups)
        targets = {split: SPLIT_FRACTIONS[split] * total for split in SPLITS}
        counts = {split: 0 for split in SPLITS}
        for group in groups:
            choice = max(SPLITS, key=lambda split: (targets[split] - counts[split], -SPLITS.index(split)))
            assignment[find(group[0])] = choice
            counts[choice] += len(group)

    moved = 0
    for index, row in enumerate(rows):
        split = assignment[find(index)]
        if row["source"] not in HELD_OUT_SOURCES and split == HELD_OUT_SPLIT:
            moved += 1
        row["split"] = split

    duplicate_clusters = sum(1 for members in clusters.values() if len(members) > 1)
    duplicate_images = sum(len(members) for members in clusters.values() if len(members) > 1)
    per_split = Counter(row["split"] for row in rows)
    per_class = {}
    for label in LABELS:
        per_class[label] = Counter(row["split"] for row in rows if row["label"] == label and row["out_of_scope"] == "")
    return {
        "n": n,
        "duplicate_clusters": duplicate_clusters,
        "duplicate_images": duplicate_images,
        "label_clashes": clash_images,
        "train_images_held_out": moved,
        "per_split": dict(per_split),
        "per_class": {label: dict(counts) for label, counts in per_class.items()},
        "plants": {plant: len(members) for plant, members in plants.items()},
    }


def assert_safe(rows: list[dict]) -> None:
    plant_splits: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["label"] not in LABELS:
            raise SystemExit(f"Refusing to write manifest: label {row['label']!r} is outside the six classes")
        if row["source"] in HELD_OUT_SOURCES and row["split"] != HELD_OUT_SPLIT:
            raise SystemExit(
                f"Refusing to write manifest: {row['source']} image {row['path']} is in split {row['split']}"
            )
        if row["out_of_scope"] == "red_spider_mite":
            if row["label"] == "rust":
                raise SystemExit("Refusing to write manifest: red spider mite was labelled rust")
            if row["label"] != "not_leaf":
                raise SystemExit("Refusing to write manifest: red spider mite label must stay not_leaf")
            if row["split"] != HELD_OUT_SPLIT:
                raise SystemExit("Refusing to write manifest: red spider mite was not held out")
        if row["source"] == "RoCoLe" and row.get("plant_id"):
            plant_splits[row["plant_id"]].add(row["split"])
    for plant, splits in plant_splits.items():
        if len(splits) != 1:
            raise SystemExit(f"Refusing to write manifest: plant {plant} spans splits {sorted(splits)}")


def write_manifest(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in MANIFEST_COLUMNS})


def build(path: Path = MANIFEST_PATH) -> int:
    rows, collect_stats = collect_rows()
    if not rows:
        print(
            "No images found under data_raw. "
            "Run download.py on the GPU laptop first. manifest.csv was not written."
        )
        return 1
    if collect_stats["brown_leaf_spot_seen"]:
        print(BROWN_LEAF_SPOT_ASSUMPTION)
    if any(row["source"] == "Uganda" for row in rows):
        print(UGANDA_PREFIX_ASSUMPTION)
    if any(row["out_of_scope"] == "red_spider_mite" for row in rows):
        print(MITE_POLICY)
    split_stats = assign_splits(rows)
    assert_safe(rows)
    write_manifest(rows, path)
    print(f"Wrote {path} ({len(rows)} rows)")
    print(
        f"Near-duplicate clusters (Hamming <= {HAMMING_MAX}): "
        f"{split_stats['duplicate_clusters']} clusters, "
        f"{split_stats['duplicate_images']} images inside them."
    )
    print(f"Label clashes marked out_of_scope and excluded from training: {split_stats['label_clashes']}")
    print(
        "Train-source images moved to heldout because they matched a held-out image "
        f"or sat in that cluster: {split_stats['train_images_held_out']}"
    )
    print(f"Skipped unmapped images: {collect_stats['skipped_unmapped']}")
    print(f"Skipped multi-label images: {collect_stats['multi_label']}")
    print(f"Unreadable images: {collect_stats['unreadable']}")
    print(f"Split counts: {split_stats['per_split']}")
    print(f"Per-class split counts (out_of_scope excluded): {split_stats['per_class']}")
    plant_sizes = Counter(split_stats["plants"].values())
    if plant_sizes:
        print(f"RoCoLe images per plant: {dict(sorted(plant_sizes.items()))}")
    return 0


def _partition(roots: list[int]) -> set[tuple[int, ...]]:
    groups: dict[int, list[int]] = defaultdict(list)
    for index, root in enumerate(roots):
        groups[root].append(index)
    return {tuple(members) for members in groups.values()}


def _brute_roots(hashes: list[int | None], max_dist: int) -> list[int]:
    parent = list(range(len(hashes)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        ra, rb = find(left), find(right)
        if ra != rb:
            parent[rb] = ra

    for i in range(len(hashes)):
        if hashes[i] is None:
            continue
        for j in range(i + 1, len(hashes)):
            if hashes[j] is None:
                continue
            if (int(hashes[i]) ^ int(hashes[j])).bit_count() <= max_dist:
                union(i, j)
    return [find(i) for i in range(len(hashes))]


def _row(source: str, label: str, hashed: int | None, plant_id: str = "", out_of_scope: str = "", original: str = "") -> dict:
    return {
        "path": f"{source}/{label}/{hashed}.jpg",
        "source": source,
        "original_label": original or label,
        "label": label,
        "out_of_scope": out_of_scope,
        "plant_id": plant_id,
        "hash": hashed,
    }


def run_self_check() -> int:
    if alias("brown leaf spot") != "cercospora":
        raise SystemExit("brown leaf spot must map to cercospora")
    if alias("cercospora leaf spot") != "cercospora":
        raise SystemExit("cercospora leaf spot must map to cercospora")
    if alias("leaf rust") != "rust" or alias("Cerscospora") != "cercospora":
        raise SystemExit("JMuBEN folder names did not map")
    if alias("Leaf rust") != "rust" or alias("Phoma") != "phoma":
        raise SystemExit("JMuBEN class folders did not map")
    if alias("Healthy") != "healthy" or alias("Miner") != "miner" or alias("leaf miner") != "miner":
        raise SystemExit("healthy or miner did not map")
    if uganda_prefix_label("1_leaf.jpg") != "healthy":
        raise SystemExit("Uganda 1_ prefix")
    if uganda_prefix_label("1200_leaf.jpg") != "rust":
        raise SystemExit("Uganda 1200_ prefix")
    if uganda_prefix_label("2300_leaf.jpg") != "phoma":
        raise SystemExit("Uganda 2300_ prefix")
    if uganda_prefix_label("999_leaf.jpg") is not None:
        raise SystemExit("unknown Uganda prefix must not be guessed")
    mite = classify_rocole("red spider mite", True, 3)
    if mite is None or mite["label"] == "rust" or mite["out_of_scope"] != "red_spider_mite":
        raise SystemExit("red spider mite must not be trained as rust")
    if "rust level 3" not in mite["original_label"]:
        raise SystemExit("mite original_label should keep the rust level")
    rust = classify_rocole("rust level 2", False, 2)
    if rust is None or rust["label"] != "rust" or rust["out_of_scope"]:
        raise SystemExit("RoCoLe rust without mites should map to rust")
    if plant_id_from_name("C10P10E1.jpg") != "C10P10":
        raise SystemExit("plant id parse failed")
    if plant_id_from_name("C10P10H2.jpg") != plant_id_from_name("C10P10E1.jpg"):
        raise SystemExit("plant images must share an id")

    rng = random.Random(0)
    for _ in range(20):
        hashes = [rng.getrandbits(64) for _ in range(40)]
        if _partition(cluster_hashes(hashes)) != _partition(_brute_roots(hashes, HAMMING_MAX)):
            raise SystemExit("hash clustering disagreed with the brute-force check")
    base = 0
    near = (1 << 6) - 1  # bits 0 to 5, distance 6 from base
    far = sum(1 << bit for bit in range(32, 39))  # bits 32 to 38, distance 7 from base and 13 from near
    sets = [set(group) for group in _partition(cluster_hashes([base, near, far]))]
    if {0, 1} not in sets or {2} not in sets:
        raise SystemExit(f"distance-6 pair was not clustered exactly: {sets}")
    sets = [set(group) for group in _partition(cluster_hashes([base, far]))]
    if {0, 1} in sets:
        raise SystemExit("distance-7 pair must not be clustered")

    def far_hash(index: int) -> int:
        # Repeat one byte eight times. Distinct bytes are at least Hamming 8 apart,
        # so they stay outside the near-duplicate radius of 6.
        byte = index & 0xFF
        value = 0
        for shift in range(0, 64, 8):
            value |= byte << shift
        return value

    rows = []
    for index in range(100):
        rows.append(_row("JMuBEN2", "healthy", far_hash(index)))
        rows.append(_row("JMuBEN", "rust", far_hash(100 + index)))
    shared = far_hash(200)
    rows.append(_row("JMuBEN2", "healthy", shared))
    rows.append(_row("JMuBEN", "rust", shared))  # same hash, different label
    rows.append(_row("Uganda", "rust", shared, original="1200_x.jpg"))
    rows.append(_row("Uganda", "healthy", far_hash(201), original="1_x.jpg"))
    for offset, side in enumerate(("E1", "E2", "H1", "H2")):
        rows.append(
            _row(
                "RoCoLe",
                "rust",
                far_hash(210 + offset),
                plant_id="C4P8",
                original=f"C4P8{side}.jpg",
            )
        )
    rows.append(
        _row(
            "RoCoLe",
            "not_leaf",
            far_hash(220),
            plant_id="C4P9",
            out_of_scope="red_spider_mite",
            original="red spider mite",
        )
    )
    stats = assign_splits(rows, seed=SEED)
    assert_safe(rows)
    splits_for_plant = {row["split"] for row in rows if row.get("plant_id") == "C4P8"}
    if splits_for_plant != {HELD_OUT_SPLIT}:
        raise SystemExit("RoCoLe plant was not kept together in heldout")
    if any(row["source"] in HELD_OUT_SOURCES and row["split"] != HELD_OUT_SPLIT for row in rows):
        raise SystemExit("held-out source left heldout")
    if any(row["out_of_scope"] == "red_spider_mite" and row["label"] == "rust" for row in rows):
        raise SystemExit("mite labelled rust in the split pass")
    clash = [row for row in rows if row["hash"] == shared and row["source"] != "Uganda"]
    if not clash or any(row["out_of_scope"] != "label_clash" for row in clash):
        raise SystemExit("cross-label near duplicates should be marked label_clash")
    healthy_counts = Counter(row["split"] for row in rows if row["label"] == "healthy" and row["out_of_scope"] == "")
    # 100 random healthy hashes, plus one shared hash that clashes and is held out.
    if (healthy_counts["train"], healthy_counts["val"], healthy_counts["test"]) != (70, 15, 15):
        raise SystemExit(f"unexpected healthy split counts {healthy_counts}")
    rust_counts = Counter(row["split"] for row in rows if row["label"] == "rust" and row["out_of_scope"] == "" and row["source"] != "RoCoLe")
    if (rust_counts["train"], rust_counts["val"], rust_counts["test"]) != (70, 15, 15):
        raise SystemExit(f"unexpected rust split counts {rust_counts}")
    if stats["n"] != len(rows):
        raise SystemExit("split stats lost rows")

    confidences = [0.99, 0.98, 0.97, 0.96, 0.90]
    correct = [True, True, True, True, False]
    chosen = choose_threshold(confidences, correct, target=0.95)
    if not chosen["target_met"] or chosen["n_accepted"] != 4:
        raise SystemExit(f"threshold cut should keep the four correct rows: {chosen}")
    empty = choose_threshold([], [], target=0.95)
    if empty["accuracy"] is not None or empty["target_met"]:
        raise SystemExit("empty threshold result must not invent an accuracy")
    uniform = softmax([1.0, 1.0, 1.0], 2.0)
    if abs(uniform[0] - (1.0 / 3.0)) > 1e-9 or abs(sum(uniform) - 1.0) > 1e-9:
        raise SystemExit(f"softmax should stay uniform when logits are equal: {uniform}")
    peaked = softmax([2.0, 0.0, 0.0], 1.0)
    flatter = softmax([2.0, 0.0, 0.0], 4.0)
    if peaked[0] <= flatter[0]:
        raise SystemExit("a higher temperature should make the distribution less peaked")
    bad_card = validate_model_card({"version": "v1", "labels": []})
    if not bad_card:
        raise SystemExit("incomplete model card must fail validation")
    print("manifest.py self-check ok")
    print(BROWN_LEAF_SPOT_ASSUMPTION)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build ml/manifest.csv with leakage-controlled splits.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--out", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    if args.self_check:
        return run_self_check()
    return build(args.out)


if __name__ == "__main__":
    sys.exit(main())
