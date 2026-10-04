# Jani PWA proof: TanStack Start + vite-plugin-pwa + onnxruntime-web, fully offline

Date: 4 Oct 2026. Lane EC1. Runnable mirror project in `_work/mirror` (node_modules and build output stay there).

## What was proven

A TanStack Start app on the exact Lovable stack (`@tanstack/react-start` 1.168.60, `@tanstack/react-router` 1.170.41, `@tanstack/router-plugin` 1.168.42, vite 8.1.5, nitro 3.0.260603-beta, react 19.2, tailwind 4 via `@tailwindcss/vite`, and the real `@lovable.dev/vite-tanstack-config` preset) can:

1. Register a service worker that precaches the client bundle, a 1.87 MB int8 `.onnx`, the 14.24 MB onnxruntime-web `.wasm`, an `.mp3` and `.json` files, with `maximumFileSizeToCacheInBytes` at 15 MB.
2. Reload with the browser context offline and complete a full in-browser ONNX inference (wasm backend, 1 thread). Every request during the offline run came from the service worker. No failed requests.
3. Keep working after the server process is killed (SIGKILL) and the page is reloaded.
4. Run the same inference under CDP 4x CPU throttling.

Test: `tests/offline.spec.ts`, one Playwright test, passes in 7.4 s. Results: `RESULTS.json`.

## Numbers

| Item | Value |
| --- | --- |
| Precache entries | 14 |
| Precache total | 16,567,819 bytes (15.80 MB) |
| onnxruntime-web 1.30.0 wasm (`ort-wasm-simd-threaded.wasm`) | 14,239,897 bytes |
| Test model int8 (`leaf.onnx`) | 1,865,272 bytes (fp32 export was 6,076,658 bytes, 1.52 M params) |
| Client JS (index + routes + ort glue + register) | about 420 KB |
| test.mp3 / answers.json | 8,482 / 20,847 bytes |
| Inference, online, no throttle | 147 ms (warm, second run) |
| Inference, offline, no throttle | 84 ms |
| Inference, offline, 4x CPU throttle | 96 ms |
| Session create (offline) | 355 ms; 225 ms throttled (JIT already warm) |
| Fetch of model + mp3 + json from SW (offline) | 174 ms; 429 ms throttled |

The wasm file actually requested at runtime is one file: `/assets/ort-wasm-simd-threaded-<hash>.wasm`. The `ort.wasm.bundle.min.mjs` entry inlines the `.mjs` glue, so no `.mjs` is fetched. The jsep, jspi and asyncify variants are never requested with the plain wasm backend.

Budget: the 15 MB budget in `kb/agents/engine.md` is missed by 0.8 MB with onnxruntime-web 1.30.0. The wasm alone is 14.24 MB. Older versions are smaller: 1.22.0 is 11.21 MB, 1.20.1 is 11.25 MB, 1.17.3 is 10.65 MB (`ort-wasm-simd-threaded.wasm`). Pinning `onnxruntime-web@1.22.0` gives about 12.8 MB total with this model. The gzip transfer size of the 1.30.0 wasm is 3.74 MB, so first download is fine; the budget question is cache storage on the phone.

## Recipe for the engine agent (apply to `web/`)

### 1. Packages

```
bun add onnxruntime-web@1.22.0            # 1.30.0 works too but wasm is 14.2 MB
bun add -d vite-plugin-pwa@1.3.0           # brings workbox-build 7.x and workbox-window
bun add -d @playwright/test@1.56.0         # must match the Chromium revision available (1194 here)
```

`vite-plugin-pwa` 2.0.0 exists but was not tested. 1.3.0 declares vite ^8 support and worked.

### 2. vite.config.ts

Use the file in this folder. It keeps Lovable's `defineConfig` from `@lovable.dev/vite-tanstack-config` and passes two user plugins:

- `VitePWA({...})` for `manifest.webmanifest`, the `virtual:pwa-register` module and types. `injectRegister: false` (there is no index.html to inject into). Its own `sw.js` is useless here (see gotcha 1) and is ignored.
- `workboxClientEnv()`, a 40-line inline plugin that runs `workbox-build`'s `generateSW` in the client environment's `closeBundle`, against that environment's `build.outDir`, and adds the files in `public/` to the precache manifest with md5 revisions. This is the step that produces the real `sw.js`.

