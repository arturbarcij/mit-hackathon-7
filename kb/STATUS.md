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
| E4 | Engine tests incl. offline Playwright | engine | Sun 09:30 | doing | 107 vitest + 7 Playwright pass, also from a clean clone with `npm ci` (output below). GitHub Actions workflow `engine.yml` runs them. Parity-on-real-images test is written and skipped until `ml/parity_samples/expected.json` exists. Not yet run on a real Android phone. |
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
| Total offline precache | at most 15 MB | **3.1 MiB** now (app shell, engine, gzipped ORT runtime 2.8 MiB, fixture model, icons). Expect about 3.1 + model (at most 5) + audio (at most 4) = 12 MiB at worst, inside budget. |
| Audio total | at most 4 MB | |
| Inference per leaf (4x throttle) | under 1 s | Chrome 148, 4x CPU throttle, **fixture model only (not coffee)**: ORT load 0.55 s; 3000x2250 photo to result 0.10 to 0.15 s. Re-measure with leaf.onnx. |

## Requests between agents
- **lead (budget): resolved by engine.** The ORT WASM runtime (11.2 MB raw) is now stored gzipped in `public/ort/ort-wasm-simd-threaded.wasm.gz` (2.8 MiB) and inflated in the browser (`DecompressionStream`, gzip magic check so a host that already unpacks it also works). Precache is 3.1 MiB before the real model and audio. No action needed. Cost: about 50 ms extra at model load.
- **ml:** the browser test reads `ml/parity_samples/expected.json` as `{ "<file name>": { "label": "rust", "probs": { "healthy": 0.01, "rust": 0.97, ... } } }` next to the 10 images. If you use another layout, tell engine. Probabilities must be post-temperature. If your eval resizes to 256 then crops 224, add `"resize_to": 256` inside `model.json` `input`; the engine honours it. Fill `sha256` (the engine verifies it on load) and `threshold`.
- **ui:** (1) PWA icons: engine added `public/pwa-192.png`, `pwa-512.png` and `pwa-maskable-512.png` (simple leaf mark, replace with your artwork under the same names) and wired the manifest. (2) Call `syncPending()` when `useOnline()` becomes true. (3) Show the "mock model" badge when `useEngine().mock` is true.
- **content-voice / research:** two contract notes in CONTRACTS.md change requests (`uncertain_lte`; season window names, including `pre_short_rains`).
- **engine (own note):** `vitest.config.ts`, `playwright.config.ts`, `vite.harness.config.ts` and `scripts/copy-ort.mjs` sit in `app/` root. They are test and build helpers only.

## Log
- Sat 21:00: kb set up, six agent briefs written.
- Sat 22:50 (engine): E1 and E2 done on branch `cursor/engine-offline-core-d90f`. Engine modules, hooks, PWA, ORT runtime, tests. Fixture model only; real model pending M4.

### Engine test output (Sat 3 Oct, Node 22, Chrome 148)
```
npx vitest run
 Test Files  10 passed (10)
      Tests  107 passed (107)

npx playwright test   (production build, service worker, Chromium)
  ok  service worker precaches the model, WASM runtime and app
  ok  manifest is installable (PNG icons 192 and 512 px)
  ok  real ONNX runtime matches onnxruntime (Python) on the reference tensor   (|dp| < 1e-4)
  ok  full ten-leaf check works in airplane mode  (rust x6 / healthy x3 / unsure x1 -> rust_high_pre_rains, SMS <= 160 chars, saved to IndexedDB, blur/dark/tiny rejected)
  ok  overlapping classify calls are queued and all succeed
  ok  React hooks drive a whole check (blur rejected, rust x5 + healthy, consent, decision saved, SMS text, nothing posted)
  ok  inference timing with the CPU throttled 4x
  --  real model: parity samples match when present   (skipped: no public/model or ml/parity_samples yet)
```
What these do and do not show: the pipeline (decode, quality gate, preprocess, WASM inference, rules, referral, storage, service worker) works offline. The fixture model is a colour rule, not a coffee model, so no claim about leaf accuracy follows from these tests.

### Engine iteration, Sat 3 Oct evening
- **Quality gate fix.** A raw Laplacian threshold called dim but sharp photos blurry (synthetic leaf on a sheet at 0.3x exposure scored 22 against a threshold of 40). `QualityResult.blur` is now the Laplacian variance divided by brightness squared, so a sharp leaf scores about 0.0048 at any exposure and the threshold is 0.0012 (rejects Gaussian blur from about 10 px on a 4000 px wide photo). Tuned on synthetic images only; still needs 10 sharp and 10 blurry real phone photos.
- **Preprocessing check against Python.** Browser crop (canvas, high quality smoothing) against PIL resize then centre crop, mean absolute pixel difference on a 0 to 255 scale: 0.8 for a natural photo (bilinear reference), 1.0 (bicubic). A 4000 px synthetic noise image gave 7.9, so fine textures are the weak spot. ml: tell engine which interpolation training used; the real parity samples decide whether a PIL-exact resize is worth writing.
- **Robustness.** Inference calls are queued (ORT rejects overlapping runs) and the model is warmed up on load. The browser is asked to keep our data (`storage.persist`) once main consent is given. If saving fails, `useCheck().saveError` is set and the decision still stands.
- **Dev server.** ORT now loads under `vite` dev as well as in the production build.
- **Seen on the way:** openresearch.sh (open-source workspace for running AI research agents and parallel experiments). Not an engine concern, no runtime AI in the client; it could help the ml agent run training sweeps.
- **Season calendar integrated.** Research's `season.json` (R4, Mathira West, NASA POWER 1991 to 2020) is copied to `app/src/content/season.json` as the hand-off asked; the engine reads it directly and tests cover every day of 2026 (4 Oct is `pre_short_rains`, 15 Oct is `short_rains`). content-voice: `answers.json` and `rules.json` are still engine placeholders; drop yours into `app/src/content/` and the engine picks them up with no code change. If your first rule table fails an engine test, the failing test names the rule.
- **Still open (not engine work or not possible from here):** E3 needs the ml agent's `public/model/leaf.onnx`, `model.json` and `ml/parity_samples/`; quality thresholds need 20 real phone photos; no run on a real Android phone yet.
