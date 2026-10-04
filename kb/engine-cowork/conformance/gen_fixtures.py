#!/usr/bin/env python3
"""Generate fixtures/decision_matrix.json from the QA harness's own decision evaluator.

The enumeration and the rule evaluation come from app/qa/checks/decision_matrix.py, so the
engine tests and the QA table can never disagree. If that module cannot be imported, a verbatim
port below is used and the fixture says so ("evaluator": "port").

Usage:
  python3 gen_fixtures.py                      # content from ./content, QA from ../../../app
  python3 gen_fixtures.py --app-root ~/Documents/MIT_Hackathon_7/app --content-dir <app>/src/content
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- verbatim port of qa/checks/decision_matrix.py (used only when the import fails) ----
PORT_LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]
PORT_WINDOWS = ["pre_short_rains", "short_rains", "pre_long_rains", "long_rains", "dry"]
PORT_N = 10


def port_matches(cond: dict, s: dict) -> bool:
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


def port_decide(rules: list[dict], s: dict) -> str:
    for r in rules:
        if port_matches(r.get("if", {}), s):
            return r.get("then", "ask_officer")
    return "ask_officer"


def load_evaluator(app_root: Path | None):
    candidates = [app_root] if app_root else [HERE / "../../../app", Path("/home/claude/jani/ref/app")]
    for root in candidates:
        if root and (root / "qa/checks/decision_matrix.py").exists():
            sys.path.insert(0, str(root.resolve()))
            try:
                from qa.checks import decision_matrix as dm  # type: ignore
                return dm.decide, dm.LABELS, dm.WINDOWS, dm.N, f"qa.checks.decision_matrix ({(root / 'qa/checks/decision_matrix.py').resolve()})"
            except Exception as e:  # pragma: no cover
                print(f"warning: could not import QA evaluator from {root}: {e}", file=sys.stderr)
            finally:
                sys.path.pop(0)
    return port_decide, PORT_LABELS, PORT_WINDOWS, PORT_N, "port"


def enumerate_like_qa(labels, windows, n):
    """Same loop and filters as decision_matrix.run()."""
    for dominant, affected, uncertain, distinct, window in product(
            labels + ["none"], range(0, n + 1), range(0, n + 1), (1, 2, 3), windows):
        if affected + uncertain > n:
            continue
        if dominant in ("healthy", "none") and affected > 0:
            continue
        if dominant not in ("healthy", "none") and affected == 0:
            continue
        if distinct > max(1, affected):
            continue
        yield dict(dominant=dominant, affected=affected, uncertain=uncertain, distinct=distinct, window=window)


DISEASES = ["rust", "cercospora", "phoma", "miner"]
# One date per window, plus the second dry spell. Local calendar days.
WINDOW_DATES = {
    "pre_short_rains": ["2026-10-04"],
    "short_rains": ["2026-11-20"],
    "pre_long_rains": ["2027-03-01"],
    "long_rains": ["2027-04-20"],
    "dry": ["2027-01-15", "2026-07-15"],
}


def to_plot_summary(s: dict, n: int) -> tuple[dict, bool]:
    """Best-effort full PlotSummary for an abstract QA row. decide() must only read the rule fields."""
    counts = {k: 0 for k in ["healthy"] + DISEASES + ["not_leaf"]}
    dom, aff, unc, dis = s["dominant"], s["affected"], s["uncertain"], s["distinct"]
    if dom in DISEASES:
        others = [d for d in DISEASES if d != dom][: max(0, dis - 1)]
        counts[dom] = aff - len(others)
        for d in others:
            counts[d] = 1
    elif dom == "not_leaf" and aff > 0:
        counts["rust"] = aff
    not_leaf = unc if dom == "not_leaf" else 0
    counts["not_leaf"] = not_leaf
    total = n if dom != "none" else aff + unc
    counts["healthy"] = max(0, total - aff - unc)
    ps = {"n": total, "counts": counts, "uncertain": unc, "dominant": dom, "affected": aff, "distinctProblems": dis if aff > 0 else 0}
    if aff == 0 and dis > 0:
        ps["distinctProblems"] = dis  # keep the QA row's value: the QA enumerates distinct=1 with affected=0
    return ps, realisable(ps)


def summarise(labels: list[str]) -> dict:
    """Python oracle of CONTRACTS summarisePlot, used for the pipeline cases."""
    counts = {k: 0 for k in ["healthy"] + DISEASES + ["not_leaf"]}
    unsure = 0
    for l in labels:
        if l == "unsure":
            unsure += 1
        else:
            counts[l] += 1
    n = len(labels)
    affected = sum(counts[d] for d in DISEASES)
    distinct = sum(1 for d in DISEASES if counts[d] > 0)
    if counts["not_leaf"] > n / 2:
        dom = "not_leaf"
    elif affected >= 1:
        dom = DISEASES[0]
        for d in DISEASES:
            if counts[d] > counts[dom]:
                dom = d
    elif counts["healthy"] > 0:
        dom = "healthy"
    else:
        dom = "none"
    return {"n": n, "counts": counts, "uncertain": unsure + counts["not_leaf"], "dominant": dom,
            "affected": affected, "distinctProblems": distinct}


def realisable(ps: dict) -> bool:
    labels = []
    for k, v in ps["counts"].items():
        labels += [k] * v
    labels += ["unsure"] * (ps["uncertain"] - ps["counts"]["not_leaf"])
    if ps["uncertain"] < ps["counts"]["not_leaf"]:
        return False
    return summarise(labels) == ps


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-root", type=Path, default=Path(os.environ["APP_ROOT"]) if os.environ.get("APP_ROOT") else None)
    ap.add_argument("--content-dir", type=Path, default=Path(os.environ.get("CONTENT_DIR", HERE / "content")))
    ap.add_argument("--out", type=Path, default=HERE / "fixtures/decision_matrix.json")
    ap.add_argument("--pipeline-samples", type=int, default=600)
    a = ap.parse_args()

    decide, labels, windows, n, evaluator = load_evaluator(a.app_root)
    rules = json.loads((a.content_dir / "rules.json").read_text(encoding="utf-8"))
    answers = json.loads((a.content_dir / "answers.json").read_text(encoding="utf-8"))
    answer_ids = {x["id"] for x in answers}

    cases = []
    for i, s in enumerate(enumerate_like_qa(labels, windows, n)):
        expected = decide(rules, s)
        dates = WINDOW_DATES[s["window"]]
        ps, ok = to_plot_summary(s, n)
        cases.append({"summary": ps, "window": s["window"], "date": dates[i % len(dates)],
                      "expected": expected, "realisable": ok, "qa_row": s})

    # Pipeline cases: real leaf lists -> summarisePlot -> decide. Includes rows the QA loop skips
    # (for example not_leaf dominant with no affected leaf).
    rng = random.Random(20261004)
    pool = ["healthy"] + DISEASES + ["not_leaf", "unsure"]
    leaf_sets = [[], ["unsure"] * 10, ["healthy"] * 10, ["not_leaf"] * 10, ["not_leaf"], ["not_leaf"] * 2 + ["healthy"],
                 ["not_leaf"] * 6 + ["healthy"] * 4, ["not_leaf"] * 5 + ["healthy"] * 5, ["rust"] * 3 + ["healthy"] * 7,
                 ["rust", "cercospora"] + ["healthy"] * 8, ["miner"] + ["healthy"] * 9, ["rust"] * 2 + ["unsure"] * 2 + ["healthy"] * 6]
    for _ in range(a.pipeline_samples):
        k = rng.randint(0, 12)
        weights = [rng.random() for _ in pool]
        leaf_sets.append(rng.choices(pool, weights=weights, k=k))
    pipeline = []
    for j, leaves in enumerate(leaf_sets):
        ps = summarise(leaves)
        w = windows[j % len(windows)]
        dates = WINDOW_DATES[w]
        s = dict(dominant=ps["dominant"], affected=ps["affected"], uncertain=ps["uncertain"], distinct=ps["distinctProblems"], window=w)
        pipeline.append({"leaves": leaves, "summary": ps, "window": w, "date": dates[j % len(dates)], "expected": decide(rules, s)})

    missing = sorted({c["expected"] for c in cases + pipeline} - answer_ids)
    out = {
        "generated_by": "gen_fixtures.py",
        "evaluator": evaluator,
        "n": n,
        "rules_sha256": sha(a.content_dir / "rules.json"),
        "answers_sha256": sha(a.content_dir / "answers.json"),
        "season_sha256": sha(a.content_dir / "season.json"),
        "window_dates": WINDOW_DATES,
        "count": len(cases),
        "expected_ids_missing_from_answers": missing,
        "cases": cases,
        "pipeline": pipeline,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(cases)} QA cases, {len(pipeline)} pipeline cases, evaluator={evaluator}, wrote {a.out}")
    if missing:
        print(f"warning: expected ids missing from answers.json: {missing}", file=sys.stderr)


if __name__ == "__main__":
    main()
