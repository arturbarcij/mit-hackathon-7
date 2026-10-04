# Orchestrator

This package runs Jani's agent lanes. It is the code version of the process in `kb/WORKFLOW.md`.

The markdown in `kb/` stays the source of truth:
- the agent briefs in `kb/agents/`;
- the task board in `kb/STATUS.md`;
- the path owners in `kb/OWNERSHIP.md`.

For each task, the orchestrator decides whether it is ready, runs one Claude agent with tools that enforce ownership, gates the change on the lane's checks, and writes the result back to that task's STATUS row.

```
STATUS board ──> plan ──> agent (sandboxed tools) ──> gates ──> keep or roll back ──> STATUS row + Requests + run log
                  │               │                     │
          deps, humans,   writes only owned paths,   lane checks must not break;
          manual lanes    allowed commands only      QA FAIL count must not rise
```

## Use (from `app/`)

```
python -m orchestrator plan                    # what is ready and why the rest waits
python -m orchestrator requests                # open Requests grouped by lane
python -m orchestrator run --fake              # offline demo with a scripted agent, changes nothing
python -m orchestrator run --dry-run --task E4 # a real agent plans; nothing is written and no command runs
python -m orchestrator run --task E4           # run one task for real
python -m orchestrator run --lane docs --max-tasks 2
python -m orchestrator loop --every 30 --stop-at 13:30
```

Real runs need `ANTHROPIC_API_KEY`, either in the environment or in `app/backend/.env`. Install the SDK with `pip install anthropic`. To pick the model, set `ORCH_MODEL`; the default is in `agent.py`. Run logs go to `app/orchestrator/runs/<stamp>/`, which git ignores. Each run log holds the full transcript, every refused write and the gate result.

## Rules the code enforces

- **Humans stay in charge.** Tasks owned by Arthur are never dispatched. Nothing is committed, pushed or sent.
- **One owner per path.** `write_file` checks `kb/OWNERSHIP.md`, and the most specific pattern wins.
  - A write to another lane's path is refused, and the agent is told to use `request_change`. The orchestrator posts that to STATUS Requests.
  - `kb/STATUS.md`, `MASTER_PROMPT.md`, `DECISIONS.md` and `OWNERSHIP.md` are lead-only.
  - `.env` files, `data_raw/`, `.git/` and `node_modules/` can be neither read nor written.
- **Review lanes write reports only.** judge, redteam, security-privacy, ux-designer, user-simulator, agronomist, mathematician and release-manager may write only to their `kb/<lane>/` folder.
- **Allowed commands only.** The `run` tool accepts tests, type checks, the build, the QA harness and read-only git commands, optionally after a single `cd app &&`. Command chaining, pipes, redirects and `..` are refused.
- **Gates.** The orchestrator records which lane checks pass before the agent starts.
  - If the agent breaks a check that passed before, all of the agent's writes are rolled back and the task is marked `blocked`.
  - QA holds the veto (WORKFLOW rule 8): if the FAIL count in `app/qa/report.md` rises, the change is also rolled back.
- **Manual lanes.** These are listed with a reason and never dispatched:
  - ml (needs the laptop GPU);
  - geo (needs satellite access);
  - ui (Lovable builds the UI);
  - lead decisions.
- **Order and safety in parallel.** Critical-path tasks (E, M, U, Q, S) run first. A real run executes one agent at a time, because gates share one working tree. Dry runs can use `--parallel`.

## Files

| File | Role |
|---|---|
| `lanes.json` | Lane registry: brief, auto or manual, owner aliases, gate checks. |
| `status.py` | Parses the STATUS board, `needs X` dependencies, Requests and the OWNERSHIP table. Edits one row at a time. |
| `scheduler.py` | Works out which tasks are ready and why the others wait. Groups tasks into rounds that never share a lane. |
| `tools.py` | The sandbox: read, list, search, write, replace, run, request_change and finish, plus rollback. |
| `agent.py` | The tool-use loop on the Anthropic Messages API, plus a scripted client for tests. |
| `gates.py` | Lane checks against their baseline, and the QA veto. |
| `runner.py` | Plan, run, gate, write back, and log. |
| `tests/` | 15 pytest cases: parsing, ownership, scheduling, sandbox escapes, rollback, end-to-end gate pass and gate fail. |

Tests: `python -m pytest orchestrator/tests -q`.

## Limits

- One working tree means one real agent at a time. Worktree isolation would allow true parallel runs.
- Dependencies come only from `needs X` in the STATUS note. Requests are passed to the agent as context. They are not tasks in their own right.
- The gate checks only what the lane's checks and the QA harness cover. A person still reviews every change before it is committed.
