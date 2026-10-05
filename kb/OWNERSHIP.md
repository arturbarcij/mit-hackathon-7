# Ownership

Who may edit what. One owner per path. If you need a change in a path you do not own, write the request in `kb/STATUS.md` under "Requests" and tell the lead. This file exists because Lovable and Cursor both push to the same `main` branch; overlapping edits get overwritten.

## Folder layout
```
MIT_Hackathon_7/              git repo
  kb/                         knowledge base and agent briefs
    agents/                   prompts for each agent
    claude-agents/            Claude Code agent definitions
    research/                 evidence, datasets, guidance
  .cursor/rules/              Cursor rules
  app/                        product (Lovable-synced)
    src/  public/             web app
    ml/                       training and evaluation code
    backend/                  build-time scripts (audio rendering, research helpers)
    docs/                     judge-facing docs
  data_raw/                   downloaded datasets (not committed)
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
| `app/src/content/answers.json`, `rules.json`, `season.json`, `i18n/**` | content-voice | Cursor |
| `app/public/audio/**`, `app/backend/scripts/**` | content-voice | Cursor + ElevenLabs |
| `app/src/content/sources.json` | docs | Cursor |
| `app/README.md`, `app/docs/**` (except numbers in EVALUATION.md), `app/LICENSE` | docs | Cursor / Claude |
| `app/docs/EVALUATION.md` numbers and plots | ml | Cursor |
| `app/backend/agent_framework/**` | lead | Cursor |
| `kb/agents/qa.md`, `kb/agents/redteam.md`, `kb/agents/judge.md` | lead | Cursor |

The orchestrator under `app/backend/agent_framework/` is an audit runner. Every seat reports gaps and does not take ownership of product paths.

## Git rules
- Lovable writes to `main`. Cursor agents pull before every push, commit small, never force-push, never rewrite history.
- Commit message prefix with the agent name: `engine: add quality gate`.
- Never commit raw data or model checkpoints other than `public/model/leaf.onnx`.
