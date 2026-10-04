# Jani farmer app: static PWA deploy (EDGE_PLAN move 3 fallback)

If the Lovable (TanStack Start) PWA is not working offline by 08:30, publish this instead. It is the farmer flow only, as a plain Vite build in `app/dist`. No server, no secrets, no runtime AI calls. Lovable keeps the officer side.

## 1. Result first

- `npm run build` passes. `npx vitest run` still gives 135 passed, 1 todo.
- `node tests/e2e/offline-flow.mjs` passes at 360 x 740 against `vite preview`: load online, the service worker caches all 25 files, the browser goes offline, the page reloads, the sample plot runs end to end on the real model, the decision screen is reached, "Ask the officer" shows the referral SMS, and history lists the saved check. Screens: `tests/e2e/screens/01..12-*.png`. Raw result: `tests/e2e/screens/result.json`.
- The same test also checks, offline: one camera photo that fails opens its own retake screen (`not_a_leaf` for `sample12_poor.jpg`), and an upload of two photos without a camera goes through the same checks.
- Merge check (01:15): `ui` merged with the current `engine` (a22f9bc, sheet gate, `public/ort/` committed) and `content` (991ad25) builds and passes the same offline test. Not committed; integrator merges.
- Real model: `v1-2026-10-04` (`public/model/leaf.onnx`, 3.08 MB, onnxruntime-web 1.30 wasm). It ran in the browser, offline, with no mock badge. 10 sample photos took about 0.4 s in the cloud test browser (2 vCPU, no throttle; not a phone).
- What the real model says about the sample plot: all 10 bundled photos come back as `not_leaf` (confidence 0.61 to 1.00). The app shows "These photos do not look like coffee leaves" for each, the summary shows 10 "not sure", and the rule table gives `too_many_unsure` (ask the officer). That matches EDGE_PLAN section 4 (v1 reads field photos as "not a leaf"). The safe path works; the sample plot will only show rust once the overnight model (move 1) or on-page sample photos land. To swap the model: replace `public/model/leaf.onnx` and `model.json`, then rebuild. Nothing in the UI changes.
- Mock: the "MOCK MODEL" badge appears only when the engine reports `mock: true` (model files missing or unloadable). In this build it did not appear.

## 2. What the farmer sees (one action per screen)

1. Language: Kiswahili, Gĩkũyũ, English, each with a speaker button.
2. Consent (`consent_main`), Yes or No. No stops; Yes is stored and the screen is skipped next time.
3. How to pick the leaves (`how_to_pick_leaves`), with a drawing.
4. How to photograph (`how_to_photograph`), with a drawing.
5. Capture, up to 10 photos: "Take photo" (`<input type=file accept=image/* capture=environment>`), "Choose photo" (upload without camera, several at once), "Try a sample plot" (the first 10 photos in `public/demo/manifest.json`, credits under "Photo credits"). Each photo is checked by the engine. A failed photo gets its retake card (`retake_blurry`, `retake_dark`, `not_a_leaf`, and `retake_on_page` once the engine sends `not_on_page`). One camera photo that fails opens its own retake screen. Photos still waiting for a retake when the farmer taps "See result" are kept as "not sure"; they are never forced into a class.
6. Summary as four tiles: Rust, No problem seen, Other spots: ask the officer, Not sure. Cercospora, phoma and miner are never named (move 5); they count as "other spots".
7. Answer card from `decide()` with its not-sure line, the `berries_out_of_scope` card under every result, the sources and an "Assumption" tag when the card is marked so.
8. Decision: I will act / I will wait / Ask the officer. Nothing is pre-selected.
9. If "Ask the officer", or the answer's severity is `ask` (the tool abstained or needs a person): the referral screen shows the JANI1 SMS built by the engine (`buildReferral`), with its length out of 160. The SMS app opens (`smsLink`) only when the farmer taps "Send SMS"; she presses send there.
10. History: checks saved on the phone (IndexedDB via the engine), newest first.

Audio: every card has a speaker. It plays `public/audio/<lang>/<id>.mp3` through the engine when the clip exists (falls back to Swahili). There are no clips in the repo yet, so for now the speaker uses the phone's own offline voice if it has one for that language, and otherwise does nothing (no error shown). Clips dropped into `public/audio/` are picked up and precached at the next build.

## 3. Precache (measured on this build)

From `dist/precache-manifest.json` (written by the plugin in `vite.config.ts`). gzip is level 9, brotli is quality 11, both measured with Python on the built files.

| Category | Files | Raw bytes | gzip | brotli |
|---|---:|---:|---:|---:|
| onnxruntime wasm + mjs (`/ort/`) | 2 | 14,264,278 | 3,661,835 | 2,363,020 |
| Model (`/model/leaf.onnx`, `model.json`) | 2 | 3,077,641 | 2,822,639 | 2,689,697 |
| Demo sample plot (`/demo/`, 12 JPEG + manifest) | 13 | 677,146 | 664,105 | 663,830 |
| App JS (includes the content JSON and the engine) | 2 | 357,730 | about 112,000 | about 97,500 |
| App CSS | 1 | 8,432 | about 2,250 | about 1,950 |
| Icons (PNG) | 4 | 37,439 | 35,206 | 35,335 |
| Web manifest | 1 | 604 | 285 | 240 |
| Audio (`/audio/`) | 0 | 0 | 0 | 0 |
| **Total** (plus the 768-byte `index.html` shell) | **25** | **18,423,270** | **about 7.30 MB** | **about 5.85 MB** |

