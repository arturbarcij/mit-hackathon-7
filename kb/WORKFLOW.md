# Workflow: running the agents concurrently

Source of truth for plans stays `kb/MASTER_PROMPT.md`. This file says who runs when, in parallel, and how they avoid breaking each other. Times are CEST. Deadline Sun 4 Oct 15:00, freeze 13:30.

## 1. How to launch in parallel
- **Cursor:** one chat message that makes several `Task` calls at once, each with `subagent_type` set to the agent name (`ml`, `engine`, `content-voice`, `docs`, `ui`, `pitch`, `research`, `qa`, `judge`, `redteam`, `mathematician`, `agronomist`, `ux-designer`, `user-simulator`, `security-privacy`, `release-manager`) and `run_in_background: true`. Ready-made launches are in `.cursor/commands/` (type `/wave-a`, `/wave-b`, `/wave-c`, `/wave-d`, or `/experts` for the six expert reviewers on their own).
- **Claude Code:** the same agents are in `.claude/agents/`; open one terminal per agent and start it by name. (The `claude` CLI was not found on this machine, so Cursor is the tested route.)
- Every launch prompt has the same shape: "Follow `kb/agents/<name>.md`. Do tasks <IDs>. Edit only your owned paths. Update your STATUS rows. When done or blocked, reply in five lines: done, not done, blocked on, unsure about, next."

## 2. Rules that make concurrency safe
1. **One owner per path** (`kb/OWNERSHIP.md`). Agents never edit each other's files; they write a line under "Requests between agents" in `kb/STATUS.md`.
2. **`kb/STATUS.md` is the only shared file.** Re-read it immediately before editing, change only your own rows with an exact-string replace, never rewrite the whole file.
3. **Git:** stage only your own paths (`git add <path>`, never `git add -A`), commit with the agent prefix (`ml: ...`), `git pull --rebase` before push, never force-push. If `index.lock` exists, wait 5 seconds and retry; do not delete it unless no git process is running.
4. **Long jobs** (downloads, training, audio render) run in a background shell, log to a file inside the agent's own folder, and are polled, not waited on.
5. **Contracts first.** `engine`, `ui` and `content-voice` build against `kb/CONTRACTS.md` and mocks, so they do not wait for each other. Contract changes go through the engine owner.
6. **Human gates stop an agent.** If a task needs Arthur (L1 Lovable sync, L2 `.env` keys, L3 Swahili reviewer, L4 phone, V1 recording, S1 submit), the agent marks the row `blocked`, names the exact action, and moves on to the next task.
7. **Paid or rate-limited calls happen once, on frozen input.** `content-voice` renders audio only from a frozen `answers.json` (ElevenLabs credits). No re-render loops. Never print or commit `app/backend/.env`.
8. **No agent marks something `done` that `qa` has not passed.** `qa` holds the veto.
9. **Anti-slop rules** (MASTER_PROMPT section 16) apply to every agent in every wave.

## 3. Dependency graph (critical path in bold)
```
R1-R4 (done)
  |-> **M1 data + splits -> M2 train -> M3 calibrate -> M4 ONNX int8 -> E3 real model in app -> U3 wire + publish -> QA matrix -> V1 videos -> S1 submit**
  |-> C1 answers + rules -> C2 translations -> C3 audio (needs L2, frozen text, L3 review)
  |-> D1 skeletons -> D2 docs (needs M5 numbers)
  |-> PT1 scripts (needs R1; numbers pending from M5)
E1 engine with mock model (needs app/ scaffold; L1 for Lovable sync) -> E2 offline PWA -> E3
U1 farmer flow with mocks -> U2 officer dashboard -> U3
```
The only chain that can lose the entry is **M1 to E3**. If M2 has not converged by Sun 00:30, ml freezes the backbone and ships the head-only model (see `kb/agents/ml.md`).

## 4. Waves

### Wave A: build in parallel (start now, Sat evening to Sun 01:00)
| Agent | Tasks | Runs on | Output |
|---|---|---|---|
| ml | M1 download, manifest, dedupe, splits; M2 train v1 | local GPU, background | `app/ml/**`, then `leaf.onnx` |
| content-voice | C1 `answers.json` + `rules.json`; C2 Swahili and Kikuyu text | Cursor | `app/src/content/**`, `kb/content/**` |
| engine | E1 engine with mock model and hooks; E2 start | Cursor | `app/src/engine/**`, `app/tests/**` |
| ui | U1 Lovable prompts for the farmer flow (Arthur pastes into Lovable) | Claude, Lovable | `kb/ui/**` (per brief) |
| docs | D1 doc skeletons from R1 to R4 | Cursor | `app/docs/**`, `app/README.md` |
| pitch | PT1 problem statement and three draft scripts | Claude | `kb/pitch/**` |
| research | on call: answer gap questions; Tier 3 price card only if idle | Claude + Bright Data | `kb/research/**` |

