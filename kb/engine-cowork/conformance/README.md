# Jani engine conformance suite

Checks any implementation of the Jani engine against `kb/CONTRACTS.md`, using the real content files (`answers.json`, `rules.json`, `season.json`). Covers the pure functions: `summarisePlot`, `seasonWindow`, `decide`, `buildReferral`, `parseReferral`, `smsLink`, plus a compile-time signature check. Browser functions (model, storage, audio, sync) are out of scope here.

## Run

```
cd ec/conformance
npm i                         # vitest 4, typescript 5 (if npm 10 fails with "edgesOut", add --legacy-peer-deps)
npx vitest run                # against ./reference (must be green)
ENGINE_PATH=/abs/path/to/app/src/engine npx vitest run     # against the real engine
ENGINE_PATH=../_inputs/lovable/src/engine npx vitest run    # against Lovable's mock
python3 scripts/golden_matrix.py                            # regenerate golden.json after rules.json changes
npx tsc --noEmit -p tsconfig.json                           # type-check the suite itself
```

`ENGINE_PATH` is a directory with an `index.ts` (or a file), absolute or relative to this folder. Tests import the engine only through `tests/engine-under-test.ts`.

In this checkout `node_modules` is a symlink to `_work/node_modules`; `npm i` in a fresh clone creates a normal one.

## Layout

- `tests/` one file per module: `plot`, `season`, `decide`, `answers`, `referral`, `types`. `fixtures.ts` loads content and builds LeafResults. `types-check.ts` is compiled by `types.test.ts` with tsc.
- `reference/` minimal pure implementation that the suite is proven green against. `gsm7.ts` is a GSM 03.38 length counter.
- `content/` read-only copies of the three content files (fixtures). Refresh them from `app/src/content` when content-voice changes them, then rerun `scripts/golden_matrix.py`.
- `scripts/golden_matrix.py` mirrors `app/qa/checks/decision_matrix.py` and writes `golden.json` (3,510 rows).
- `RESULTS.md` pass/fail tables and CONTRACTS findings. `AUDIT_LOVABLE.md` drift list. `LOVABLE_PROMPT_L3.md` paste-ready UI prompt.
- `_work/` npm install and run logs. Not a deliverable.

## What a green run proves

- summarisePlot follows every clause of the CONTRACTS semantics, including tie order and the not_leaf majority rule.
- seasonWindow maps every day of a leap and a non-leap year to exactly one window from season.json.
- decide agrees with the Python QA harness on all 3,510 abstract summaries, returns only ids in answers.json for all 40,040 real 10-leaf decisions, and the cards carry the exact answers.json text, audio paths, sources and assumption flag.
- buildReferral emits the JANI1 line, at most 160 GSM-7 characters, and parseReferral round-trips it and rejects garbage.
- Exported signatures and types match CONTRACTS at compile time.
