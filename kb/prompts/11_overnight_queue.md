# 11 Overnight research queue (ml lane): launch only

The lead built and tested the harness in `app/ml/research/` (README there). v1's split is already frozen in `research/manifest_frozen.csv` (63,687 rows; train 31,477, val 6,764). Paste into the ml Cursor chat once v1 is fixed and shipped, before 01:30.

Read app/ml/research/README.md. Do not edit anything in app/ml/research/ (lead-owned; plan.py is pre-registered).

1. Prerequisites: at least 10 GB free on C:; calibrate() fixed (largest k, temperature grid to 6.0) and v1 recalibrated; export.py using per-channel quantisation with int8 parity at least 95%; eval.py re-run so ml/metrics.json is newer than ml/calibration.json.
2. If the Uganda and RoCoLe downloads finished: `python research/data.py merge --write-ml-manifest` (adds held-out rows without touching train/val/test), then re-run eval.py only. Never re-run manifest.py.
3. From app/ml: `python research/sweep.py --smoke`. It must end with `SMOKE OK` (CPU, about 3 to 5 minutes; also downloads the MobileNetV4 weights). If it fails, paste the last 30 lines of research/smoke/runs/*/stdout.log into the reply and stop.
4. Launch in a separate PowerShell window, not inside an agent turn: `powershell -ExecutionPolicy Bypass -File research\run_overnight.ps1`. It waits for v1, then runs v1 (re-scored), protocol, mnv4, replicate and maybe combo, selects by the rule in research/overnight/PLAN.md, and scores held-out sets once.
5. After launch, no agent edits code, pushes to git, downloads or uses the GPU until 06:30. Update STATUS M6 to "running".

06:30: read research/overnight/SUMMARY.md. If it names a winner, follow its "Next" section (engine must confirm under 1 s per leaf at 4x CPU throttling; not done by 08:00 means keep v1). Either way, put the results table into EVALUATION.md as the ablation, with the held-out rows for both models. Reply in five lines: done, not done, blocked on, unsure about, next.
