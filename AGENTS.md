# Jani (MIT AI Hackathon 7)

Read `kb/MASTER_PROMPT.md` first. Agent briefs are in `kb/agents/`; matching Claude Code agents are in `.claude/agents/`. Ownership rules: `kb/OWNERSHIP.md`. Contracts: `kb/CONTRACTS.md`. Status: `kb/STATUS.md`. Decisions: `kb/DECISIONS.md`.

The Git repository root is this directory. The Vite app lives in `app/`. API keys live in `app/backend/.env` (git-ignored). Never print or commit them.

## Cursor Cloud specific instructions

- The runnable product is the Vite + React app in `app/`. There is no root `package.json` and no backend server yet.
- From `app/`, install with `npm ci` when `package-lock.json` is present, otherwise `npm install`.
- Lint: `npm run lint` (oxlint). Type-check and production build: `npm run build` (`tsc -b && vite build`). There is no automated test script yet.
- Dev server: `npm run dev -- --host 0.0.0.0 --port 5173`. Vite listens on localhost only unless `--host` is set.
- The current UI does not call external APIs. `app/backend/.env` is optional and unused by the app.
- Helpers under `kb/research/` use the Python standard library, except `pdf_to_raw.py`, which imports `pypdf`.
