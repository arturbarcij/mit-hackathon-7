"""CLI: python -m agent_framework --root <workspace>

From app/backend, or with PYTHONPATH pointing at app/backend.

The default run orchestrates the audit DAG. --static-only skips Claude.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from .client import AgentClientError, load_api_key, model_name
from .graph import build_plan, edges_for
from .orchestrator import blocked_report, orchestrate
from .report import write_run
from .roster import select_agents
from .snapshot import build_pack

# This file lives at app/backend/agent_framework/__main__.py
DEFAULT_ROOT = Path(__file__).resolve().parents[3]

STATIC_ERROR = "Static only. Claude was not called."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Orchestrate Jani audit seats in dependency order. They check the app and do not edit it."
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Workspace root that contains app/ and kb/.")
    parser.add_argument("--out", type=Path, default=None, help="Report directory. Default: kb/agent-runs/<stamp>.")
    parser.add_argument(
        "--agents",
        default="",
        help="Comma-separated agent ids. Default: the full roster. Edges that touch a dropped seat are removed.",
    )
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument(
        "--orchestrate",
        action="store_true",
        help="Run the audit DAG. This is the default; the flag is accepted so the command can say so.",
    )
    parser.add_argument("--static-only", action="store_true", help="Write the file probe matrix and do not call Claude.")
    args = parser.parse_args(argv)
    # Orchestration is the default path. --orchestrate does not change it.
    _ = args.orchestrate

    root = args.root.resolve()
    if not (root / "app").is_dir() or not (root / "kb").is_dir():
        print(f"Root {root} does not contain app/ and kb/.", file=sys.stderr)
        return 1

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out or (root / "kb" / "agent-runs" / stamp)
    pack = build_pack(root)
    names = [part for part in args.agents.split(",") if part.strip()]
    specs = select_agents(names or None)
    edges = edges_for(spec.id for spec in specs)

    claude_results = None
    plan = None
    error = None
    model = None
    exit_code = 0
    if args.static_only:
        error = STATIC_ERROR
        claude_results = [blocked_report(spec, error, "skipped") for spec in specs]
        plan = build_plan(
            specs,
            edges,
            {spec.id: "skipped" for spec in specs},
            claude="not_called",
            block_reason=error,
        )
    else:
        try:
            api_key = load_api_key(root)
        except AgentClientError as exc:
            error = str(exc)
            exit_code = 2
            claude_results = [blocked_report(spec, error, "blocked") for spec in specs]
            plan = build_plan(
                specs,
                edges,
                {spec.id: "blocked" for spec in specs},
                claude="not_called",
                block_reason=error,
            )
        else:
            model = model_name()
            print(
                f"Orchestrating {len(specs)} audit seats on {model} with concurrency {args.concurrency}.",
                file=sys.stderr,
            )
            claude_results, plan = asyncio.run(
                orchestrate(
                    specs,
                    pack,
                    root,
                    api_key,
                    model,
                    concurrency=args.concurrency,
                )
            )
            failed = [item["agent"] for item in claude_results if not item.get("ok")]
            if failed:
                print("Agents that did not return JSON: " + ", ".join(failed), file=sys.stderr)
                exit_code = 1

    summary = write_run(out_dir, pack, claude_results, model, error, plan)
    tally = pack["tally"]
    print(
        f"Wrote {summary}. Matrix pass {tally['pass']} fail {tally['fail']} missing {tally['missing']}."
    )
    if error and exit_code == 2:
        print(error, file=sys.stderr)
    if tally["blockers"]:
        # A product fail is still a successful run of the checker.
        print(f"Product blockers: {tally['blockers']}.", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
