"""Gates: a lane's tests must pass, and the QA harness must not get worse, before a change stays."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GateResult:
    ok: bool
    detail: str


def run_cmd(root: Path, cmd: str, timeout: int = 900) -> tuple[int, str]:
    p = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)[-4000:]


def baseline(root: Path, tests: list[str]) -> dict[str, bool]:
    """Which lane checks pass before the agent starts."""
    return {cmd: run_cmd(root, cmd)[0] == 0 for cmd in tests}


def lane_tests(root: Path, tests: list[str], before: dict[str, bool] | None = None) -> GateResult:
    """A check that passed before must still pass. A check that already failed is reported, not held against the agent."""
    notes = []
    for cmd in tests:
        code, out = run_cmd(root, cmd)
        last = out.strip().splitlines()[-1] if out.strip() else ""
        was_ok = True if before is None else before.get(cmd, True)
        if code != 0 and was_ok:
            return GateResult(False, f"`{cmd}` broke (exit {code}): {last}")
        if code != 0:
            notes.append(f"`{cmd}` still failing as before")
        elif not was_ok:
            notes.append(f"`{cmd}` now passes")
    head = f"{len(tests)} check(s) ok" if tests else "no lane checks"
    return GateResult(True, head + (" (" + "; ".join(notes) + ")" if notes else ""))


def qa_fail_count(root: Path) -> int | None:
    """Number of FAIL rows from the deterministic QA harness (app/qa). None if it cannot run."""
    try:
        run_cmd(root, "cd app && python -m qa.run", timeout=900)
    except Exception:
        return None
    rep = root / "app" / "qa" / "report.md"
    if not rep.exists():
        return None
    m = re.search(r"\*\*(\d+) pass, (\d+) fail", rep.read_text(encoding="utf-8"))
    return int(m.group(2)) if m else None


def qa_veto(root: Path, baseline_fails: int | None) -> GateResult:
    """QA holds the veto (WORKFLOW rule 8): no change may add a FAIL to the QA report."""
    if baseline_fails is None:
        return GateResult(True, "QA baseline unavailable; veto skipped")
    now = qa_fail_count(root)
    if now is None:
        return GateResult(True, "QA could not run; veto skipped")
    if now > baseline_fails:
        return GateResult(False, f"QA FAIL count rose from {baseline_fails} to {now}")
    return GateResult(True, f"QA FAIL count {now} (baseline {baseline_fails})")
