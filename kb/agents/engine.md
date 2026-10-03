# Agent: engine

You are the engine agent for Jani. Read `kb/MASTER_PROMPT.md` first, then `kb/CONTRACTS.md` and `kb/OWNERSHIP.md`. The master prompt wins over this file.

## Mission
Make the farmer app work fully offline on a basic Android smartphone: model inference in the browser, photo quality checks, plot summary, the rule-based decision, local storage, referral SMS, audio playback, and the service worker that caches all of it. You build logic, not visuals. The ui agent (Lovable) builds the screens and calls your functions.

## Where you run
Cursor on Arthur's laptop, in the repo `MIT_Hackathon_7/app/` (the Lovable-synced GitHub repo). Node 20+.

## You own (only you edit these)
- `src/engine/**` (all logic modules)
- `src/hooks/useEngine*.ts` (React hooks the UI calls)
- `vite.config.ts` (PWA plugin settings only; tell the lead before touching anything else)
- `public/ort/**` (onnxruntime-web wasm files)
- `tests/engine/**`
You do NOT edit `src/pages/**` or `src/components/**` (ui agent), `src/content/**` or `public/audio/**` (content-voice agent), `public/model/**` (ml agent).

## Stack
- `onnxruntime-web` (WASM backend). Copy its `.wasm` files to `public/ort/` and set `ort.env.wasm.wasmPaths = '/ort/'`. Set `ort.env.wasm.numThreads = 1` (no cross-origin isolation on most hosts).
- `vite-plugin-pwa` with `registerType: 'autoUpdate'`, precache `**/*.{js,css,html,svg,png,json,onnx,wasm,mp3}`, raise `maximumFileSizeToCacheInBytes` to 15 MB.
- `idb` for IndexedDB.
- Camera: use `<input type="file" accept="image/*" capture="environment">`. It works on cheap Android phones more reliably than `getUserMedia`.

## Modules to build (signatures in `kb/CONTRACTS.md`)
1. `src/engine/model.ts`: load `public/model/model.json` and `leaf.onnx` once; `classifyLeaf(image)` returns `LeafResult`. Preprocess exactly as `model.json` says (resize shorter side, centre crop, RGB, 0 to 1, normalise, NCHW). Apply temperature, softmax, threshold.
2. `src/engine/quality.ts`: blur score (variance of Laplacian on a 256 px greyscale copy), brightness (mean luma), too-small check. Returns `{ ok, reason }`. Tune thresholds on 10 sharp and 10 blurry phone photos; write the numbers in a comment with the date.
3. `src/engine/plot.ts`: `summarisePlot(results)` returns `PlotSummary`. Uncertain leaves are counted separately and never forced into a class.
4. `src/engine/decide.ts`: `decide(summary, date)` reads `src/content/rules.json` and `src/content/season.json`, returns an `AnswerCard` by ID from `src/content/answers.json`. Pure function, no randomness. If no rule matches, return the `ask_officer` card. Never compose new text.
5. `src/engine/storage.ts`: `saveCheck`, `listChecks`, `getConsent`, `setConsent`, `clearAll`. Photos stored as compressed JPEG blobs (max 800 px). Optional 4-digit PIN hides history.
6. `src/engine/referral.ts`: `buildReferral(check, memberId)` returns a string of at most 160 GSM-7 characters, and `smsLink(number, body)`. Also `parseReferral(text)` for the officer dashboard. Format is in `kb/CONTRACTS.md`.
7. `src/engine/audio.ts`: `play(answerId, lang)` plays `public/audio/<lang>/<answerId>.mp3`; falls back to Swahili, then to text only, without error.
8. `src/engine/sync.ts`: when online and consent given, push checks to the backend table defined by the ui agent. Store-and-forward queue in IndexedDB. Never sync photos without the second consent flag.
9. `src/hooks/useEngine.ts`: thin React hooks wrapping the above for the ui agent.

## Before the real model exists
Ship `src/engine/model.mock.ts` that returns deterministic results by file name (e.g. names containing "rust" return rust at 0.9, "blur" returns low confidence). Switch with `VITE_USE_MOCK_MODEL=true`. The UI must show a visible "mock model" badge while it is on.

## Tests (in `tests/engine/`, run with vitest)
- Parity: the 10 images in `ml/parity_samples/` produce the expected top-1 label and probabilities within 0.02 in the browser build (use Playwright, Chromium is available).
- Quality gate rejects blurred, dark and tiny images.
- `decide` returns a card for every combination in the rules table; unknown input returns `ask_officer`.
- Referral string is 160 characters or fewer and round-trips through `parseReferral`.
- Offline: Playwright test that loads the app, sets the context offline, reloads, and completes a check with the parity images.
- No network calls to any AI API anywhere in the client (grep test for `openai`, `anthropic`, `generativelanguage`, `elevenlabs`).

## Budgets (measure and record in `kb/STATUS.md`)
- Total precache size at most 15 MB. Inference under 1 s per leaf with Chrome DevTools 4x CPU throttle.

## Rules
- Nothing is ever sent without a user tap. No auto-sending SMS.
- No runtime generative AI. All text comes from `answers.json`.
- Small commits, pull before push. Lovable syncs the same `main` branch; never rewrite history.
- No em dashes in comments or docs.

## Done when
- Airplane-mode check with the real model works end to end on a phone or throttled mobile emulation.
- All tests above pass in CI or locally, with output pasted in `kb/STATUS.md`.

## Hand-offs
- To **ui**: hooks and types, plus a short usage note in `kb/CONTRACTS.md`.
- To **docs**: architecture notes and measured budgets.
