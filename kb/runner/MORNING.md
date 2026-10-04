# Morning brief, Sun 4 Oct (overnight runner RN1, 00:50 to 01:55 CEST)

**Bottom line.** app/ now holds a working offline farmer PWA with the real model (fp16, 2.93 MB), and all 4 safety blockers in app/ are fixed and checked. One blocker is still open: two pitch files claim human review that has not happened. The demo cannot show rust yet: the real model reads every bundled demo photo as "not a leaf". Everything below is on cloud master acfa5b2 and has been applied to the laptop. No git commits were made on the laptop.

## 1. What changed in app/
- **Engine** (app/src/engine): `decide.ts` never throws and returns ask_officer on bad input. With fewer than 10 leaves it now returns the new `too_few_leaves` card (MIN_LEAVES = 10, decide.ts:109). `gate.ts` is a port of sheet_gate.py: a photo without a page gets `retake_on_page`. `preprocess.ts` is bit-exact and runs on native-size pixels. The ORT wasm is in `public/ort` (14.26 MB). `model.ts` no longer falls back to the mock silently: if the model fails to load, every leaf is "not sure". New scripts: `app/scripts/check_parity.mjs`, `copy-ort-wasm.mjs`, `browser-smoke`.
- **Content** (app/src/content/answers.json, kb/content/REVIEW_LOG.md): new cards `retake_on_page` and `too_few_leaves`. The cercospora, phoma and miner farmer text no longer names a disease. Agronomist changes F10 to F14, F17 and F20 to F22 are in. F1 to F9 are not. Kikuyu was removed from rust_high_pre_rains. All Swahili is still a Claude draft.
- **UI** (app/src/pages, app/src/ui, app/public/sw.js, app/vite.config.ts): a static Vite PWA, one action per screen: language, consent, pick, photograph, up to 10 photos, summary, answer, act/wait/ask, referral SMS, history. See result stays off until there are 10 leaves. Duplicate photos are dropped. Draft text is tagged "Draft, pending review". The service worker precaches everything. Netlify config and deploy notes are in `app/README_DEPLOY.md`.
- **Docs**: `app/docs/RESPONSIBLE_AI.md` and `LANGUAGES.md` now match the build: Swahili is a draft, there is no audio, and the PIN, photo sync and dashboard are marked planned.
- **Applied to the laptop**: runner_apply1 (98 files), integration1, judge1, redteam1 and apply2 (18 files), with 0 refused. **Still to do by hand:** move the 3 files in `kb/runner/pending/` (kb/CONTRACTS.md, app/netlify.toml, app/README_DEPLOY.md) to their real paths, delete `app/src/App.css` (unused), and delete `kb/engine-cowork/_sync/_to_delete/`.

## 2. Tests and checks (cloud master acfa5b2)
- vitest: 19 files, 262 passed, 0 failed (snapshot: 135 + 1 todo). tsc engine and app configs: clean. `npm run build`: passes.
- Offline e2e at 360x740: PASS. Offline reload works, the real model runs with no mock badge, and the referral SMS and history work. Precache: 25 files, 18,433,009 bytes raw, about 7.3 MB gzip.
- Conformance: 125 of 133 pass against the shared fixtures. The 8 failures come from stale fixtures and rows with n<10. With fixtures regenerated and the n<10 rule added: 132 of 133 pass. The 1 left is a harness bug (toPct reads Q:100 as 1%).
- qa.run: 4 FAIL, all known: EVALUATION.md source labels, elevenlabs in sources.json, the requirements table is all todo, and the bundle is 17.7 MB against a 15 MB cap. 1 WARN (kikuyu_core, removed on purpose).
- check_parity: 9 of 10 pass, top-1 10 of 10. 07.jpg is off by 0.0281 against a 0.02 limit (ml-1: expected.json needs recomputing).
- Sheet gate matches Python on 37 of 37 images. Preprocess is byte-identical on 22 of 22. Node and Chromium agree with Python ORT to within 0.0063.
- Laptop: 250 passed after apply1 (run in a VM copy). The apply2 files have the same sha256 as cloud master. The Mac itself has no node_modules.