- The onnxruntime wasm is 77% of the raw bytes. Vite's duplicate copy of it under `assets/` is dropped by the plugin.
- `public/ort/` is not in the repo. The plugin copies `ort-wasm-simd-threaded.{wasm,mjs}` from `node_modules/onnxruntime-web/dist` into `dist/ort/` at build time (and serves them in `npm run dev`). If the engine lane commits `public/ort/`, those files win.
- `public/geo/` (officer data) is copied to `dist/` by Vite but not precached.
- Raw total is over the 15 MiB cap in `qa/checks/budgets.py` (RECIPE.md risk 1 said the real model would do this). Transfer size is about 7.3 MB with gzip.

## 4. First load at 1 Mbit/s (measured)

`MEASURE=1 node tests/e2e/offline-flow.mjs` serves `dist/` from a small throttled server: all connections share one 125,000 bytes per second link (1 Mbit/s, no latency or protocol overhead added: assumption), service worker downloads included. Chromium headless, cloud machine, 360 x 740.

| Server | First screen (language) | Offline ready (every file cached) | Bytes on the wire |
|---|---:|---:|---:|
| gzip on (like Netlify) | 0.9 s | 60 s | 7,436,867 |
| no compression | 2.9 s | 151 s | 18,725,147 |

- The app does not start the model until the service worker has finished caching, so on a first visit the model and the 14 MB wasm are downloaded once, not twice. Before that change the same runs moved 11.6 MB (gzip) and 33.5 MB (raw) and took 93 s and 268 s.
- "Works offline" appears in the top bar only once the service worker is active, which only happens after every file is cached.
- Whether Netlify or GitHub Pages compress `application/wasm` was not checked. GitHub Pages gzips most text types; Netlify serves brotli or gzip. Assume the gzip row is the realistic case and the raw row is the worst case.

## 5. Deploy: Netlify drag-and-drop (fastest, no account setup beyond login)

1. `cd app && npm ci --legacy-peer-deps && npm run build` (or reuse `app/node_modules`).
2. Open https://app.netlify.com/drop and drag the `app/dist` folder onto the page.
3. Open the URL it gives on a phone, wait for "Works offline" in the top bar, switch on airplane mode, reload, run a check.

`dist/_headers` (written by the build) keeps `sw.js`, `precache-manifest.js` and `/ort/*` uncached by the browser HTTP cache and makes `/assets/*` immutable. `app/netlify.toml` does the same for a Git-linked Netlify site (base directory `app`, build `npm ci --legacy-peer-deps && npm run build`, publish `dist`). No environment variables are needed.

Optional: `VITE_COOP_NUMBER=+2547XXXXXXXX npm run build` sets the cooperative SMS number. Without it the app uses `+254700000000` and shows "Demo number, not a real cooperative line" next to it.

## 6. Deploy: GitHub Pages (no secrets)

The engine loads `/model/`, `/ort/` and `/audio/` from the site root. So GitHub Pages works as is only where the site is served from `/`:

- a user or organisation site (repo named `<name>.github.io`), or
- a project site with a custom domain.

Steps (either case):

1. `cd app && npm run build`.
2. Push the contents of `app/dist` to the branch GitHub Pages serves (for example a `gh-pages` branch), or use a GitHub Actions workflow with `actions/upload-pages-artifact` (path `app/dist`) and `actions/deploy-pages`; both use the built-in `GITHUB_TOKEN`, no secrets.
3. Settings, Pages: choose that branch (or "GitHub Actions"). Add an empty `.nojekyll` file next to `index.html` if using a branch.

A project site at `https://<user>.github.io/<repo>/` needs `BASE=/<repo>/ npm run build`. The UI, the service worker, the web manifest and the demo plot follow `BASE`, but the engine's model, wasm and audio URLs do not yet (see Requests), so the model would fall back to the mock there and the badge would say so. Use Netlify in that case.

## 7. Files (ui lane)

- `src/App.tsx`, `src/main.tsx`, `src/index.css`: flow and styles.
- `src/pages/`: Language, Consent, Guide, Capture (with Retake), Result (Summary, Answer, Decision), After (Referral, Done, History).
- `src/components/`: Icon (inline SVG), Parts (screen frame, speaker, big button, top bar), EngineProbe.
- `src/ui/`: strings (short labels; Swahili labels are a builder draft, Kikuyu falls back to Swahili with "Not translated yet"), farmer (four farmer groups), photos (decode, sample plot, retake mapping, classify adapter), voice (clip or device voice), offline (service worker registration).
- `public/sw.js`, `public/manifest.webmanifest`, `public/icons/`: offline and install.
- `vite.config.ts`: precache plugin, ort copy, `_headers`, `__JANI_AUDIO__`.
- `tests/e2e/offline-flow.mjs`, `tests/e2e/screens/`: offline test and its screens.

Run the test: `npm run build && node tests/e2e/offline-flow.mjs` (add `MEASURE=1` for the 1 Mbit/s timing, about 4 extra minutes). It finds Playwright through `PLAYWRIGHT_MODULE`, a local `playwright` package or the global install, and falls back to `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`.

## 8. Not done or not checked

- No real phone test, no 4x CPU throttle timing.
- No recorded audio; device voice only where the phone has one (Swahili voices are rare).
- Swahili button labels are not reviewed by a native speaker. Kikuyu labels are not written.
- Photo sharing consent and sync to the officer (`syncPending`) are not wired: the static app has no backend. Only the SMS referral leaves the phone, and only when the farmer sends it.
- PIN lock (`setPin`, `unlock`) is not exposed in the UI.
- The sample plot uses the bundled iNaturalist and Wikimedia photos (not on a page). The engine's sheet gate is skipped for them (`classifyLeaf(img, { sheetGate: false })`, ignored by the current engine).
