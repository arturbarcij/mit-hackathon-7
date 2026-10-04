# Overnight research harness (lead)

Pre-registered experiments for the leaf model, run while we sleep. Owner: lead (see kb/OWNERSHIP.md).
It reads app/ml (train.py, export.py, eval.py, common.py, manifest.py) and writes only inside this folder.

## Run (from app/ml, jani env)
1. `python research/sweep.py --smoke` (about 3 to 5 min on CPU; must end with `SMOKE OK`). Also caches the MobileNetV4 weights.
2. Overnight: `powershell -ExecutionPolicy Bypass -File research/run_overnight.ps1`. It waits for v1 (calibration.json, checkpoint, newer metrics.json), then runs the queue. Leave the laptop on mains power with the lid open. The process keeps Windows awake while it runs.
3. Morning: read `research/overnight/SUMMARY.md`. `python research/sweep.py --status` shows progress.

## What it guarantees
- v1's split is frozen in `manifest_frozen.csv` (manifest.py cannot regenerate it). Held-out rows are refreshed from disk without touching train/val/test.
- `plan.py` holds every choice (jobs, metric, margins, rule). `PLAN.md` and `plan_lock.json` record its sha256 before any job runs; selection refuses to run if it changed.
- Selection uses in-domain val only. Uganda, RoCoLe and wild photos are scored once, after `selection.json` exists, for v1 and the winner.
- Coverage is the LARGEST share of val that is at least 95% accurate (train.py's calibrate() had this backwards).
- Never writes public/model/, ml/calibration.json, ml/metrics.json or docs/EVALUATION.md.

## Jobs
v1 (re-scored), protocol (BRACOL x6 + daylight/shadow shifts), mnv4 (MobileNetV4-conv-small, fallbacks listed in plan.py), replicate (seed 43, sets the noise margin), combo (only if protocol and mnv4 both beat v1).

## Held-out data
`python research/data.py merge` refreshes held-out rows after downloads. Add `--write-ml-manifest` to give eval.py the new rows too (refuses if ml/manifest.csv no longer has v1's split).
