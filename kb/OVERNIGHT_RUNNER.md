# Overnight agent runner (RN1), Sun 4 Oct 2026, from 00:50 CEST

Cowork workflow `jani-overnight-runner` (run wf_731671c2-411). Arthur approved overnight edits to app/ owned paths. It does not touch app/ml, the GPU sweep, git remotes or Lovable credits.

## Pipeline
1. Build, three lanes in parallel, each in its own git worktree of a cloud mirror (snapshot snap0, 00:40):
   - engine: decide fail-safe and Q:0 referral fixes; sheet gate port (kb/edge/sheet_gate.py to src/engine/gate.ts, card retake_on_page); bit-exact preprocess.ts; onnxruntime-web/wasm with local /ort/; check_parity and demo predictions with the real leaf.onnx.
   - content: retake_on_page card; farmer cards no longer name phoma, cercospora or miner as findings; agronomist requests F10 to F22; REVIEW_LOG entry with the audio files that are now stale.
   - ui: static Vite farmer PWA in app/ (EDGE_PLAN move 3 fallback), with "Try a sample plot" (move 4), service worker, Playwright offline end-to-end test at 360x740, deploy notes.
2. Integrate: merge, full tests (vitest, contract suite, qa.run, build, offline e2e), apply to the laptop through kb/engine-cowork/_sync/apply.py. apply.py refuses any file changed on the laptop since the snapshot.
3. Review: a judge pass and a red-team pass write to kb/judge/pass1.md and kb/redteam/pass1.md.
4. Fix: one round on blockers, each checked by an adversarial verifier.
5. Report: kb/runner/MORNING.md plus the STATUS RN1 row.

A scheduled morning pass runs at 06:20 CEST in the same session. It reads the sweep summary, runs field_check on v1 and the winner, re-runs the tests and messages Arthur.
