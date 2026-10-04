"""One agent run: a tool-use loop against the Anthropic Messages API (or a scripted fake for tests)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .tools import TOOL_SCHEMAS, Sandbox

DEFAULT_MODEL = os.environ.get("ORCH_MODEL", "claude-opus-5-5")

SYSTEM = """You are the {lane} agent on the Jani project (offline coffee-leaf check, World Bank Small AI hackathon, Annex B).
Your brief is below; kb/MASTER_PROMPT.md wins over it. Work only through the tools.
Rules that the orchestrator enforces and you must respect:
- You may write only paths your lane owns in kb/OWNERSHIP.md{review_rule}. For anything else call request_change.
- No runtime AI calls in product code, nothing that sends without a user tap, no invented agronomy, pesticide names or doses.
- Every number needs a source or an "assumption" / "synthetic" label. No accuracy figure without its test set.
- Plain British English, short sentences, no em dashes, no marketing words.
- Run your lane's checks with the run tool before you finish. When done or stuck, call finish exactly once.
Your lane's gate (run by the orchestrator after you finish; your changes are rolled back if it fails): {tests}

=== BRIEF ({brief_path}) ===
{brief}
"""


class Client(Protocol):
    def create(self, **kw: Any) -> dict: ...


class AnthropicClient:
    """Thin wrapper so tests can swap in a fake. Reads ANTHROPIC_API_KEY from the env or app/backend/.env."""

    def __init__(self, root: Path):
        key = os.environ.get("ANTHROPIC_API_KEY") or _read_env_key(root / "app" / "backend" / ".env", "ANTHROPIC_API_KEY")
        if not key:
            raise SystemExit("ANTHROPIC_API_KEY is empty (env or app/backend/.env). Use --dry-run to plan without it.")
        import anthropic  # pip install anthropic
        self._c = anthropic.Anthropic(api_key=key)

    def create(self, **kw: Any) -> dict:
        return self._c.messages.create(**kw).model_dump()


def _read_env_key(path: Path, name: str) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


@dataclass
class AgentResult:
    status: str = "partial"
    summary: str = "agent stopped without calling finish"
    requests: list[dict] = field(default_factory=list)
    turns: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    transcript: list[dict] = field(default_factory=list)


def run_agent(client: Client, sandbox: Sandbox, *, lane: str, brief_path: str, task_prompt: str,
              tests: list[str], review_dir: str | None, max_turns: int = 40, model: str = DEFAULT_MODEL) -> AgentResult:
    root = sandbox.root
    brief = (root / brief_path).read_text(encoding="utf-8") if (root / brief_path).exists() else "(brief missing)"
    system = SYSTEM.format(lane=lane, brief_path=brief_path, brief=brief, tests="; ".join(tests) or "(none)",
                           review_rule=f" (you are a review lane: write only your report under {review_dir}/)" if review_dir else "")
    messages: list[dict] = [{"role": "user", "content": task_prompt}]
    res = AgentResult()
    for turn in range(max_turns):
        res.turns = turn + 1
        resp = client.create(model=model, max_tokens=8000, system=system, tools=TOOL_SCHEMAS, messages=messages)
        usage = resp.get("usage") or {}
        res.tokens_in += usage.get("input_tokens", 0)
        res.tokens_out += usage.get("output_tokens", 0)
        content = [_clean(b) for b in resp.get("content", [])]
        messages.append({"role": "assistant", "content": content})
        res.transcript.append({"turn": turn + 1, "content": content})
        calls = [b for b in content if b.get("type") == "tool_use"]
        if not calls:
            if resp.get("stop_reason") == "end_turn":
                messages.append({"role": "user", "content": "Call finish with status and summary, or continue with tools."})
                continue
            break
        results, finished = [], False
        for call in calls:
            name, args = call["name"], call.get("input", {}) or {}
            out = _dispatch(sandbox, name, args, res)
            if name == "finish":
                finished = True
            results.append({"type": "tool_result", "tool_use_id": call["id"], "content": out})
        messages.append({"role": "user", "content": results})
        if finished:
            break
    return res


_KEEP = {"text": ("type", "text"), "tool_use": ("type", "id", "name", "input"),
         "thinking": ("type", "thinking", "signature"), "redacted_thinking": ("type", "data")}


def _clean(block: dict) -> dict:
    """Send back only the fields the Messages API accepts for each block type."""
    keep = _KEEP.get(block.get("type"))
    return {k: block[k] for k in keep if k in block} if keep else block


def _dispatch(sb: Sandbox, name: str, args: dict, res: AgentResult) -> str:
    try:
        if name == "read_file":
            return sb.read_file(args["path"])
        if name == "list_dir":
            return sb.list_dir(args.get("path", "."))
        if name == "search":
            return sb.search(args["pattern"], args.get("path", "."))
        if name == "write_file":
            return sb.write_file(args["path"], args["content"])
        if name == "replace_in_file":
            return sb.replace_in_file(args["path"], args["old"], args["new"])
        if name == "run":
            return sb.run(args["command"])
        if name == "request_change":
            res.requests.append({"to": args["to"], "text": args["text"]})
            return "noted; the orchestrator posts it to STATUS Requests"
        if name == "finish":
            res.status, res.summary = args.get("status", "partial"), args.get("summary", "")
            return "finished"
        return f"ERROR: unknown tool {name}"
    except PermissionError as e:
        return f"REFUSED: {e}"
    except Exception as e:  # keep the loop alive; the agent sees the error
        return f"ERROR: {type(e).__name__}: {e}"


class ScriptedClient:
    """Fake client for tests and demos: replays a list of tool calls, one per turn."""

    def __init__(self, steps: list[list[dict]]):
        self.steps, self.i, self.calls = steps, 0, []

    def create(self, **kw: Any) -> dict:
        self.calls.append(kw)
        step = self.steps[min(self.i, len(self.steps) - 1)]
        self.i += 1
        content = [{"type": "tool_use", "id": f"t{self.i}_{j}", "name": c["name"], "input": c.get("input", {})} for j, c in enumerate(step)]
        return {"content": content, "stop_reason": "tool_use", "usage": {"input_tokens": 100, "output_tokens": 20}}


def to_jsonable(res: AgentResult) -> dict:
    d = res.__dict__.copy()
    d["transcript"] = json.loads(json.dumps(d["transcript"], default=str))
    return d
