"""LLM review steps: judge (scores us as a sceptical evaluator) and red-team (attacks the safety gate).

Needs ANTHROPIC_API_KEY in backend/.env. Skips cleanly when absent. Both steps are advisory:
they write findings into the report; they never edit files.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from qa.common import Result, read_text

PROMPTS = Path(__file__).parent / "prompts"
DOC_FILES = ["README.md", "docs/DATA_CARD.md", "docs/EVALUATION.md", "docs/RESPONSIBLE_AI.md",
             "docs/LANGUAGES.md", "docs/REPLICATION.md", "src/content/answers.json", "src/content/rules.json"]
MAX_CHARS = 60_000


def _load_env(root: Path) -> None:
    env = root / "backend/.env"
    if not env.exists():
        return
    for line in read_text(env).splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _bundle(root: Path) -> str:
    parts = []
    for rel in DOC_FILES:
        p = root / rel
        if p.exists():
            parts.append(f"\n\n===== {rel} =====\n{read_text(p)[:12_000]}")
    brief = root.parent / "kb/MASTER_PROMPT.md"
    if brief.exists():
        parts.insert(0, f"===== kb/MASTER_PROMPT.md (sections 2 and 12 only matter) =====\n{read_text(brief)[:14_000]}")
    return "".join(parts)[:MAX_CHARS]


def _ask(system: str, user: str) -> str:
    try:
        import anthropic  # type: ignore
    except ImportError:
        return "SKIP: `pip install anthropic` to run LLM steps."
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.environ.get("QA_MODEL", "claude-sonnet-4-5"),
        max_tokens=2500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def run_all(root: Path, results: list[Result]) -> list[str]:
    _load_env(root)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ["## LLM steps\n\nSkipped: ANTHROPIC_API_KEY not set in backend/.env."]
    bundle = _bundle(root)
    det = "\n".join(f"- {r.check}: {r.status}: {r.detail}" for r in results)
    sections = []
    for name in ("judge", "redteam"):
        system = read_text(PROMPTS / f"{name}.md")
        user = f"Deterministic QA results so far:\n{det}\n\nProject files:\n{bundle}"
        try:
            text = _ask(system, user)
        except Exception as e:
            text = f"ERROR: {type(e).__name__}: {e}"
        (root / f"qa/{name}_latest.md").write_text(text, encoding="utf-8")
        sections.append(f"## {name.capitalize()} (LLM, advisory)\n\n{text}")
    return sections
