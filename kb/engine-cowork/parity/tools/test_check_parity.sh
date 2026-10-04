#!/usr/bin/env bash
# Self-test for check_parity.mjs on the fixture case: good case must exit 0, a tampered copy must exit 1.
set -u
cd "$(dirname "$0")/.."
CASE=fixtures/parity_case
PRE=${PRE:-src/preprocess.ts}
node tools/check_parity.mjs --model $CASE/public/model --samples $CASE/ml/parity_samples --preprocess $PRE > /dev/null; good=$?
TMP=$(mktemp -d); cp -r $CASE/ml/parity_samples/. "$TMP"/
python3 - "$TMP/expected.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p))
s = d["samples"][2]; s["label"] = "not_leaf" if s["label"] != "not_leaf" else "healthy"
d["samples"][4]["probs"]["rust"] += 0.05
json.dump(d, open(p, "w"))
PY
node tools/check_parity.mjs --model $CASE/public/model --samples "$TMP" --preprocess $PRE > "$TMP/out.txt"; bad=$?
grep -c false "$TMP/out.txt" | xargs echo "rows flagged in tampered case:"
rm -rf "$TMP"
echo "good case exit=$good (want 0), tampered case exit=$bad (want 1)"
[ "$good" = 0 ] && [ "$bad" = 1 ]
