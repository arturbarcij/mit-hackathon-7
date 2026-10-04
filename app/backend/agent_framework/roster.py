"""Reviewer roster. Each agent runs at the same time on one evidence pack."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentSpec:
    id: str
    title: str
    brief: str
    mission: str


AGENTS: tuple[AgentSpec, ...] = (
    AgentSpec(
        id="qa",
        title="QA",
        brief="kb/agents/qa.md",
        mission=(
            "Score every requirement in MASTER_PROMPT section 12. "
            "Nothing is pass unless the evidence pack shows the file, probe, or command output. "
            "You have a veto: if a row is missing or failed, the app is not done."
        ),
    ),
    AgentSpec(
        id="redteam",
        title="Red team",
        brief="kb/agents/redteam.md",
        mission=(
            "Attack the responsible-AI gate. Look for a runtime model call, generated advice, "
            "an automatic send, a forced label when the tool should abstain, an invented dose, "
            "a secret in client code, and any place the status board claims work the files do not contain."
        ),
    ),
    AgentSpec(
        id="judge",
        title="Judge",
        brief="kb/agents/judge.md",
        mission=(
            "Score the entry the way the brief scores it: built solution, development relevance, "
            "data grounding, evidence it works, clarity and why not a simpler tool, scalability, "
            "and the responsible-AI pass/fail gate. Use only the evidence pack. Do not award a mark for a planned file."
        ),
    ),
    AgentSpec(
        id="engine",
        title="Engine audit",
        brief="kb/agents/engine.md",
        mission=(
            "Check the offline engine against kb/CONTRACTS.md: inference, quality gate, plot summary, "
            "rules, storage, referral SMS, audio, and service worker. Report each missing module. "
            "Do not treat a Vite starter as an engine."
        ),
    ),
    AgentSpec(
        id="ui",
        title="UI audit",
        brief="kb/agents/ui.md",
        mission=(
            "Check the farmer journey and the officer dashboard. One action per screen, large targets, "
            "360 px, icons plus audio, no hard-coded English, no gradient hero, a visible mock badge, "
            "and a simulated label on simulated parts. The route /officer must exist."
        ),
    ),
    AgentSpec(
        id="content",
        title="Content audit",
        brief="kb/agents/content-voice.md",
        mission=(
            "Check the fixed answer bank, the rule table, season windows, and Swahili plus Kikuyu coverage. "
            "Every farmer-facing sentence must be able to come from answers.json. "
            "Flag assumptions that are not marked for an officer to confirm."
        ),
    ),
    AgentSpec(
        id="docs",
        title="Docs audit",
        brief="kb/agents/docs.md",
        mission=(
            "Check README, DATA_CARD, RESPONSIBLE_AI, LANGUAGES, REPLICATION, ARCHITECTURE, "
            "REQUIREMENTS, and LICENSE. Every number needs a source or an assumption label. "
            "Research notes in kb/ are not a substitute for app/docs."
        ),
    ),
    AgentSpec(
        id="ml",
        title="ML audit",
        brief="kb/agents/ml.md",
        mission=(
            "Check the on-device model, model.json, the 5 MB cap, EVALUATION.md, "
            "named test sets, abstention numbers, and the cross-domain results. "
            "A missing model is a fail, not a pending pass."
        ),
    ),
)


def select_agents(names: list[str] | None) -> list[AgentSpec]:
    if not names:
        return list(AGENTS)
    wanted = {name.strip() for name in names if name.strip()}
    known = {spec.id: spec for spec in AGENTS}
    missing = sorted(wanted - set(known))
    if missing:
        raise SystemExit(
            "Unknown agent id: "
            + ", ".join(missing)
            + ". Known: "
            + ", ".join(known)
        )
    return [spec for spec in AGENTS if spec.id in wanted]
