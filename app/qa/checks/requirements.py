"""Traceability matrix (docs/REQUIREMENTS.md): every row has a status and, when pass, an evidence link."""
from __future__ import annotations

import re
from pathlib import Path

from qa.common import Result, read_text

ROW_RE = re.compile(r"^\|\s*([A-Z]\d+)\s*\|(.*)\|\s*$")


def run(root: Path) -> list[Result]:
    p = root / "docs/REQUIREMENTS.md"
    if not p.exists():
        return [Result("requirements", "skip", "docs/REQUIREMENTS.md missing")]
    rows = []
    for line in read_text(p).splitlines():
        m = ROW_RE.match(line.strip())
        if m:
            rows.append((m.group(1), [c.strip() for c in m.group(2).split("|")]))
    if not rows:
        return [Result("requirements", "fail", "no requirement rows found (expected | R1 | ... | status | evidence |)")]
    not_pass, no_evidence = [], []
    for rid, cells in rows:
        joined = " ".join(cells).lower()
        status = "pass" if re.search(r"\bpass\b", joined) else ("fail" if "fail" in joined else "todo")
        if status != "pass":
            not_pass.append(f"{rid}: {status}")
        elif not re.search(r"\]\(|https?://|\.md|\.png|\.mp4|\.json", joined):
            no_evidence.append(rid)
    out = [Result("requirements:all_pass", "fail" if not_pass else "pass",
                  f"{len(not_pass)} of {len(rows)} requirements not passing" if not_pass else f"all {len(rows)} requirements marked pass",
                  not_pass)]
    out.append(Result("requirements:evidence_links", "fail" if no_evidence else "pass",
                      f"{len(no_evidence)} passing rows have no evidence link" if no_evidence else "every passing row links to evidence",
                      no_evidence))
    return out
