# Jani agent framework

Read-only reviewers. They call the Claude API at the same time, on one evidence pack, and write a report. They do not edit the app.

## Run

From the workspace root:

```bash
PYTHONPATH=app/backend python3 -m agent_framework --root .
```

Static file matrix only, no API call:

```bash
PYTHONPATH=app/backend python3 -m agent_framework --root . --static-only
```

A subset:

```bash
PYTHONPATH=app/backend python3 -m agent_framework --root . --agents qa,redteam,judge
```

## Key

`ANTHROPIC_API_KEY` in the environment, or in `app/backend/.env`. That file is git-ignored. The runner never prints the key. Do not put the key in a `VITE_` variable.

Optional: `CLAUDE_MODEL` (default `claude-sonnet-5-5`).

## Roster

qa, redteam, judge, engine, ui, content, docs, ml. Briefs are in `kb/agents/`. The engine, ui, content, docs, and ml seats audit only. They do not take over those paths.

## Output

`kb/agent-runs/<stamp>/summary.md`, `pack.json`, and `claude.json` when the API ran.

The static matrix is the file check. Claude reviewers may dispute a row, but they may not mark a missing file as present.

## Tests

```bash
cd app/backend && python3 -m unittest discover -s agent_framework/tests -t .
```
