# Prompts: what to paste where

One person, many lanes. Each prompt is self-contained: paste it into a fresh Cursor Agent chat (Ctrl+L, "New chat") unless it says Lovable or Gemini. Agents read their brief in `kb/agents/` and stay inside the paths in `kb/OWNERSHIP.md`.

| # | Lane | Where | Start | Status |
|---|---|---|---|---|
| 01 | research pass 2 (Bright Data) | Cursor, same chat as research | now, optional | |
| 02 | ml | Cursor chat | now | |
| 03 | engine | Cursor chat | now | |
| 04 | geo | Cursor chat | running | running |
| 05 | content-voice | Cursor chat | after GUIDANCE.md (done) | |
| 06 | docs | Cursor chat or Claude | now | |
| 10 | research pass 3: prior art (AI Repository via Bright Data) | Cursor, research chat | after pass 2 | |
| 11 | ml: overnight research queue (pre-registered sweep) | Cursor, ml chat | after v1 hand-off, before 01:00 | |
| 07 | qa | Cursor chat or terminal | 01:00, 08:30, 09:30, 11:00, 12:30 | |
| L1 | UI: farmer flow | Lovable (Claude via MCP, or paste) | now | |
| L2 | UI: officer dashboard and outlier map | Lovable | after L1 finishes | |
| L3 | UI: real engine, publish | Lovable | after web/ has the engine | |
| 08 | pitch and videos | Claude | Sun 10:00 | |
| 09 | Gemini review | Gemini Pro | Sun 08:30 and 12:00 | |
| 13 | Q&A rehearsal (judge) | Claude | Sun 11:00 | |
| 14 | Noor walkthrough script (pitch) | Claude | Sun 10:00 | |
| 15 | Video recording checklist (pitch) | Claude | Sun 10:30 | |
| 16 | Fallback plan (release-manager) | Claude | Sun 08:00, refresh 12:00 | |

## Layout reminder
- `app/` (in the mit-hackathon-7 repo): ml, geo, qa, backend scripts, docs, and the produced assets (model, audio, content, geo).
- `web/` (separate Lovable repo, cloned here, git-ignored by the root repo): UI + engine; the live URL.
- `python app/backend/scripts/sync_to_web.py` copies finished assets from app/ into web/.
