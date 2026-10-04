"""Framework tests. No network and no API key."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from agent_framework.__main__ import main
from agent_framework.client import AgentClientError, load_api_key, safe_error
from agent_framework.graph import EDGES, edges_for
from agent_framework.orchestrator import orchestrate
from agent_framework.probes import build_scan, run_probes, tally
from agent_framework.report import render_summary, write_run
from agent_framework.roster import AGENTS, select_agents
from agent_framework.runner import parse_agent_json, run_agents, system_prompt
from agent_framework.snapshot import build_pack, redact


def _write(root: Path, rel: str, body: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class ProbeTests(unittest.TestCase):
    def test_empty_product_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "app/src/App.tsx", "export default function App(){ return <button>Count is {count}</button> }\n")
            _write(root, "app/package.json", '{"dependencies":{"react":"1"}}\n')
            _write(root, "app/README.md", "# React + TypeScript + Vite\n")
            _write(root, "app/index.html", "<div id=root></div>\n")
            _write(root, "kb/research/EVIDENCE.md", "Because of Jani, notes live here.\n")
            findings = run_probes(build_scan(root))
            by_id = {item.id: item for item in findings}
            self.assertEqual(by_id["R1"].status, "fail")
            self.assertEqual(by_id["R4"].status, "fail")
            self.assertEqual(by_id["D1"].status, "fail")
            self.assertEqual(by_id["W1"].status, "fail")
            self.assertNotEqual(by_id["S1"].status, "pass")
            self.assertGreater(tally(findings)["blockers"], 0)

    def test_template_urls_are_not_a_live_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "app/README.md", "See https://oxc.rs and https://vite.dev/guide\n")
            _write(root, "app/package.json", "{}\n")
            findings = {item.id: item for item in run_probes(build_scan(root))}
            self.assertNotEqual(findings["S1"].status, "pass")
            self.assertNotIn("oxc.rs", findings["S1"].evidence)

    def test_minimal_pass_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root,
                "app/package.json",
                '{"dependencies":{"vite-plugin-pwa":"1"}}\n',
            )
            _write(root, "app/index.html", "<div id=root></div>\n")
            _write(
                root,
                "app/vite.config.ts",
                "export default { plugins: ['vite-plugin-pwa'] }\n",
            )
            _write(root, "app/public/model/leaf.onnx", "not-really-onnx")
            _write(
                root,
                "app/src/content/answers.json",
                json.dumps({"a": {"text": {"sw": "Jani", "kik": "Jani"}}}),
            )
            _write(
                root,
                "app/src/engine/decide.ts",
                "export const choices = ['act','wait','ask']; import '../content/answers.json'; sms: ; abstain\n",
            )
            _write(root, "app/src/pages/Officer.tsx", "export const route = '/officer'\n")
            _write(root, "app/src/App.tsx", "export default function App(){ return null }\n")
            _write(
                root,
                "app/README.md",
                "Because of Jani, Noor will check a leaf. Vision on a photo. A spreadsheet cannot name the disease.\nhttps://jani.example\n",
            )
            _write(
                root,
                "app/docs/DATA_CARD.md",
                "Source and licence. What the data does not cover: berries.\n",
            )
            _write(
                root,
                "app/docs/RESPONSIBLE_AI.md",
                "Privacy. Consent. Bias.\n",
            )
            _write(root, "app/docs/EVALUATION.md", "Held-out test set F1 is not invented here.\n")
            _write(root, "app/docs/REPLICATION.md", "Swap example: cocoa in Cote d'Ivoire.\n")
            _write(root, "app/LICENSE", "MIT\n")
            findings = {item.id: item for item in run_probes(build_scan(root))}
            for req in ("R1", "R2", "R3", "R4", "R5", "G1", "G3", "P1", "P2", "D1", "D2", "W2", "W3", "B2", "S1", "S2", "J1"):
                self.assertEqual(findings[req].status, "pass", req)

    def test_secret_scan_reports_path_not_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = "sk-ant-api03-" + ("a" * 20)
            _write(root, "app/src/leak.ts", f"const key = '{token}'\n")
            _write(root, "app/backend/.env.example", "ANTHROPIC_API_KEY=\n")
            findings = run_probes(build_scan(root))
            secret = next(item for item in findings if item.id == "S2")
            self.assertEqual(secret.status, "fail")
            self.assertNotIn(token, secret.evidence)
            self.assertIn("app/src/leak.ts:1", secret.evidence)


class ClientTests(unittest.TestCase):
    def test_env_file_loader_and_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = "sk-ant-" + "testsecretvalue"
            _write(root, "app/backend/.env", f"ANTHROPIC_API_KEY={secret}\n")
            with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
                loaded = load_api_key(root)
            self.assertEqual(loaded, secret)
            message = safe_error(RuntimeError(f"header {secret} rejected"), secret)
            self.assertNotIn(secret, message)

    def test_missing_key_message_has_no_secret_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("ANTHROPIC_API_KEY", None)
                with self.assertRaises(AgentClientError) as caught:
                    load_api_key(Path(tmp))
            self.assertIn("app/backend/.env", str(caught.exception))
            self.assertNotIn("sk-", str(caught.exception))


class RunnerTests(unittest.TestCase):
    def test_parse_fenced_json(self) -> None:
        raw = textwrap.dedent(
            """
            ```json
            {"agent":"qa","verdict":"fail","summary":"Not done.","findings":[{"id":"R1","status":"fail","severity":"blocker","claim":"No PWA","evidence":"app/package.json"}]}
            ```
            """
        )
        parsed = parse_agent_json(raw, "qa")
        self.assertEqual(parsed["verdict"], "fail")
        self.assertEqual(parsed["findings"][0]["id"], "R1")

    def test_agents_overlap(self) -> None:
        # A barrier of 2 deadlocks if the calls are serial. Both must be in flight.
        barrier = threading.Barrier(2)

        def completer(system: str, user: str, key: str, model: str) -> str:
            barrier.wait(timeout=3)
            agent = "qa" if "Agent id: qa" in system else "redteam"
            return json.dumps(
                {
                    "agent": agent,
                    "verdict": "fail",
                    "summary": "Checked.",
                    "findings": [],
                }
            )

        specs = select_agents(["qa", "redteam"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "kb/agents/qa.md", "QA brief\n")
            results = asyncio.run(
                run_agents(
                    specs,
                    {"findings": []},
                    root,
                    "test-key",
                    "claude-sonnet-5-5",
                    concurrency=2,
                    completer=completer,
                )
            )
        self.assertEqual({item["agent"] for item in results}, {"qa", "redteam"})
        self.assertTrue(all(item["ok"] for item in results))
        self.assertIn("Agent id: qa", system_prompt(specs[0], "brief"))


class SnapshotTests(unittest.TestCase):
    def test_pack_redacts_and_skips_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = "sk-ant-" + ("b" * 24)
            _write(root, "app/src/App.tsx", f"token {secret}\n")
            _write(root, "app/backend/.env", f"ANTHROPIC_API_KEY={secret}\n")
            _write(root, "app/package.json", "{}\n")
            _write(root, "kb/CONTRACTS.md", "types\n")
            pack = build_pack(root)
            blob = json.dumps(pack)
            self.assertNotIn(secret, blob)
            self.assertNotIn("app/backend/.env", blob)
            self.assertIn("[redacted]", blob)
            self.assertEqual(redact(secret), "[redacted]")

    def test_summary_lists_static_rows(self) -> None:
        finding_dicts = [
            {
                "id": "R1",
                "status": "fail",
                "severity": "blocker",
                "claim": "No PWA",
                "evidence": "app/package.json",
            }
        ]
        from agent_framework.probes import Finding

        text = render_summary(
            [Finding(**finding_dicts[0])],
            {"pass": 0, "fail": 1, "missing": 0, "blockers": 1},
            None,
            None,
            "ANTHROPIC_API_KEY is not set.",
        )
        self.assertIn("R1", text)
        self.assertIn("ANTHROPIC_API_KEY is not set.", text)
        self.assertNotIn("\u2014", text)


def _agent_id(system: str) -> str:
    match = re.search(r"Agent id: (\w+)", system)
    if match is None:
        raise AssertionError("system prompt has no agent id")
    return match.group(1)


def _moment(trace: list[dict], agent: str, event: str) -> float:
    return next(item["t"] for item in trace if item["agent"] == agent and item["event"] == event)


class GraphTests(unittest.TestCase):
    def test_edges_name_roster_seats_only(self) -> None:
        known = {spec.id for spec in AGENTS}
        for src, dst in EDGES:
            self.assertIn(src, known)
            self.assertIn(dst, known)
        self.assertEqual(EDGES[0], ("research", "content"))
        self.assertEqual(EDGES[1], ("research", "docs"))
        self.assertIn(("ml", "engine"), EDGES)
        self.assertIn(("content", "ui"), EDGES)
        self.assertIn(("engine", "ui"), EDGES)
        self.assertIn(("qa", "redteam"), EDGES)
        self.assertIn(("qa", "judge"), EDGES)

    def test_edges_touching_excluded_seats_are_dropped(self) -> None:
        self.assertEqual(edges_for(["redteam", "judge"]), [])
        self.assertEqual(edges_for(["qa", "redteam"]), [("qa", "redteam")])
        kept = edges_for(["research", "content", "docs"])
        self.assertIn(("research", "content"), kept)
        self.assertIn(("research", "docs"), kept)
        self.assertNotIn(("content", "ui"), kept)
        self.assertNotIn(("research", "qa"), kept)


class OrchestratorTests(unittest.TestCase):
    def test_dependency_order_and_overlap(self) -> None:
        roots = threading.Barrier(2)
        reviewers = threading.Barrier(2)
        trace: list[dict] = []
        problems: list[str] = []

        def completer(system: str, user: str, key: str, model: str) -> str:
            agent = _agent_id(system)
            payload = json.loads(user)
            upstream = [item["agent"] for item in payload["upstream_audits"]]
            if agent == "content" and upstream != ["research"]:
                problems.append("content upstream " + ",".join(upstream))
            if agent == "ui" and upstream != ["content", "engine"]:
                problems.append("ui upstream " + ",".join(upstream))
            if agent == "research" and upstream:
                problems.append("research should start with no upstream")
            if agent in {"research", "ml"}:
                roots.wait(timeout=3)
            if agent == "ml":
                time.sleep(0.4)
            if agent in {"redteam", "judge"}:
                reviewers.wait(timeout=3)
            return json.dumps(
                {"agent": agent, "verdict": "fail", "summary": "Checked.", "findings": []}
            )

        with tempfile.TemporaryDirectory() as tmp:
            results, plan = asyncio.run(
                asyncio.wait_for(
                    orchestrate(
                        select_agents(None),
                        {"findings": []},
                        Path(tmp),
                        "test-key",
                        "claude-sonnet-5-5",
                        concurrency=8,
                        completer=completer,
                        trace=trace,
                    ),
                    timeout=5,
                )
            )
        self.assertEqual(problems, [])
        self.assertEqual({item["agent"] for item in results}, {spec.id for spec in AGENTS})
        self.assertTrue(all(item["ok"] for item in results))
        self.assertTrue(all(plan["state"][spec.id] == "done" for spec in AGENTS))
        self.assertEqual(plan["claude"], "called")

        self.assertGreater(_moment(trace, "content", "start"), _moment(trace, "research", "finish"))
        self.assertGreater(_moment(trace, "docs", "start"), _moment(trace, "research", "finish"))
        self.assertGreater(_moment(trace, "engine", "start"), _moment(trace, "ml", "finish"))
        self.assertLess(_moment(trace, "content", "start"), _moment(trace, "ml", "finish"))
        self.assertGreater(_moment(trace, "ui", "start"), _moment(trace, "content", "finish"))
        self.assertGreater(_moment(trace, "ui", "start"), _moment(trace, "engine", "finish"))
        for upstream in ("research", "ml", "engine", "ui", "content", "docs"):
            self.assertGreater(_moment(trace, "qa", "start"), _moment(trace, upstream, "finish"), upstream)
        self.assertGreater(_moment(trace, "redteam", "start"), _moment(trace, "qa", "finish"))
        self.assertGreater(_moment(trace, "judge", "start"), _moment(trace, "qa", "finish"))
        self.assertLess(_moment(trace, "research", "start"), _moment(trace, "ml", "finish"))
        self.assertLess(_moment(trace, "ml", "start"), _moment(trace, "research", "finish"))
        self.assertLess(_moment(trace, "redteam", "start"), _moment(trace, "judge", "finish"))
        self.assertLess(_moment(trace, "judge", "start"), _moment(trace, "redteam", "finish"))

    def test_excluded_upstream_does_not_block_independent_seats(self) -> None:
        barrier = threading.Barrier(2)
        trace: list[dict] = []

        def completer(system: str, user: str, key: str, model: str) -> str:
            agent = _agent_id(system)
            barrier.wait(timeout=3)
            return json.dumps({"agent": agent, "verdict": "fail", "summary": "Checked.", "findings": []})

        with tempfile.TemporaryDirectory() as tmp:
            results, plan = asyncio.run(
                asyncio.wait_for(
                    orchestrate(
                        select_agents(["redteam", "judge"]),
                        {"findings": []},
                        Path(tmp),
                        "test-key",
                        "claude-sonnet-5-5",
                        concurrency=2,
                        completer=completer,
                        trace=trace,
                    ),
                    timeout=5,
                )
            )
        self.assertEqual(plan["edges"], [])
        self.assertTrue(all(item["ok"] for item in results))
        self.assertLess(_moment(trace, "redteam", "start"), _moment(trace, "judge", "finish"))
        self.assertLess(_moment(trace, "judge", "start"), _moment(trace, "redteam", "finish"))


class CliTests(unittest.TestCase):
    def _tree(self, root: Path) -> None:
        _write(root, "app/package.json", "{}\n")
        _write(root, "app/src/App.tsx", "export default function App(){ return <button>Count is {count}</button> }\n")
        _write(root, "app/README.md", "# React + TypeScript + Vite\n")
        _write(root, "kb/CONTRACTS.md", "types\n")

    def test_missing_key_writes_plan_without_inventing_claude(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "kb" / "agent-runs" / "missing"
            self._tree(root)
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("ANTHROPIC_API_KEY", None)
                with mock.patch("agent_framework.runner.complete") as complete:
                    code = main(["--root", str(root), "--out", str(out), "--orchestrate"])
                    complete.assert_not_called()
            self.assertEqual(code, 2)
            plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
            self.assertIn("nodes", plan)
            self.assertIn("edges", plan)
            self.assertIn("state", plan)
            self.assertTrue(plan["edges"])
            self.assertTrue(plan["audit_only"])
            self.assertEqual(plan["claude"], "not_called")
            self.assertTrue(all(value == "blocked" for value in plan["state"].values()))
            qa = json.loads((out / "qa.json").read_text(encoding="utf-8"))
            self.assertEqual(qa["findings"], [])
            self.assertEqual(qa["summary"], "")
            self.assertFalse(qa["ok"])
            self.assertIn("ANTHROPIC_API_KEY", qa["error"])
            self.assertFalse((out / "claude.json").exists())
            summary = (out / "summary.md").read_text(encoding="utf-8")
            self.assertIn("ANTHROPIC_API_KEY", summary)
            self.assertIn("No Claude output was invented.", summary)
            self.assertNotIn("\u2014", summary)
            blob = summary + (out / "plan.json").read_text(encoding="utf-8") + (out / "qa.json").read_text(encoding="utf-8")
            self.assertNotIn("sk-", blob)

    def test_static_only_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            self._tree(root)
            with mock.patch("agent_framework.runner.complete") as complete:
                code = main(
                    ["--root", str(root), "--out", str(out), "--static-only", "--agents", "qa,redteam"]
                )
                complete.assert_not_called()
            self.assertEqual(code, 0)
            plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
            self.assertEqual([node["id"] for node in plan["nodes"]], ["qa", "redteam"])
            self.assertEqual(plan["edges"], [{"from": "qa", "to": "redteam"}])
            self.assertTrue(all(value == "skipped" for value in plan["state"].values()))
            summary = (out / "summary.md").read_text(encoding="utf-8")
            self.assertIn("Static only. Claude was not called.", summary)
            self.assertIn("R1", summary)
            self.assertIn("| R1 | fail |", summary)
            self.assertFalse((out / "claude.json").exists())
            redteam = json.loads((out / "redteam.json").read_text(encoding="utf-8"))
            self.assertEqual(redteam["findings"], [])
            self.assertNotIn("\u2014", summary)

    def test_write_run_skips_claude_file_when_no_call_succeeded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            pack = {"findings": [], "tally": {"pass": 0, "fail": 0, "missing": 0, "blockers": 0}}
            blocked = {
                "agent": "qa",
                "ok": False,
                "verdict": "blocked",
                "summary": "",
                "findings": [],
                "error": "ANTHROPIC_API_KEY is not set.",
            }
            write_run(out, pack, [blocked], None, blocked["error"], {"nodes": [], "edges": [], "state": {"qa": "blocked"}})
            self.assertTrue((out / "plan.json").is_file())
            self.assertTrue((out / "qa.json").is_file())
            self.assertFalse((out / "claude.json").exists())


if __name__ == "__main__":
    unittest.main()