## 3. Judge and red-team
- Judge: **56.5/100** (previous pass 50). Gate: FAIL before the fixes. There was no rescore after the fixes.
- Red-team gate: FAIL before the fixes, with 3 blockers.
- Judge B1, small plots get definitive answers: **verified fixed.**
- Judge B2, review over-claims: **partly fixed.** app/docs is fixed. Still open: `kb/pitch/SUBMISSION_FORM.md:32,60,63` and `kb/pitch/VIDEO3_tech.md:36`.
- Red-team B1, silent fallback to the mock model: **verified fixed.**
- Red-team B2, no minimum leaf count and no duplicate check: **verified fixed.** Copies of a rejected photo still count, but they can only lead to an ask card.
- Red-team B3, Responsible AI claims: **verified fixed.** The Capture and History lists still show Swahili without the draft tag.
- **Open, not blockers:**
  - Berries and drawn shapes come out as phoma at 0.67 to 0.81.
  - Consent "No" can be bypassed through History, then New check.
  - int8 is still claimed in ARCHITECTURE.md:12,40 and REQUIREMENTS R3.
  - README:13 over-claims rust detection.
  - CONTRACTS.md has no too_few_leaves.

## 4. Decide before 08:30
1. **Hosting.** Option A, static app/ PWA on Netlify: real model, offline e2e PASS, every app blocker fixed, about 30 minutes to deploy. Option B, Lovable TanStack (jani-farm-assist.lovable.app): has the officer side, but uses its own engine port and a mock vision model, and the red-team found blockers there (5-leaf finish, mock labels). **Recommended:** A as the farmer app, with the Lovable URL linked only as the officer dashboard using synthetic records.
2. **The 15 MB budget: raw or transfer bytes?** Raw is 18.4 MB, of which the ORT wasm is 14.26 MB. Transfer is about 7.3 MB gzip or 5.85 MB brotli. **Recommended:** transfer. Report both numbers and change qa/checks/budgets.py to match.
3. **Audio.** No clips exist yet, because the ElevenLabs key in app/backend/.env is empty. Either render now or remove the voice claims from README section 12, sources.json, SUBMISSION_FORM and LANGUAGES. If you render, re-render these:
   - en and sw: retake_on_page, too_few_leaves, how_to_photograph, retake_dark, rust_high_pre_rains, rust_high_in_rains, rust_high_dry, healthy_all, cercospora, phoma, miner, mixed_problems.
   - sw only: rust_low.
   - Delete: kik/rust_high_pre_rains.mp3.
- Also needed: the real cooperative SMS number for VITE_COOP_NUMBER (the default is a labelled demo number), and new demo photos (see action 4).

## 5. Your first 5 actions
1. Move the 3 pending files and delete App.css (section 1). Then run `cd app && npm install && npx vitest run` and expect 262 passed.
2. Fix the last blocker: correct SUBMISSION_FORM.md lines 32, 60 and 63 and VIDEO3_tech.md line 36 to say "Swahili drafted, native review pending; no audio in this build". Alternatively, do a 10-minute Swahili review and log it in REVIEW_LOG and reviewed_by.
3. Make the hosting call. If you choose A: `npm run build`, drop app/dist on Netlify, put the URL in README:5 and SUBMISSION_FORM, then do one airplane-mode run on an Android phone and note the time per leaf.
4. Fix the demo: take 10 photos of leaves flat on a white page, or add 10 BRACOL test leaves the model accepts (CC BY 4.0, labelled as chosen). Put them in app/public/demo/ and check that the model reads rust.
5. Port the evidence to EVALUATION.md and README sections 5 and 8: the EDGE_PLAN section 4 tables and the browser numbers above. Change int8 to fp16. Then run `python -m qa.run` again.

Lane reports: kb/runner/INTEGRATION.md, kb/judge/pass1.md, kb/redteam/pass1.md, kb/content/REVIEW_LOG.md.
