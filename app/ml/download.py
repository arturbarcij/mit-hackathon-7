"""Idempotent dataset downloader for Jani.

Usage (from app/ml):  python download.py [--only jmuben2 jmuben bracol plantdoc uganda rocole]

Raw data goes to MIT_Hackathon_7/data_raw/ (outside the git repo, never committed).
Large files are fetched with curl.exe and resumed with -C -. A file is skipped when its
size already matches the expected size. Sources and licences: kb/research/DATASETS.md.
All sets are CC BY 4.0.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data_raw"
MD = "https://data.mendeley.com/public-files/datasets"
API = "https://data.mendeley.com/public-api/datasets"

# (dataset, filename, url, expected bytes)
BIG = [
    ("jmuben2", "healthy.zip", f"{MD}/tgv3zb82nd/files/d126777d-c495-4b7a-846a-c0228540ea10/file_downloaded", 566_927_674),
    ("jmuben2", "miner.zip", f"{MD}/tgv3zb82nd/files/f6d37632-6349-4be9-9af0-c3177dbfaa8a/file_downloaded", 724_766_477),
    ("jmuben", "rust.zip", f"{MD}/t2r6rszp5c/files/8c7c2915-f979-43f6-b3fd-b3bc7407da87/file_downloaded", 69_450_673),
    ("jmuben", "cercospora.zip", f"{MD}/t2r6rszp5c/files/8657d2a2-c9a1-4733-9dbc-00c83aa3575a/file_downloaded", 252_204_134),
    ("jmuben", "phoma.zip", f"{MD}/t2r6rszp5c/files/82625dd3-e908-4224-93b5-06a3b74f0c8a/file_downloaded", 227_452_725),
    ("bracol", "bracol.zip", f"{MD}/yy2k5y8mxg/files/c16b08ee-3ca6-4bf0-8f4e-4285a53a4a24/file_downloaded", 164_516_964),
]


def curl(url: str, dest: Path, expected: int | None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if expected and dest.exists() and dest.stat().st_size == expected:
        print(f"skip  {dest.name} (complete)", flush=True)
        return
    print(f"fetch {dest.name}", flush=True)
    for attempt in range(5):
        r = subprocess.run(
            ["curl.exe", "-L", "-sS", "-C", "-", "--retry", "3", "-o", str(dest), url]
        )
        ok = r.returncode == 0 and (not expected or dest.stat().st_size == expected)
        if ok:
            print(f"done  {dest.name} {dest.stat().st_size}", flush=True)
            return
        print(f"retry {dest.name} attempt {attempt + 1} rc={r.returncode}", flush=True)
    print(f"FAIL  {dest.name}", flush=True)


def get_json(url: str):
    out = subprocess.run(
        ["curl.exe", "-sS", "-L", "-H", "Accept: application/vnd.mendeley-public-dataset.1+json", url],
        capture_output=True, check=True,
    ).stdout
    return json.loads(out)

def mendeley_files(dataset_id: str, out: Path, accept=lambda name: True, workers: int = 8) -> None:
    meta = get_json(f"{API}/{dataset_id}")
    files = meta["files"]
    jobs = []
    for f in files:
        name = f["filename"]
        if not accept(name):
            continue
        cd = f["content_details"]
        jobs.append((cd["download_url"], out / name, cd.get("size")))
    print(f"{dataset_id}: {len(jobs)} files", flush=True)

    def one(j):
        url, dest, size = j
        if dest.exists() and size and dest.stat().st_size == size:
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl.exe", "-L", "-sS", "--retry", "3", "-o", str(dest), url], check=False)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, jobs))
    print(f"done  {dataset_id}", flush=True)


def plantdoc() -> None:
    """Clone (history-free) then export blobs with safe names.

    Some PlantDoc file names contain '?' which Windows cannot check out, so the working tree
    is skipped and images are written from git objects to data_raw/plantdoc_images/.
    """
    repo = RAW / "plantdoc"
    out = RAW / "plantdoc_images"
    if (out / ".exported").exists():
        print("skip  plantdoc (exported)", flush=True)
        return
    if not (repo / ".git").exists():
        subprocess.run(["git", "clone", "--depth", "1", "--no-checkout",
                        "https://github.com/pratikkayal/PlantDoc-Dataset", str(repo)], check=False)
    names = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "-z", "--name-only", "HEAD"],
                           capture_output=True, check=True).stdout.split(b"\0")
    n = 0
    for raw in names:
        p = raw.decode("utf-8", "replace")
        if not p.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        parts = p.split("/")
        safe = "__".join("".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in s) for s in parts)
        blob = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{p}"], capture_output=True).stdout
        if blob:
            out.mkdir(parents=True, exist_ok=True)
            (out / safe).write_bytes(blob)
            n += 1
    (out / ".exported").write_text(str(n))
    print(f"done  plantdoc {n} images", flush=True)

def unzip_all() -> None:
    for ds, name, _, _ in BIG:
        z = RAW / ds / name
        out = RAW / ds / z.stem
        marker = out / ".extracted"
        if z.exists() and not marker.exists():
            print(f"unzip {z.name}", flush=True)
            out.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(out)
            except zipfile.BadZipFile:
                # BRACOL zip from Mendeley is truncated; bsdtar recovers the readable entries.
                print(f"tar fallback for {z.name}", flush=True)
                subprocess.run(["tar", "-xf", str(z), "-C", str(out)])
            marker.write_text("ok")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--no-unzip", action="store_true")
    a = ap.parse_args()
    want = lambda k: a.only is None or k in a.only

    # JMuBEN2 first (biggest), both files in parallel; the rest queue behind.
    big = [b for b in BIG if want(b[0])]
    with ThreadPoolExecutor(3) as ex:
        futs = [ex.submit(curl, url, RAW / ds / name, size) for ds, name, url, size in big]
        if want("plantdoc"):
            futs.append(ex.submit(plantdoc))
        if want("uganda"):
            futs.append(ex.submit(mendeley_files, "k36wnd6knb", RAW / "uganda"))
        if want("rocole"):
            # Skip the 697 MB VOC tarball and COCO/JSON/CSV duplicates; keep jpgs and the xlsx labels.
            futs.append(
                ex.submit(
                    mendeley_files, "c5yvn32dzg", RAW / "rocole",
                    lambda n: n.lower().endswith((".jpg", ".xlsx", ".csv")), 6,
                )
            )
        for f in futs:
            f.result()
    if not a.no_unzip:
        unzip_all()
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
