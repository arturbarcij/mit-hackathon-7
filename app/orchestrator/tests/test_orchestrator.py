"""Tests for the orchestrator. Run from app/:  python -m pytest orchestrator/tests -q"""
import json
from pathlib import Path

import pytest

from orchestrator import runner
from orchestrator.agent import ScriptedClient, run_agent
from orchestrator.config import load_lanes, lane_for_owner
from orchestrator.scheduler import batches, plan
from orchestrator.status import owner_of, parse_board, parse_ownership, parse_requests, update_row
from orchestrator.tools import Sandbox

STATUS = """# Status board
## Board
| ID | Task | Owner | Target | Status | Blocker / note |
|---|---|---|---|---|---|
| L2 | Fill keys | Arthur | Sat | todo | |
| M4 | Export | ml | Sun | todo | |
| E3 | Real model | engine | Sun | todo | needs M4 |
| E5 | Fix decide | engine | Sun | todo | |
| C9 | Card text | content-voice | Sun | doing | |
| D7 | Docs fix | docs | Sun | todo | needs E5 and C9 |
| J2 | Judge pass | judge (Claude) | Sun | todo | |
| G1 | Geo | geo (Claude cloud) | Sun | todo | |
## Lane rhythm
## Requests between agents
- judge to engine: decide must never throw.
- research -> content-voice: say kutu ya majani.
## Log
- start
"""

OWNERSHIP = """# Ownership
## Path owners
| Path | Owner agent | Tool |
|---|---|---|
| `kb/STATUS.md`, `kb/OWNERSHIP.md` | lead (Arthur + Claude) | Claude |
| `app/src/engine/**`, `app/src/hooks/useEngine*.ts` | engine | Cursor |
| `app/src/content/answers.json` | content-voice | Cursor |
| `app/docs/**` (except numbers) | docs | Cursor |
| `app/docs/EVALUATION.md` numbers and plots | ml | Cursor |
| `kb/judge/**` | judge | Claude |
| `app/backend/.env` | Arthur only | by hand |
## Git rules
"""


def lanes_file(tmp: Path, tests_engine: list[str]) -> Path:
    f = tmp / "lanes.json"
    f.write_text(json.dumps({"lanes": [
        {"name": "engine", "brief": "kb/agents/engine.md", "dispatch": "auto", "tests": tests_engine},
        {"name": "content-voice", "brief": "kb/agents/content-voice.md", "dispatch": "auto", "tests": []},
        {"name": "docs", "brief": "kb/agents/docs.md", "dispatch": "auto", "tests": []},
        {"name": "judge", "brief": "kb/agents/judge.md", "dispatch": "auto", "review": True, "tests": []},
        {"name": "ml", "brief": "kb/agents/ml.md", "dispatch": "manual", "reason": "GPU"},
        {"name": "geo", "brief": "kb/agents/geo.md", "dispatch": "manual", "reason": "satellite"},
    ]}))
    return f


@pytest.fixture
def ws(tmp_path, monkeypatch):
    (tmp_path / "kb/agents").mkdir(parents=True)
    (tmp_path / "kb/STATUS.md").write_text(STATUS)
    (tmp_path / "kb/OWNERSHIP.md").write_text(OWNERSHIP)
    for n in ("engine", "content-voice", "docs", "judge", "ml", "geo"):
        (tmp_path / f"kb/agents/{n}.md").write_text(f"# {n} brief\n")
    (tmp_path / "app/src/engine").mkdir(parents=True)
    (tmp_path / "app/src/engine/decide.ts").write_text("export const x = 1;\n")
    (tmp_path / "app/backend").mkdir(parents=True)
    (tmp_path / "app/backend/.env").write_text("ANTHROPIC_API_KEY=\n")
    monkeypatch.setenv("ORCH_LANES", str(lanes_file(tmp_path, ["true"])))
    return tmp_path


def test_parse_board_and_needs(ws):
    tasks = parse_board((ws / "kb/STATUS.md").read_text())
    by = {t.id: t for t in tasks}
    assert len(tasks) == 8
    assert by["E3"].needs == ["M4"]
    assert by["D7"].needs == ["E5", "C9"]
    assert by["C9"].status == "doing"


