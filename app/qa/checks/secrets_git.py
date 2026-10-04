"""Repo is safe to make public: .env not tracked, no key-like strings in history (S2)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from qa.common import Result
from qa.checks.client_clean import SECRET_RE

PRIVATE_FILES = ["backend/.env", ".env", ".mcp.json", ".cursor/mcp.json", "world_bank_Challenge.pdf"]


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=120,
                           encoding="utf-8", errors="replace")
        return p.returncode, p.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def run(root: Path) -> list[Result]:
    code, top = _git(root, "rev-parse", "--show-toplevel")
    if code != 0:
        return [Result("secrets_git", "skip", "not inside a git repo (or git missing)")]
    repo = Path(top.strip())
    out: list[Result] = []

    _, tracked = _git(repo, "ls-files")
    tracked_set = set(tracked.split())
    leaked = [f for f in tracked_set if any(f.endswith(pf) or f == pf for pf in PRIVATE_FILES)]
    out.append(Result("secrets_git:tracked_private_files", "fail" if leaked else "pass",
                      "private files are tracked by git" if leaked else "no private files tracked", leaked))

    _, hist = _git(repo, "log", "-p", "--all", "--no-color", "-M", "--diff-filter=AM",
                   "--", ".", ":(exclude)*.onnx", ":(exclude)*.mp3", ":(exclude)*.png", ":(exclude)*.jpg")
    hits = sorted({m.group(0)[:12] + "..." for m in SECRET_RE.finditer(hist)})
    out.append(Result("secrets_git:history", "fail" if hits else "pass",
                      f"{len(hits)} key-like string(s) in git history: rotate the key and rewrite history before going public" if hits else "no key-like strings in git history",
                      hits))

    lic = (repo / "LICENSE").exists() or (root / "LICENSE").exists()
    out.append(Result("secrets_git:license", "pass" if lic else "warn", "LICENSE present" if lic else "LICENSE missing (MIT planned)"))
    return out
