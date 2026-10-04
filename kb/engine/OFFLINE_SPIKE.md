# Offline spike (R2): result and recipe

Owner: engine (offline track). Spike code: `/home/claude/spike`. Date: Sun 4 Oct 2026, about 00:30 CEST.

## Verdict: works with changes

A hand-written service worker plus a 25-line Vite plugin makes `/` load and the full check run offline after one online visit, on the exact Lovable stack. vite-plugin-pwa (option a) was dropped: it writes `sw.js` to the top-level `dist/`, but the client build lives in `.output/public` locally and `dist/client` inside Lovable, so it would need a hard-coded, environment-specific path. Option (b) passed.

Two engine changes are required, or the budget breaks:
1. `src/engine/model.ts`: `import('onnxruntime-web')` must become `import('onnxruntime-web/wasm')`. The default entry loads `ort-wasm-simd-threaded.jsep.wasm` (28.3 MB raw, 6.6 MB gzip, over Cloudflare's 25 MiB per-file asset limit). The `/wasm` entry loads `ort-wasm-simd-threaded.wasm` (14.2 MB raw, 3.66 MB gzip).
2. With `wasmPaths = '/ort/'` ORT also fetches the JS glue from that folder, so `public/ort/` needs two files, not one (first test run failed with `Failed to fetch dynamically imported module: /ort/ort-wasm-simd-threaded.mjs`).

## Evidence (Playwright 1.63, Chromium 1194, `node offline-test.mjs`, log in `spike/offline-test.log`)

Setup: same versions as the Lovable repo (vite 8.1.5, react-start 1.168.60, react-router 1.170.41, router-plugin 1.168.42, nitro 3.0.260603-beta, `@lovable.dev/vite-tanstack-config` 2.25.1 installed from npm), SSR on. Locally built with nitro `node-server` preset only so it can be served (Lovable pins `cloudflare-module`; `vite preview` cannot serve that preset). Offline = `context.setOffline(true)` and the server process killed.

```
[test] ORT-related requests: /assets/ort.wasm.bundle.min-*.js /ort/ort-wasm-simd-threaded.mjs /ort/ort-wasm-simd-threaded.wasm
[test] precache complete: 19/19 entries, 23.56 MB, 509 ms on localhost
[test] PASS offline reload renders '/' (#h = Habari, Noor)
[test] PASS offline inference + 5 MB leaf.onnx + mp3: ok 1,4,9,16,25,36 leaf=5000000 mp3=481115
[test] PASS wasm from SW cache: 200/sw
[test] PASS leaf.onnx from SW cache: 200/sw
[test] PASS offline <audio> plays from cache: currentTime=1.45 duration=30.0   (served as 206 by the SW)
[test] PASS offline client navigation / -> /about, /about -> /
[test] PASS offline cold open of '/' in new tab
[test] RESULT: ALL PASS
```

Inference used a real ONNX model (`mul_1.onnx`, x*x) through `InferenceSession.create` with `numThreads=1`, `executionProviders:['wasm']`, nothing fetched from the network.

## Sizes

| | stored in Cache Storage | on the wire (gzip) |
|---|---|---|
| Spike (5 MB dummy model, 3.8 MB audio, wasm, 0.44 MB JS/CSS) | 23.56 MB | 10.64 MB |
| `ort-wasm-simd-threaded.wasm` alone | 14.24 MB | 3.66 MB |
| Real app estimate (Lovable JS about 1 to 1.5 MB raw) | about 25 MB | about 11 to 12 MB |

The 15 MB budget holds only as download size, and only if the host compresses `.wasm`. Stored size is about 25 MB; fine for Chrome on Android (quota is a share of free disk). Report both in the evaluation.

## Recipe for the Lovable repo

ENGINE-OWNED files (copy from the spike; Lovable must not edit them):

1. `public/sw.js`: copy `/home/claude/spike/public/sw.js` verbatim (60 lines, no dependencies). It `importScripts('/sw-precache.js')`, `cache.addAll` on install (with `cache:'reload'`), deletes old `jani-*` caches on activate, `skipWaiting` plus `clients.claim`. Fetch: same-origin GET only; navigations are network-first with a 3 s timeout, falling back to the cached `/`; everything else is cache-first by pathname, with Range requests answered as 206 slices (needed for `new Audio(src)`).
2. `public/ort/ort-wasm-simd-threaded.wasm` and `public/ort/ort-wasm-simd-threaded.mjs`, copied from `node_modules/onnxruntime-web/dist/` (version 1.30.0; recopy if ORT is upgraded).
3. `public/model/model.json`, `public/model/leaf.onnx`, `public/audio/<lang>/<id>.mp3` (all precached by pattern).
4. `src/engine/sw-register.ts`: copy `/home/claude/spike/src/sw-register.ts` (`registerOfflineSW()`, prod only, `updateViaCache:'none'`; `isOfflineReady()` for a "Ready offline" badge).
5. `vite.config.ts`: add this block above `export default`, then `plugins: [janiPrecache()]` inside `defineConfig({...})`:

```ts
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import type { Plugin } from "vite";
// ---- ENGINE-OWNED: offline precache list for public/sw.js ----
const PUBLIC_PRECACHE = [/^model\/[^/]+\.(json|onnx)$/, /^ort\/ort-wasm-simd-threaded\.(wasm|mjs)$/, /^audio\/.+\.mp3$/, /^favicon\.ico$/];
function janiPrecache(): Plugin {
  return {
    name: "jani-precache", apply: "build",
    applyToEnvironment: (env) => env.name === "client",
    generateBundle(_opts, bundle) {
      const pub = "public";
      const walk = (d: string): string[] => readdirSync(d).flatMap((f) =>
        statSync(join(d, f)).isDirectory() ? walk(join(d, f)) : [relative(pub, join(d, f)).split("\\").join("/")]);
      const publicFiles = walk(pub).filter((f) => PUBLIC_PRECACHE.some((re) => re.test(f)));
      const assetFiles = Object.keys(bundle).filter((f) => /\.(js|css)$/.test(f)); // skips Vite's duplicate assets/*.wasm
      const hash = createHash("sha256");
      for (const f of assetFiles.sort()) hash.update(f);
      for (const f of publicFiles.sort()) hash.update(f).update(readFileSync(join(pub, f)));
      const version = hash.digest("hex").slice(0, 12);
      const urls = ["/", ...assetFiles.map((f) => "/" + f), ...publicFiles.map((f) => "/" + f)];
      this.emitFile({ type: "asset", fileName: "sw-precache.js", source: `self.__JANI_PRECACHE=${JSON.stringify({ version, urls })};\n` });
    },
  };
}
// ---- END ENGINE-OWNED ----
```

Content JSON is imported by engine modules, so it is inside the hashed JS and precached with it.

LOVABLE-OWNED change (one line): in `src/routes/__root.tsx` `RootComponent`, `useEffect(() => { registerOfflineSW(); }, [])`. Alternative with no Lovable change: the engine calls `registerOfflineSW()` itself from the first engine hook the UI mounts (for example `useEngine`), but that is less explicit.

## ORT runtime files (numThreads = 1, wasmPaths = '/ort/', `onnxruntime-web/wasm`)

- `/ort/ort-wasm-simd-threaded.wasm` (14,239,897 B)
- `/ort/ort-wasm-simd-threaded.mjs` (24,381 B)

Observed in the network log; no other ORT file is requested. The JS entry `ort.wasm.bundle.min.mjs` is bundled by Vite into `/assets/` and precached with the app JS. Vite also emits a duplicate 14 MB `assets/ort-wasm-simd-threaded-<hash>.wasm` that is never fetched; the plugin skips it, but it still ships in the deploy.

## Risks

- **First visit must finish precaching online.** About 11 to 12 MB on the wire, about 90 to 100 s at 1 Mbit/s. Show "Ready offline" (`isOfflineReady()`) and tell the demo operator to wait for it.
- **SSR navigation fallback.** Offline, every navigation gets the cached SSR HTML of `/`. Cold-loading `/` and client-side navigation are clean. Cold-loading another URL (tested `/about`) renders correctly but logs React error #418 (hydration mismatch, recovered by client render). Keep the offline flow entering at `/` (PWA `start_url: "/"`) and avoid route loaders that call server functions on the offline path.
- **Lovable hosting headers (unverified on the real host).** Check on the published URL: `curl -sI -H 'Accept-Encoding: br, gzip' <site>/ort/ort-wasm-simd-threaded.wasm` must show `content-type: application/wasm` and ideally `content-encoding`; if not compressed, download is about 24 MB and over budget. `sw.js` must be served from the origin root as JavaScript. Nitro's `_headers` marks only `/assets/*` immutable, which is fine; `updateViaCache:'none'` avoids stale `sw.js`/`sw-precache.js`.
- **Update flow.** Any change to JS or public files changes the version, and the new SW re-downloads the whole list (about 11 MB) before it takes over; `skipWaiting` then swaps caches and the next load uses the new build. The cached `/` HTML only refreshes when the version changes. Avoid deploys during the demo; if bandwidth matters later, reuse unchanged entries from the old cache in `install`.
- **Lovable preview.** Registration is prod-only, so the editor preview (dev server) is unaffected. A phone that visited an old build keeps it until it is online again.
- **Manifest/installability** (R1 "installed PWA") is not covered here: needs `public/manifest.webmanifest`, icons and a `<link rel="manifest">` in `__root.tsx` head.

## Lovable prompt (for lead approval; read-only so far, nothing sent)

> In src/routes/__root.tsx, inside RootComponent, add `useEffect(() => { registerOfflineSW(); }, []);` and import `registerOfflineSW` from "@/engine/sw-register" (useEffect is already imported from react). Also add `{ rel: "manifest", href: "/manifest.webmanifest" }` to the `links` array in the root `head()`. Change nothing else. Do not add vite-plugin-pwa, workbox or any other service worker, and do not edit vite.config.ts, public/sw.js, public/ort/**, public/model/**, public/audio/** or src/engine/**: those are owned by the engine track.

The manifest line is only needed if the engine track adds `public/manifest.webmanifest`; drop it otherwise.
