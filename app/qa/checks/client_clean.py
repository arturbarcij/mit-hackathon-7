"""No runtime AI API calls and no secrets in the client (G3, S2).

Scans src/ and, when present, the built dist/ bundle.
"""
from __future__ import annotations

import re
from pathlib import Path

from qa.common import Result, read_text

FORBIDDEN_HOSTS = [
    "api.openai.com", "api.anthropic.com", "generativelanguage.googleapis.com",
    "api.elevenlabs.io", "api.brightdata.com", "mcp.brightdata.com",
    "api-inference.huggingface.co", "openrouter.ai", "api.mistral.ai", "api.cohere.",
]
FORBIDDEN_PKGS = ["from 'openai'", 'from "openai"', "@anthropic-ai/sdk", "@google/generative-ai",
                  "elevenlabs", "@google/genai"]
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{20,}|sk_[a-z]+_[A-Za-z0-9]{16,}|AIza[0-9A-Za-z\-_]{30,}|"
                       r"xi-api-key\s*[:=]\s*['\"][A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
                       r"token=[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
VITE_SECRET_RE = re.compile(r"VITE_[A-Z_]*(KEY|SECRET|TOKEN|PASSWORD)")


def _scan(files: list[Path], root: Path) -> tuple[list[str], list[str], list[str]]:
    hosts, pkgs, secrets = [], [], []
    for f in files:
        try:
            txt = read_text(f)
        except Exception:
            continue
        rel = f.relative_to(root).as_posix()
        for h in FORBIDDEN_HOSTS:
            if h in txt:
                hosts.append(f"{rel}: {h}")
        for p in FORBIDDEN_PKGS:
            if p in txt:
                pkgs.append(f"{rel}: {p}")
        if SECRET_RE.search(txt) or VITE_SECRET_RE.search(txt):
            secrets.append(rel)
    return hosts, pkgs, secrets


def run(root: Path) -> list[Result]:
    out: list[Result] = []
    src = root / "src"
    if not src.exists():
        return [Result("client_clean", "skip", "src/ missing")]
    exts = {".ts", ".tsx", ".js", ".jsx", ".json", ".html", ".css"}
    src_files = [p for p in src.rglob("*") if p.is_file() and p.suffix in exts]
    hosts, pkgs, secrets = _scan(src_files, root)
    out.append(Result("client_clean:no_ai_apis_src", "fail" if hosts or pkgs else "pass",
                      "AI API hosts or SDKs referenced in src/" if hosts or pkgs else f"{len(src_files)} source files, no AI API references",
                      hosts + pkgs))
    out.append(Result("client_clean:no_secrets_src", "fail" if secrets else "pass",
                      "secret-like strings or VITE_*KEY variables in src/" if secrets else "no secrets in src/", secrets))

    dist = root / "dist"
    if dist.exists():
        dist_files = [p for p in dist.rglob("*") if p.is_file() and p.suffix in {".js", ".html", ".json"}]
        hosts, pkgs, secrets = _scan(dist_files, root)
        out.append(Result("client_clean:dist", "fail" if hosts or secrets else "pass",
                          "built bundle references AI APIs or contains secrets" if hosts or secrets else f"built bundle clean ({len(dist_files)} files)",
                          hosts + secrets))
    else:
        out.append(Result("client_clean:dist", "skip", "dist/ not built yet (run npm run build)"))
    return out
