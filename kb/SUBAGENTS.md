# Sub-agents: running work in parallel

How any Jani agent (research, ml, engine, ui, content-voice, docs, or the lead) splits its work across sub-agents when we need more done at once. This is a playbook, not a framework (Decision 9). The master prompt wins over this file.

## 1. When to spawn, and when not to

Spawn a sub-agent only when all of these hold:
- The task splits into pieces that touch **different files**.
- Each piece can be checked on its own (a test, a file that exists, a table that is filled).
- Each piece needs less than about an hour of agent work. Longer, and it should be a STATUS row instead.
- The parent has time to review what comes back.

Do not spawn:
- For anything that edits a path you do not own (see `kb/OWNERSHIP.md`). Sub-agents inherit your ownership, never more.
- For a decision already in `kb/DECISIONS.md`. Sub-agents do not reopen decisions.
- For runtime LLM features, new user-journey features, or anything in master prompt Section 5.3 (non-goals).
- After the **09:30 CEST cut line**, except for fixes, tests, docs and video checks. After **13:30**, nothing.

Cap: at most **4 sub-agents per parent** at a time, and no sub-agent spawns its own sub-agents. More than that and review becomes the bottleneck.

## 2. Safe parallel lanes

These pieces have no shared files and can run at the same time. Dependencies are from `kb/STATUS.md`.

| Parent | Sub-agent pieces that can run in parallel | Each piece writes only |
|---|---|---|
| research | R1 problem evidence, R2 agronomy guidance, R3 dataset facts and licences, R4 season data | one file each under `kb/research/` |
| ml | M1 data download and manifest; training script skeleton; OOD negatives set; evaluation script | separate files under `app/ml/` |
| engine | one module each: `model.ts` (and `model.mock.ts`), `quality.ts`, `plot.ts`, `decide.ts`, `storage.ts`, `referral.ts`, `audio.ts`, `sync.ts` | `app/src/engine/<module>.ts` plus `app/tests/engine/<module>.test.ts` |
| content-voice | Swahili text; Kikuyu text; audio render script | `app/src/content/i18n/<lang>.json`, `app/backend/scripts/**` |
| docs | one doc each: DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION, ARCHITECTURE | `app/docs/<DOC>.md` |
| lead | reviewers once Tier 1 runs: qa (Section 12 matrix), redteam (pass/fail safety gate), judge (weighted criteria) | a report in `kb/reviews/<name>.md`, no code |

Never parallel (one writer only, done by the parent):
- `kb/CONTRACTS.md` (engine), `app/src/content/answers.json` and `rules.json` (content-voice), `app/vite.config.ts` (engine), `app/package.json` and the lockfile (whoever adds a dependency tells the lead first).
- Anything under `app/src/pages/**` or `app/src/components/**`. Lovable writes there.
- `kb/STATUS.md` rows: sub-agents report back to the parent; the parent updates its own rows.

If two pieces need the same file, they are one piece.

## 3. How to spawn

### Cursor (local or cloud)
- Use the Task tool with `subagent_type: generalPurpose` for build work, `explore` for read-only searching. Launch independent sub-agents in **one message** so they run at the same time.
- For risky or competing attempts (for example two training configs), use `best-of-n-runner`: each runs in its own git worktree and branch, and you keep the better one.
- Cloud agents: one branch per sub-agent, named `cursor/<agent>-<piece>-<suffix>`. Open a draft PR; the parent or Arthur merges.

### Claude Code
- Use the Task tool with the matching agent from `.claude/agents/` (copies in `kb/claude-agents/`) when the piece belongs to another builder, or a general agent for a slice of your own work.
- Run independent tasks in one message so they run in parallel.

### Any tool
Paste the template in Section 4, filled in. Sub-agents start with no memory of your conversation, so the prompt must stand on its own.

## 4. Sub-agent prompt template

Copy, fill every `<...>`, delete nothing.

