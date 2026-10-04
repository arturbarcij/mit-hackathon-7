"""Write the static matrix and the concurrent Claude results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .probes import Finding, tally


def write_run(
    out_dir: Path,
    pack: dict,
    claude_results: list[dict] | None,
    model: str | None,
    error: str | None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    findings = [Finding(**item) for item in pack["findings"]]
    (out_dir / "pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if claude_results is not None:
        (out_dir / "claude.json").write_text(
            json.dumps(claude_results, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    summary = render_summary(findings, pack["tally"], claude_results, model, error)
    path = out_dir / "summary.md"
    path.write_text(summary, encoding="utf-8")
    return path


def render_summary(
    findings: list[Finding],
    counts: dict[str, int] | None,
    claude_results: list[dict] | None,
    model: str | None,
    error: str | None,
) -> str:
    counts = counts or tally(findings)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Jani app check",
        "",
        f"Checked at {stamp}.",
        "",
        "The static matrix reads the git tree. It does not trust the status board.",
        "",
        "## Requirement matrix",
        "",
        f"Pass {counts.get('pass', 0)}, fail {counts.get('fail', 0)}, missing {counts.get('missing', 0)}. Blockers {counts.get('blockers', 0)}.",
        "",
        "| ID | Status | Severity | Claim | Evidence |",
        "|---|---|---|---|---|",
    ]
    for finding in findings:
        lines.append(
            "| {id} | {status} | {severity} | {claim} | {evidence} |".format(
                id=finding.id,
                status=finding.status,
                severity=finding.severity,
                claim=_cell(finding.claim),
                evidence=_cell(finding.evidence),
            )
        )
    lines.extend(["", "## Concurrent Claude reviewers", ""])
    if error:
        lines.append(error)
        lines.append("")
        lines.append("The static matrix above is the check that ran.")
    elif not claude_results:
        lines.append("No Claude results were returned.")
    else:
        lines.append(f"Model `{model}`. Agents ran together on the same pack.")
        lines.append("")
        for result in claude_results:
            agent = result.get("agent", "?")
            verdict = result.get("verdict", "?")
            seconds = result.get("seconds", "?")
            lines.append(f"### {agent}")
            lines.append("")
            if result.get("ok"):
                lines.append(f"Verdict: {verdict}. Took {seconds} s.")
                summary = (result.get("summary") or "").strip()
                if summary:
                    lines.append("")
                    lines.append(summary)
                agent_findings = result.get("findings") or []
                if agent_findings:
                    lines.append("")
                    lines.append("| ID | Status | Claim |")
                    lines.append("|---|---|---|")
                    for item in agent_findings:
                        lines.append(
                            "| {id} | {status} | {claim} |".format(
                                id=_cell(str(item.get("id", ""))),
                                status=_cell(str(item.get("status", ""))),
                                claim=_cell(str(item.get("claim", ""))),
                            )
                        )
            else:
                lines.append(f"Blocked after {seconds} s. {result.get('error', 'unknown error')}")
            lines.append("")
    lines.append("Reviewers do not edit the app. Fixes stay with the path owner.")
    lines.append("")
    return "\n".join(lines)


def _cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")
