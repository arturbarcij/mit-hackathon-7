# Engine port (lead, Sat 3 Oct night)

The non-ML engine, written by the lead because the engine lane was blocked on the Lovable GitHub sync (L1/U0). Pasted verbatim into the Lovable project (jani-web) as src/engine/{types,decision,vision,index}.ts.

- `decision.ts`: summarisePlot, seasonWindow, seasonClock, decide (rules.json), answerCard and cardText (answers.json), buildReferral (JANI1), explain.
- `vision.ts`: quality gate (Laplacian variance blur, brightness, size) and the colour-heuristic MOCK classifier, used until leaf.onnx is wired in. Thresholds are assumptions.
- Tests: `python3 test/ref.py && tsx test/decision.test.ts` (copy src/content/*.json and src/lib/parseReferral.ts next to it first). Parity with app/qa decision matrix on 3,510 summaries, 3,000 random plots, every day of 2026, 500 SMS round trips.

Engine lane: take ownership back, add onnxruntime-web inference in classifyLeaf, keep the same exports.
