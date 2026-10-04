"""Evidence pack sent to every reviewer. Secrets are stripped before it leaves the machine."""

from __future__ import annotations

import re
from pathlib import Path

from .probes import Finding, Scan, build_scan, run_probes, tally

REDACT = re.compile(
    r"(sk-ant-[A-Za-z0-9_\-]{8,}|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{20,}|"
    r"ghp_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9\-]{10,})"
)

EXCERPT_FILES = (
    "app/package.json",
    "app/vite.config.ts",
    "app/index.html",
    "app/README.md",
    "app/src/App.tsx",
    "app/src/main.tsx",
    "kb/CONTRACTS.md",
)

EXCERPT_CAP = 6_000


def redact(text: str) -> str:
    return REDACT.sub("[redacted]", text)


def build_pack(root: Path) -> dict:
    scan = build_scan(root)
    findings = run_probes(scan)
    excerpts = {}
    for rel in EXCERPT_FILES:
        body = scan.read(rel)
        if not body:
            excerpts[rel] = None
            continue
        excerpts[rel] = redact(body[:EXCERPT_CAP])
    manifest = [
        {"path": path, "bytes": scan.sizes[path]}
        for path in scan.files
        if not path.endswith((".png", ".svg", ".jpg", ".onnx", ".mp3", ".wasm"))
    ]
    return {
        "root_name": root.resolve().name,
        "file_count": len(scan.files),
        "tally": tally(findings),
        "findings": [item.as_dict() for item in findings],
        "excerpts": excerpts,
        "manifest": manifest,
        "note": (
            "This pack is the whole tree the runner could see, minus dependencies, git metadata, "
            "and env files. A path that is not in the manifest is not in the checkout. "
            "kb/STATUS.md is a board, not proof that a file exists."
        ),
    }


def findings_from_pack(pack: dict) -> list[Finding]:
    return [Finding(**item) for item in pack["findings"]]