Set `tsconfig.json` `compilerOptions.types` to include `"vite-plugin-pwa/client"` for the virtual module types.

### 3. Service worker registration (TanStack Start root route)

`sw-registration.__root.tsx` is the full file. The important part is in the `shellComponent`:

```tsx
useEffect(() => {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return
  import('virtual:pwa-register').then(({ registerSW }) => registerSW({ immediate: true }))
}, [])
```

and in `head()`:

```ts
links: [{ rel: 'manifest', href: '/manifest.webmanifest' }, { rel: 'icon', href: '/icons/icon-192.png' }]
```

Import global CSS as a plain side-effect import (`import '../styles.css'`), not `?url` (gotcha 5).

### 4. onnxruntime-web usage

```ts
const ort = await import('onnxruntime-web/wasm')   // dynamic import keeps it out of SSR
ort.env.wasm.numThreads = 1
ort.env.wasm.proxy = false
// do not set ort.env.wasm.wasmPaths; see "public/ort" below
const session = await ort.InferenceSession.create(new Uint8Array(await (await fetch('/model/leaf.onnx')).arrayBuffer()), { executionProviders: ['wasm'] })
```

### 5. public/ folder layout

```
public/
  model/leaf.onnx, model/model.json      (ml agent)
  audio/<lang>/<answerId>.mp3            (content-voice agent)
  content/answers.json                   (if served statically; src/content imports are bundled anyway)
  icons/icon-192.png, icons/icon-512.png (manifest icons; 192 and 512, PNG)
```

Everything under `public/` matching `js,css,html,svg,png,ico,json,onnx,wasm,mp3,webmanifest` is precached by the plugin. Keep `public/` lean: a stray 5 MB file goes into every phone's cache.

`public/ort/`: not needed with this setup, and copying the wasm there doubles the output (30 MB instead of 16 MB) because Vite also emits the wasm that `ort.wasm.bundle.min.mjs` references through `new URL(..., import.meta.url)`. The emitted copy lands in `/assets/ort-wasm-simd-threaded-<hash>.wasm` and is precached by the glob. If you insist on `public/ort/` and `wasmPaths = '/ort/'`, you must also stop Vite emitting the asset (for example `resolve.conditions: ['onnxruntime-web-use-extern-wasm', ...]`, which switches to the non-bundle entry that fetches both `/ort/ort-wasm-simd-threaded.mjs` and `.wasm`). Not tested.

### 6. Build and run locally

```
NITRO_PRESET=node-server bun run build     # vite build; see gotcha 2 for why the env var
PORT=3000 node .output/server/index.mjs
bunx playwright test                       # tests/offline.spec.ts starts and kills the server itself
```

Build log must show a line like `[jani:workbox-client-env] 14 built files (13.99 MB) + 6 public/ files (1.81 MB) precached -> .../.output/public/sw.js`.

### 7. What to check in the Lovable preset (@lovable.dev/vite-tanstack-config)

It is on npm (2.24.0 and 2.25.1), so the mirror used it. Facts read from its source:

- `defineConfig({ plugins, vite, nitro, tanstackStart, react })`. Plugins you pass are appended after tailwind, tsconfig-paths, tanstackStart, nitro and react.
- Outside the Lovable sandbox, nitro's preset comes from `NITRO_PRESET`, else `defaultPreset: 'cloudflare-module'`. Inside the sandbox (`LOVABLE_SANDBOX=1` or `DEV_SERVER__PROJECT_PATH` set) it forces `cloudflare-module` with output `dist/`, server `dist/server`, public `dist/client`. The `closeBundle` plugin uses `this.environment.config.build.outDir`, so it follows whatever nitro sets. Confirm the Lovable build log shows the `[jani:workbox-client-env]` line and that `dist/client/sw.js` exists in the published output.
- The preset's own `lovable:document-set` plugin fails the build if a prerendered route would overwrite a committed `public/` file. Do not put `index.html` in `public/`.
- `css.transformer: 'lightningcss'` is set by the preset.

## Gotchas (in the order they were hit)

