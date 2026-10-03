#!/usr/bin/env python3
"""Download Jani leaf datasets into data_raw, outside the git repo.

Idempotent: a file that already has the expected size is left in place.
Prints the licence before each download. Uganda and RoCoLe are held-out
only. This script does nothing on import.

Downloads are large (JMuBEN2 alone is about 1.29 GB, RoCoLe about 2.27 GB).
Run it on a machine that can store that, not as a syntax check.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from common import DATASETS_PATH, DATA_RAW

MENDELEY_ACCEPT = "application/vnd.mendeley-public-dataset.1+json"
USER_AGENT = "jani-ml-download/1.0"
CHUNK = 1 << 20


class HeldOutTrainError(RuntimeError):
    """Uganda or RoCoLe was aimed at a train folder."""


def load_datasets(path: Path | None = None) -> list[dict]:
    path = path or DATASETS_PATH
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        rows = payload.get("datasets")
    else:
        rows = payload
    if not isinstance(rows, list) or not rows:
        raise SystemExit(f"No datasets listed in {path}")
    return rows


def is_held_out(dataset: dict) -> bool:
    role = str(dataset.get("role", "")).lower().replace("_", "-")
    if role in {"held-out", "heldout"}:
        return True
    blob = f"{dataset.get('name', '')} {dataset.get('url', '')}".lower()
    return "uganda" in blob or "rocole" in blob


def slug_for(name: str) -> str:
    lowered = name.lower()
    if "jmuben2" in lowered:
        return "jmuben2"
    if "jmuben" in lowered:
        return "jmuben"
    if "bracol" in lowered:
        return "bracol"
    if "uganda" in lowered:
        return "uganda"
    if "rocole" in lowered:
        return "rocole"
    if "plantdoc" in lowered:
        return "plantdoc"
    if "coleaf" in lowered:
        return "coleaf"
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in lowered)
    return "-".join(part for part in cleaned.split("-") if part)


def resolve_dest(dataset: dict, data_root: Path, into: Path | None = None) -> Path:
    """Return the directory for this dataset. Refuse a train folder for held-out sets."""
    slug = slug_for(dataset["name"])
    role = str(dataset.get("role", "")).lower().replace("_", "-")
    if into is not None:
        dest = Path(into) / slug
    elif is_held_out(dataset):
        dest = data_root / "heldout" / slug
    elif role == "negatives":
        dest = data_root / "negatives" / slug
    elif role == "future":
        dest = data_root / "future" / slug
    else:
        dest = data_root / "train" / slug
    if is_held_out(dataset) and "train" in {part.lower() for part in dest.parts}:
        raise HeldOutTrainError(
            f"Refusing to put {dataset['name']} into a train folder ({dest}). "
            "Uganda and RoCoLe are held-out only and must stay under heldout/."
        )
    return dest


def _licence_line(dataset: dict, filename: str) -> str:
    return f"Licence: {dataset['licence']} | {dataset['name']} | {filename} | {dataset['url']}"


def _already(path: Path, expected: int | None) -> bool:
    if not path.is_file():
        return False
    size = path.stat().st_size
    if expected is None:
        return size > 0
    return size == expected


def _stream_to(url: str, dest: Path, headers: dict | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".partial")
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None
    last_error = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                total = response.headers.get("Content-Length")
                total_int = int(total) if total and total.isdigit() else None
                bar = tqdm(total=total_int, unit="B", unit_scale=True, desc=dest.name) if tqdm else None
                with open(partial, "wb") as handle:
                    while True:
                        chunk = response.read(CHUNK)
                        if not chunk:
                            break
                        handle.write(chunk)
                        if bar is not None:
                            bar.update(len(chunk))
                if bar is not None:
                    bar.close()
            os.replace(partial, dest)
            return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if partial.exists():
                partial.unlink()
            print(f"Download attempt {attempt} failed for {url}: {exc}", file=sys.stderr)
    raise SystemExit(f"Could not download {url}: {last_error}")


def _safe_extract(zip_path: Path, dest: Path) -> None:
    import zipfile

    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            target = (dest / info.filename).resolve()
            if not target.is_relative_to(dest.resolve()):
                raise SystemExit(f"Refusing zip entry that escapes {dest}: {info.filename}")
        archive.extractall(dest)
    (dest / ".extracted").write_text(zip_path.name + "\n", encoding="utf-8")


def _skip_name(dataset: dict, filename: str) -> str | None:
    lowered = filename.lower()
    listed = {name.lower() for name in dataset.get("skip_files", [])}
    if lowered in listed or Path(lowered).name in listed:
        return "listed in skip_files"
    if "rocole" in dataset["name"].lower() and "voc" in lowered:
        return "RoCoLe VOC archive is not used; labels come from the csv and xlsx"
    return None


def _iter_api_files(payload) -> list[dict]:
    found: list[dict] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            details = node.get("content_details") if isinstance(node.get("content_details"), dict) else {}
            url = details.get("download_url") or node.get("download_url")
            name = node.get("filename") or node.get("name")
            if isinstance(url, str) and url.startswith("http") and isinstance(name, str):
                size = details.get("size", node.get("size"))
                found.append({"filename": name, "url": url, "bytes": size if isinstance(size, int) else None})
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    unique = []
    seen = set()
    for item in found:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        unique.append(item)
    return unique


def _fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": MENDELEY_ACCEPT},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def _download_file(dataset: dict, filename: str, url: str, dest_dir: Path, expected: int | None) -> None:
    print(_licence_line(dataset, filename))
    reason = _skip_name(dataset, filename)
    if reason:
        print(f"Skipping {filename}: {reason}")
        return
    dest = dest_dir / filename
    if _already(dest, expected):
        print(f"Already present, skipping download: {dest}")
    else:
        print(f"Downloading {url} -> {dest}")
        _stream_to(url, dest)
        if expected is not None and dest.stat().st_size != expected:
            size = dest.stat().st_size
            dest.unlink()
            raise SystemExit(
                f"Size mismatch for {filename}: got {size} bytes, expected {expected}. File removed."
            )
    if dest.suffix.lower() == ".zip":
        extracted = dest_dir / "extracted" / dest.stem
        if (extracted / ".extracted").exists():
            print(f"Already extracted: {extracted}")
        else:
            print(f"Extracting {dest} -> {extracted}")
            _safe_extract(dest, extracted)


def _download_known_files(dataset: dict, dest: Path) -> None:
    for item in dataset.get("files", []):
        _download_file(dataset, item["filename"], item["url"], dest, item.get("bytes"))


def _download_api(dataset: dict, dest: Path) -> None:
    api = dataset.get("api")
    if not api:
        raise SystemExit(f"{dataset['name']} is marked as an API download but has no api URL")
    print(_licence_line(dataset, "API file list"))
    print(f"Fetching file list {api}")
    payload = _fetch_json(api)
    files = _iter_api_files(payload)
    if not files:
        raise SystemExit(f"API returned no download URLs for {dataset['name']}: {api}")
    print(f"{dataset['name']}: {len(files)} files listed")
    for item in files:
        _download_file(dataset, item["filename"], item["url"], dest, item.get("bytes"))


def _download_git(dataset: dict, dest: Path) -> None:
    import subprocess

    print(_licence_line(dataset, "git clone --depth 1"))
    if dest.exists() and any(dest.iterdir()):
        print(f"Already present, skipping clone: {dest}")
        return
    if dest.exists():
        dest.rmdir()
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning {dataset['url']} -> {dest}")
    subprocess.run(
        ["git", "clone", "--depth", "1", dataset["url"], str(dest)],
        check=True,
    )


def download_dataset(dataset: dict, dest: Path) -> None:
    method = dataset.get("download")
    if method == "git":
        _download_git(dataset, dest)
        return
    if method == "api":
        _download_api(dataset, dest)
        return
    if dataset.get("files"):
        _download_known_files(dataset, dest)
        return
    raise SystemExit(f"{dataset['name']} has no files, api, or git URL to download")


def _selected(datasets: list[dict], only: list[str] | None, include_future: bool) -> list[dict]:
    chosen = []
    only_set = {name.lower() for name in only} if only else None
    for dataset in datasets:
        if only_set is not None and dataset["name"].lower() not in only_set:
            continue
        if dataset.get("role") == "future" and not include_future and only_set is None:
            print(
                f"Skipping {dataset['name']} (role future, not used for the six-class model). "
                "Pass --include-future to download it."
            )
            continue
        chosen.append(dataset)
    if not chosen:
        raise SystemExit("No datasets selected")
    return chosen


def run_self_check() -> int:
    datasets = load_datasets()
    by_name = {row["name"]: row for row in datasets}
    required = ["name", "url", "licence", "role", "classes"]
    for row in datasets:
        for key in required:
            if key not in row:
                raise SystemExit(f"{row.get('name')} is missing {key}")
        if not str(row["url"]).startswith("https://"):
            raise SystemExit(f"{row['name']} url is not https")
        if row["licence"] != "CC BY 4.0":
            raise SystemExit(f"{row['name']} licence is not CC BY 4.0")
    expected_counts = {
        "JMuBEN": 22588,
        "JMuBEN2": 35962,
        "Uganda": 3322,
        "RoCoLe": 1560,
    }
    for name, count in expected_counts.items():
        if by_name[name]["images_counted"] != count:
            raise SystemExit(f"{name} images_counted is {by_name[name]['images_counted']}, expected {count}")
    if by_name["BRACOL"]["images_counted"] is not None:
        raise SystemExit("BRACOL was not counted in DATASETS.md; images_counted must stay null")
    if by_name["PlantDoc"]["images_counted"] is not None:
        raise SystemExit("PlantDoc image counts were not checked; images_counted must stay null")
    if by_name["BRACOL"]["images_stated_leaf"] != 1747 or by_name["BRACOL"]["images_stated_symptom"] != 2147:
        raise SystemExit("BRACOL stated image figures do not match DATASETS.md")
    if by_name["Uganda"]["images_stated"] != 3312:
        raise SystemExit("Uganda stated image count does not match DATASETS.md")
    file_counts = [item["images_counted"] for item in by_name["JMuBEN"]["files"]]
    if file_counts != [7681, 8336, 6571]:
        raise SystemExit(f"JMuBEN file counts {file_counts} do not match DATASETS.md")
    file_counts = [item["images_counted"] for item in by_name["JMuBEN2"]["files"]]
    if file_counts != [18984, 16978]:
        raise SystemExit(f"JMuBEN2 file counts {file_counts} do not match DATASETS.md")
    root = DATA_RAW
    for dataset in datasets:
        dest = resolve_dest(dataset, root)
        if is_held_out(dataset) and "train" in {part.lower() for part in dest.parts}:
            raise SystemExit(f"held-out dataset resolved into train: {dest}")
        if is_held_out(dataset):
            try:
                resolve_dest(dataset, root, into=root / "train")
            except HeldOutTrainError:
                pass
            else:
                raise SystemExit(f"failed to refuse train folder for {dataset['name']}")
    if resolve_dest(by_name["Uganda"], root) != root / "heldout" / "uganda":
        raise SystemExit("Uganda destination is not heldout/uganda")
    if resolve_dest(by_name["RoCoLe"], root) != root / "heldout" / "rocole":
        raise SystemExit("RoCoLe destination is not heldout/rocole")
    if resolve_dest(by_name["JMuBEN"], root) != root / "train" / "jmuben":
        raise SystemExit("JMuBEN destination is not train/jmuben")
    if "train" in {part.lower() for part in resolve_dest(by_name["CoLeaf-DB"], root).parts}:
        raise SystemExit("CoLeaf-DB must not land in a train folder by default")
    print("download.py self-check ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download Jani datasets into data_raw (outside the git repo).")
    parser.add_argument("--dry-run", action="store_true", help="Print licences and destinations. Do not download.")
    parser.add_argument("--self-check", action="store_true", help="Check dataset facts and the held-out rule.")
    parser.add_argument("--include-future", action="store_true", help="Also download role=future (CoLeaf-DB).")
    parser.add_argument("--only", action="append", default=None, help="Dataset name to download. Repeatable.")
    parser.add_argument(
        "--into",
        type=Path,
        default=None,
        help="Override the destination root. Held-out datasets still refuse a path that contains a train folder.",
    )
    parser.add_argument("--data-root", type=Path, default=DATA_RAW)
    args = parser.parse_args(argv)
    if args.self_check:
        return run_self_check()

    datasets = _selected(load_datasets(), args.only, args.include_future)
    plans = []
    for dataset in datasets:
        print(_licence_line(dataset, dataset["name"]))
        try:
            dest = resolve_dest(dataset, args.data_root, args.into)
        except HeldOutTrainError as exc:
            print(exc)
            return 1
        plans.append((dataset, dest))
        print(f"Destination: {dest}")

    if args.dry_run:
        for dataset, dest in plans:
            method = dataset.get("download", "files")
            print(f"Dry run: would download {dataset['name']} via {method} into {dest}")
            for item in dataset.get("files", []):
                print(_licence_line(dataset, item["filename"]))
                print(f"  file {item['filename']} ({item.get('bytes')} bytes)")
            if method == "api":
                print(f"  API list (not fetched in dry run): {dataset.get('api')}")
        print("Dry run finished. Nothing was downloaded.")
        return 0

    for dataset, dest in plans:
        dest.mkdir(parents=True, exist_ok=True)
        download_dataset(dataset, dest)
    print(f"Downloads finished under {args.data_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
