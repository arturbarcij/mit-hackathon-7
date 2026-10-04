"""Run manifest -> train -> export -> eval. Stop on first failure."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PY = sys.executable
HERE = Path(__file__).resolve().parent


def run(script: str, extra: list[str] | None = None) -> None:
    cmd = [PY, str(HERE / script), *(extra or [])]
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(HERE))
    if r.returncode != 0:
        raise SystemExit(r.returncode)


if __name__ == "__main__":
    extra_train = sys.argv[1:]
    run("manifest.py")
    run("train.py", extra_train)
    run("export.py")
    run("eval.py")
    print("PIPELINE OK", flush=True)
