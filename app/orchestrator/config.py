"""Paths and lane registry."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

PKG = Path(__file__).resolve().parent


def find_root(start: Path | None = None) -> Path:
    """The workspace root holds kb/ and app/ (MIT_Hackathon_7/). Override with JANI_ROOT."""
    env = os.environ.get("JANI_ROOT")
    if env:
        return Path(env).resolve()
    p = (start or PKG).resolve()
    for cand in [p, *p.parents]:
        if (cand / "kb" / "STATUS.md").exists() and (cand / "app").is_dir():
            return cand
    raise SystemExit("Cannot find the workspace root (a folder with kb/STATUS.md and app/). Set JANI_ROOT.")


@dataclass
class Lane:
    name: str
    brief: str
    dispatch: str                     # "auto" (an API agent may run it) or "manual" (another tool or a human runs it)
    reason: str = ""                  # why manual
    owner_aliases: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)   # commands run from the root; all must exit 0
    review: bool = False              # review lanes write reports only, never code
    max_turns: int = 40


def load_lanes(path: Path | None = None) -> dict[str, Lane]:
    path = path or Path(os.environ.get("ORCH_LANES", PKG / "lanes.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    return {d["name"]: Lane(**d) for d in data["lanes"]}


def lane_for_owner(owner: str, lanes: dict[str, Lane]) -> Lane | None:
    """Map a STATUS owner cell ('qa (Claude)', 'engine-cowork (Claude Cowork)') to a lane."""
    o = owner.strip().lower()
    if not o or o.startswith("arthur"):
        return None
    head = o.split("(")[0].strip()
    for lane in lanes.values():
        if head == lane.name or head in [a.lower() for a in lane.owner_aliases]:
            return lane
    return None
