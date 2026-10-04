"""Download the raw datasets into data_raw/<dataset>/. Idempotent: finished steps leave a .done marker.

Usage: python app/ml/download.py [--only jmuben,uganda,...] [--plantdoc-per-class 15]
"""
import argparse
import json
import random
import shutil
import sys
import urllib.parse
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data_raw"
MENDELEY = "https://data.mendeley.com/public-api"

# Mendeley datasets: (dataset id, version). "files" downloads the root files one by one,
# "zip" downloads Mendeley's whole-dataset zip.
SOURCES = {
    "jmuben": ("t2r6rszp5c", 1, "files"),   # cercospora, rust, phoma
    "jmuben2": ("tgv3zb82nd", 1, "files"),  # healthy, miner
    "uganda": ("k36wnd6knb", 1, "zip"),
    "bracol": ("yy2k5y8mxg", 1, "zip"),
    "rocole": ("c5yvn32dzg", 2, "zip"),
}

PLANTDOC_REPO = "pratikkayal/PlantDoc-Dataset"


def fetch(url: str, dest: Path) -> None:
    if dest.exists():
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=120, allow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.rename(dest)


def salvage(zip_path: Path, out: Path) -> int:
    """Extract complete entries from a zip with no central directory by walking local headers."""
    import struct
    import zlib
    data = zip_path.read_bytes()
    off = n = 0
    while data[off:off + 4] == b"PK\x03\x04":
        _, flag, method, _, _, _, csize, _, nlen, elen = struct.unpack("<HHHHHIIIHH", data[off + 4:off + 30])
        name = data[off + 30:off + 30 + nlen].decode("utf8", "replace")
        start = off + 30 + nlen + elen
        if flag & 8 or start + csize > len(data):
            break
        blob = data[start:start + csize]
        if not name.endswith("/"):
            dest = out / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zlib.decompress(blob, -15) if method == 8 else blob)
            n += 1
        off = start + csize
    return n


def extract(zip_path: Path, out: Path) -> None:
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(out)
    # Nested zips (Mendeley sometimes wraps zips in zips)
    for inner in list(out.rglob("*.zip")):
        sub = inner.with_suffix("")
        if not sub.exists():
            try:
                with zipfile.ZipFile(inner) as z:
                    z.extractall(sub)
            except zipfile.BadZipFile:
                n = salvage(inner, sub)
                (sub / "SALVAGED.txt").write_text(
                    f"{inner.name} has no central directory (truncated upload); {n} complete files recovered.\n")
                print(f"  salvaged {n} files from truncated {inner.name}")
        inner.unlink()


def mendeley(name: str, ds_id: str, version: int, mode: str) -> None:
    out = DATA_RAW / name
    done = out / ".done"
    if done.exists():
        print(f"[{name}] already done")
        return
    out.mkdir(parents=True, exist_ok=True)
    meta = requests.get(f"{MENDELEY}/datasets/{ds_id}", timeout=60).json()
    (out / "mendeley_meta.json").write_text(json.dumps(
        {"name": meta.get("name"), "doi": meta.get("doi", {}).get("id"), "version": version,
         "licence": meta.get("data_licence", {}).get("short_name")}, indent=2))
    if mode == "files":
        files = requests.get(f"{MENDELEY}/datasets/{ds_id}/files",
                             params={"folder_id": "root", "version": version}, timeout=60).json()
        zips = []
        for f in files:
            dest = out / f["filename"]
            print(f"[{name}] {f['filename']} ({f['size'] / 1e6:.0f} MB)")
            fetch(f["content_details"]["download_url"], dest)
            zips.append(dest)
    else:
        dest = out / f"{ds_id}-{version}.zip"
        print(f"[{name}] whole-dataset zip")
        fetch(f"{MENDELEY}/zip/{ds_id}/download/{version}", dest)
        zips = [dest]
    ext = out / "extracted"
    if ext.exists():
        shutil.rmtree(ext)
    for z in zips:
        print(f"[{name}] extracting {z.name}")
        extract(z, ext / z.stem)
        z.unlink()
    # RoCoLe ships a large VOC tarball we do not need; photos are extracted separately.
    for tar in ext.rglob("*.tar.gz"):
        tar.unlink()
    done.write_text("ok\n")
    print(f"[{name}] done")


def plantdoc(per_class: int) -> None:
    out = DATA_RAW / "plantdoc"
    done = out / ".done"
    if done.exists():
        print("[plantdoc] already done")
        return
    out.mkdir(parents=True, exist_ok=True)
    tree = requests.get(f"https://api.github.com/repos/{PLANTDOC_REPO}/git/trees/master?recursive=1",
                        timeout=60).json()["tree"]
    by_class: dict[str, list[str]] = {}
    for t in tree:
        p = t["path"]
        if t["type"] == "blob" and p.startswith("train/") and p.lower().endswith((".jpg", ".jpeg", ".png")):
            by_class.setdefault(p.split("/")[1], []).append(p)
    rng = random.Random(42)
    picks = []
    for cls in sorted(by_class):
        paths = sorted(by_class[cls])
        rng.shuffle(paths)
        picks += paths[:per_class]

    def get(p: str) -> str | None:
        cls, fname = p.split("/")[1], p.split("/")[-1]
        dest = out / "images" / cls.replace(" ", "_") / fname.replace(" ", "_")
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://raw.githubusercontent.com/{PLANTDOC_REPO}/master/{urllib.parse.quote(p)}"
        try:
            fetch(url, dest)
            return None
        except Exception as e:  # some PlantDoc files are broken links; skip them
            return f"{p}: {e}"

    with ThreadPoolExecutor(8) as ex:
        errors = [e for e in ex.map(get, picks) if e]
    print(f"[plantdoc] {len(picks) - len(errors)} images, {len(errors)} failed")
    (out / "mendeley_meta.json").write_text(json.dumps(
        {"name": "PlantDoc (train split, sampled)", "repo": PLANTDOC_REPO, "licence": "CC BY 4.0",
         "per_class": per_class, "seed": 42, "failed": errors}, indent=2))
    done.write_text("ok\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated subset of: " + ",".join([*SOURCES, "plantdoc"]))
    ap.add_argument("--plantdoc-per-class", type=int, default=15)
    a = ap.parse_args()
    wanted = [s for s in a.only.split(",") if s] or [*SOURCES, "plantdoc"]
    failed = []
    for name in wanted:
        try:
            if name == "plantdoc":
                plantdoc(a.plantdoc_per_class)
            else:
                mendeley(name, *SOURCES[name])
        except Exception as e:
            print(f"[{name}] NOT AVAILABLE: {e}", file=sys.stderr)
            failed.append(name)
    if failed:
        print("failed:", ",".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
