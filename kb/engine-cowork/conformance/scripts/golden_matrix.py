#!/usr/bin/env python3
"""Golden decision table for the conformance suite.

Re-implements the enumeration and rule semantics of app/qa/checks/decision_matrix.py
(the QA harness) faithfully, so the TypeScript engine can be checked against the
Python reading of CONTRACTS. Writes ../golden.json:

  {
    "meta": {...},
    "rows": { "<dominant>|<affected>|<uncertain>|<distinct>|<window>": "<answer id>", ... }
  }

Run from anywhere: python3 scripts/golden_matrix.py
"""
from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONTENT = ROOT / "content"

LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]
WINDOWS = ["pre_short_rains", "short_rains", "pre_long_rains", "long_rains", "dry"]
N = 10


def matches(cond: dict, s: dict) -> bool:
    """Same body as decision_matrix.matches."""
    for k, v in cond.items():
        if k == "dominant" and s["dominant"] != v:
            return False
        if k == "affected_gte" and not s["affected"] >= v:
            return False
        if k == "affected_lte" and not s["affected"] <= v:
            return False
        if k == "uncertain_gte" and not s["uncertain"] >= v:
            return False
        if k == "distinct_problems_gte" and not s["distinct"] >= v:
            return False
        if k == "window" and s["window"] != v:
            return False
    return True


def decide(rules: list[dict], s: dict) -> str:
    for r in rules:
        if matches(r.get("if", {}), s):
            return r.get("then", "ask_officer")
    return "ask_officer"


def enumerate_summaries():
    """Same filter as decision_matrix.run. Yields (dominant, affected, uncertain, distinct, window)."""
    for dominant, affected, uncertain, distinct, window in product(
            LABELS + ["none"], range(0, N + 1), range(0, N + 1), (1, 2, 3), WINDOWS):
        if affected + uncertain > N:
            continue
        if dominant in ("healthy", "none") and affected > 0:
            continue
        if dominant not in ("healthy", "none") and affected == 0:
            continue
        if distinct > max(1, affected):
            continue
        yield dominant, affected, uncertain, distinct, window


def main() -> int:
    rules = json.loads((CONTENT / "rules.json").read_text(encoding="utf-8"))
    answers = json.loads((CONTENT / "answers.json").read_text(encoding="utf-8"))
    if isinstance(answers, dict):
        answers = list(answers.values())
    ids = {a["id"] for a in answers}

    rows = {}
    reached = set()
    for dominant, affected, uncertain, distinct, window in enumerate_summaries():
        s = dict(dominant=dominant, affected=affected, uncertain=uncertain, distinct=distinct, window=window)
        card = decide(rules, s)
        reached.add(card)
        rows[f"{dominant}|{affected}|{uncertain}|{distinct}|{window}"] = card

    missing = sorted(c for c in reached if c not in ids)
    out = {
        "meta": {
            "source": "scripts/golden_matrix.py, mirrors app/qa/checks/decision_matrix.py",
            "n": N,
            "count": len(rows),
            "windows": WINDOWS,
            "key": "dominant|affected|uncertain|distinct|window",
            "reached": sorted(reached),
            "reached_missing_from_answers": missing,
            "rules_count": len(rules),
        },
        "rows": rows,
    }
    (ROOT / "golden.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote golden.json: {len(rows)} summaries, {len(reached)} distinct cards, missing={missing}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
