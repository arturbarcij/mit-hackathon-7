# Wave B: first reviews (run from Sun 01:00)

Read `kb/WORKFLOW.md` first. Launch in ONE message as parallel `Task` calls with `run_in_background: true`:

1. [qa] Run `python -m qa.run --llm` from `app/`, route every FAIL and WARN to its owner in `kb/STATUS.md`.
2. [judge] Pass 1 per `kb/agents/judge.md`. Report to `kb/judge/`.
3. [redteam] Pass 1 per `kb/agents/redteam.md`. Report to `kb/redteam/`.
4. [ml] Continue M3, M4, M5 if not finished (calibration, int8 ONNX, parity, EVALUATION numbers).

Each prompt ends with "When done or blocked, reply in five lines: done, not done, blocked on, unsure about, next."
When they report, list the blockers and majors by owner and stop.