```text
You are a sub-agent of the <parent agent> agent on Jani, a Small AI entry for the
World Bank x Hack-Nation hackathon (Annex B, Agriculture). Deadline Sun 4 Oct 2026,
15:00 CEST; freeze 13:30.

Read first, in order:
1. kb/MASTER_PROMPT.md (source of truth)
2. kb/agents/<parent agent>.md (parent brief)
3. kb/CONTRACTS.md (shared types and formats; do not change them)
4. kb/SUBAGENTS.md section 5 (rules for sub-agents)

Your one task: <one sentence, a single deliverable>

You may create or edit ONLY these paths:
- <path 1>
- <path 2>
Everything else is read-only for you.

Inputs you can rely on: <files, contracts, mock data; say "none" if none>
Do not wait for: <pieces another sub-agent is building at the same time>

Done when:
- <checkable criterion, e.g. "vitest tests/engine/plot.test.ts passes">
- <second criterion>

Git: <choose one>
- "Do not commit. Leave changes in the working tree; the parent commits."
- "Work on branch <branch>. Commit with prefix '<parent agent>: '. Pull before push.
   Never force-push. Do not merge."

Report back in under 15 lines: files changed, how you checked it, test output,
anything you could not do, and any request for a path you do not own.
If you are unsure about agronomy, data licences or a contract, stop and say so.
Do not guess.
```

## 5. Rules every sub-agent follows

- Same rules as the parent: master prompt Section 16 (anti-slop), plain British English, no em dashes, no marketing words.
- Edit only the paths listed in your prompt. If you need another file changed, put it in your report, not in the file.
- No runtime LLM or AI API calls in the client. All farmer-facing text comes from `app/src/content/answers.json`.
- Never read aloud, print or commit `app/backend/.env`. Never put secrets in `VITE_*` variables.
- No invented numbers. Every figure needs a source, or an "assumption" or "synthetic" label.
- No invented pesticide products or doses. Write "ask the officer".
- Do not touch `kb/STATUS.md`, `kb/DECISIONS.md`, `kb/OWNERSHIP.md` or `kb/MASTER_PROMPT.md`.
- Do not install dependencies unless the prompt says so.
- Finish with the report format in the template. A sub-agent that cannot finish says so plainly.

## 6. Parent checklist

Before spawning:
1. Write the split as a short list in your head or in your STATUS note: piece, owner path, done criterion.
2. Check no two pieces share a file (Section 2).
3. Pull `main` so every sub-agent starts from the same base.

While they run:
4. Keep working on something that does not touch their files, or wait.

When they report:
5. Read each diff. Do not merge on the report alone; other agents can be wrong.
6. Run the checks yourself (tests, lint, file sizes).
7. Commit in small pieces with your agent prefix (`engine: add plot summary`), pull, then push. Never force-push. Lovable pushes to `main` too.
8. Update your rows in `kb/STATUS.md` and add any cross-agent requests under "Requests between agents".
9. If a sub-agent went outside its paths, revert those changes and redo the piece with a tighter prompt.

## 7. Worked example: engine before E1

Engine needs E1 (engine with mock model and hooks) by Sat 23:30. `kb/CONTRACTS.md` already defines the types, so the modules are independent.

Spawn three sub-agents in one message:
- A: `app/src/engine/quality.ts` and `app/tests/engine/quality.test.ts`. Done when blurred, dark and tiny test images are rejected.
- B: `app/src/engine/plot.ts`, `app/src/engine/decide.ts` and their tests. Done when every rules combination returns a card and unknown input returns `ask_officer`.
- C: `app/src/engine/referral.ts` and its test. Done when the referral is at most 160 GSM-7 characters and round-trips through `parseReferral`.

The parent writes `model.mock.ts` and `app/src/hooks/useEngine.ts` itself (they depend on the others), reviews A, B and C, commits each as its own `engine:` commit, and marks E1 done in `kb/STATUS.md`.
