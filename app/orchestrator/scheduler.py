"""Decide which STATUS tasks an agent may run now, and explain the rest."""
from __future__ import annotations

from dataclasses import dataclass

from .config import Lane, lane_for_owner
from .status import DONE, Task

# Tasks on the critical path go first (WORKFLOW.md section 3).
CRITICAL_PREFIXES = ("E", "M", "U", "Q", "S")


@dataclass
class Plan:
    ready: list[tuple[Task, Lane]]
    waiting: list[tuple[Task, str]]   # (task, reason)


def plan(tasks: list[Task], lanes: dict[str, Lane], only_lane: str | None = None,
         include_doing: bool = False, task_ids: list[str] | None = None) -> Plan:
    by_id = {t.id: t for t in tasks}
    ready, waiting = [], []
    for t in tasks:
        if task_ids and t.id not in task_ids:
            continue
        if t.status in DONE:
            continue
        lane = lane_for_owner(t.owner, lanes)
        if lane is None:
            waiting.append((t, "human task (Arthur)" if t.owner.lower().startswith("arthur") else f"no lane for owner '{t.owner}'"))
            continue
        if only_lane and lane.name != only_lane:
            continue
        if lane.dispatch != "auto":
            waiting.append((t, f"manual lane '{lane.name}': {lane.reason}"))
            continue
        if t.status == "blocked":
            waiting.append((t, "blocked: " + t.note[:80]))
            continue
        if t.status == "doing" and not include_doing:
            waiting.append((t, "already in progress elsewhere (use --include-doing to take it over)"))
            continue
        missing = [d for d in t.needs if d in by_id and by_id[d].status not in DONE]
        if missing:
            waiting.append((t, "needs " + ", ".join(f"{d} ({by_id[d].status})" for d in missing)))
            continue
        ready.append((t, lane))
    ready.sort(key=lambda tl: (0 if tl[0].id.startswith(CRITICAL_PREFIXES) else 1, tl[0].id))
    return Plan(ready, waiting)


def batches(ready: list[tuple[Task, Lane]]) -> list[list[tuple[Task, Lane]]]:
    """Group into rounds where no two tasks share a lane, so parallel agents never touch the same paths."""
    rounds: list[list[tuple[Task, Lane]]] = []
    for tl in ready:
        for r in rounds:
            if all(x[1].name != tl[1].name for x in r):
                r.append(tl)
                break
        else:
            rounds.append([tl])
    return rounds
