"""Anthropic Messages API client. The key is read once and never written to logs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5-5"


class AgentClientError(RuntimeError):
    pass


def load_api_key(root: Path) -> str:
    env_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env_key:
        return env_key
    candidates = (
        root / "app" / "backend" / ".env",
        root / "backend" / ".env",
        root / ".env",
    )
    for path in candidates:
        parsed = _parse_env(path)
        key = parsed.get("ANTHROPIC_API_KEY", "").strip()
        if key:
            return key
    raise AgentClientError(
        "ANTHROPIC_API_KEY is not set. Add it to app/backend/.env (git-ignored) or the environment. "
        "The file is not in this checkout."
    )


def model_name() -> str:
    return os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _parse_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[name.strip()] = value
    return values


def safe_error(exc: BaseException, secret: str = "") -> str:
    text = f"{type(exc).__name__}: {exc}"
    if secret:
        text = text.replace(secret, "[redacted]")
    # urllib can echo request headers in odd cases. Strip a bearer-looking tail.
    return text[:500]


def complete(api_key: str, model: str, system: str, user: str, max_tokens: int = 2500) -> str:
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "content-type": "application/json",
            "anthropic-version": API_VERSION,
            "x-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        detail = detail.replace(api_key, "[redacted]")
        raise AgentClientError(f"Claude API HTTP {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise AgentClientError(f"Claude API network error: {exc.reason}") from None
    parsed = json.loads(body)
    parts = []
    for block in parsed.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    if not parts:
        raise AgentClientError("Claude API returned no text content.")
    return "\n".join(parts)
