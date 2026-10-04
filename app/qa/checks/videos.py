"""Submission videos (S3, S4): three files, MP4/MOV, each under 60 s and 1 GB; coverage of items a to e.

Expects: video/final/01_team.mp4, 02_demo.mp4, 03_technical.mp4 (or .mov), and video/COVERAGE.md.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from qa.common import Result, human_bytes, read_text

EXPECTED = ["01_team", "02_demo", "03_technical"]
MAX_SECONDS = 60.0
MAX_BYTES = 1024 ** 3
ITEMS = ["(a)", "(b)", "(c)", "(d)", "(e)"]


def _probe(path: Path) -> dict | None:
    if not shutil.which("ffprobe"):
        return None
    p = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
                       capture_output=True, text=True)
    try:
        return json.loads(p.stdout)["format"]
    except Exception:
        return {}


def run(root: Path) -> list[Result]:
    out: list[Result] = []
    final = root / "video/final"
    if not final.exists():
        return [Result("videos", "skip", "video/final/ missing (record the three videos first)")]
    for stem in EXPECTED:
        cands = [p for p in final.iterdir() if p.stem == stem and p.suffix.lower() in (".mp4", ".mov")]
        if not cands:
            out.append(Result(f"videos:{stem}", "fail", f"{stem}.mp4 or .mov not found in video/final/"))
            continue
        v = cands[0]
        size = v.stat().st_size
        fmt = _probe(v)
        if fmt is None:
            out.append(Result(f"videos:{stem}", "warn", f"{v.name} {human_bytes(size)}; ffprobe not installed, duration not checked"))
            continue
        dur = float(fmt.get("duration", 0) or 0)
        probs = []
        if dur <= 0:
            probs.append("could not read duration")
        elif dur > MAX_SECONDS:
            probs.append(f"duration {dur:.1f}s > 60s")
        if size > MAX_BYTES:
            probs.append(f"size {human_bytes(size)} > 1 GB")
        out.append(Result(f"videos:{stem}", "fail" if probs else "pass",
                          "; ".join(probs) if probs else f"{v.name}: {dur:.1f}s, {human_bytes(size)}"))

    cov = root / "video/COVERAGE.md"
    if not cov.exists():
        out.append(Result("videos:coverage", "fail", "video/COVERAGE.md missing: tick which video covers PDF items (a) to (e)"))
    else:
        txt = read_text(cov)
        missing = [i for i in ITEMS if i not in txt]
        out.append(Result("videos:coverage", "fail" if missing else "pass",
                          "items not mapped: " + ", ".join(missing) if missing else "items (a) to (e) all mapped to a video"))
    return out
