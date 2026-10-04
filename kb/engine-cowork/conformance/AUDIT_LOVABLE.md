# Audit: Lovable mock engine and farmer route against CONTRACTS

Source: `_inputs/lovable/src/engine/{index.ts,types.ts}` and `_inputs/lovable/NOTES.md` (facts read from the live project, Sat 3 Oct about 23:30 CEST). Suite result against the mock: 115 of 147 tests fail (`RESULTS.md`).

Who fixes: **engine** means Cursor replaces `src/engine/**` and the drift disappears with it; Lovable must not touch it. **ui** means `src/routes/index.tsx` (or another Lovable-owned file) must change, see `LOVABLE_PROMPT_L3.md`.

Severity: high = wrong advice or data loss possible; medium = flow or contract breaks when the real engine lands; low = cosmetic or documentation.

| # | Drift | Severity | Who fixes | One-line fix |
|---|---|---|---|---|
| 1 | `decide()` returns three hard-coded cards (`ask-officer`, `rust-action`, `keep-watching`) with composed English text in all three languages. Ids are not in `answers.json`. | high | engine | Replace with rules.json evaluation and cards built from answers.json (reference/decide.ts). |
| 2 | `decide()` ignores `date`, `rules.json` and `season.json`. No season logic anywhere. | high | engine | Real engine adds `seasonWindow(date)` and uses it in `decide`. |
| 3 | `summarisePlot.dominant` is the most common label of any kind, so 8 healthy + 2 miner gives `healthy`. CONTRACTS: a disease wins whenever `affected >= 1`. | high | engine | Reference/plot.ts semantics. |
| 4 | `summarisePlot.uncertain` counts only `unsure`; CONTRACTS adds `not_leaf`. `not_leaf` majority rule missing. Ties resolved by array order (rust, cercospora, phoma, miner) by accident, not by rule. | high | engine | Same as 3. |
| 5 | `buildReferral()` emits free English text ("Jani check: 10 leaves...") with no member id, plot, date, per-disease counts, answer id or confidence. Not the JANI1 format. | high | engine (format), ui (inputs) | Engine emits JANI1; UI must collect `memberId` and `plotId` and pass a CONTRACTS `Check`. |
| 6 | `buildReferral` takes Lovable's `ReferralCheck {summary, answer, decision, date}` not CONTRACTS `Check`. `index.tsx` builds that shape, so the real engine will not type-check against the route. | high | ui | Build a `Check` object in `index.tsx` (id, createdAt, lang, leaves, summary, window, answerId, decision, memberId, plotId, consentMain, consentPhotos, synced). |
| 7 | No `parseReferral` in `src/engine`. A JANI1 parser lives in `src/lib/parseReferral.ts` with regexes member `^[A-Z]{2,4}\d{2,6}$`, plot `^P\d{1,3}$`. CONTRACTS example `P:2` fails it. | medium | ui (remove or wrap), engine (provide) | Officer route imports `parseReferral` from `@/engine`; delete `src/lib/parseReferral.ts` once the engine lands or make it a thin re-export. Plot alphabet to be fixed in CONTRACTS (RESULTS.md finding 2). |
| 8 | No `seasonWindow`, `saveCheck`, `listChecks`, `getConsent`, `setConsent`, `syncPending` exports. No `SeasonWindow` or `Check` types exported. `types.test.ts` fails. | medium | engine | Real engine exports the full CONTRACTS surface. |
| 9 | `index.tsx` calls `play()` with screen names (`language`, `consent`, `guide`, `capture`, `summary`, `decision`, `referral`, `history`, `limits`). These are not answer ids; the real `play()` would 404 on `/audio/sw/consent.mp3` and fall back to silence. | medium | ui | Call `play` only with answer ids (`consent_main`, `how_to_pick_leaves`, `decision_act` etc.) or with a documented `ui_<screen>` prefix the engine maps to UI audio. |
| 10 | No member number or plot id inputs anywhere in the farmer flow. Referral cannot carry them. | high | ui | Add two inputs on the referral screen (remembered in localStorage like the cooperative number); allow empty. |
| 11 | History is React state only; lost on reload. CONTRACTS: `saveCheck`/`listChecks` via IndexedDB. Photos not stored. | medium | engine (storage), ui (call it) | UI calls `saveCheck(check)` after the decision step and renders `listChecks()` on the history screen. |
| 12 | No consent flags carried. Consent screen answer is not stored; photo-sharing toggle is UI state only. | medium | ui | Set `consentMain` on the Check from the consent screen and `consentPhotos` from the referral toggle; call `setConsent`. |
| 13 | `classifyLeaf` is called with a fake `{width, height}` object when `createImageBitmap` fails. With the real engine this would classify a failed decode as a leaf, or throw inside ONNX. | high | ui | On decode failure show `retake_blurry` and do not call `classifyLeaf`. |
| 14 | `checkQuality`/`classifyLeaf` mock derive the label from image dimensions. Harmless as a mock, but the UI shows the "mock model" badge only via `loadModel().mock`. Keep that badge. | low | engine | Replaced by the real model; badge stays driven by `loadModel().mock`. |
| 15 | Card text: `answer.text[lang] ?? answer.text.en` fallback is right, but `review_status` label for Kikuyu is not shown (prompt 11 item 1). | low | ui | Show "pending native review" under kik text when the answer's review_status says so. |
| 16 | `smsLink` sniffs `navigator.userAgent` for iOS and uses `&body=`. Matches the reference. No drift. | none | - | Keep. |
| 17 | `audio: {}` in every mock card, so the UI never exercises the audio path. Real cards carry `/audio/<lang>/<id>.mp3` for languages with text. | low | ui | Use `card.audio[lang]` to decide whether to show the speaker button active. |
| 18 | `index.tsx` never shows the referral preview as the exact SMS body with a character count. Prompt 11 asked for it. | medium | ui | Render `buildReferral(check)` verbatim in a monospace box with `n/160`. |
| 19 | Decision step: the app stores `decision` only for the referral string. CONTRACTS `Check.decision` must be saved with the check. | low | ui | Include `decision` in the Check before `saveCheck`. |
| 20 | Routes live in `src/routes/index.tsx` (TanStack Start) while `kb/agents/ui.md` names `src/pages/**`. Ownership rules still hold by intent, but OWNERSHIP.md should list `src/routes/**` as ui-owned. | low | docs | Update OWNERSHIP.md. |

## What is fine

- Type definitions for `Lang`, `Label`, `QualityResult`, `LeafResult`, `PlotSummary`, `AnswerCard`, `Decision` match CONTRACTS exactly (`types-check.ts` passes for those eight assertions; only `SeasonWindow` and `Check` are missing).
- `smsLink` behaviour matches.
- Mock badge wired to `loadModel().mock`.
- All content tests pass; the content files are consistent.

## Order of work

1. Send `LOVABLE_PROMPT_L3.md` (UI-side only, items 6, 9, 10, 11, 12, 13, 15, 17, 18, 19).
2. Cursor replaces `src/engine/**` (items 1 to 5, 8, 14). Run `ENGINE_PATH=<app>/src/engine npx vitest run` in this folder until green.
3. Delete or re-export `src/lib/parseReferral.ts` (item 7) after agreeing the plot id alphabet in CONTRACTS.