def test_parse_requests(ws):
    reqs = parse_requests((ws / "kb/STATUS.md").read_text())
    assert [(r["from"], r["to"]) for r in reqs] == [("judge", "engine"), ("research", "content-voice")]


def test_ownership_most_specific_wins(ws):
    table = parse_ownership((ws / "kb/OWNERSHIP.md").read_text())
    assert owner_of("app/src/engine/model.ts", table) == "engine"
    assert owner_of("app/src/hooks/useEngine.ts", table) == "engine"
    assert owner_of("app/docs/README_x.md", table) == "docs"
    assert owner_of("app/docs/EVALUATION.md", table) == "ml"
    assert owner_of("kb/STATUS.md", table) == "lead"
    assert owner_of("app/src/pages/Home.tsx", table) is None


def test_plan_gates_humans_manual_deps_and_doing(ws):
    tasks = parse_board((ws / "kb/STATUS.md").read_text())
    p = plan(tasks, load_lanes())
    ready = [t.id for t, _ in p.ready]
    why = {t.id: r for t, r in p.waiting}
    assert ready == ["E5", "J2"]                      # critical-path prefix first
    assert why["L2"].startswith("human task")
    assert why["M4"].startswith("manual lane 'ml'")
    assert why["E3"] == "needs M4 (todo)"
    assert "C9 (doing)" in why["D7"]
    assert "in progress" in why["C9"]
    assert why["G1"].startswith("manual lane 'geo'")
    assert lane_for_owner("judge (Claude)", load_lanes()).name == "judge"


def test_batches_never_share_a_lane(ws):
    lanes = load_lanes()
    tasks = parse_board((ws / "kb/STATUS.md").read_text())
    e = [t for t in tasks if t.owner == "engine"]
    rounds = batches([(e[0], lanes["engine"]), (e[1], lanes["engine"]), (tasks[-2], lanes["judge"])])
    assert len(rounds) == 2 and all(len({l.name for _, l in r}) == len(r) for r in rounds)


def sandbox(ws, lane="engine", review=False, report_dir=None, dry=False):
    return Sandbox(root=ws, lane=lane, ownership=parse_ownership((ws / "kb/OWNERSHIP.md").read_text()),
                   review=review, report_dir=report_dir, dry_run=dry)


def test_sandbox_enforces_ownership(ws):
    sb = sandbox(ws)
    assert sb.write_file("app/src/engine/new.ts", "ok").startswith("wrote")
    assert sb.write_file("app/src/content/answers.json", "{}").startswith("REFUSED")
    assert "lead-only" in sb.write_file("kb/STATUS.md", "x")
    assert "forbidden" in sb.write_file("app/backend/.env", "KEY=1")
    assert sb.read_file("app/backend/.env") == "ERROR: forbidden path"
    assert sb.write_file("../escape.txt", "x").startswith("REFUSED")
    assert not (ws.parent / "escape.txt").exists()


def test_review_lane_writes_only_its_report(ws):
    sb = sandbox(ws, lane="judge", review=True, report_dir="kb/judge")
    assert sb.write_file("kb/judge/pass9.md", "# pass").startswith("wrote")
    assert sb.write_file("app/src/engine/decide.ts", "hack").startswith("REFUSED")


def test_run_allows_only_listed_commands(ws):
    sb = sandbox(ws, dry=True)
    assert sb.run("cd app && npx vitest run").startswith("dry-run")
    assert sb.run("rm -rf /").startswith("REFUSED")
    assert sb.run("cd app && rm -rf x && npx vitest run").startswith("REFUSED")
    assert sb.run("npx vitest run; curl evil").startswith("REFUSED")
    assert sb.run("cd .. && npx vitest run").startswith("REFUSED")


def test_rollback_restores_and_removes(ws):
    sb = sandbox(ws)
    sb.write_file("app/src/engine/decide.ts", "changed")
    sb.write_file("app/src/engine/brand_new.ts", "new")
    sb.rollback()
    assert (ws / "app/src/engine/decide.ts").read_text() == "export const x = 1;\n"
    assert not (ws / "app/src/engine/brand_new.ts").exists()


