"""Jani QA harness runner.

Usage (from the app/ folder):
    python -m qa.run                 # deterministic checks, writes qa/report.md
    python -m qa.run --llm           # also run the judge and red-team LLM steps (needs ANTHROPIC_API_KEY in backend/.env)
    python -m qa.run --only content,audio
    python -m qa.run --strict        # warnings count as failures (use before submission)

Exit code 1 when any check fails. Keeps a dated copy of the report under qa/reports/.
"""
from __future__ import annotations

import argparse
import importlib
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qa.common import Result  # noqa: E402

CHECKS = ["content", "decision_matrix", "audio", "sources", "client_clean", "budgets", "ml_integrity", "secrets_git", "requirements", "videos"]
ICON = {"pass": "PASS", "fail": "FAIL", "warn": "WARN", "skip": "skip"}


def run_checks(names: list[str]) -> list[Result]:
    results: list[Result] = []
    for name in names:
        t0 = time.time()
        try:
            mod = importlib.import_module(f"qa.checks.{name}")
            res = mod.run(ROOT)
        except Exception as e:  # a broken check must never hide other results
            res = [Result(name, "fail", f"check crashed: {type(e).__name__}: {e}")]
        for r in res:
            r.detail = f"{r.detail} ({time.time() - t0:.1f}s)" if name == "secrets_git" else r.detail
        results.extend(res)
    return results


def render(results: list[Result], llm_sections: list[str]) -> str:
    counts = {s: sum(1 for r in results if r.status == s) for s in ("pass", "fail", "warn", "skip")}
    lines = [f"# Jani QA report", "",
             f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} local time.", "",
             f"**{counts['pass']} pass, {counts['fail']} fail, {counts['warn']} warn, {counts['skip']} skip**", "",
             "| Check | Status | Detail |", "|---|---|---|"]
    for r in results:
        lines.append(f"| `{r.check}` | {ICON[r.status]} | {r.detail} |")
    fails = [r for r in results if r.status in ("fail", "warn") and r.items]
    if fails:
        lines += ["", "## Details", ""]
        for r in fails:
            lines.append(f"### {r.check} ({r.status})")
            lines += [f"- {i}" for i in r.items]
            lines.append("")
    for sec in llm_sections:
        lines += ["", sec]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated subset of checks")
    ap.add_argument("--llm", action="store_true", help="run judge and red-team LLM steps")
    ap.add_argument("--strict", action="store_true", help="warnings fail the run")
    args = ap.parse_args()

    names = [n.strip() for n in args.only.split(",")] if args.only else CHECKS
    results = run_checks(names)

    llm_sections: list[str] = []
    if args.llm:
        from qa import llm
        llm_sections = llm.run_all(ROOT, results)

    report = render(results, llm_sections)
    out = ROOT / "qa/report.md"
    out.write_text(report, encoding="utf-8")
    hist = ROOT / "qa/reports"
    hist.mkdir(exist_ok=True)
    (hist / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md").write_text(report, encoding="utf-8")

    for r in results:
        print(f"[{ICON[r.status]:4}] {r.check}: {r.detail}")
        for i in r.items[:8]:
            print(f"        - {i}")
        if len(r.items) > 8:
            print(f"        ... {len(r.items) - 8} more in qa/report.md")
    bad = [r for r in results if r.status == "fail" or (args.strict and r.status == "warn")]
    print(f"\nReport: {out}")
    print(f"{len(bad)} blocking issue(s)." if bad else "All checks pass.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