1. vite-plugin-pwa's generateSW globs the wrong folder. With TanStack Start the client bundle goes to the client environment's outDir (`dist/client`, or `.output/public` when nitro's vite plugin is active). vite-plugin-pwa globbed the root `dist/` and produced a 3-entry manifest with `sw.js` in `dist/`. It also ran three times (once per environment). Fix: generate the SW yourself in the client environment's `closeBundle` (the `workboxClientEnv` plugin).
2. Nitro bakes a public-asset manifest for the node server. Any file written to `.output/public` after nitro's build step (for example from a `buildApp` hook with `order: 'post'`) is served as 404 by `node .output/server/index.mjs`. The SW must exist before nitro scans the folder, which `closeBundle` of the client environment guarantees.
3. `buildApp` with `order: 'pre'` runs before the environment builds, not between them, because nitro's own `buildApp` hook is what triggers the client and ssr builds. Not usable for this.
4. Nitro copies `public/` itself, after the client environment closes. At `closeBundle` time the model, audio and content files are not on disk in the output folder, so the glob misses them. Fix: `additionalManifestEntries` computed from the project's `public/` with md5 revisions.
5. `import appCss from '../styles.css?url'` (the TanStack Start docs pattern) linked `/assets/styles-<hashA>.css` in the SSR HTML while the client build emitted `styles-<hashB>.css`. Tailwind's output differs between the ssr and client environments (10.5 kB vs 9.1 kB), so the hashes differ and the stylesheet 404s even online. A plain `import '../styles.css'` is resolved through the Start manifest and gives one consistent `index-<hash>.css`. Check the live Lovable project for this bug.
6. `tanstackStart.spa: { enabled: true }` (to prerender a `/_shell` for `navigateFallback`) made `vite build` hang after a successful build; killed after 6 minutes. Dropped. Offline navigation instead uses a Workbox `runtimeCaching` rule: `request.mode === 'navigate'` with `NetworkFirst` (3 s timeout, cache `jani-pages`). The first online visit stores the SSR HTML of `/`; offline reloads serve it. Consequence: a route the user never opened online is not available offline. For Jani, the farmer flow is one route, so this is fine. If more routes are needed, open them once online or revisit the shell prerender.
7. `injectRegister: 'auto'` does nothing without an index.html. Register manually in `__root.tsx` with `virtual:pwa-register` behind a dynamic import so the SSR bundle does not execute it.
8. The default import `onnxruntime-web` resolves to `ort.bundle.min.mjs` (webgpu + wasm, 368 KB of JS). Import `onnxruntime-web/wasm` (71 KB) instead.
9. Importing onnxruntime-web statically in a route pulls it into the SSR bundle (nitro built `_libs/onnxruntime-web.mjs`). Harmless here because of the dynamic import, but keep all ORT code behind `await import()` or inside `useEffect`.
10. `npm install` failed with "Cannot read properties of null (reading 'edgesOut')"; `--legacy-peer-deps` fixed it. Lovable uses bun, which is on this machine too (`/root/.bun/bin/bun`), untested here.
11. Playwright 1.56.0 is the version that matches the Chromium 1194 in `/opt/pw-browsers`. `@playwright/test@1.58+` would try to download a browser.
12. With the server killed and the context back online, the navigation probe (`NetworkFirst`) fails and is logged as a failed request before the cached page is served. The test allows exactly that one failure.
13. The untrained test model yields logits of about +/-0.01, so argmax differs between ORT wasm (1) and ORT CPU in Python (3). Not a caching issue. Parity tests must use the trained model and a tolerance.
14. `maximumFileSizeToCacheInBytes` only applies to globbed files, not to `additionalManifestEntries`. The 15 MB limit is still needed for the 14.2 MB wasm in `assets/`.

## Files

- `README.md` this file
- `RESULTS.json` measured numbers
- `vite.config.ts` the working config (Lovable preset + VitePWA + workboxClientEnv)
- `sw-registration.__root.tsx` root route with manual SW registration and manifest link
- `demo-route.index.tsx` the test route: fetches, creates the ORT session, runs inference
- `tests/offline.spec.ts`, `playwright.config.ts`
- `package.json` of the mirror
- `scripts/make_test_model.py` builds the int8 test model (`python3 scripts/make_test_model.py public/model _work/model`)
- `_work/mirror` the full runnable mirror (node_modules, `.output`); `_work/RESULTS.raw.json`, `_work/build.log`
