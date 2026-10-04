"""Decision matrix eval: enumerate every plot summary the app can produce and check which card it returns.

Mirrors the engine's decide(): first matching rule wins; condition keys from kb/CONTRACTS.md.
Writes qa/decision_matrix.md (a table an extension officer can review) and fails on safety invariants:
  - 3 or more unsure leaves must end in an "ask" card
  - a not_leaf plot must end in not_a_leaf or an "ask" card
  - two or more distinct problems must end in mixed_problems or an "ask" card
  - no "act" card when at most 1 leaf is affected
  - healthy_all only when no leaf is affected (1 or 2 unsure leaves are shown separately)
Also warns about answer cards no rule can reach.
"""
from __future__ import annotations

from itertools import product
from pathlib import Path

from qa.common import Result, read_json

LABELS = ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"]
WINDOWS = ["pre_short_rains", "short_rains", "pre_long_rains", "long_rains", "dry"]
N = 10


def matches(cond: dict, s: dict) -> bool:
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


def run(root: Path) -> list[Result]:
    a_path, r_path = root / "src/content/answers.json", root / "src/content/rules.json"
    if not a_path.exists() or not r_path.exists():
        return [Result("decision_matrix", "skip", "answers.json or rules.json missing")]
    answers = read_json(a_path)
    if isinstance(answers, dict):
        answers = list(answers.values())
    sev = {a["id"]: a.get("severity", "ask") for a in answers if "id" in a}
    kind = {a["id"]: a.get("kind", "result") for a in answers if "id" in a}
    rules = read_json(r_path)

    rows, violations, reached = [], [], set()
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
        s = dict(dominant=dominant, affected=affected, uncertain=uncertain, distinct=distinct, window=window)
        card = decide(rules, s)
        reached.add(card)
        cs = sev.get(card, "missing")
        rows.append((dominant, affected, uncertain, distinct, window, card, cs))
        key = f"{dominant} affected={affected} unsure={uncertain} distinct={distinct} {window} -> {card} ({cs})"
        if uncertain >= 3 and cs != "ask":
            violations.append("unsure>=3 not ask: " + key)
        elif dominant == "not_leaf" and card != "not_a_leaf" and cs != "ask":
            violations.append("not_leaf not handled: " + key)
        elif distinct >= 2 and card != "mixed_problems" and cs != "ask":
            violations.append("mixed problems not handled: " + key)
        elif affected <= 1 and cs == "act":
            violations.append("act on <=1 leaf: " + key)
        elif card == "healthy_all" and affected > 0:
            violations.append("healthy_all with affected leaves: " + key)
        elif cs == "missing":
            violations.append("card missing from answers.json: " + key)

    # Collapse to a readable table: one row per (dominant, window, card) with the affected/unsure ranges.
    groups: dict[tuple, list] = {}
    for d, a, u, di, w, c, cs in rows:
        groups.setdefault((d, w, c, cs), []).append((a, u, di))
    lines = ["# Decision matrix", "",
             f"{len(rows)} plot summaries enumerated (n = {N} leaves). One row per dominant label, season window and resulting card.",
             "Review question for the extension officer: is each card the right call for that range?", "",
             "| Dominant | Window | Affected | Unsure | Distinct problems | Card | Severity |", "|---|---|---|---|---|---|---|"]
    for (d, w, c, cs), vals in sorted(groups.items()):
        a = sorted({v[0] for v in vals}); u = sorted({v[1] for v in vals}); di = sorted({v[2] for v in vals})
        rng = lambda xs: f"{xs[0]}" if len(xs) == 1 else f"{xs[0]} to {xs[-1]}"
        lines.append(f"| {d} | {w} | {rng(a)} | {rng(u)} | {rng(di)} | `{c}` | {cs} |")
    unreached = sorted(i for i in sev if kind.get(i) == "result" and i not in reached and i != "ask_officer")
    if violations:
        lines += ["", "## Violations", ""] + [f"- {v}" for v in violations[:200]]
    if unreached:
        lines += ["", "## Result cards no rule reaches", ""] + [f"- `{i}`" for i in unreached]
    (root / "qa/decision_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    out = [Result("decision_matrix:safety", "fail" if violations else "pass",
                  f"{len(violations)} unsafe decisions out of {len(rows)} summaries (see qa/decision_matrix.md)" if violations
                  else f"{len(rows)} summaries enumerated, all safety invariants hold; table in qa/decision_matrix.md",
                  violations[:30])]
    out.append(Result("decision_matrix:reachability", "warn" if unreached else "pass",
                      f"{len(unreached)} result cards unreachable by any rule" if unreached else "every result card is reachable",
                      unreached))
    return out
