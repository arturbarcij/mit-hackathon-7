# Lovable compatibility audit (EC3)

Lovable project `4619dfd1-32ea-4daa-aaf8-89b51321cbe1`, commit `e47a8a7` (3 Oct 2026, about 23:55 CEST), read through the Lovable MCP. Nothing in Lovable was edited or sent.
Compared against `kb/CONTRACTS.md`, `kb/agents/engine.md`, `kb/agents/ui.md`, `kb/MASTER_PROMPT.md` sections 4, 7, 8 and 16, and the repo content JSON.

## Summary (top-down)
1. **Content JSON shape will break the UI when the repo content syncs.** Lovable code reads `answerData.answers`, `ruleData.rules`, `seasonData.season.windows`, `seasonData.season.source`. The repo files are a bare array (`answers.json`, `rules.json`) and a bare object (`season.json`). After a GitHub sync, `answerText.ts`, `mockBridge.ts` and the Limits screen throw on first render. Owner: ui (read both shapes). Engine loaders should also accept both.
2. **The UI does not use the engine for most of the flow.** It calls `loadModel`, `classifyLeaf`, `summarisePlot`, `decide`, `play`, `smsLink`. It builds the SMS, parses the SMS, picks the season and (in mock mode) runs the rules itself in `src/lib/`. It never calls `saveCheck`, `listChecks`, `getConsent`, `setConsent`, `syncPending`, `buildReferral`, `parseReferral`, `seasonWindow` or any hook. History and consent live in React state and are lost on reload. Nothing reaches Supabase from the farmer app.
3. **Lovable's own mock-mode logic is right.** `lib/mockBridge.ts` (`summariseForRules`, `applyRules`, `seasonWindow`) passes all plot, season and 3,510 decision-matrix cases (target `lovable-bridge`, 123 of 133). The failures are garbage input, missing referral fields and the number-with-spaces SMS link.
4. **Lovable's `src/engine/index.ts` mock is far from CONTRACTS** (41 of 133). The UI hides this by switching to `mockBridge` when `loadModel().mock` is true. It is safe only while that switch stays.
5. **The officer parser rejects valid JANI1 referrals:** the CONTRACTS example itself (`P:2`), `N:0`, and a missing member or plot. The farmer app sends `M:?` / `P:?` when the fields are empty, which its own parser then rejects.
6. **Sync contract is missing.** `referrals` needs `uncertain` without `not_leaf` (or the dashboard counts not_leaf twice), `confidence` as a fraction, and a client id for idempotent retries. Anon can insert but not select, so sync must insert without returning rows.

## Test results (logs/)
| Target | What it is | Engine suite | UI compat |
|---|---|---|---|
| `reference` | test oracle (ours) | 133 / 133 | 5 / 10 |
| `lovable-mock` | Lovable `src/engine/index.ts` + `types.ts` | 41 / 133 | 2 / 10 |
| `lovable-bridge` | what `routes/index.tsx` computes in mock mode | 123 / 133 | 5 / 10 |
| `cursor-engine` | `app/src/engine/` on the laptop | not run: folder does not exist yet (checked 23:53) | |

UI compat failures for `reference` are all UI parser findings (point 5), not engine defects.

### Drift: Lovable `src/engine` mock vs CONTRACTS
| Area | Mock behaviour | CONTRACTS | Tests failed |
|---|---|---|---|
| `summarisePlot.uncertain` | unsure only | unsure + not_leaf | plot 10 of 25 |
| `summarisePlot.dominant` | most common of all labels, healthy included; not_leaf wins at half | not_leaf only if more than half; else top disease if any; else healthy | (same) |
| `decide` | three hard-coded ids `ask-officer`, `rust-action`, `keep-watching`, none in `answers.json`; English text in sw and kik; ignores date | rules.json first match, card copied from answers.json | decide 46 of 51 (all 3,510 cases) |
| `decide(null)` | throws | `ask_officer` | (same) |
| `seasonWindow` | not exported | required | season 20 of 23 |
| `buildReferral` | free English text, takes `ReferralCheck` | JANI1, takes `Check` | referral 15 of 18 |
| `parseReferral` | not exported | required | (same) |
| `smsLink` | keeps spaces in the number | no raw spaces | sms 1 of 7 |
| guardrails | clean | | 0 of 9 |

