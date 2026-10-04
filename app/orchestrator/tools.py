"""The agent's only way to touch the workspace. Every write is checked against kb/OWNERSHIP.md."""
from __future__ import annotations

import fnmatch
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .status import owner_of

# Never readable or writable by any agent.
FORBIDDEN = ["app/backend/.env", "**/.env", "**/.env.*", "data_raw/**", ".git/**", "**/node_modules/**", "kb/world_bank_Challenge.pdf"]
# Shared files only the orchestrator itself edits (STATUS rows are written back after the gate).
LEAD_ONLY = ["kb/STATUS.md", "kb/MASTER_PROMPT.md", "kb/DECISIONS.md", "kb/OWNERSHIP.md", "app/orchestrator/**"]
# Commands an agent may run. Anything else is refused.
ALLOWED_CMDS = ("npx vitest", "npx tsc", "npm run build", "npm test", "python -m qa.run", "python3 -m qa.run",
                "python app/backend/scripts/sync_to_web.py --dry-run", "node app/scripts/check_parity.mjs",
                "git status", "git diff", "git log")
MAX_READ = 60_000


def _match(rel: str, pats: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, p) or (p.endswith("/**") and rel.startswith(p[:-3] + "/")) for p in pats)


@dataclass
class Sandbox:
    root: Path
    lane: str
    ownership: list[tuple[str, str]]
    review: bool = False
    report_dir: str | None = None           # review lanes may write only here, e.g. kb/judge
    dry_run: bool = False
    writes: dict[str, bytes | None] = field(default_factory=dict)   # rel -> original bytes (None = new file)
    log: list[str] = field(default_factory=list)

    def _rel(self, path: str) -> str:
        p = (self.root / path).resolve()
        if not p.is_relative_to(self.root.resolve()):
            raise PermissionError(f"outside the workspace: {path}")
        return p.relative_to(self.root.resolve()).as_posix()

    def can_write(self, rel: str) -> tuple[bool, str]:
        if _match(rel, FORBIDDEN):
            return False, "forbidden path"
        if _match(rel, LEAD_ONLY):
            return False, "lead-only file; write a request instead"
        if self.review:
            if self.report_dir and rel.startswith(self.report_dir.rstrip("/") + "/"):
                return True, "review report"
            return False, f"review lanes write only to {self.report_dir}/"
        own = owner_of(rel, self.ownership)
        if own == self.lane:
            return True, "owned"
        return False, f"owned by '{own}'" if own else "path has no owner in OWNERSHIP.md"

    # ---- tool implementations ----
    def read_file(self, path: str) -> str:
        try:
            rel = self._rel(path)
        except PermissionError as e:
            return f"REFUSED: {e}"
        if _match(rel, FORBIDDEN):
            return "ERROR: forbidden path"
        f = self.root / rel
        if not f.is_file():
            return f"ERROR: no such file {rel}"
        data = f.read_text(encoding="utf-8", errors="replace")
        return data if len(data) <= MAX_READ else data[:MAX_READ] + f"\n[truncated at {MAX_READ} chars of {len(data)}]"

    def list_dir(self, path: str = ".") -> str:
        try:
            rel = self._rel(path)
        except PermissionError as e:
            return f"REFUSED: {e}"
        d = self.root / rel
        if not d.is_dir():
            return f"ERROR: not a directory {rel}"
        items = []
        for p in sorted(d.iterdir()):
            r = p.relative_to(self.root).as_posix()
            if p.name in ("node_modules", ".git", "__pycache__") or _match(r, FORBIDDEN):
                continue
            items.append(r + ("/" if p.is_dir() else f"  ({p.stat().st_size} B)"))
        return "\n".join(items[:400]) or "(empty)"

    def search(self, pattern: str, path: str = ".") -> str:
        try:
            rel = self._rel(path)
        except PermissionError as e:
            return f"REFUSED: {e}"
        try:
            out = subprocess.run(["grep", "-rnI", "--exclude-dir=node_modules", "--exclude-dir=.git", "--exclude=.env",
                                  "-e", pattern, rel], cwd=self.root, capture_output=True, text=True, timeout=30)
        except FileNotFoundError:
            return "ERROR: grep not available"
        lines = out.stdout.splitlines()
        return "\n".join(lines[:200]) + (f"\n[{len(lines) - 200} more]" if len(lines) > 200 else "") or "(no matches)"

    def write_file(self, path: str, content: str) -> str:
        try:
            rel = self._rel(path)
        except PermissionError as e:
            return f"REFUSED: {e}"
        ok, why = self.can_write(rel)
        if not ok:
            self.log.append(f"REFUSED write {rel}: {why}")
            return f"REFUSED: {rel} ({why}). If another lane must change it, call request_change."
        f = self.root / rel
        if rel not in self.writes:
            self.writes[rel] = f.read_bytes() if f.exists() else None
        if self.dry_run:
            self.log.append(f"dry-run write {rel} ({len(content)} chars)")
            return f"dry-run: would write {rel}"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        self.log.append(f"wrote {rel} ({len(content)} chars)")
        return f"wrote {rel}"

    def replace_in_file(self, path: str, old: str, new: str) -> str:
        cur = self.read_file(path)
        if cur.startswith("ERROR"):
            return cur
        n = cur.count(old)
        if n != 1:
            return f"ERROR: old text found {n} times; it must match exactly once"
        return self.write_file(path, cur.replace(old, new, 1))

    def run(self, command: str) -> str:
        cmd = command.strip()
        parts = [x.strip() for x in cmd.split("&&")]
        if len(parts) == 2 and re.fullmatch(r"cd [\w./-]+", parts[0]) and ".." not in parts[0]:
            bare = parts[1]
        elif len(parts) == 1:
            bare = parts[0]
        else:
            bare = ""
        if not bare.startswith(ALLOWED_CMDS) or any(x in cmd for x in (";", "|", "`", "$(", ">", "<", "\n")):
            return f"REFUSED: only these commands are allowed: {', '.join(ALLOWED_CMDS)} (optionally after 'cd app &&')"
        if self.dry_run:
            return f"dry-run: would run {cmd}"
        p = subprocess.run(cmd, shell=True, cwd=self.root, capture_output=True, text=True, timeout=600)
        out = (p.stdout + p.stderr)[-8000:]
        self.log.append(f"ran `{cmd}` -> exit {p.returncode}")
        return f"exit {p.returncode}\n{out}"

    def rollback(self) -> list[str]:
        """Restore every file this agent wrote. Used when the gate fails."""
        restored = []
        for rel, orig in self.writes.items():
            f = self.root / rel
            if orig is None:
                if f.exists():
                    f.unlink()
            else:
                f.write_bytes(orig)
            restored.append(rel)
        return restored


TOOL_SCHEMAS = [
    {"name": "read_file", "description": "Read a UTF-8 file relative to the workspace root.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "list_dir", "description": "List a directory relative to the workspace root.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}},
    {"name": "search", "description": "grep -rn for a pattern under a path.",
     "input_schema": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}},
    {"name": "write_file", "description": "Create or replace a file. Only paths your lane owns in kb/OWNERSHIP.md are accepted.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "replace_in_file", "description": "Replace one exact, unique snippet in a file you own.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}},
    {"name": "run", "description": "Run an allowed check command (tests, type check, build, QA harness) from the workspace root.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "request_change", "description": "Ask another lane (or Arthur) to change something you do not own. Posted to STATUS Requests by the orchestrator.",
     "input_schema": {"type": "object", "properties": {"to": {"type": "string"}, "text": {"type": "string"}}, "required": ["to", "text"]}},
    {"name": "finish", "description": "End the task. status is done, partial or blocked. summary is one or two plain sentences for the STATUS row.",
     "input_schema": {"type": "object", "properties": {"status": {"type": "string", "enum": ["done", "partial", "blocked"]},
                                                         "summary": {"type": "string"}}, "required": ["status", "summary"]}},
]
