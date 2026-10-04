"""CLI. Run from app/:  python -m orchestrator <plan|requests|run> [options]"""
from __future__ import annotations

import argparse
import json
import sys

from . import agent as agent_mod
from .config import find_root
from .runner import make_plan, run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="orchestrator", description="Run Jani's agent lanes from kb/STATUS.md")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "run"):
        s = sub.add_parser(name)
        s.add_argument("--lane")
        s.add_argument("--task", action="append", help="task id from STATUS, repeatable")
        s.add_argument("--include-doing", action="store_true", help="also take tasks marked doing")
    r = sub.choices["run"]
    r.add_argument("--dry-run", action="store_true", help="agents may read and plan; nothing is written and no command runs")
    r.add_argument("--fake", action="store_true", help="use a scripted client (no API key); implies --dry-run")
    r.add_argument("--max-tasks", type=int, default=5)
    r.add_argument("--parallel", type=int, default=1, help="parallel agents (dry runs only)")
    r.add_argument("--model", default=agent_mod.DEFAULT_MODEL)
    lp = sub.add_parser("loop", help="run repeatedly until the freeze")
    lp.add_argument("--every", type=int, default=30, help="minutes between rounds")
    lp.add_argument("--stop-at", default="13:30", help="local HH:MM; no round starts after this")
    lp.add_argument("--max-tasks", type=int, default=3)
    lp.add_argument("--model", default=agent_mod.DEFAULT_MODEL)
    sub.add_parser("requests")
    a = ap.parse_args(argv)
    root = find_root()

    if a.cmd == "plan":
        p, _ = make_plan(root, only_lane=a.lane, include_doing=a.include_doing, task_ids=a.task)
        print(f"READY ({len(p.ready)})")
        for t, lane in p.ready:
            print(f"  {t.id:5} {lane.name:16} {t.task[:70]}")
        print(f"\nWAITING ({len(p.waiting)})")
        for t, why in p.waiting:
            print(f"  {t.id:5} {why[:100]}")
        return 0

    if a.cmd == "requests":
        _, reqs = make_plan(root)
        by: dict[str, list[str]] = {}
        for q in reqs:
            by.setdefault(q["to"], []).append(f"[{q['from']}] {q['text'][:110]}")
        for to, items in sorted(by.items()):
            print(f"{to} ({len(items)})")
            for i in items:
                print("  - " + i)
        return 0

    if a.cmd == "loop":
        import time
        hh, mm = map(int, a.stop_at.split(":"))
        while True:
            now = time.localtime()
            if (now.tm_hour, now.tm_min) >= (hh, mm):
                print(f"stop: it is past {a.stop_at}; freeze rule")
                return 0
            outs = run(root, max_tasks=a.max_tasks, model=a.model)
            print(time.strftime("%H:%M"), [(o.task, o.status) for o in outs] or "nothing ready", flush=True)
            time.sleep(a.every * 60)

    client = None
    if a.fake:
        a.dry_run = True
        client = agent_mod.ScriptedClient([[{"name": "read_file", "input": {"path": "kb/STATUS.md"}}],
                                           [{"name": "finish", "input": {"status": "partial", "summary": "fake run: read STATUS only"}}]])
    outs = run(root, client=client, dry_run=a.dry_run, only_lane=a.lane, task_ids=a.task, include_doing=a.include_doing,
               max_tasks=a.max_tasks, parallel=a.parallel, model=a.model)
    print(json.dumps([o.__dict__ for o in outs], indent=1))
    return 0 if all(o.status != "blocked" for o in outs) else 1


if __name__ == "__main__":
    sys.exit(main())
