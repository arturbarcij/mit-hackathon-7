"""Run the browser parity harness in Chromium via Playwright.

Usage: python browser_parity.py <serve_dir> <python_logits.json> <node_logits.json> <out_json>
serve_dir must contain index.html, ort/, src/preprocess.js, fixtures/, model/.
Starts python -m http.server on a free port, loads the page, runs parity and latency,
then repeats latency with CDP Emulation.setCPUThrottlingRate 4.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main():
    serve, py_path, node_path, out_path = (Path(a) for a in sys.argv[1:5])
    py = json.loads(py_path.read_text())
    node = json.loads(node_path.read_text())
    port = free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=serve,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    exe = os.environ.get("CHROMIUM_PATH")
    if not exe:
        cands = sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
        exe = str(cands[-1]) if cands else None
    fixtures = json.loads((serve / "fixtures" / "fixtures.json").read_text())["fixtures"]
    result = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=exe, headless=True)
            page = browser.new_page()
            loaded = []
            page.on("response", lambda r: loaded.append((r.url, r.status, r.headers.get("content-length"))))
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            page.goto(f"http://127.0.0.1:{port}/index.html")
            page.wait_for_function("window.harnessReady === true")
            result["chromium"] = browser.version
            result["chromium_path"] = exe
            par = page.evaluate("(f) => window.runParity(f, true)", fixtures)
            result["ort_web_version"] = par.get("ort_web")
            result["user_agent"] = par.get("ua")
            # compare logits against python ORT and node ORT
            pyrows = {r["name"]: r for r in py["per_image"]}
            nd32 = {r["name"]: r for r in node["fp32"]["per_image"]}
            nd8 = {r["name"]: r for r in node["int8"]["per_image"]}
            m = {"fp32_vs_python_ort": 0.0, "fp32_vs_node_ort": 0.0, "int8_vs_python_ort": 0.0, "int8_vs_node_ort": 0.0,
                 "fp32_vs_pytorch": 0.0, "int8_vs_pytorch": 0.0}
            agree = {"fp32_vs_python_ort": 0, "int8_vs_python_ort": 0, "fp32_vs_node_ort": 0, "int8_vs_node_ort": 0, "int8_vs_pytorch": 0}
            for row in par["images"]:
                n = row["name"]
                b32, b8 = np.array(row["logits_fp32"]), np.array(row["logits_int8"])
                p32, p8, pt = np.array(pyrows[n]["ort_fp32"]), np.array(pyrows[n]["ort_int8"]), np.array(pyrows[n]["pytorch"])
                n32, n8 = np.array(nd32[n]["logits"]), np.array(nd8[n]["logits"])
                m["fp32_vs_python_ort"] = max(m["fp32_vs_python_ort"], float(np.abs(b32 - p32).max()))
                m["int8_vs_python_ort"] = max(m["int8_vs_python_ort"], float(np.abs(b8 - p8).max()))
                m["fp32_vs_node_ort"] = max(m["fp32_vs_node_ort"], float(np.abs(b32 - n32).max()))
                m["int8_vs_node_ort"] = max(m["int8_vs_node_ort"], float(np.abs(b8 - n8).max()))
                m["fp32_vs_pytorch"] = max(m["fp32_vs_pytorch"], float(np.abs(b32 - pt).max()))
                m["int8_vs_pytorch"] = max(m["int8_vs_pytorch"], float(np.abs(b8 - pt).max()))
                agree["fp32_vs_python_ort"] += int(b32.argmax() == p32.argmax())
                agree["int8_vs_python_ort"] += int(b8.argmax() == p8.argmax())
                agree["fp32_vs_node_ort"] += int(b32.argmax() == n32.argmax())
                agree["int8_vs_node_ort"] += int(b8.argmax() == n8.argmax())
                agree["int8_vs_pytorch"] += int(b8.argmax() == pt.argmax())
            N = len(par["images"])
            result["logits_max_abs_diff"] = m
            result["top1_agreement"] = {k: v / N for k, v in agree.items()}
            result["preprocess"] = {
                "png_max_levels": max(r["png"]["max_abs"] for r in par["images"]),
                "png_max_tensor_abs": max(r["png"]["tensor"]["max_abs"] for r in par["images"]),
                "png_all_bit_exact": all(r["png"]["tensor"]["exact_frac"] == 1 for r in par["images"]),
                "jpg_max_levels": max(r["jpg"]["max_abs"] for r in par["images"]),
                "jpg_mean_levels": float(np.mean([r["jpg"]["mean_abs"] for r in par["images"]])),
                "jpg_max_tensor_abs": max(r["jpg"]["tensor"]["max_abs"] for r in par["images"]),
                "jpg_exact_frac_mean": float(np.mean([r["jpg"]["exact_frac"] for r in par["images"]])),
                "per_image": [{"name": r["name"], "png_max_levels": r["png"]["max_abs"], "jpg_max_levels": r["jpg"]["max_abs"],
                               "jpg_mean_levels": r["jpg"]["mean_abs"], "jpg_exact_frac": r["jpg"]["exact_frac"]} for r in par["images"]],
            }
            result["latency_unthrottled"] = {
                "fp32_ms_median": par["fp32_ms_median"], "fp32_ms_first": par["fp32_ms_first"],
                "int8_ms_median": par["int8_ms_median"], "int8_ms_first": par["int8_ms_first"],
                "fp32_session_load_ms": par["fp32_load_ms"], "int8_session_load_ms": par["int8_load_ms"],
                "preprocess_ms_median_png_fixtures": par["preprocess_ms_median"],
            }
            lat1 = page.evaluate("() => window.runLatency(20)")
            result["latency_unthrottled"].update({k + "_rerun" if k.endswith("median") else k: v for k, v in lat1.items()})
            cdp = page.context.new_cdp_session(page)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
            lat4 = page.evaluate("() => window.runLatency(20)")
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            result["latency_cpu_throttle_4x"] = lat4
            result["wasm_files_loaded"] = []
            seen = set()
            for url, status, cl in loaded:
                if "/ort/" in url and url not in seen:
                    seen.add(url)
                    rel = url.split(f":{port}/", 1)[1]
                    fp = serve / rel
                    result["wasm_files_loaded"].append({"url": rel, "status": status, "bytes": fp.stat().st_size if fp.exists() else None})
            result["page_errors"] = errors
            browser.close()
    finally:
        srv.terminate()
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "preprocess"} | {"preprocess": {k: v for k, v in result["preprocess"].items() if k != "per_image"}}, indent=2))


if __name__ == "__main__":
    main()
