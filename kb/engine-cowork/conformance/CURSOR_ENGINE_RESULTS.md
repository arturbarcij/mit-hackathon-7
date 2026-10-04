# Contract suite against the Cursor engine (app/src/engine, staged 00:23 CEST Sun)

Result: 125 of 133 pass. All 3,510 decide cases from the QA evaluator pass. Plot, season, sms and guardrails specs pass.

## Failures (8), two real bugs

1. decide is not fail-safe on bad input (5 tests). Safety gate relevant.
   - `decide(null)` and `decide(undefined)` throw `TypeError: Cannot read properties of null (reading 'uncertain')`.
   - Negative `uncertain`, `n = Infinity` and an invalid date return `healthy_all`. They should return `ask_officer`.
   - Fix: validate the summary and date at the top of decide; anything not finite, negative or inconsistent returns the ask_officer card. Never throw.
2. The engine's own parseReferral cannot read its own SMS when no leaf was accepted (3 tests, 40 of 300 random round trips).
   - buildReferral writes `Q:-` when there is no accepted leaf (for example n = 0 or all unsure). CONTRACTS says `Q:<conf%>`, and parseReferral returns null on `Q:-`.
   - Example: `JANI1 M:OCC0412 P:P07 D:20261004 N:0 R:0 C:0 H:0 L:0 U:0 A:ask_officer Q:- X:ask`
   - Fix: write `Q:0` (and say in CONTRACTS that Q is the mean confidence of accepted leaves, 0 when none), or make parseReferral accept `-`. The first is simpler for the officer dashboard parser too.

Rerun: from kb/engine-cowork/conformance, `npm install --legacy-peer-deps`, then
`ENGINE_DIR=../../../app/src/engine CONTENT_DIR=../../../app/src/content npx vitest run`.
Full log: logs/cursor-engine.engine-suite.txt
