"""Small AI budgets (R3): model under 5 MB, offline bundle under 15 MB, and model.json complete."""
from __future__ import annotations

import hashlib
from pathlib import Path

from qa.common import Result, dir_size, human_bytes, read_json

MODEL_CAP = 5 * 1024 * 1024
BUNDLE_CAP = 15 * 1024 * 1024
BITRATE_3G = 1_000_000 / 8  # bytes per second at 1 Mbit/s


def run(root: Path) -> list[Result]:
    out: list[Result] = []
    onnx = root / "public/model/leaf.onnx"
    mj = root / "public/model/model.json"
    if not onnx.exists():
        out.append(Result("budgets:model_size", "skip", "public/model/leaf.onnx missing"))
    else:
        size = onnx.stat().st_size
        out.append(Result("budgets:model_size", "fail" if size > MODEL_CAP else "pass",
                          f"leaf.onnx {human_bytes(size)} (cap {human_bytes(MODEL_CAP)})"))
        if mj.exists():
            m = read_json(mj)
            problems = []
            for k in ("version", "labels", "input", "temperature", "threshold", "sha256", "bytes"):
                if k not in m or m[k] in ("", None) or (k != "threshold" and m[k] == 0):
                    problems.append(f"model.json: '{k}' missing or empty")
            if m.get("bytes") and m["bytes"] != size:
                problems.append(f"model.json bytes {m['bytes']} != file {size}")
            if m.get("sha256"):
                h = hashlib.sha256(onnx.read_bytes()).hexdigest()
                if h != m["sha256"]:
                    problems.append("model.json sha256 does not match leaf.onnx")
            if m.get("threshold") in (0, 0.0):
                problems.append("threshold is 0: abstention is disabled")
            out.append(Result("budgets:model_json", "fail" if problems else "pass",
                              "; ".join(problems) if problems else "model.json complete and matches the file", problems))
        else:
            out.append(Result("budgets:model_json", "fail", "public/model/model.json missing"))

    dist = root / "dist"
    if dist.exists():
        size = dir_size(dist)
        secs = size / BITRATE_3G
        out.append(Result("budgets:bundle_size", "fail" if size > BUNDLE_CAP else "pass",
                          f"dist/ {human_bytes(size)} (cap {human_bytes(BUNDLE_CAP)}); about {secs/60:.1f} min at 1 Mbit/s 3G"))
        sw = list(dist.glob("sw.js")) + list(dist.glob("workbox-*.js"))
        out.append(Result("budgets:service_worker", "pass" if sw else "fail",
                          "service worker built" if sw else "no sw.js in dist/: offline caching not set up"))
        wasm = list((root / "public/ort").glob("*.wasm")) if (root / "public/ort").exists() else []
        out.append(Result("budgets:ort_wasm", "pass" if wasm else "warn",
                          f"{len(wasm)} onnxruntime wasm file(s) in public/ort" if wasm else "public/ort has no wasm files; inference will try to fetch from a CDN (breaks offline)"))
    else:
        out.append(Result("budgets:bundle_size", "skip", "dist/ not built yet (run npm run build)"))
    return out