Gate to leave Wave A: M2 has a checkpoint or the head-only fallback is chosen; `answers.json` has every required ID; engine runs a full mock flow.

### Wave B: first reviews (Sun 01:00 to 02:30, can overlap Wave A's tail)
| Agent | Task |
|---|---|
| ux-designer | Pass 1 at 02:30 on the live mock flow and officer dashboard |
| user-simulator | Pass 1 at 03:00 (personas: Noor, daughter, clerk, officer, sceptic, hurried judge) |
| security-privacy | Pass 1 at 03:30 (secrets, Supabase access, referral string) |
| mathematician | Pass 1 done. Routed fixes: eval_shift measurement, macro F1 fix, honest EVALUATION numbers, rule changes (see STATUS Requests) |
| agronomist | Pass 1 done. Routed fixes: rust check step, prune wording, safety lines, sampling protocol (see STATUS Requests) |
| qa | `python -m qa.run --llm` from `app/` at 01:00 |
| judge | Pass 1 at 01:30 |
| redteam | Pass 1 at 02:00 |
| mathematician | Pass 1 done (Sat 23:55, `kb/math/20261003_2355.md`); pass 2 at 09:45, pass 3 at 12:00 |
| agronomist | Pass 1 done (Sat 23:55, `kb/agronomy/20261003_2355.md`); pass 2 at 09:45, pass 3 at 12:00 |
| ml | M3 calibrate, M4 export, M5 EVALUATION draft (continues overnight) |
Output: top fixes routed into STATUS "Requests". Owners clear them at the start of Wave C.

### Wave C: integrate (Sun 06:30 to 09:30)
| Agent | Tasks |
|---|---|
| engine | E3 real model with browser parity; E4 tests including offline Playwright |
| ui | U2 officer dashboard; U3 wire real hooks, publish live URL |
| content-voice | C3 audio render (after L2 and L3), Kikuyu clips; `REVIEW_LOG.md` |
| ml | M5 final numbers |
| docs | D2 DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION using measured numbers |
| qa | deterministic run at 08:30 |
| pitch | scripts final against the real app |
**Cut line 09:30:** if the real model is not in the app, ship the best working version, drop Tier 2 and Tier 3, stop adding features.

### Wave D: gate and finish (Sun 09:30 to 13:30)
| Time | Agent | Task |
|---|---|---|
| 09:30 | qa | `--llm` cut-line run, then manual matrix (airplane mode, five bad inputs, incognito URL) |
| 09:45 | judge, redteam, mathematician, agronomist, ux-designer, user-simulator, security-privacy | Pass 2 (experts check that routed fixes landed and re-test the corrected protocol, cards and eval numbers) |
| 09:45 to 11:00 | all builders | Clear routed fixes; docs complete (D3 README) |
| 11:00 | qa | deterministic run (sources, docs) |
| 11:00 to 12:45 | pitch + humans | Record and edit; pitch checks takes against scripts |
| 12:00 | judge, redteam, mathematician, agronomist, ux-designer (11:00), user-simulator (12:15), security-privacy (12:30) | Pass 3 |
| 13:00 and 13:25 | release-manager | Final sweep, frozen-commit record, go / no-go |
| 12:30 | qa | `--strict --llm`; any FAIL blocks submission |
| 12:45 | pitch | `ffprobe` results and coverage checklist (a) to (e) |
| 13:00 | pitch | Submission form text |
| 13:30 | Arthur | Freeze and submit (S1); repo public after confirmation |

## 5. Lead checkpoint after every wave (5 minutes, you or the lead chat)
1. Read "Requests between agents" in `kb/STATUS.md`; assign each line to its owner.
2. Check the board for `blocked` rows and do the human action.
3. Check `git log` for each agent's prefix and that nothing outside owned paths changed (`git status`).
4. Decide waivers in `kb/DECISIONS.md`.

## 6. Failure handling
- Agent stalls or loops: stop it, note in STATUS, restart with a narrower task.
- Two agents need the same file: the lower-priority one writes a Request; do not edit in parallel.
- A background job fails (download, training, render): the owner records the log path and the error in STATUS and tries the documented fallback in their brief.
- Lovable overwrites a file: engine and ui re-pull before continuing; ownership list decides who is right.
