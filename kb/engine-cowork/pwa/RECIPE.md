# EC1 recipe: offline PWA for the Lovable app (TanStack Start, Vite 8)

Lane EC1, engine-cowork. Proof run on a mirror of Lovable project 4619dfd1 at commit `e47a8a7116177264897f8240f13a72466ae314df` (3 Oct 2026, about 23:50 CEST). Nothing here was pushed to Lovable or GitHub.

## 0. Two EC1 proofs are in this folder

A parallel EC1 run wrote `README.md`, `RESULTS.json`, `vite.config.ts`, `sw-registration.__root.tsx`, `demo-route.index.tsx`, `tests/`, `scripts/` and `package.json` here (vite-plugin-pwa 1.3.0 plus a Workbox step, on a fresh TanStack Start app with the Lovable preset). This `RECIPE.md` and `files/`, `fixture/`, `logs/` are the other proof (hand-written service worker, on the real Lovable project code). Both pass an offline reload plus inference in Playwright.

| Point | This recipe (`files/`) | README.md proof |
|---|---|---|
| Code base tested | Lovable project at `e47a8a7` (real farmer screen, officer route, Supabase) | Fresh app on the same versions |
| Service worker | Hand-written `public/sw.js`, no Workbox | Workbox `generateSW` run in the client environment |
| ui-owned file changes | None: `loadModel()` registers it | `__root.tsx` (registration, manifest link, CSS import) |
| Offline shell | `/` cached at install, so offline works right after the first visit | `/` cached at runtime by NetworkFirst; the first visit is not controlled yet, so likely needs a second online visit (not checked) |
| ORT wasm location | `public/ort/` with `wasmPaths`, Vite's duplicate removed by the plugin | Vite-emitted `/assets/ort-...wasm`, no `public/ort/` |
| Installable (manifest, icons) | Not done | Done |
| 4x CPU throttle, killed server | Not done | Done |

Advice to engine: take this recipe's files (fewer moving parts, no ui change, tested on the real code), and take the web manifest, icons and the onnxruntime pin from README.md. The CSS hash mismatch in README.md gotcha 5 did not show up on the Lovable code: the SSR HTML links `/assets/styles-DSeGUKfS.css`, which is the file the client build emits. README.md also notes that inside the Lovable sandbox Nitro writes the client to `dist/client/`, not `.output/public/`; the plugin follows Vite's output, so `sw.js` lands there too (not checked on Lovable).

## 1. Result first

- Works: a hand-written service worker plus a 60-line Vite plugin. On a production build, at 360x740, the app loads online, the service worker installs and caches every file, the browser goes offline, the farmer screen reloads and renders, and one onnxruntime-web inference on a fixture model returns `logits` with shape [1,6]. Log: `logs/playwright-offline.log`, screenshot: `logs/offline-360x740.png`.
- Works: the same plugin and service worker come out of the default Lovable build (Nitro `cloudflare` preset), not only the node build used for the test.
- Existing vitest suite: 3 files, 13 tests pass, before and after the change.
- Budget warning: the onnxruntime-web 1.30.0 wasm is 14.24 MB raw. The precache is 15.12 MB raw (14.42 MiB) with a 1.5 KB fixture model and no audio. That leaves 0.6 MiB under the 15 MiB cap in `qa/checks/budgets.py`. The real model and audio will push the raw total over. Compressed transfer is 2.58 MB (brotli) or 3.94 MB (gzip).
- Not tried: `vite-plugin-pwa`. Reason: time box, and this stack has no static `index.html` (the HTML for `/` is rendered by the server), the client output goes to `.output/public` through Nitro, and the build uses Vite 8 environments. The custom route was faster to make reliable. It is untested whether `vite-plugin-pwa` 2.0.0 (which lists Vite 8 as a peer) would work here.
- Not done: install prompt (web manifest and icons), real model, audio, 4x CPU throttle timing, real phone.

## 2. Versions used

| Item | Version |
|---|---|
| vite | 8.1.5 (rolldown 1.2.1 via override) |
| @tanstack/react-start | 1.168.60 |
| @lovable.dev/vite-tanstack-config | ^2.24.0 |
| nitro | 3.0.260603-beta |
| vitest | 4.1.11 |
| onnxruntime-web | 1.30.0 (latest on 3 Oct 2026), entry `onnxruntime-web/wasm` |
| playwright | 1.56.0 (global install), Chromium 1194 |
| node | 22.22.0 |

