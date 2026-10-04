"""Deterministic checks. These do not call a model.

A pass needs a file or a string that is actually in the tree.
Research notes under kb/ do not satisfy an app/ requirement.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "dist-ssr",
    "data_raw",
    "__pycache__",
    ".cursor",
}

TEXT_SUFFIXES = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".css",
    ".html",
    ".py",
    ".txt",
    ".yml",
    ".yaml",
}

LLM_HOSTS = (
    "api.openai.com",
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "api.elevenlabs.io",
    "api.groq.com",
)

SECRET_RE = re.compile(
    r"(sk-ant-[A-Za-z0-9_\-]{8,}|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{20,}|"
    r"ghp_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9\-]{10,})"
)

REQUIREMENT_IDS = (
    "R1",
    "R2",
    "R3",
    "R4",
    "R5",
    "G1",
    "G2",
    "G3",
    "P1",
    "P2",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "W1",
    "W2",
    "W3",
    "B1",
    "B2",
    "S1",
    "S2",
    "S3",
    "S4",
    "S5",
    "J1",
)


@dataclass
class Finding:
    id: str
    status: str
    severity: str
    claim: str
    evidence: str

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "status": self.status,
            "severity": self.severity,
            "claim": self.claim,
            "evidence": self.evidence,
        }


@dataclass
class Scan:
    root: Path
    files: list[str] = field(default_factory=list)
    text: dict[str, str] = field(default_factory=dict)
    sizes: dict[str, int] = field(default_factory=dict)

    def has(self, rel: str) -> bool:
        return rel in self.sizes

    def read(self, rel: str) -> str:
        return self.text.get(rel, "")

    def under(self, prefix: str) -> list[str]:
        prefix = prefix.rstrip("/") + "/"
        return [path for path in self.files if path.startswith(prefix)]

    def joined_src(self) -> str:
        parts = []
        for path in self.files:
            if path.startswith("app/src/") or path in {"app/index.html", "app/vite.config.ts", "app/package.json"}:
                parts.append(self.text.get(path, ""))
        return "\n".join(parts)


def build_scan(root: Path) -> Scan:
    root = root.resolve()
    scan = Scan(root=root)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel_path.parts):
            continue
        if path.name == ".env" or path.name.startswith(".env."):
            if path.name != ".env.example":
                continue
        rel = rel_path.as_posix()
        scan.files.append(rel)
        scan.sizes[rel] = path.stat().st_size
        if path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= 200_000:
            scan.text[rel] = path.read_text(encoding="utf-8", errors="replace")
    scan.files.sort()
    return scan


def _fail(id_: str, claim: str, evidence: str, severity: str = "blocker") -> Finding:
    return Finding(id_, "fail", severity, claim, evidence)


def _missing(id_: str, claim: str, evidence: str, severity: str = "major") -> Finding:
    return Finding(id_, "missing", severity, claim, evidence)


def _pass(id_: str, claim: str, evidence: str) -> Finding:
    return Finding(id_, "pass", "note", claim, evidence)


def _json_text(scan: Scan, rel: str) -> dict | None:
    raw = scan.read(rel)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _has_lang_text(payload: dict | None, lang: str) -> bool:
    if not isinstance(payload, dict):
        return False
    blob = json.dumps(payload)
    # A language key with a non-empty string somewhere in the bank.
    return bool(re.search(rf'"{lang}"\s*:\s*"[^"]+"', blob))


def run_probes(scan: Scan) -> list[Finding]:
    src = scan.joined_src()
    pkg = scan.read("app/package.json")
    readme = scan.read("app/README.md")
    app_tsx = scan.read("app/src/App.tsx")
    answers = _json_text(scan, "app/src/content/answers.json")
    data_card = scan.read("app/docs/DATA_CARD.md")
    responsible = scan.read("app/docs/RESPONSIBLE_AI.md")
    evaluation = scan.read("app/docs/EVALUATION.md")
    replication = scan.read("app/docs/REPLICATION.md")

    findings: list[Finding] = []

    pwa = "vite-plugin-pwa" in pkg or scan.has("app/public/manifest.webmanifest")
    if pwa and scan.has("app/index.html"):
        findings.append(_pass("R1", "A web app manifest or PWA plugin is present.", "app/package.json"))
    else:
        findings.append(
            _fail(
                "R1",
                "The app is not set up as an installable PWA on a phone the household already has.",
                "app/package.json has no vite-plugin-pwa and app/public/manifest.webmanifest is absent",
            )
        )

    offline = any(
        token in src or token in scan.read("app/vite.config.ts")
        for token in ("vite-plugin-pwa", "serviceWorker", "workbox", "registerSW")
    )
    if offline:
        findings.append(_pass("R2", "A service worker registration is present.", "app/src or app/vite.config.ts"))
    else:
        findings.append(
            _fail(
                "R2",
                "Nothing caches the app, model, audio, or rules for offline use.",
                "no service worker, workbox, or vite-plugin-pwa reference",
            )
        )

    model_rel = "app/public/model/leaf.onnx"
    if scan.has(model_rel):
        size = scan.sizes[model_rel]
        if size <= 5_000_000:
            findings.append(_pass("R3", f"leaf.onnx is {size} bytes, within the 5 MB cap.", model_rel))
        else:
            findings.append(_fail("R3", f"leaf.onnx is {size} bytes, over the 5 MB cap.", model_rel))
    else:
        findings.append(_fail("R3", "The on-device model file is not in the tree.", model_rel))

    if _has_lang_text(answers, "sw"):
        findings.append(_pass("R4", "answers.json contains Swahili text.", "app/src/content/answers.json"))
    else:
        findings.append(
            _fail("R4", "There is no Swahili answer bank.", "app/src/content/answers.json")
        )

    kik_audio = [path for path in scan.under("app/public/audio/kik") if path.endswith(".mp3")]
    if _has_lang_text(answers, "kik") or kik_audio:
        findings.append(
            _pass("R5", "A Kikuyu text or audio subset is present.", "answers.json or app/public/audio/kik")
        )
    else:
        findings.append(
            _fail("R5", "No Kikuyu answer text or audio is in the app.", "app/src/content and app/public/audio/kik")
        )

    decisions = all(token in src for token in ("act", "wait", "ask"))
    if decisions:
        findings.append(_pass("G1", "Act, wait, and ask appear in the client source.", "app/src"))
    else:
        findings.append(
            _fail("G1", "The farmer cannot choose act, wait, or ask the officer.", "app/src has no decision controls")
        )

    has_sms = "sms:" in src or "buildReferral" in src
    auto_send = bool(re.search(r"sms:[^\n]{0,80}(location\.|window\.open)", src))
    if has_sms and not auto_send:
        findings.append(_pass("G2", "An SMS link exists and no auto-send pattern was found.", "app/src"))
    elif auto_send:
        findings.append(_fail("G2", "The client appears to open an SMS link without a separate send step.", "app/src"))
    else:
        findings.append(
            _missing("G2", "There is no referral SMS path to review for auto-send.", "app/src", "blocker")
        )

    llm_hits = []
    for path, body in scan.text.items():
        if not path.startswith("app/src/") and path not in {"app/index.html", "app/vite.config.ts"}:
            continue
        for host in LLM_HOSTS:
            if host in body:
                llm_hits.append(f"{path}: {host}")
    bank_wired = "answers.json" in src
    if not llm_hits and bank_wired:
        findings.append(_pass("G3", "No runtime model host, and the client references the answer bank.", "app/src"))
    elif llm_hits:
        findings.append(_fail("G3", "The client names a runtime model host.", "; ".join(llm_hits)))
    else:
        findings.append(
            _fail(
                "G3",
                "The client does not call a model API, but farmer-facing text is not loaded from a fixed answer bank.",
                "app/src/App.tsx is hard-coded; app/src/content/answers.json is absent",
            )
        )

    abstain = any(token in src for token in ("abstain", "unsure", "ask_officer", "not sure"))
    if abstain:
        findings.append(_pass("P1", "An abstain or not-sure path is present in the client.", "app/src"))
    else:
        findings.append(
            _fail("P1", "There is no fail-safe that says not sure and asks a person.", "app/src and app/src/content")
        )

    if responsible and all(word in responsible.lower() for word in ("privacy", "consent", "bias")):
        findings.append(_pass("P2", "RESPONSIBLE_AI.md covers privacy, consent, and bias.", "app/docs/RESPONSIBLE_AI.md"))
    else:
        findings.append(
            _fail("P2", "The responsible-AI document is missing from the app docs.", "app/docs/RESPONSIBLE_AI.md")
        )

    if data_card.strip():
        findings.append(_pass("D1", "DATA_CARD.md exists in the app docs.", "app/docs/DATA_CARD.md"))
    else:
        findings.append(
            _fail(
                "D1",
                "Cited data sources are not in the app docs. Notes under kb/research do not meet this row.",
                "app/docs/DATA_CARD.md",
            )
        )

    if "Because of Jani" in readme:
        findings.append(_pass("D2", "The README contains the problem statement.", "app/README.md"))
    else:
        findings.append(
            _fail("D2", "The README is not the Jani problem statement with source, year, and country.", "app/README.md")
        )

    if data_card and "licence" in data_card.lower() and "source" in data_card.lower():
        findings.append(_pass("D3", "DATA_CARD.md names source and licence.", "app/docs/DATA_CARD.md"))
    else:
        findings.append(_fail("D3", "Build data is not recorded with source, licence, and size.", "app/docs/DATA_CARD.md"))

    if data_card and ("does not cover" in data_card.lower() or "gap" in data_card.lower()):
        findings.append(_pass("D4", "DATA_CARD.md states coverage gaps.", "app/docs/DATA_CARD.md"))
    else:
        findings.append(_fail("D4", "The app docs do not state what the data does not cover.", "app/docs/DATA_CARD.md"))

    synthetic = any(
        "synthetic" in scan.read(path).lower()
        for path in scan.files
        if path.startswith("app/") and path.endswith((".ts", ".tsx", ".json", ".md"))
    )
    if synthetic:
        findings.append(_pass("D5", "The app tree mentions synthetic labelling.", "app/"))
    else:
        findings.append(
            _missing("D5", "No synthetic officer records are in the app to check the tag.", "app/", "major")
        )

    starter = "Count is" in app_tsx
    engine_files = scan.under("app/src/engine")
    if engine_files and not starter:
        findings.append(_pass("W1", "Engine modules exist and the starter counter is gone.", "app/src/engine"))
    else:
        findings.append(
            _fail(
                "W1",
                "The running UI is the Vite starter, not a leaf-check prototype.",
                "app/src/App.tsx contains the starter counter" if starter else "app/src/engine is empty",
            )
        )

    if "spreadsheet" in readme.lower() and any(word in readme.lower() for word in ("vision", "leaf", "photo")):
        findings.append(_pass("W2", "The README says what the model does and why a spreadsheet does not.", "app/README.md"))
    else:
        findings.append(_fail("W2", "The README does not explain the model or why a simpler tool fails.", "app/README.md"))

    if evaluation and any(token in evaluation.lower() for token in ("f1", "test set", "held-out", "held out")):
        findings.append(_pass("W3", "EVALUATION.md names a test result.", "app/docs/EVALUATION.md"))
    else:
        findings.append(_fail("W3", "There is no evaluation write-up with a named test set.", "app/docs/EVALUATION.md"))

    if decisions:
        findings.append(_pass("B1", "The decision words are in the client.", "app/src"))
    else:
        findings.append(_fail("B1", "The one agricultural decision is not implemented.", "app/src"))

    if "/officer" in src:
        findings.append(_pass("B2", "An /officer route is present.", "app/src"))
    else:
        findings.append(_fail("B2", "There is no officer dashboard route.", "app/src"))

    live = re.findall(r"https?://[^\s)]+", readme)
    live = [url for url in live if "vite.dev" not in url and "react.dev" not in url and "github.com/vitejs" not in url]
    if live:
        findings.append(_pass("S1", "The README names a project URL.", live[0]))
    else:
        findings.append(_missing("S1", "No live project URL is recorded in the README.", "app/README.md", "blocker"))

    licence = scan.has("app/LICENSE") or scan.has("LICENSE")
    secret_hits = _secret_locations(scan)
    if licence and not secret_hits:
        findings.append(_pass("S2", "A licence file is present and the secret scan found no tokens.", "app/LICENSE"))
    elif secret_hits:
        findings.append(
            _fail("S2", "The secret scan found token-like strings.", ", ".join(secret_hits[:8]), "blocker")
        )
    else:
        findings.append(_fail("S2", "There is no licence file.", "app/LICENSE", "major"))

    videos = [
        path
        for path in scan.files
        if path.lower().endswith((".mp4", ".mov"))
    ]
    if videos:
        findings.append(_pass("S3", "Video files are in the tree. Duration still needs ffprobe.", ", ".join(videos[:5])))
    else:
        findings.append(_missing("S3", "No MP4 or MOV video is in the tree.", "repo", "major"))

    if scan.has("video/COVERAGE.md") or scan.has("kb/pitch/COVERAGE.md"):
        findings.append(_pass("S4", "A video coverage checklist exists.", "COVERAGE.md"))
    else:
        findings.append(_missing("S4", "No video coverage checklist is in the tree.", "video/COVERAGE.md", "major"))

    if any("submission" in path.lower() and path.lower().endswith((".png", ".jpg", ".md")) for path in scan.files):
        findings.append(_pass("S5", "A submission note or screenshot is in the tree.", "submission file"))
    else:
        findings.append(_missing("S5", "No submission confirmation is in the tree.", "repo", "note"))

    if replication and "cocoa" in replication.lower():
        findings.append(_pass("J1", "REPLICATION.md includes the cocoa example.", "app/docs/REPLICATION.md"))
    else:
        findings.append(
            _fail("J1", "There is no replication note with a worked swap example.", "app/docs/REPLICATION.md", "major")
        )

    findings.extend(_extra(scan, starter))
    return findings


def _secret_locations(scan: Scan) -> list[str]:
    hits = []
    for path, body in scan.text.items():
        if path.endswith(".env.example"):
            continue
        for index, line in enumerate(body.splitlines(), start=1):
            if SECRET_RE.search(line):
                hits.append(f"{path}:{index}")
    return hits


def _extra(scan: Scan, starter: bool) -> list[Finding]:
    extra = []
    if starter:
        extra.append(
            Finding(
                "UI0",
                "fail",
                "blocker",
                "app/src/App.tsx is the Vite starter: a counter, hero art, and links to Vite and React.",
                "app/src/App.tsx",
            )
        )
    expected = (
        "app/src/engine",
        "app/src/pages",
        "app/src/content/answers.json",
        "app/src/content/rules.json",
        "app/src/content/season.json",
        "app/public/model/model.json",
        "app/docs/ARCHITECTURE.md",
        "app/docs/LANGUAGES.md",
        "app/ml",
    )
    absent = []
    for rel in expected:
        present = scan.has(rel) or any(path.startswith(rel.rstrip("/") + "/") for path in scan.files)
        if not present:
            absent.append(rel)
    if absent:
        extra.append(
            Finding(
                "TREE",
                "fail",
                "blocker",
                "Expected product paths are absent: " + ", ".join(absent) + ".",
                "repo tree",
            )
        )
    return extra


def tally(findings: list[Finding]) -> dict[str, int]:
    counts = {"pass": 0, "fail": 0, "missing": 0}
    for finding in findings:
        if finding.id in REQUIREMENT_IDS and finding.status in counts:
            counts[finding.status] += 1
    counts["blockers"] = sum(1 for finding in findings if finding.severity == "blocker" and finding.status != "pass")
    return counts
