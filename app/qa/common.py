"""Shared helpers for the Jani QA harness."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

STATUSES = ("pass", "fail", "warn", "skip")


@dataclass
class Result:
    check: str
    status: str  # pass | fail | warn | skip
    detail: str = ""
    items: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        assert self.status in STATUSES, self.status


def read_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} GB"


def dir_size(path: Path, patterns: tuple[str, ...] | None = None) -> int:
    total = 0
    for p in path.rglob("*"):
        if p.is_file() and (patterns is None or p.suffix.lower() in patterns):
            total += p.stat().st_size
    return total


# A "number" worth sourcing: digits followed by %, a unit, or a large bare number.
NUMBER_RE = re.compile(
    r"(?<![\w/\-.:])("
    r"\d[\d,]*\.?\d*\s?%"                     # percentages
    r"|\d[\d,]*\.?\d*\s?(?:MB|KB|GB|ms|s|mm|km|ha|kg|KES|USD|\$)"  # units
    r"|\b\d{1,3}(?:,\d{3})+\b"                # 1,234 style
    r"|\b\d{4,}\b"                            # 4+ digit bare numbers (years included)
    r")(?![\w/\-.:])"
)

# Lines that are exempt from the "every number has a source" rule.
EXEMPT_LINE_RE = re.compile(
    r"(https?://|\[S\d+\]|\(S\d+|\bS\d{2}\b|\[\d+\]|\(source|source:|assumption|synthetic|TODO|"
    r"^\s*\|?\s*-+\s*\|?|^#|^\s*```|version|v\d|\d{4}-\d{2}-\d{2}|opset|"
    r"\d{3,4}\s?px|\d+x\d+|CEST|UTC|deadline|freeze)",
    re.IGNORECASE,
)