Install note: `bun install` against the Lovable lockfile fails in the cloud (Lovable's private registry returns 403). Plain `npm install` fails with `Cannot read properties of null (reading 'edgesOut')`. `npm install --legacy-peer-deps` works (10 min in the cloud). Logs: `logs/npm-install-*.log`, `logs/bun-install*.log`.

## 3. How it works

- `pwa/precache-plugin.ts` (new, Vite plugin, client build only). It lists the client JS and CSS from the bundle, plus every file in `public/model/`, `public/ort/`, `public/audio/` and `public/favicon.ico` if present. It skips officer-only chunks (`officer`, `OutlierMap`, `leaflet-src`, `geo`) and source maps. It drops the 14 MB duplicate wasm that Vite emits under `assets/` because of the onnxruntime-web bundle entry. It writes `/precache-manifest.json` (for QA) and `/precache-manifest.js` (for the service worker). The version is a hash of all URLs, sizes and public file bytes.
- `public/sw.js` (new, hand-written). `importScripts('/precache-manifest.js')`. Install: caches `/` and every manifest file into `jani-precache-<version>`, with `cache: "reload"`; install fails if one file fails, so "active" means "fully cached". Activate: deletes older `jani-*` caches, claims clients. Navigations: network first with a 3 s timeout, then the cached page, then the cached `/`. Precached URLs: cache first. Everything else (Supabase, officer data, other origins): network only, never cached.
- `src/engine/pwa.ts` (new). `registerServiceWorker()` registers `/sw.js` with scope `/` and `updateViaCache: "none"`, then resolves `{ ready, version, files, bytes }` once a worker is active. `offlineReady()` returns the same promise. It does nothing in dev, inside an iframe, or on `id-preview--*` and `*.lovableproject.com` hosts (the Lovable editor), so editing never sees a stale build.
- `src/engine/ort.ts` (new). Imports `onnxruntime-web/wasm` (wasm-only, no WebGL or WebGPU code), sets `wasmPaths = "/ort/"`, `numThreads = 1`, `proxy = false`.
- `src/engine/selftest.ts` (new). Only with `?selftest=1`: loads `/model/model.json`, creates a session, runs one input of 0.5s, stores the result on `window.__janiSelftest`. Lazy chunk, so normal users never download it.
- Call site: `loadModel()` in `src/engine/index.ts` calls `registerServiceWorker()` and the self-test hook. The farmer screen already calls `loadModel()` on mount. No ui-owned file has to change for offline to work.

## 4. Files to add or change in web/

All full contents are under `files/web/` at their web/ paths. Diffs are under `files/diffs/`.

| web/ path | Action | Owner |
|---|---|---|
| `pwa/precache-plugin.ts` | add | engine (new folder; see Request) |
| `public/sw.js` | add | engine |
| `src/engine/pwa.ts` | add | engine |
| `src/engine/ort.ts` | add | engine |
| `src/engine/selftest.ts` | add | engine |
| `src/engine/index.ts` | 4 lines in `loadModel()` (diff) | engine |
| `vite.config.ts` | import plugin, add `vite: { plugins: [janiPrecache()] }` (full file and diff) | engine |
| `package.json` | add `"onnxruntime-web": "1.30.0"` (pin exact, the wasm must match the JS) | engine |
| `public/ort/ort-wasm-simd-threaded.wasm`, `public/ort/ort-wasm-simd-threaded.mjs` | add, copied by `scripts/copy-ort-wasm.mjs`; commit both (14.2 MB + 24 KB) | engine |
| `scripts/copy-ort-wasm.mjs` | add | engine |
| `tests/e2e/offline-proof.mjs` | add | engine |

The fixture model is not for web/. Its generator is `fixture/make_fixture_model.py` (seeded Conv, Relu, GlobalAveragePool, Flatten, Gemm; input `input` [1,3,224,224] float32; output `logits` [1,6]; 1,465 bytes; `model.json` version `fixture-not-a-real-model`). It was placed in the mirror's `public/model/` only.

Both onnxruntime files are needed. With `wasmPaths` set as a folder, onnxruntime-web 1.30 also imports `ort-wasm-simd-threaded.mjs` from that folder; without it the offline inference failed with "Failed to fetch dynamically imported module".

## 5. Commands

```
cd web
npm install --legacy-peer-deps onnxruntime-web@1.30.0     # Lovable itself uses bun; fine there
node scripts/copy-ort-wasm.mjs                            # puts wasm + mjs in public/ort/
npx vite build                                            # Lovable default (cloudflare preset); client in .output/public
NITRO_PRESET=node_server npx vite build                   # local test build
PORT=4173 HOST=127.0.0.1 node .output/server/index.mjs    # serve the production build
BASE=http://127.0.0.1:4173 node tests/e2e/offline-proof.mjs
npx vitest run
```

`npx vite preview` does not work with this output (it looks for `dist/server/server.js`, HTTP 500). Use the node preset and `node .output/server/index.mjs`.

## 6. Precache budget (measured, mirror build)

| Category | Files | Raw bytes | gzip -9 | brotli 11 |
|---|---|---|---|---|
| onnxruntime wasm + mjs | 2 | 14,264,278 | 3,696,284 | 2,363,020 |
| App JS (includes content JSON and the 73 KB ort JS) | 5 | 779,452 | 232,014 | 199,924 |
| App CSS | 1 | 78,880 | 13,445 | 11,473 |
| Model (fixture only) | 2 | 2,096 | 1,746 | 1,646 |
| Audio | 0 | 0 | 0 | 0 |
| Shell HTML `/` | 1 | 12,491 | not measured | not measured |
| **Total** | 11 | **15,137,197** | **about 3.95 MB** | **about 2.59 MB** |

- Cap in `budgets.py`: 15 x 1024 x 1024 = 15,728,640 bytes. Raw headroom now: about 0.59 MB.
- A 3 MB model plus any audio puts the raw total over the cap.
- First load at 1 Mbit/s (assumption: 125,000 bytes per second, no overhead): raw 15.1 MB is about 2.0 min; gzip about 32 s; brotli about 21 s. Whether Lovable's Cloudflare hosting compresses `application/wasm` was not checked.
- Officer-only chunks (`leaflet-src`, `OutlierMap`, `officer`, `geo`, about 0.2 MB) are built but not precached.

## 7. What qa budgets.py sees on this stack

- It looks for `dist/`. Locally, TanStack Start with Nitro writes `.output/public/` (client) and `.output/server/` (worker); inside the Lovable sandbox it writes `dist/client/` and `dist/server/` (per README.md, from the preset source). Locally there is no `dist/`, so `budgets:bundle_size` and `budgets:service_worker` are skipped and `client_clean:dist` is skipped.
- If pointed at `.output/public/`, the size check would count the officer chunks and `precache-manifest.*` too (15.33 MB total), slightly more than the true precache.
- `budgets:ort_wasm` (looks in `public/ort/*.wasm`) works as is.
- `budgets:service_worker` would find `.output/public/sw.js`.

## 8. Risks

1. **Budget.** onnxruntime-web is 94% of the bytes. Options, cheapest first: count the cap on transfer bytes and report raw beside it; try an older onnxruntime-web (raw wasm size from the npm tarball: 1.30.0 is 14.24 MB, 1.20.1 is 11.25 MB, 1.17.3 is 10.55 MB for `ort-wasm-simd.wasm`; older versions not run here, and the int8 model's operators must be supported); a reduced-operator onnxruntime build (hours, not tonight).
2. **Lovable hosting.** Publish uses Cloudflare Workers via Nitro. `sw.js` is served from the root, so scope `/` works. `_headers` only marks `/assets/*` immutable, so `sw.js` and `precache-manifest.js` are not cached for a year. Not checked on the live publish URL.
3. **Lovable editor preview.** The worker is off there by design. Offline can only be shown on the published URL or a local production build.
4. **Updates.** A new deploy changes `precache-manifest.js`, so the browser installs a new worker on the next visit, which takes over at once and deletes the old cache. A page left open from the old version could then fail to lazy-load an old chunk. Fix if needed: reload once on `controllerchange` in `pwa.ts`, or drop `skipWaiting`.
5. **Shell is the SSR HTML of `/` at install time.** It is not refreshed by later visits on purpose (a newer HTML could point at assets the old cache lacks). Offline, any other path gets this shell; `/officer` will then fail to load its chunk and show the error screen. The officer route needs a connection.
6. **First-visit offline.** Nothing works offline until the first full install has finished (about 15 MB). The UI should show "ready offline" only after `offlineReady()` says `ready: true`.
7. **Storage.** Chrome on Android grants plenty for 15 MB, but low-storage phones can evict caches. Not tested.
8. **Inference time.** 298 ms for session creation plus one run on the fixture, no throttle. Says nothing about the real model.

## 9. What ui must call

Nothing for offline caching: `loadModel()` already starts it. Optional: `import { offlineReady } from "@/engine/pwa"` and show a small "works offline" badge when it resolves `ready: true`. For installability (Add to Home Screen), ui needs one line in `src/routes/__root.tsx` `links`: `{ rel: "manifest", href: "/manifest.webmanifest" }`, plus a manifest and two icons (not made here).

## 10. Proposed Requests

- engine: adopt `files/web/*` and the three diffs; call `registerServiceWorker()` from the real `loadModel()`; pin `onnxruntime-web` to `1.30.0`; commit `public/ort/` (wasm + mjs); run `tests/e2e/offline-proof.mjs` with the real model.
- engine: add `pwa/precache-plugin.ts` to the engine row in `kb/OWNERSHIP.md` (it sits outside `src/engine`).
- qa: in `budgets.py` and `client_clean.py`, look for the client output in `dist/client/`, then `.output/public/`, then `dist/`; and size the bundle from `.output/public/precache-manifest.json` `total`; report gzip and brotli next to raw.
- engine: if the cap stays raw, test onnxruntime-web 1.20.1 (wasm 11.25 MB, 3 MB smaller) with the real model.
- lead: decide whether the 15 MB cap means stored (raw) bytes or transfer bytes; onnxruntime alone is 14.2 MB raw, 2.4 MB brotli.
- ml: keep the real model at 3 MB or less; the raw headroom is about 0.6 MB if the cap stays raw.
- ui: add the web manifest link line in `__root.tsx` and two icons (192 and 512 px) for install.

## 11. Delivered

- `RECIPE.md` (this file)
- `files/web/...` (full files at web/ paths), `files/diffs/*.diff`
- `fixture/make_fixture_model.py`
- `logs/`: `playwright-offline.log`, `offline-360x740.png`, `precache-manifest.json`, `vitest.log`, `vitest-after.log`, `build-baseline.log`, `build-pwa.log`, `build-cloudflare-preset.log`, `npm-install-*.log`, `bun-install*.log`
- Mirror source not delivered (it stays in the cloud workspace, `.env` local only).
