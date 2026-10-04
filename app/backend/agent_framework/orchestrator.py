"""Run audit seats in dependency order.

Ready seats run together. A seat starts only after the seats it depends on
have finished. Finishing includes a failed or blocked call: later seats still
run, and they are told that the earlier audit did not return JSON.

Nothing in this module writes product files.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from .graph import build_plan, edges_for
from .roster import AgentSpec
from .runner import Completer, execute_agent


def blocked_report(spec: AgentSpec, error: str, state: str) -> dict:
    """A seat record with no model text and no invented findings."""
    return {
        "agent": spec.id,
        "ok": False,
        "verdict": "blocked",
        "summary": "",
        "findings": [],
        "error": error,
        "state": state,
        "called": False,
    }


async def orchestrate(
    specs: list[AgentSpec],
    pack: dict,
    root: Path,
    api_key: str,
    model: str,
    concurrency: int = 8,
    completer: Completer | None = None,
    trace: list[dict] | None = None,
) -> tuple[list[dict], dict]:
    """Run specs in DAG order. Returns reports in roster order, and the plan."""
    selected = [spec.id for spec in specs]
    by_id = {spec.id: spec for spec in specs}
    edges = edges_for(selected)
    deps: dict[str, set[str]] = {agent_id: set() for agent_id in selected}
    dep_order: dict[str, list[str]] = {agent_id: [] for agent_id in selected}
    for src, dst in edges:
        deps[dst].add(src)
        dep_order[dst].append(src)

    state = {agent_id: "pending" for agent_id in selected}
    results: dict[str, dict] = {}
    finished: set[str] = set()
    pending = set(selected)
    tasks: dict[asyncio.Task, str] = {}
    semaphore = asyncio.Semaphore(max(1, concurrency))

    def mark(agent_id: str, event: str) -> None:
        if trace is None:
            return
        trace.append({"agent": agent_id, "event": event, "t": time.perf_counter()})

    async def launch(agent_id: str) -> None:
        spec = by_id[agent_id]
        async with semaphore:
            state[agent_id] = "running"
            mark(agent_id, "start")
            upstream = [dict(results[dep]) for dep in dep_order[agent_id]]
            payload = {"evidence": pack, "upstream_audits": upstream}
            try:
                report = await execute_agent(
                    spec,
                    root,
                    api_key,
                    model,
                    payload,
                    completer,
                )
            finally:
                mark(agent_id, "finish")
            report["state"] = "done" if report.get("ok") else "blocked"
            report["called"] = True
            state[agent_id] = report["state"]
            results[agent_id] = report

    while pending or tasks:
        ready = [
            agent_id
            for agent_id in selected
            if agent_id in pending and deps[agent_id] <= finished
        ]
        for agent_id in ready:
            pending.remove(agent_id)
            task = asyncio.create_task(launch(agent_id))
            tasks[task] = agent_id
        if not tasks:
            if pending:
                stuck = ", ".join(sorted(pending))
                raise RuntimeError(f"Orchestrator deadlock. Still waiting: {stuck}")
            break
        done, _pending = await asyncio.wait(set(tasks), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            agent_id = tasks.pop(task)
            task.result()
            finished.add(agent_id)

    ordered = [results[spec.id] for spec in specs]
    plan = build_plan(specs, edges, state, claude="called", block_reason=None)
    return ordered, plan
