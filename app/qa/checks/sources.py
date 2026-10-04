"""Every number in judge-facing docs has a source, or an assumption/synthetic label.

Scored under: data grounding (15%), evidence it works (15%).
Rule from MASTER_PROMPT section 16: no number without a named source or a visible
"assumption" / "synthetic" label.
"""
from __future__ import annotations

from pathlib import Path

from qa.common import EXEMPT_LINE_RE, NUMBER_RE, Result, read_text

DOCS = ["README.md", "docs/DATA_CARD.md", "docs/EVALUATION.md", "docs/RESPONSIBLE_AI.md",
        "docs/LANGUAGES.md", "docs/REPLICATION.md", "docs/ARCHITECTURE.md"]


def run(root: Path) -> list[Result]:
    out: list[Result] = []
    for rel in DOCS:
        p = root / rel
        if not p.exists():
            out.append(Result(f"sources:{rel}", "skip", "file missing"))
            continue
        lines = read_text(p).splitlines()
        bad: list[str] = []
        in_table_header = False
        for i, line in enumerate(lines, 1):
            if not NUMBER_RE.search(line):
                continue
            if EXEMPT_LINE_RE.search(line):
                continue
            # Table rows: accept if the row or the previous/next row holds a link or tag.
            window = " ".join(lines[max(0, i - 2): i + 1])
            if line.lstrip().startswith("|") and EXEMPT_LINE_RE.search(window):
                continue
            bad.append(f"{rel}:{i}: {line.strip()[:110]}")
        if bad:
            out.append(Result(f"sources:{rel}", "fail",
                              f"{len(bad)} line(s) with a number but no source/assumption/synthetic label",
                              bad[:25]))
        else:
            out.append(Result(f"sources:{rel}", "pass", "all numbered lines carry a source or label"))
    return out
