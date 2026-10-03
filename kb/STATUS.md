# Status board

Update your own rows only. Keep it short. Status: `todo`, `doing`, `blocked`, `done`. Times are CEST.

**Deadline:** Sun 4 Oct 15:00. **Freeze and submit:** 13:30. **Cut line:** 09:30 (no new features after this; if the real model is not in the app, ship what works).

## Board
| ID | Task | Owner | Target | Status | Blocker / note |
|---|---|---|---|---|---|
| L1 | Connect GitHub in Lovable, clone repo into `MIT_Hackathon_7/app` | Arthur | Sat 21:30 | todo | |
| L2 | Fill `app/backend/.env` with keys | Arthur | Sat 21:30 | todo | |
| L3 | Find a Swahili speaker to review answers (10 min, Sun morning) | Arthur | Sun 09:00 | todo | |
| L4 | Android phone for demo (or emulation, stated) | Arthur | Sun 10:00 | todo | |
| R1 | Problem evidence table | research | Sat 22:30 | todo | |
| R2 | Agronomy guidance | research | Sat 23:00 | todo | |
| R3 | Dataset facts and licences | research | Sat 23:00 | todo | |
| R4 | season.json | research | Sat 23:30 | todo | |
| M1 | Data download, manifest, dedupe, splits | ml | Sat 22:30 | todo | needs R3 (can start from ml.md list) |
| M2 | Train v1 | ml | Sun 00:30 | todo | |
| M3 | Calibrate, threshold, OOD | ml | Sun 01:00 | todo | |
| M4 | ONNX int8 export, parity, model.json | ml | Sun 01:30 | todo | |
| M5 | EVALUATION.md | ml | Sun 02:00 | todo | |
| E1 | Engine with mock model + hooks | engine | Sat 23:30 | done | Branch `cursor/engine-offline-core-d90f`, PR to main. Usage notes in CONTRACTS.md. Content is read from `src/content/*.json` when present, else engine placeholders. |
| E2 | PWA offline caching | engine | Sun 00:30 | done | vite-plugin-pwa precaches onnx, wasm, mjs, mp3. Offline reload and full check proven in Chromium (see E4). Raw precache is over budget once model and audio land, see Requests. |
| E3 | Real model integrated, parity in browser | engine | Sun 08:30 | doing | ORT-web (1.22.0, WASM, 1 thread) loads and runs a fixture ONNX in prod build and Vite dev; matches Python onnxruntime within 1e-4. Waiting on M4 (`public/model/*`, `ml/parity_samples/`). Until then `mock: true` is reported. |
| E4 | Engine tests incl. offline Playwright | engine | Sun 09:30 | doing | 97 vitest + 4 Playwright pass (output below). Parity-on-real-images test is written and skipped until `ml/parity_samples/expected.json` exists. Not yet run on a real Android phone. |
| U1 | Lovable project, routes, farmer flow with mocks | ui | Sat 23:30 | todo | |
| U2 | Officer dashboard, tables, seed data | ui | Sun 08:00 | todo | |
| U3 | Wire real engine hooks, publish live URL | ui | Sun 09:30 | todo | needs E1 |
| C1 | answers.json + rules.json | content-voice | Sat 23:00 | todo | needs R2 |
| C2 | Swahili + Kikuyu translations | content-voice | Sat 23:30 | todo | |
| C3 | Audio rendered (ElevenLabs, MMS) | content-voice | Sun 00:30 | todo | needs L2 |
| D1 | Doc skeletons | docs | Sat 22:30 | todo | |
| D2 | DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION | docs | Sun 10:30 | todo | needs R1, R3, M5 |
| D3 | README final | docs | Sun 11:00 | todo | |
| V1 | Three videos recorded and checked | Arthur (pitch later) | Sun 12:45 | todo | |
| S1 | Submit, save confirmation, make repo public | Arthur | Sun 13:30 | todo | |

## Measured budgets
| Item | Target | Measured |
|---|---|---|
| leaf.onnx | at most 5 MB | not delivered yet (ml) |
| Total offline precache | at most 15 MB | App shell + engine + ORT runtime: about 11.4 MB raw (WASM runtime alone is 11.2 MB raw, 2.9 MB gzip). Before model and audio. Over budget once they land, see Requests. |
| Audio total | at most 4 MB | |
| Inference per leaf (4x throttle) | under 1 s | Chrome 148, 4x CPU throttle, **fixture model only (not coffee)**: ORT load 0.55 s; 3000x2250 photo to result 0.10 to 0.15 s. Re-measure with leaf.onnx. |

## Requests between agents
- **lead (budget decision):** onnxruntime-web 1.22.0 needs `ort-wasm-simd-threaded.wasm`, 11.2 MB raw (2.9 MB gzip on the wire). That alone is over the 15 MB precache target once model (up to 5 MB) and audio (up to 4 MB) are added: about 20 MB raw, about 10 MB transferred if the host gzips wasm (Lovable, Vercel and Netlify do). Options: (a) accept and report both raw and transferred sizes honestly in EVALUATION.md, (b) build a minimal ORT with only the operators in leaf.onnx (about 1 to 2 MB, needs a few hours of C++ build), (c) older ORT is no smaller (1.17.3 is 10.5 MB). Engine default: (a).
- **ml:** the browser test reads `ml/parity_samples/expected.json` as `{ "<file name>": { "label": "rust", "probs": { "healthy": 0.01, "rust": 0.97, ... } } }` next to the 10 images. If you use another layout, tell engine. Probabilities must be post-temperature. If your eval resizes to 256 then crops 224, add `"resize_to": 256` inside `model.json` `input`; the engine honours it. Fill `sha256` (the engine verifies it on load) and `threshold`.
- **ui:** (1) PWA installability needs PNG icons at 192 and 512 px; the manifest currently points at `favicon.svg`. Add `public/pwa-192.png` and `public/pwa-512.png` and tell engine to wire them (manifest is in `vite.config.ts`). (2) Call `syncPending()` when `useOnline()` becomes true. (3) Show the "mock model" badge when `useEngine().mock` is true.
- **content-voice / research:** two contract notes in CONTRACTS.md change requests (`uncertain_lte`; season window names, including `pre_short_rains`).
- **engine (own note):** `vitest.config.ts`, `playwright.config.ts`, `vite.harness.config.ts` and `scripts/copy-ort.mjs` sit in `app/` root. They are test and build helpers only.

## Log
- Sat 21:00: kb set up, six agent briefs written.
- Sat 22:50 (engine): E1 and E2 done on branch `cursor/engine-offline-core-d90f`. Engine modules, hooks, PWA, ORT runtime, tests. Fixture model only; real model pending M4.

### Engine test output (Sat 3 Oct, Node 22, Chrome 148)
```
npx vitest run
 Test Files  10 passed (10)
      Tests  97 passed (97)

npx playwright test   (production build, service worker, Chromium)
  ok  service worker precaches the model, WASM runtime and app
  ok  real ONNX runtime matches onnxruntime (Python) on the reference tensor   (|dp| < 1e-4)
  ok  full ten-leaf check works in airplane mode  (rust x6 / healthy x3 / unsure x1 -> rust_high_pre_rains, SMS <= 160 chars, saved to IndexedDB, blur/dark/tiny rejected)
  ok  inference timing with the CPU throttled 4x
  --  real model: parity samples match when present   (skipped: no public/model or ml/parity_samples yet)
```
What these do and do not show: the pipeline (decode, quality gate, preprocess, WASM inference, rules, referral, storage, service worker) works offline. The fixture model is a colour rule, not a coffee model, so no claim about leaf accuracy follows from these tests.
