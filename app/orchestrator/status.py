"""Read and update kb/STATUS.md and kb/OWNERSHIP.md without disturbing other agents' rows."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

DONE = {"done"}
OPEN = {"todo", "doing", "partial", "blocked"}
NEEDS_RE = re.compile(r"\bneeds\s+((?:[A-Z]{1,3}\d+[a-z]?)(?:\s*(?:,|and|\+)\s*[A-Z]{1,3}\d+[a-z]?)*)")
ID_RE = re.compile(r"[A-Z]{1,3}\d+[a-z]?")


@dataclass
class Task:
    id: str
    task: str
    owner: str
    target: str
    status: str
    note: str
    line: str

    @property
    def needs(self) -> list[str]:
        """Dependencies written in the note as 'needs M4' or 'needs E1 and U0'."""
        out: list[str] = []
        for m in NEEDS_RE.finditer(self.note):
            out += ID_RE.findall(m.group(1))
        return out


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_board(text: str) -> list[Task]:
    """Rows of the '## Board' table: | ID | Task | Owner | Target | Status | Blocker / note |."""
    tasks, in_board = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            in_board = line.strip() == "## Board"
            continue
        if not in_board or not line.startswith("|"):
            continue
        c = _cells(line)
        if len(c) < 6 or c[0] in ("ID", "") or set(c[0]) <= {"-"}:
            continue
        tasks.append(Task(c[0], c[1], c[2], c[3], c[4].lower(), " | ".join(c[5:]), line))
    return tasks


def parse_requests(text: str) -> list[dict]:
    """Bullets under '## Requests between agents': '- <from> to|-> <to>: <text>'."""
    out, in_req = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            in_req = line.strip().startswith("## Requests")
            continue
        if in_req and line.startswith("- "):
            m = re.match(r"-\s*([\w\- ()]+?)\s+(?:to|->)\s+([\w\-/ ]+?):\s*(.*)", line)
            if m:
                out.append({"from": m.group(1).strip(), "to": m.group(2).strip(), "text": m.group(3).strip()})
    return out


def update_row(path: Path, task_id: str, status: str, note: str) -> bool:
    """Replace one row's status and note. Re-reads the file first, touches only that row."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"| {task_id} |"):
            c = _cells(line)
            c = c[:4] + [status, note.replace("|", "/").replace("\n", " ")]
            lines[i] = "| " + " | ".join(c) + " |"
            path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
            return True
    return False


def append_log(path: Path, entry: str) -> None:
    text = path.read_text(encoding="utf-8").rstrip("\n")
    path.write_text(text + "\n- " + entry.replace("\n", " ") + "\n", encoding="utf-8")


def append_request(path: Path, line: str) -> None:
    text = path.read_text(encoding="utf-8")
    head = "## Requests between agents"
    if head in text and line not in text:
        text = text.replace(head, head + "\n- " + line.replace("\n", " "), 1)
        path.write_text(text, encoding="utf-8")


# ---------- ownership ----------

def parse_ownership(text: str) -> list[tuple[str, str]]:
    """(glob, owner) pairs from the '## Path owners' table. Owner is the first word of the owner cell."""
    out, in_tab = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            in_tab = line.strip() == "## Path owners"
            continue
        if not in_tab or not line.startswith("|"):
            continue
        c = _cells(line)
        if len(c) < 2 or c[0] in ("Path", "") or set(c[0]) <= {"-"}:
            continue
        owner = re.split(r"[\s(]", c[1].strip(), maxsplit=1)[0].lower()
        for g in re.findall(r"`([^`]+)`", c[0]):
            for part in g.split(","):
                out.append((part.strip(), owner))
    return out


def owner_of(rel_path: str, table: list[tuple[str, str]]) -> str | None:
    """Most specific matching glob wins (longest pattern)."""
    rel = rel_path.replace("\\", "/").lstrip("./")
    best: tuple[int, str] | None = None
    for pat, owner in table:
        p = pat.rstrip("/")
        hit = fnmatch.fnmatch(rel, p) or (p.endswith("/**") and rel.startswith(p[:-3] + "/")) \
            or (p.endswith("**") and rel.startswith(p[:-2])) or rel == p
        if hit and (best is None or len(p) > best[0]):
            best = (len(p), owner)
    return best[1] if best else None
