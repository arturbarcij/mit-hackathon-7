# Ownership

Who may edit what. One owner per path. If you need a change in a path you do not own, write the request in `kb/STATUS.md` under "Requests" and tell the lead. This file exists because Lovable and Cursor both push to the same `main` branch; overlapping edits get overwritten.

## Folder layout
```
MIT_Hackathon_7/              Cursor workspace root = the git repo (github.com/arturbarcij/mit-hackathon-7)
  kb/                         knowledge base for agents (private, not in the repo)
  data_raw/                   downloaded datasets (never committed)
  .claude/agents/             Claude Code agent definitions
  .cursor/rules/              Cursor rules
  app/                        the web app (public with the repo after submission)
    src/  public/             web app
    ml/                       training and evaluation code
    backend/                  scripts that use API keys (audio rendering, research helpers)
      .env                    API keys (git-ignored, never committed)
    docs/                     judge-facing docs
```

## Path owners
| Path | Owner agent | Tool |
|---|---|---|
| `kb/MASTER_PROMPT.md`, `kb/STATUS.md`, `kb/DECISIONS.md`, `kb/OWNERSHIP.md` | lead (Arthur + Claude) | Claude |
| `kb/CONTRACTS.md` | engine (ui and content-voice propose changes) | Cursor |
| `kb/research/**` | research | Claude + BrightData |
| `kb/content/**` | content-voice | Claude / Cursor |
| `app/src/pages/**`, `app/src/components/**`, `app/src/App.tsx`, styles | ui | Lovable |
| Supabase / Lovable Cloud tables, auth | ui | Lovable |
| `app/src/engine/**`, `app/src/hooks/useEngine*.ts` | engine | Cursor |
| `app/vite.config.ts`, `app/public/ort/**` | engine | Cursor |
| `app/tests/**` | engine | Cursor |
| `app/public/model/**`, `app/ml/**` | ml | Cursor + local GPU |
| `app/ml/research/**` (overnight research harness; reads app/ml, never writes outside its folder unless a flag says so) | lead | Claude |
| `app/src/content/answers.json`, `rules.json`, `season.json`, `i18n/**` | content-voice | Cursor |
| `app/public/audio/**`, `app/backend/scripts/**` | content-voice | Cursor + ElevenLabs |
| `app/src/content/sources.json` | docs | Cursor |
| `app/README.md`, `app/docs/**` (except numbers in EVALUATION.md), `app/LICENSE` | docs | Cursor / Claude |
| `app/docs/EVALUATION.md` numbers and plots | ml | Cursor |
| `app/geo/**`, `app/public/geo/**`, `kb/geo/**` | geo | Cursor (Windows, satellite access) |
| `app/qa/**`, status and evidence columns of `app/docs/REQUIREMENTS.md` | qa | Claude / Cursor |
| `kb/WORKFLOW.md`, `.cursor/commands/**` | lead | Claude / Cursor |
| `kb/judge/**` | judge | Claude |
| `kb/redteam/**` | redteam | Claude |
| `kb/math/**` | mathematician (reviewer: statistics, sampling, decision rule, evaluation design) | Claude |
| `kb/ux/**` | ux-designer (reviewer: accessibility, low-literacy UX, video style) | Claude |
| `kb/usersim/**` | user-simulator (reviewer: persona walkthroughs of the live app) | Claude |
| `kb/security/**` | security-privacy (reviewer: secrets, access, consent, licences, repo flip) | Claude |
| `kb/release/**` | release-manager (submission checklist, consistency sweep, fallback, go / no-go) | Claude |
| `kb/agronomy/**` | agronomist (reviewer: farmer and extension realism, advice safety, sampling protocol) | Claude |
| `kb/pitch/**`, `video/COVERAGE.md` (video files under `video/` are never committed) | pitch | Claude |
| `kb/engine-cowork/**` | engine-cowork (Cowork helper lanes for engine: PWA proof, parity, contract tests) | Claude (Cowork) |
| `app/orchestrator/**` | lead (orchestrator code; agents may not edit it) | Claude |
| `app/backend/.env` | Arthur only | by hand |

## Git rules
- Lovable writes to `main`. Cursor agents pull before every push, commit small, never force-push, never rewrite history.
- Commit message prefix with the agent name: `engine: add quality gate`.
- Never commit `.env`, raw data, or model checkpoints other than `public/model/leaf.onnx`.