### Drift: Lovable UI mock mode (`lovable-bridge`)
| Area | Behaviour | Fix owner |
|---|---|---|
| `applyRules` on garbage (negative uncertain, `n: Infinity`, invalid date) | returns `healthy_all` instead of `ask_officer` | engine (real `decide` must validate); ui only if mock mode stays in the demo |
| `referralSms` with empty member or plot | sends `M:?` / `P:?`; `?` is outside the JANI1 field charset and its own parser rejects it | ui: send `-` |
| `referralSms` with no decision | sends `X:undefined` | ui |
| `parseReferral` round trip | rejects `P:2`, `N:0`, `M:-` | ui (relax regexes) |
| `smsLink` (mock) | spaces in the number kept | engine (real `smsLink` strips them) |

## Engine symbols the UI uses
| Symbol | Where | Signature used | CONTRACTS | Gap | Fix owner |
|---|---|---|---|---|---|
| `loadModel` | routes/index.tsx | `() => Promise<{version, mock}>`; `mock` drives the badge and the mockBridge switch | same | none | none |
| `classifyLeaf` | routes/index.tsx | `(ImageBitmap)`; on decode failure the UI passes a fake `{width:720,height:960} as ImageBitmap` | same | real engine will throw on the fake bitmap inside a `catch`, so the capture screen hangs | engine: never throw, return an `unsure` leaf with `quality.ok = false`; ui: show retake instead of the fake call |
| `checkQuality` | not called (inside `classifyLeaf`) | | exported | none | none |
| `summarisePlot` | routes/index.tsx | `(LeafResult[]) => PlotSummary` | same | none for the real engine | none |
| `decide` | routes/index.tsx | `(PlotSummary, Date) => AnswerCard` | same | UI ignores `card.text` and re-reads `answers.json` by id (`lib/answerText.ts`); fine if ids match the bank | none |
| `play` | routes/index.tsx | `(id, lang)` with ids `language`, `summary`, `decision`, `history`, `limits` and every answer id | `(answerId, lang)` | five ids are not in `answers.json`, so there is no mp3 for them | engine: `play` resolves silently when the file is missing; content-voice: add or map ids (`language` -> `language_name`) |
| `smsLink` | routes/index.tsx, officer Dashboard (nudge) | `(number, body)` | same | none | none |
| `seasonWindow` | not used; UI has its own in `lib/mockBridge.ts` | | required | duplicate logic | ui: import from `@/engine` |
| `buildReferral` | not used; UI has `lib/referralSms.ts` | UI: `{memberId, plotId, date, summary, answer, confidence, decision}` | `(c: Check)` | UI has no `Check` object; Q differs (see below) | ui: build a `Check` and call the engine, or keep `referralSms` as the agreed builder; engine decides |
| `parseReferral` | not used; officer uses `lib/parseReferral.ts` | returns a `referrals` row (snake_case, confidence 0 to 1) | `ParsedReferral` (shape not written in CONTRACTS) | two parsers, different shapes | engine: write `ParsedReferral` into CONTRACTS; ui: keep its row mapper but relax regexes |
| `saveCheck`, `listChecks` | not used | | required | History is in-memory only | ui (via hooks) |
| `getConsent`, `setConsent` | not used | | required | consent is not stored; photo consent switch goes nowhere | ui (via hooks) |
| `syncPending` | not used | | required | no sync | engine + ui |
| `useEngine`, `useCheck`, `useConsent`, `useOnline` | not used | | required | UI has its own online listener | engine ships hooks; ui adopts in L3 |
| types `AnswerCard`, `Decision`, `Label`, `Lang`, `LeafResult`, `PlotSummary` | routes, lib, components | from `@/engine` | same | none, as long as `index.ts` re-exports them | engine |
| type `ReferralCheck` | exported by the mock, imported nowhere at HEAD | | not in CONTRACTS | none | none (drop) |

## Referral format mismatch
CONTRACTS: `JANI1 M:<member> P:<plot> D:<yyyymmdd> N:<n> R:<rust> C:<cerco> H:<phoma> L:<miner> U:<unsure> A:<answerId> Q:<conf%> X:<decision>`

