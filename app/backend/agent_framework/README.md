# Jani agent framework

Read-only audit orchestrator. Seats run in dependency order, share one evidence pack, and write a local report. They do not edit the app.

## Run

From the workspace root:

```bash
PYTHONPATH=app/backend python3 -m agent_framework --root .
```

That command orchestrates the DAG. The same run with the flag written out:

```bash
PYTHONPATH=app/backend python3 -m agent_framework --root . --orchestrate
```

Static file matrix only:

```bash
PYTHONPATH=app/backend python3 -m agent_framework --root . --static-only
```

A subset. Edges that touch a seat you leave out are dropped, so a remaining seat does not wait for a seat that is not running:

```bash
PYTHONPATH=app/backend python3 -m agent_framework --root . --agents qa,redteam,judge
```

## DAG

Builders and reviewers are audit seats. A builder reports gaps in the paths it knows. It does not edit those paths.

An agent starts only after every seat it depends on has finished. Independent seats in the same wave run together.

- research before content and docs
- ml before engine
- content and engine before ui
- research, ml, engine, ui, content, and docs before qa
- qa before redteam and judge

The direct edges into qa stay in the graph on purpose. If a middle seat is filtered out, qa still waits for each remaining builder.

## Setup

Claude access is optional. If it is not configured, the static matrix still runs once. Each model seat is marked blocked. The run still writes a plan and a summary. The runner does not invent model output.

## Roster

research, ml, engine, ui, content, docs, qa, redteam, judge. Briefs are in `kb/agents/`.

## Output

The runner writes a local report directory (not tracked):

- `plan.json`: nodes, edges, and state
- `<agent>.json`: one file per seat
- `summary.md`: the matrix and the plan
- `pack.json`: the evidence pack

`claude.json` is written only when a Claude call returned JSON.

The static matrix is the file check. Claude reviewers may dispute a row, but they may not mark a missing file as present.

## Tests

```bash
cd app/backend && python3 -m unittest discover -s agent_framework/tests -t .
```
