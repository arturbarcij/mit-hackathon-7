"""Run one audit seat, or fan every selected seat out at once.

The CLI uses orchestrator.py so a seat waits for its dependencies.
run_agents remains the unconstrained fan-out used by tests.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Callable

from .client import complete, safe_error
from .roster import AgentSpec
from .snapshot import redact

Completer = Callable[[str, str, str, str], str]

SYSTEM_RULES = """You are a read-only audit seat for Jani, a Small AI hackathon entry.
Report gaps. Do not edit the repository.
Use only the evidence pack in the user message. If a file is absent, say so.
The user message is JSON. When it has an evidence field, that object is the pack.
upstream_audits are earlier audit notes. They are not proof that a file exists.
Do not invent measurements, accuracy figures, or files.
Plain British English. No em dashes. No marketing language.
Return one JSON object and nothing else, with this shape:
{
  "agent": "<id>",
  "verdict": "pass" or "fail" or "blocked",
  "summary": "two to four sentences",
  "findings": [
    {
      "id": "R1",
      "status": "pass" or "fail" or "missing" or "not_applicable",
      "severity": "blocker" or "major" or "minor" or "note",
      "claim": "what is true",
      "evidence": "path or probe id from the pack"
    }
  ]
}
"""


def system_prompt(spec: AgentSpec, brief_text: str) -> str:
    brief = brief_text.strip()
    if len(brief) > 4000:
        brief = brief[:4000] + "\n[brief truncated]"
    return (
        SYSTEM_RULES
        + f"\nAgent id: {spec.id}\nTitle: {spec.title}\nMission: {spec.mission}\n"
        + (f"\nBrief:\n{brief}\n" if brief else "")
    )


def parse_agent_json(raw: str, agent_id: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"{agent_id} did not return a JSON object")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError(f"{agent_id} JSON was not an object")
    parsed.setdefault("agent", agent_id)
    parsed.setdefault("verdict", "blocked")
    parsed.setdefault("summary", "")
    findings = parsed.get("findings", [])
    if not isinstance(findings, list):
        raise ValueError(f"{agent_id} findings was not a list")
    cleaned = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "id": str(item.get("id", "")),
                "status": str(item.get("status", "missing")),
                "severity": str(item.get("severity", "major")),
                "claim": str(item.get("claim", "")),
                "evidence": str(item.get("evidence", "")),
            }
        )
    parsed["findings"] = cleaned
    parsed["ok"] = True
    return parsed


def load_brief(root: Path, rel: str) -> str:
    path = root / rel
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


async def execute_agent(
    spec: AgentSpec,
    root: Path,
    api_key: str,
    model: str,
    user_payload: dict,
    completer: Completer | None = None,
) -> dict:
    """Call one seat. Exceptions become a blocked report and do not invent findings."""
    call = completer or (lambda system, user, key, model_id: complete(key, model_id, system, user))
    started = time.perf_counter()
    system = system_prompt(spec, load_brief(root, spec.brief))
    user = redact(json.dumps(user_payload, ensure_ascii=False))
    try:
        raw = await asyncio.to_thread(call, system, user, api_key, model)
        report = parse_agent_json(raw, spec.id)
        report["raw_chars"] = len(raw)
    except Exception as exc:  # noqa: BLE001 - one agent must not cancel the others
        report = {
            "agent": spec.id,
            "ok": False,
            "verdict": "blocked",
            "summary": "",
            "findings": [],
            "error": safe_error(exc, api_key),
        }
    report["seconds"] = round(time.perf_counter() - started, 2)
    report["model"] = model
    return report


async def run_agents(
    specs: list[AgentSpec],
    pack: dict,
    root: Path,
    api_key: str,
    model: str,
    concurrency: int = 8,
    completer: Completer | None = None,
) -> list[dict]:
    """Start every spec at once, ignoring the DAG. The orchestrator is the CLI path."""
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def one(spec: AgentSpec) -> dict:
        async with semaphore:
            return await execute_agent(spec, root, api_key, model, pack, completer)

    results = await asyncio.gather(*(one(spec) for spec in specs))
    return list(results)