| Point | Farmer app (`lib/referralSms.ts`) | Officer parser (`lib/parseReferral.ts`) | Reference oracle | Proposal |
|---|---|---|---|---|
| Version and field order | JANI1, same order | JANI1 | JANI1 | same everywhere: done |
| Member | upper-case, `[A-Z0-9-]`, 12 chars, `?` if empty | must match `^[A-Z]{2,4}\d{2,6}$` | 16 chars, `-` if empty | parser accepts `[A-Z0-9-]{1,16}` or `-` |
| Plot | as member, `?` if empty | must match `^P\d{1,3}$`, so `P:2` (the CONTRACTS example) fails | 8 chars, `-` if empty | parser accepts `[A-Z0-9-]{1,8}` or `-` |
| N | `summary.n` | rejects `N:0` | allows 0 | parser allows `N:0` (all photos rejected is still a referral) |
| U | `summary.uncertain` (unsure + not_leaf) | healthy = N minus R C H L U, `not_leaf` set to 0 | same as UI | agreed; write it into CONTRACTS |
| Q | mean confidence of accepted leaves (not unsure, not not_leaf) | read as fraction | mean of all leaves | engine decides; the UI choice is the better signal. Write it into CONTRACTS |
| X | `X:undefined` when no decision | `null` | `X:-` | send `-` |
| Date | local day | `yyyy-mm-dd` | local day | agreed |

The farmer SMS and the reference `buildReferral` agree on every field except Q for a normal check (ui-compat test).

## What the real engine provides differently
- **Uncertain counted separately.** `summary.uncertain` includes not_leaf. The UI blocks accepting not_leaf and failed-quality leaves at capture, so in practice uncertain equals unsure. The Summary screen states the uncertain count in the sentence; it has no separate "not sure" tile. MASTER_PROMPT section 4 step 5 wants it shown separately.
- **not_leaf triggers a retake.** UI already does it: `current.result.label === "not_leaf"` shows the `not_a_leaf` card and a Retake button. Matches CONTRACTS.
- **AnswerCard from answers.json with audio and notSure.** The real `decide` returns `audio: {sw: '/audio/sw/<id>.mp3', ...}`. The UI ignores `card.audio` and calls `play(id, lang)`; that is fine. It reads `notSure` through `answerText`, which falls back to English and shows "not translated yet". Fine.
- **Consent.** Order is right (language, then main consent, then photo consent at the referral step). But neither answer is stored, and the "No" path only stops this session. The real engine's `setConsent` must be called on both screens, and `syncPending` must read it.
- **Mock badge.** Shown while `loadModel().mock` is true. Keep it.
- **Season.** The UI reads `season.json` itself for Limits and in mock mode. With the real engine, `decide` uses the engine's `seasonWindow`; the UI copy is then only for display.

## Supabase tables vs what `sync.ts` must send
`referrals` (migration `20261003205625`): `id uuid`, `created_at`, `member_id text NOT NULL`, `plot_id text NOT NULL`, `check_date date`, `counts jsonb`, `uncertain int`, `answer_id text`, `confidence numeric`, `decision text`, `photos_shared bool`, `photo_urls text[]`, `status text default 'new'`, `synthetic bool`.
Grants: anon may INSERT only. Trigger `referrals_daily_limit`: 20 inserts per member per day, error code 23514.
`corrections`: officer only. The engine never writes it.

| Column | `sync.ts` sends | Note |
|---|---|---|
| `member_id`, `plot_id` | `Check.memberId`, `Check.plotId`, `-` if empty | NOT NULL; the dashboard groups map pins by `plot_id` |
| `check_date` | local day of `createdAt` as `yyyy-mm-dd` | |
| `counts` | `{healthy, rust, cercospora, phoma, miner, not_leaf}` from `summary.counts` | |
| `uncertain` | `summary.uncertain - summary.counts.not_leaf` (unsure only) | the dashboard computes `n = sum(counts) + uncertain`; sending `summary.uncertain` with `counts.not_leaf` counts not_leaf twice |
| `answer_id` | `Check.answerId` | the dashboard looks the text up in `answers.json` |
| `confidence` | Q / 100 (fraction 0 to 1) | the dashboard shows `confidence * 100` |
| `decision` | `Check.decision` or null | column exists in Lovable, missing from ui.md |
| `photos_shared` | `Check.consentPhotos` | |
| `photo_urls` | `[]` | there is no storage bucket or upload policy yet; never upload without `consentPhotos` |
| `status`, `synthetic`, `id`, `created_at` | do not send | defaults |
| (missing) `client_check_id` | `Check.id` | needed so a retried sync does not create duplicates; add with a unique index and treat error 23505 as "already synced" |

