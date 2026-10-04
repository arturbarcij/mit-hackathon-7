# Jani QA harness

Automated checks against the hackathon requirements (see `docs/REQUIREMENTS.md` and `kb/MASTER_PROMPT.md` section 12). Run it before every milestone and before submission. Nothing is "done" until this passes.

## Run

From the `app/` folder:

```
python -m qa.run                 # deterministic checks, writes qa/report.md
python -m qa.run --llm           # add the judge and red-team reviews (needs ANTHROPIC_API_KEY in backend/.env, pip install anthropic)
python -m qa.run --only content,audio
python -m qa.run --strict        # warnings block; use for the final run
```

Exit code 1 when something blocks. `qa/report.md` holds the latest report; `qa/reports/` keeps history.

## Checks

| Check | Requirement | What it verifies |
|---|---|---|
| `content` | G3, P1, R4, R5 | Every required answer ID exists; Swahili and English text for all, Kikuyu for the 8 core; result cards sourced or flagged as assumption; no pesticide doses, brands or marketing words; rules reference real answers, numeric thresholds are sourced or flagged, catch-all is `ask_officer`; season windows valid and sourced. |
| `decision_matrix` | P1, G1 | Enumerates every plot summary (dominant label x affected x unsure x distinct problems x season window) through the rule table and writes `qa/decision_matrix.md` for an officer to review. Fails if 3+ unsure leaves, a not-leaf plot, or mixed problems do not end in an ask card, if an act card fires on 1 leaf or fewer, or if `healthy_all` fires with problems present. Warns on unreachable cards. |
| `audio` | R4, R5 | Swahili mp3 for every answer, Kikuyu for the core; total under 4 MB; manifest present. |
| `sources` | D1 to D4 | In README and docs, every line with a number carries a link, a `[S#]` tag, or the word assumption or synthetic. |
| `client_clean` | G3, S2 | No AI API hosts or SDKs in `src/` or `dist/`; no secret-like strings; no `VITE_*KEY` variables. |
| `budgets` | R3 | `leaf.onnx` under 5 MB; `model.json` complete, sha256 and bytes match, threshold not 0; `dist/` under 15 MB with a service worker and local onnxruntime wasm. |
| `ml_integrity` | W3, P1, D4 | v1's split unchanged since freezing; no held-out rows in train/val/test; near-duplicate clusters never cross splits; held-out sets cover their classes; calibration threshold below 0.999 and val coverage at least 30%; int8 parity at least 95%; research queue selected before scoring held-out sets. |
| `secrets_git` | S2 | `.env`, MCP configs and the challenge PDF are not tracked; no key-like strings in git history; LICENSE present. |
| `requirements` | all | Every row in `docs/REQUIREMENTS.md` is `pass` and links to evidence. |
| `videos` | S3, S4 | `video/final/01_team`, `02_demo`, `03_technical` exist as MP4 or MOV, each under 60 s and 1 GB (needs `ffprobe`); `video/COVERAGE.md` maps PDF items (a) to (e). |
| `judge` (LLM) | judging criteria | Scores the docs as a sceptical evaluator; lists slop signals and the top 3 fixes. Output in `qa/judge_latest.md`. |
| `redteam` (LLM) | pass/fail gate | Tries to break the safety gate: unsafe advice, abstention holes, consent gaps, over-claims. Output in `qa/redteam_latest.md`. |

Skips are normal early on (file not built yet). By 12:30 Sunday there should be no skips except `videos` until the videos exist.

## Adding a check

Create `qa/checks/<name>.py` with `run(root: Path) -> list[Result]`, add the name to `CHECKS` in `qa/run.py`, and add a row above.

## CI

`.github/workflows/qa.yml` (repo root) runs the deterministic checks on every push. The LLM steps run only locally.
