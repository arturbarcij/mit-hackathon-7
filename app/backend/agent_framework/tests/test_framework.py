"""Framework tests. No network and no API key."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import textwrap
import threading
import unittest
from pathlib import Path
from unittest import mock

from agent_framework.client import AgentClientError, load_api_key, safe_error
from agent_framework.probes import build_scan, run_probes, tally
from agent_framework.report import render_summary
from agent_framework.roster import select_agents
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
            self.assertGreater(tally(findings)["blockers"], 0)

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
            secret = "sk-ant-testsecretvalue"
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


if __name__ == "__main__":
    unittest.main()
