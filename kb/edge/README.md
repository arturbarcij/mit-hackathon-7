# kb/edge: field check and sheet gate (lead, Sun 4 Oct)

- `sheet_gate.py`: image-validity gate for the capture protocol (one leaf flat on a plain page). Reference for the engine's TypeScript port. Run `python kb/edge/sheet_gate.py <photo.jpg>` to see the decision and its three numbers.
- `field_check.py`: scores a model on BRACOL val/test (protocol proxy), a random Uganda sample and iNaturalist Hemileia, before and after the gate, then simulates 4,000 ten-leaf plots per scenario through `app/src/content/rules.json`. Writes `out/per_image.csv`, `out/summary.json`, `out/summary.md`.
  - v1: `python kb/edge/field_check.py --model app/public/model --out kb/edge/out/v1`
  - candidate: `python kb/edge/field_check.py --model <folder with leaf.onnx and model.json> --out kb/edge/out/<name>`
- Numbers and reasoning: `kb/EDGE_PLAN.md` section 4. Gate thresholds were set on the same images, so validate on fresh photos before quoting them as final.