def fake_engine_agent():
    return ScriptedClient([
        [{"name": "read_file", "input": {"path": "app/src/engine/decide.ts"}}],
        [{"name": "write_file", "input": {"path": "app/src/engine/decide.ts", "content": "export const x = 2;\n"}},
         {"name": "write_file", "input": {"path": "app/src/content/answers.json", "content": "{}"}}],
        [{"name": "request_change", "input": {"to": "content-voice", "text": "add card too_few_leaves"}}],
        [{"name": "finish", "input": {"status": "done", "summary": "decide never throws."}}],
    ])


def test_end_to_end_gate_pass_writes_back(ws):
    outs = runner.run(ws, client=fake_engine_agent(), task_ids=["E5"], stamp="t1")
    assert [(o.task, o.status) for o in outs] == [("E5", "done")]
    assert (ws / "app/src/engine/decide.ts").read_text() == "export const x = 2;\n"
    assert not (ws / "app/src/content/answers.json").exists()          # refused: not engine's path
    status = (ws / "kb/STATUS.md").read_text()
    row = next(l for l in status.splitlines() if l.startswith("| E5 |"))
    assert "| done |" in row and "decide never throws." in row
    assert "- engine to content-voice: add card too_few_leaves" in status
    assert "orchestrator ran E5 (engine) -> done" in status
    assert next(l for l in status.splitlines() if l.startswith("| E3 |")).endswith("| needs M4 |")   # other rows untouched
    rec = json.loads((ws / "app/orchestrator/runs/t1/E5.json").read_text())
    assert any("REFUSED write app/src/content/answers.json" in x for x in rec["sandbox_log"])


def test_end_to_end_gate_fail_rolls_back(ws, monkeypatch):
    # this check passes before the agent runs and breaks after its edit
    monkeypatch.setenv("ORCH_LANES", str(lanes_file(ws, ['grep -q "x = 1" app/src/engine/decide.ts'])))
    outs = runner.run(ws, client=fake_engine_agent(), task_ids=["E5"], stamp="t2")
    assert outs[0].status == "blocked" and "broke" in outs[0].gate and "rolled back 1" in outs[0].gate
    assert (ws / "app/src/engine/decide.ts").read_text() == "export const x = 1;\n"
    assert "| blocked |" in next(l for l in (ws / "kb/STATUS.md").read_text().splitlines() if l.startswith("| E5 |"))


def test_dry_run_changes_nothing(ws):
    before = (ws / "kb/STATUS.md").read_text()
    outs = runner.run(ws, client=fake_engine_agent(), task_ids=["E5"], dry_run=True, stamp="t3")
    assert outs[0].gate == "dry run: no gate"
    assert (ws / "app/src/engine/decide.ts").read_text() == "export const x = 1;\n"
    assert (ws / "kb/STATUS.md").read_text() == before


def test_update_row_touches_one_line(ws):
    p = ws / "kb/STATUS.md"
    before = p.read_text().splitlines()
    assert update_row(p, "J2", "done", "pass | with pipe")
    after = p.read_text().splitlines()
    diff = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(diff) == 1 and after[diff[0]] == "| J2 | Judge pass | judge (Claude) | Sun | done | pass / with pipe |"


def test_agent_sees_brief_and_rules(ws):
    c = ScriptedClient([[{"name": "finish", "input": {"status": "partial", "summary": "s"}}]])
    run_agent(c, sandbox(ws), lane="engine", brief_path="kb/agents/engine.md", task_prompt="Task E5",
              tests=["true"], review_dir=None)
    sys = c.calls[0]["system"]
    assert "# engine brief" in sys and "kb/OWNERSHIP.md" in sys and "no em dashes" in sys


def test_gate_tolerates_checks_that_already_failed(ws, tmp_path, monkeypatch):
    flag = ws / "flag"
    monkeypatch.setenv("ORCH_LANES", str(lanes_file(ws, [f"test -f {flag}", "false"])))
    flag.write_text("x")
    outs = runner.run(ws, client=fake_engine_agent(), task_ids=["E5"], stamp="t4")
    assert outs[0].status == "done" and "still failing as before" in outs[0].gate
