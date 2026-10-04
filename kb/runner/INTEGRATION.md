# Integration report: overnight run 1 (Sun 4 Oct, about 01:20 CEST)

Integrator merged the three builder lanes into the cloud mirror and applied the result to the laptop.

## What merged
In /home/claude/runner/tree, branch master (snapshot c37ff0b, plus 5aa82ab runner .gitignore):
- engine (fast-forward to a22f9bc): decide never throws, sheet gate in checkQuality, bit-exact preprocess on native-size pixels, ORT wasm in public/ort, check_parity script, real-model e2e and browser smoke tests.
- content (d6d4b63, merges 5022f8e and 991ad25): retake_on_page card, farmer text no longer names cercospora, phoma or miner, agronomist fixes F10 to F14, F17, F20 to F22, REVIEW_LOG section.
- ui (4105b56, merges ff1a6b3 to d20a677): static farmer PWA, service worker precache, manifest and icons, offline e2e test, netlify.toml, README_DEPLOY.md.
- No merge conflicts. app/package.json came only from engine (sharp devDependency, parity and ort:copy scripts).

Integration commit 24b03a7:
- app/package.json: added `"e2e": "node tests/e2e/offline-flow.mjs"` (ui lane request).
- app/tests/e2e/offline-flow.mjs: refuses to start when its port already serves something. A stale wt-ui `vite preview` was still on port 4173, so the first e2e run silently tested the ui-lane build (it showed `Q:-` and `not_a_leaf` retakes). Run it with a free port: `PORT=4611 npm run e2e`.
- app/tests/e2e/screens/: screenshots and result.json from the merged build.

## Test counts (cloud, merged tree)
| Check | Result |
|---|---|
| app vitest | 18 files, 250 passed, 0 failed (snapshot: 135 passed, 1 todo) |
| tsc -p tsconfig.engine.json | clean |
| tsc -p tsconfig.app.json | clean |
| Conformance (ws-conformance, ENGINE_DIR=tree/app/src/engine) | 131/133 with the old fixtures; 132/133 after regenerating fixtures from the merged rules.json and answers.json (in a scratch copy; the shared ws-conformance copy is unchanged). The 1 remaining failure is the harness: specs/helpers.ts toPct reads confidence 1.0 (Q:100) as 1%. The engine is correct (Q:87 parses to 0.87). |
| python -m qa.run | 3 FAIL, all present at the snapshot too: sources:docs/EVALUATION.md (4 metric lines without a source label), client_clean:no_ai_apis_src (src/content/sources.json mentions elevenlabs), requirements:all_pass (26 of 26 todo). After build, 1 more FAIL: budgets:bundle_size, dist 17.7 MB against a 15.0 MB cap. 1 WARN: kikuyu_core (rust_high_pre_rains, removed on purpose by content F20). Skips: audio (no public/audio), ml_integrity (no ml/manifest.csv), videos (no video/final). |
| npm run build | passes; one ort wasm in dist (Vite's duplicate is dropped by the ui precache plugin) |
| Offline e2e at 360x740 (`PORT=4611 npm run e2e`) | E2E PASS: precache 25 files, 18,432,447 bytes; offline reload; real model, no mock badge; sample plot gives 10 not_a_leaf, summary 10 Not sure, answer too_many_unsure, berries line shown, referral `JANI1 M:OCC0412 P:P07 D:20261004 N:10 R:0 C:0 H:0 L:0 U:10 A:too_many_unsure Q:0 X:ask` (86 chars), history 1 item; camera photo and 2-photo upload give retake_on_page (sheet gate) |

## Apply report (laptop)
- runner_apply1.tgz: 98 files (95 changed since snap0, plus 3 copies under kb/runner/pending/), 7.6 MB, committed to kb/engine-cowork/_sync/.
- apply.py against snap0.tgz.baseline.json: applied 98, refused 0.
- Not applied, outside apply.py's allowed paths. Copies are in kb/runner/pending/ for Arthur to move in:
  - kb/runner/pending/kb/CONTRACTS.md -> kb/CONTRACTS.md (engine: Q line, Q:0 and N:0, sheet gate, retake_on_page)
  - kb/runner/pending/app/netlify.toml -> app/netlify.toml
  - kb/runner/pending/app/README_DEPLOY.md -> app/README_DEPLOY.md
- Not applied: the ui lane deleted app/src/App.css; apply.py cannot delete. The laptop copy is unused (nothing imports it) and can be deleted by hand.
- Laptop tests: app/ has no node_modules. To avoid putting Linux binaries (sharp) into the macOS folder, I copied the laptop's app/ (plus the read-only ml/parity_samples) into the Cowork VM and ran `npm install --legacy-peer-deps` there (24 s). Result on the laptop files: vitest 18 files, 250 passed; both tsc configs clean; npm run build passes with the same bundle hash as the cloud. On the Mac, run `cd app && npm install` (no package-lock.json on the laptop) before `npm test`.

## Open issues
1. Demo photos: the real model (v1-2026-10-04) labels all 12 bundled demo photos not_leaf (0.60 to 0.998, same in Python onnxruntime), and all fail the sheet gate. The sample plot always ends at too_many_unsure and a referral. Needs on-page demo photos close to the training domain, or the demo must say so.
2. parity: check_parity.mjs fails 9/10 (07.jpg max prob diff 0.0281 against 0.02) until expected.json is recomputed from the saved jpg (ml-1).
3. Budget: raw precache 18.4 MB against the 15 MiB cap in qa/checks/budgets.py; about 7.3 MB with gzip. Arthur to decide whether the cap means raw or transfer bytes, and whether the host compresses wasm.
4. Conformance harness: specs/helpers.ts toPct treats 1.0 as 1%; fixtures in the shared ws-conformance copy (and the laptop copy) need `python3 gen_fixtures.py` against the new answers.json.
5. Engine URLs are absolute (/model, /ort, /audio), so a GitHub Pages project subpath falls back to mock. Use Netlify or a root-served site, or build URLs from import.meta.env.BASE_URL.
6. Audio: no clips in this snapshot. Stale if rendered on the laptop: en+sw for retake_on_page, how_to_photograph, retake_dark, rust_high_pre_rains, rust_high_in_rains, rust_high_dry, cercospora, phoma, miner, mixed_problems; sw for rust_low. Delete kik/rust_high_pre_rains.mp3.
7. Swahili: 10 items in kb/content/REVIEW_LOG.md for the native reviewer; Swahili button labels in app/src/ui/strings.ts are an unreviewed draft; no Kikuyu UI labels.
8. Pre-existing qa FAILs: docs/EVALUATION.md metric lines need a source label; src/content/sources.json mentions elevenlabs (offline TTS source credit, trips the AI-API check); requirements table all todo.
9. Not tested: real phone, 4x CPU throttle, sheet gate and blur/dark thresholds on fresh phone photos (EDGE_PLAN move 2).
10. Not wired: consent_photos, syncPending, PIN lock. Cooperative SMS number is a placeholder (+254700000000, labelled 'Demo number'); set VITE_COOP_NUMBER at deploy.
11. Content F1 to F9 were out of scope tonight and not applied.
12. Stale vite preview processes from lanes are still running on ports 4173, 4190, 4573, 4574 (left alone).