Sync must call `insert(row)` without `.select()` (return minimal). With `.select()` the anon role hits the SELECT policy and the insert reports an error even though the row was written, so the queue would retry and duplicate. Use the existing client from `@/integrations/supabase/client`; do not add keys to the engine.

## Minimal engine-side adapter so the UI works on day one
The UI imports only these from `@/engine`: `classifyLeaf`, `decide`, `loadModel`, `play`, `smsLink`, `summarisePlot` and the types `AnswerCard`, `Decision`, `Label`, `Lang`, `LeafResult`, `PlotSummary`. The real engine already has them. Three small additions remove the day-one breakages:

```ts
// app/src/engine/compat.ts (engine-owned)
// 1. Accept both content shapes: the repo's bare arrays and Lovable's wrapped copies.
export const listOf = <T>(json: unknown, key: string): T[] =>
  Array.isArray(json) ? (json as T[]) : (((json as any)?.[key] ?? []) as T[]);
export const seasonOf = (json: any) => (json?.windows ? json : json?.season);

// 2. classifyLeaf must not throw on a bad bitmap (the UI passes a fake one on decode failure).
export async function safeClassify(img: ImageBitmap, run: (i: ImageBitmap) => Promise<LeafResult>, modelVersion: string): Promise<LeafResult> {
  try { return await run(img); } catch {
    const probs = { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
    return { label: 'unsure', probs, confidence: 0, abstained: true, modelVersion,
      quality: { ok: false, reason: 'too_small', blur: 0, brightness: 0 } };
  }
}
// 3. play() resolves without error when /audio/<lang>/<id>.mp3 is missing (ids 'language', 'summary',
//    'decision', 'history', 'limits' are played by the UI but have no file).
```
And in `index.ts`: re-export all types from `./types` (the UI imports types from `@/engine`), keep `ReferralCheck` out of CONTRACTS.

## Requests (one line each, for the lead to post)
- ui: read content JSON in both shapes (`Array.isArray(x) ? x : x.answers`, same for `rules`, `season`, `sources`) before the GitHub content sync, or the app crashes on first render.
- ui: relax `lib/parseReferral.ts` to accept member `[A-Z0-9-]{1,16}`, plot `[A-Z0-9-]{1,8}`, `-` for empty, and `N:0`; it rejects the CONTRACTS example `P:2` today.
- ui: in `lib/referralSms.ts` send `-` instead of `?` for empty member or plot, and `X:-` when no decision.
- ui: add `referrals.client_check_id text unique` so engine sync retries are idempotent.
- ui: in L3, switch to `useEngine`/`useCheck`/`useConsent`/`useOnline`, call `setConsent`, `saveCheck`, `syncPending`, and `seasonWindow` from the engine; delete `lib/mockBridge.ts` only after the real engine passes this suite.
- ui: replace the fake `{width:720,height:960}` classify fallback with a retake prompt.
- engine: re-export every type from `index.ts`; make `classifyLeaf` and `play` never throw; accept both content JSON shapes.
- engine: write `ParsedReferral` and the Q definition (mean confidence of accepted leaves, whole percent) into CONTRACTS.
- engine: `sync.ts` sends `uncertain = summary.uncertain - counts.not_leaf`, `confidence = Q/100`, `photo_urls = []`, inserts without `.select()`.
- engine: run `ENGINE_DIR=../../../app/src/engine CONTENT_DIR=../../../app/src/content npx vitest run` in `kb/engine-cowork/conformance` before each push.
- content-voice: add audio (or map ids) for `language`, `summary`, `decision`, `history`, `limits`, which the UI plays.
- qa: add `kb/engine-cowork/conformance` to the QA run (it reuses `qa.checks.decision_matrix` for its fixtures).
