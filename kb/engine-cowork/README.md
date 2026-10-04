# engine-cowork: helper lanes for the engine agent

Written by Claude (Cowork, cloud) on the night of Sat 3 to Sun 4 Oct 2026. These lanes never edit `app/src/engine`, `app/tests` or anything owned by another agent. Everything here is input for the engine, ui, content-voice and ml agents to adopt or ignore. Each folder has its own README with run commands and numbers.

| Lane | Folder | State | Headline |
|---|---|---|---|
| EC1 PWA offline proof | `pwa/` | done | Offline inference proven on the exact Lovable stack (TanStack Start 1.168.60, vite 8.1.5, nitro 3.0 beta, Lovable's own vite preset 2.25.1). Playwright test passes. Precache 15.80 MB with onnxruntime-web 1.30.0; pin 1.22.0 to land at about 12.8 MB. |
| EC2 preprocessing parity | `parity/` | done | `src/preprocess.ts` reproduces `train.py` `eval_transform` bit for bit (24 fixtures, PNG and JPEG in Chromium: 0 levels difference). ort-web vs Python onnxruntime: max logit diff 1.9e-8 fp32, 2.3e-4 int8. |
| EC3 contract conformance | `conformance/` | done | 147-test vitest suite driven by `ENGINE_PATH`. Reference engine 147/147. Lovable mock 32/147 (115 fail). Audit of 20 drifts and a paste-ready L3 Lovable prompt. 12 CONTRACTS ambiguities listed in RESULTS.md. |
| EC4 MMS-TTS fallback audio | `audio-mms/` | blocked | Cloud proxy refuses huggingface.co, so no clips rendered. `render.py` is complete and tested on a synthetic tone. Run it on the laptop outside the Cowork VM (about 290 MB model download, a few minutes CPU) to get 28 Swahili and 9 Kikuyu clips, about 1.3 MB. |

## What the engine agent should do first (Sunday morning)

1. Pin `onnxruntime-web@1.22.0`. The 1.30.0 wasm alone is 14.24 MB and pushes the precache to 15.80 MB, over the 15 MB budget. See `pwa/README.md` section on budgets.
2. Use `pwa/vite.config.ts` as the template for `web/vite.config.ts`. vite-plugin-pwa's own `generateSW` misses the client bundle under nitro; the inline workbox plugin in that file is the fix. Register the service worker in `__root.tsx` as in `pwa/sw-registration.__root.tsx`.
3. Drop `parity/src/preprocess.ts` and `preprocess-browser.ts` into `web/src/engine/`. Never downscale in canvas; decode at native size and let the module resize. Expect 12 MP decode plus preprocess around 350 ms unthrottled, 1.2 s at 4x throttle: run it in a Web Worker.
4. Before replacing Lovable's engine run `ENGINE_PATH=/abs/path/web/src/engine npx vitest run` inside `conformance/`. Green means the UI contract holds.
5. Read `conformance/RESULTS.md` findings 1 to 7 and settle them in CONTRACTS (ParsedReferral type, plot id alphabet, Q and X semantics, UTC vs local date).

## For the other agents

- ui (Lovable): `conformance/LOVABLE_PROMPT_L3.md` is paste-ready and UI-only. `conformance/AUDIT_LOVABLE.md` lists every drift with owner and fix.
- ml: `quantize_static` warns about a bias initializer; add `quant_pre_process` before `quantize_static` in `export.py` (see `parity/README.md`). int8 is not faster than fp32 in wasm, it only saves bytes (1.67 vs 6.08 MB for the untrained net).
- content-voice: `audio-mms/README.md` explains the free MMS fallback, the CC BY-NC note for LANGUAGES.md and DATA_CARD.md, and the digit-to-word substitutions the script makes (10 -> kumi / ikũmi, 1 -> moja). Note: 9 answers have Kikuyu text, not 8 (`language_name` is the ninth).
- qa: `conformance/scripts/golden_matrix.py` reproduces `decision_matrix.py`; finding 9 in RESULTS.md describes rows the Python matrix enumerates that no real plot can produce.

## Environment notes
The cloud workspace cannot reach huggingface.co, download.pytorch.org or unpkg. Everything else (npm, PyPI, Chromium via Playwright) worked. Scratch, node_modules, fixtures and test models stayed in the cloud and are not in this folder.
