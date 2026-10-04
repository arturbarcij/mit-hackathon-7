"""Plan and run lanes: STATUS -> ready tasks -> agent in a sandbox -> gates -> write back."""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from . import agent as agent_mod
from .config import Lane, load_lanes
from .gates import baseline, lane_tests, qa_fail_count, qa_veto
from .scheduler import Plan, batches, plan
from .status import (Task, append_log, append_request, parse_board, parse_ownership, parse_requests, update_row)
from .tools import Sandbox

REVIEW_DIRS = {"judge": "kb/judge", "redteam": "kb/redteam", "agronomist": "kb/agronomy", "mathematician": "kb/math",
               "security-privacy": "kb/security", "ux-designer": "kb/ux", "user-simulator": "kb/usersim",
               "release-manager": "kb/release"}


@dataclass
class Outcome:
    task: str
    lane: str
    status: str
    summary: str
    gate: str
    files: list[str]
    requests: list[dict]
    tokens: int


def load(root: Path):
    status_text = (root / "kb/STATUS.md").read_text(encoding="utf-8")
    return (parse_board(status_text), parse_requests(status_text), load_lanes(),
            parse_ownership((root / "kb/OWNERSHIP.md").read_text(encoding="utf-8")))


def make_plan(root: Path, **kw) -> tuple[Plan, list[dict]]:
    tasks, requests, lanes, _ = load(root)
    return plan(tasks, lanes, **kw), requests


def task_prompt(t: Task, lane: Lane, requests: list[dict]) -> str:
    mine = [r for r in requests if r["to"].lower().split("/")[0].strip() in (lane.name, *[a.lower() for a in lane.owner_aliases])]
    req_txt = "\n".join(f"- from {r['from']}: {r['text']}" for r in mine) or "(none)"
    return (f"Task {t.id}: {t.task}\nTarget: {t.target}. Current status: {t.status}. Note: {t.note or '(none)'}\n\n"
            f"Open requests addressed to your lane (handle the ones this task covers):\n{req_txt}\n\n"
            "Start by reading kb/STATUS.md and the files the task names. Make the smallest change that completes the task, "
            "run your lane's checks, then call finish with status and a one or two sentence summary for the STATUS row.")


def run_task(root: Path, t: Task, lane: Lane, requests: list[dict], ownership, client, *, dry_run: bool,
             qa_baseline: int | None, run_dir: Path, model: str) -> Outcome:
    review_dir = REVIEW_DIRS.get(lane.name, f"kb/{lane.name}") if lane.review else None
    before = None if dry_run else baseline(root, lane.tests)
    sb = Sandbox(root=root, lane=lane.name, ownership=ownership, review=lane.review, report_dir=review_dir, dry_run=dry_run)
    res = agent_mod.run_agent(client, sb, lane=lane.name, brief_path=lane.brief, task_prompt=task_prompt(t, lane, requests),
                              tests=lane.tests, review_dir=review_dir, max_turns=lane.max_turns, model=model)
    files = list(sb.writes)
    if dry_run:
        gate, status = "dry run: no gate", res.status
    else:
        g = lane_tests(root, lane.tests, before)
        if g.ok and not lane.review and files:
            g2 = qa_veto(root, qa_baseline)
            g = g2 if not g2.ok else type(g)(True, g.detail + "; " + g2.detail)
        gate = g.detail
        status = res.status if g.ok else "blocked"
        if not g.ok:
            restored = sb.rollback()
            gate += f"; rolled back {len(restored)} file(s)"
            files = []
    rec = agent_mod.to_jsonable(res) | {"task": t.id, "lane": lane.name, "gate": gate, "final_status": status, "sandbox_log": sb.log}
    (run_dir / f"{t.id}.json").write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
    return Outcome(t.id, lane.name, status, res.summary, gate, files, res.requests, res.tokens_in + res.tokens_out)


def write_back(root: Path, o: Outcome, stamp: str) -> None:
    status_path = root / "kb/STATUS.md"
    note = f"orchestrator {stamp}: {o.summary} Gate: {o.gate}."
    if o.files:
        note += f" Files: {', '.join(o.files[:6])}{' ...' if len(o.files) > 6 else ''}."
    update_row(status_path, o.task, o.status, note)
    for r in o.requests:
        append_request(status_path, f"{o.lane} to {r['to']}: {r['text']}")
    append_log(status_path, f"{stamp}: orchestrator ran {o.task} ({o.lane}) -> {o.status}. {o.gate}.")


def run(root: Path, *, client=None, dry_run: bool = False, only_lane: str | None = None, task_ids: list[str] | None = None,
        include_doing: bool = False, max_tasks: int = 5, parallel: int = 1, model: str = agent_mod.DEFAULT_MODEL,
        stamp: str | None = None) -> list[Outcome]:
    tasks, requests, lanes, ownership = load(root)
    p = plan(tasks, lanes, only_lane=only_lane, include_doing=include_doing, task_ids=task_ids)
    chosen = p.ready[:max_tasks]
    stamp = stamp or time.strftime("%Y%m%d_%H%M")
    run_dir = root / "app/orchestrator/runs" / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    if client is None:
        client = agent_mod.AnthropicClient(root)
    qa_baseline = None if dry_run else qa_fail_count(root)
    outcomes: list[Outcome] = []
    # Gates share one working tree, so they run one at a time; agents in a round may think in parallel.
    for rnd in batches(chosen):
        workers = max(1, parallel) if dry_run else 1   # real runs share one tree: one agent at a time
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(run_task, root, t, lane, requests, ownership, client, dry_run=dry_run,
                              qa_baseline=qa_baseline, run_dir=run_dir, model=model) for t, lane in rnd]
            results = [f.result() for f in futs]
        outcomes += results
    if not dry_run:
        for o in outcomes:
            write_back(root, o, stamp)
    summary = {"stamp": stamp, "dry_run": dry_run, "outcomes": [o.__dict__ for o in outcomes],
               "waiting": [{"task": t.id, "reason": r} for t, r in p.waiting]}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return outcomes
