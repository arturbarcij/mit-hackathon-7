"""Write the static matrix, the plan, and per-seat audit records."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .probes import Finding, tally
from .snapshot import redact

_AGENT_ID = re.compile(r"^[a-z0-9_-]+$")


def write_run(
    out_dir: Path,
    pack: dict,
    claude_results: list[dict] | None,
    model: str | None,
    error: str | None,
    plan: dict | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    findings = [Finding(**item) for item in pack["findings"]]
    _write_json(out_dir / "pack.json", pack)
    if plan is not None:
        _write_json(out_dir / "plan.json", plan)
    public_results = None
    if claude_results is not None:
        public_results = [_public_result(item) for item in claude_results]
        for result in public_results:
            agent_id = str(result.get("agent", ""))
            if not _AGENT_ID.fullmatch(agent_id):
                raise ValueError(f"Unsafe agent id for a report file: {agent_id!r}")
            _write_json(out_dir / f"{agent_id}.json", result)
        if any(item.get("ok") for item in public_results):
            _write_json(out_dir / "claude.json", public_results)
    summary = render_summary(findings, pack["tally"], public_results, model, error, plan)
    path = out_dir / "summary.md"
    path.write_text(summary, encoding="utf-8")
    return path


def _write_json(path: Path, payload: object) -> None:
    text = redact(json.dumps(payload, indent=2, ensure_ascii=False))
    path.write_text(text + "\n", encoding="utf-8")


def _public_result(result: dict) -> dict:
    raw = redact(json.dumps(result, ensure_ascii=False))
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Agent report was not a JSON object")
    return parsed


def render_summary(
    findings: list[Finding],
    counts: dict[str, int] | None,
    claude_results: list[dict] | None,
    model: str | None,
    error: str | None,
    plan: dict | None = None,
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
    ]
    if plan is not None:
        lines.extend(_render_plan(plan))
    lines.extend(
        [
            "## Requirement matrix",
            "",
            f"Pass {counts.get('pass', 0)}, fail {counts.get('fail', 0)}, missing {counts.get('missing', 0)}. Blockers {counts.get('blockers', 0)}.",
            "",
            "| ID | Status | Severity | Claim | Evidence |",
            "|---|---|---|---|---|",
        ]
    )
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
    lines.extend(["", "## Agent calls", ""])
    if error:
        lines.append(error)
        lines.append("")
        lines.append("The static matrix above is the check that ran.")
        lines.append("No Claude output was invented.")
    elif not claude_results:
        lines.append("No Claude results were returned.")
    else:
        lines.append(f"Model `{model}`. Seats ran in dependency order on the same pack.")
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
    lines.append("Audit seats do not edit the app. Builder seats report gaps. Fixes stay with the path owner.")
    lines.append("")
    return "\n".join(lines)


def _render_plan(plan: dict) -> list[str]:
    lines = [
        "## Orchestration",
        "",
        str(plan.get("note", "Every seat is an audit.")),
        "",
        str(plan.get("edges_doc", "")),
        "",
        "| Seat | Kind | State | After |",
        "|---|---|---|---|",
    ]
    for node in plan.get("nodes", []):
        after = ", ".join(node.get("depends_on") or []) or "none"
        lines.append(
            "| {id} | {kind} | {state} | {after} |".format(
                id=_cell(str(node.get("id", ""))),
                kind=_cell(str(node.get("kind", ""))),
                state=_cell(str(node.get("state", ""))),
                after=_cell(after),
            )
        )
    lines.extend(["", "Edges:", ""])
    for edge in plan.get("edges", []):
        lines.append(f"- {edge.get('from', '?')} -> {edge.get('to', '?')}")
    if not plan.get("edges"):
        lines.append("- none")
    lines.append("")
    if plan.get("claude") == "not_called" and plan.get("block_reason"):
        lines.append(str(plan["block_reason"]))
        lines.append("")
    return lines


def _cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")
