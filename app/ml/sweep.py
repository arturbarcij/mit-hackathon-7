"""Overnight research queue. Never writes public/model, calibration.json, metrics.json or EVALUATION.md."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from common import LABELS, ML, ROOT

PY = sys.executable
CEST = ZoneInfo("Europe/Paris")
SWEEP = ML / "sweep"
LOG = ML / "logs" / "sweep.log"
RESULTS = SWEEP / "results.csv"
MANIFEST = SWEEP / "manifest_v1.csv"
CUT_START = (5, 0)   # no new job after 05:00 CEST
CUT_STOP = (6, 15)   # abort a running job at 06:15 CEST


def now_cest() -> datetime:
    return datetime.now(CEST)


def _morning_past(cut: tuple[int, int]) -> bool:
    """Cuts are 05:00 / 06:15 CEST. Evening hours stay in the overnight window."""
    t = now_cest()
    return t.hour < 12 and (t.hour, t.minute) >= cut


def too_late_to_start() -> bool:
    return _morning_past(CUT_START)


def past_hard_stop() -> bool:
    return _morning_past(CUT_STOP)


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{now_cest().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def run(cmd: list[str], cwd=None) -> int:
    log("+ " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=cwd or str(ML))
    return p.returncode


def append_row(row: dict) -> None:
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name", "arch", "aug", "status", "val_coverage", "val_selective_acc",
        "val_macro_f1", "bracol_val_macro_f1", "bytes", "quantization",
        "int8_parity", "qualifies", "note", "finished",
    ]
    new = not RESULTS.exists()
    with RESULTS.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def probe_large075() -> tuple[bool, int, str]:
    """Export an untrained 6-class copy. Skip job B if the small file is over 4.5 MB."""
    import torch
    import timm
    from export import export_onnx
    dest = SWEEP / "_probe_large075.onnx"
    dest.parent.mkdir(parents=True, exist_ok=True)
    model = timm.create_model("mobilenetv3_large_075", pretrained=False, num_classes=len(LABELS))
    model.eval()
    export_onnx(model, dest)
    raw = dest.stat().st_size
    try:
        import onnx
        from onnxruntime.transformers.float16 import convert_float_to_float16
        fp16 = dest.with_name("_probe_large075_fp16.onnx")
        onnx.save(convert_float_to_float16(onnx.load(str(dest)), keep_io_types=True), fp16)
        n = fp16.stat().st_size
        note = f"untrained fp32={raw} fp16={n}"
        return n <= 4.5 * 1024 * 1024, n, note
    except Exception as e:
        return raw <= 4.5 * 1024 * 1024, raw, f"fp16 convert failed ({e}); fp32={raw}"


def read_cal(run_dir: Path) -> dict:
    p = run_dir / "calibration.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def read_parity(out_dir: Path) -> dict:
    p = out_dir / "parity.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def job(name: str, arch: str, aug: str, batch: int = 96) -> dict:
    out = SWEEP / name
    run_dir = out / "run"
    out.mkdir(parents=True, exist_ok=True)
    row = {
        "name": name, "arch": arch, "aug": aug, "status": "fail",
        "val_coverage": "", "val_selective_acc": "", "val_macro_f1": "",
        "bracol_val_macro_f1": "", "bytes": "", "quantization": "",
        "int8_parity": "", "qualifies": "0", "note": "", "finished": "",
    }
    if too_late_to_start():
        row["status"] = "skipped"
        row["note"] = "after 05:00 CEST"
        return row
    rc = run([
        PY, "train.py",
        "--arch", arch, "--aug", aug,
        "--manifest", str(MANIFEST),
        "--run-dir", str(run_dir),
        "--no-global",
        "--epochs", "8", "--patience", "2", "--batch", str(batch),
    ])
    if rc != 0:
        row["note"] = f"train rc={rc}"
        return row
    if past_hard_stop():
        row["status"] = "stopped"
        row["note"] = "hard stop 06:15"
        return row
    rc = run([
        PY, "export.py",
        "--run", str(run_dir),
        "--out", str(out),
        "--manifest", str(MANIFEST),
    ])
    if rc != 0:
        row["note"] = f"export rc={rc}"
        return row
    cal = read_cal(run_dir)
    par = read_parity(out)
    cov = float(cal.get("val_coverage") or 0)
    sel = float(cal.get("val_selective_acc") or 0)
    # Primary metric: coverage at 95% selective acc. If 95% never reached, 0.
    if sel < 0.95:
        cov_metric = 0.0
    else:
        cov_metric = cov
    qfmt = par.get("format") or ""
    ipar = float(par.get("pt_vs_onnx_int8") or 0)
    size = 0
    for cand in (out / "leaf.onnx", out / "leaf_int8.onnx"):
        if cand.exists():
            size = cand.stat().st_size
            break
    qualifies = (
        qfmt == "int8"
        and ipar >= 0.95
        and 0 < size <= 5 * 1024 * 1024
        and sel >= 0.95
    )
    row.update({
        "status": "ok",
        "val_coverage": f"{cov_metric:.4f}",
        "val_selective_acc": f"{sel:.4f}",
        "val_macro_f1": f"{float(cal.get('val_macro_f1') or 0):.4f}",
        "bracol_val_macro_f1": "" if cal.get("bracol_val_macro_f1") is None else f"{float(cal['bracol_val_macro_f1']):.4f}",
        "bytes": str(size),
        "quantization": qfmt,
        "int8_parity": f"{ipar:.3f}",
        "qualifies": "1" if qualifies else "0",
        "note": cal.get("command", ""),
        "finished": now_cest().isoformat(timespec="seconds"),
    })
    return row


def write_selection(rows: list[dict], v1: dict) -> None:
    """Val-only. Held-out sets are not read here."""
    v1_bracol = float(v1.get("bracol_val_macro_f1") or 0)
    v1_cov = float(v1.get("val_coverage") or 0)
    qualified = []
    for r in rows:
        if r.get("qualifies") != "1":
            continue
        try:
            bf = float(r["bracol_val_macro_f1"])
        except (TypeError, ValueError):
            continue
        if v1_bracol and bf < v1_bracol - 0.02:
            continue
        qualified.append(r)
    winner = "v1"
    reason = "no qualifying candidate; keep v1"
    if qualified:
        best = max(qualified, key=lambda r: (float(r["val_coverage"]), float(r["val_macro_f1"])))
        if float(best["val_coverage"]) >= v1_cov + 0.02:
            winner = best["name"]
            reason = "beats v1 coverage by at least 2 points"
        else:
            reason = "best qualifier under the 2-point coverage margin; keep v1"
    payload = {
        "winner": winner,
        "reason": reason,
        "rule_time": now_cest().isoformat(timespec="seconds"),
        "v1": v1,
        "candidates": rows,
        "held_out_used_for_selection": False,
    }
    (SWEEP / "selection.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"selection winner={winner} {reason}")


def v1_bracol_f1() -> str:
    """Val BRACOL macro F1 for the shipped v1. Writes sweep/v1_bracol.json only."""
    cached = SWEEP / "v1_bracol.json"
    if cached.exists():
        return f"{float(json.loads(cached.read_text(encoding='utf-8'))['bracol_val_macro_f1']):.4f}"
    import torch
    from torch.utils.data import DataLoader
    from export import load_best
    from train import LeafDataset, eval_transform, load_manifest, run_eval

    val_rows = [r for r in load_manifest({"val"}, MANIFEST) if r["source"] == "bracol"]
    if not val_rows:
        return ""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _ = load_best()
    model.to(device)
    loader = DataLoader(
        LeafDataset(val_rows, eval_transform()),
        batch_size=96, shuffle=False, num_workers=2, pin_memory=True,
    )
    ev = run_eval(model, loader, device)
    payload = {"bracol_val_macro_f1": ev["macro_f1"], "n": len(val_rows)}
    cached.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"v1 bracol val macro F1={ev['macro_f1']:.4f} n={len(val_rows)}")
    return f"{ev['macro_f1']:.4f}"


def v1_row() -> dict:
    cal = json.loads((ML / "calibration.json").read_text(encoding="utf-8"))
    par = {}
    pf = ML / "parity.json"
    if pf.exists():
        par = json.loads(pf.read_text(encoding="utf-8"))
    bracol = cal.get("bracol_val_macro_f1") or v1_bracol_f1()
    return {
        "name": "v1",
        "arch": cal.get("arch", "mobilenetv3_small_100"),
        "aug": "v1",
        "status": "ok",
        "val_coverage": f"{float(cal.get('val_coverage') or 0):.4f}",
        "val_selective_acc": f"{float(cal.get('val_selective_acc') or 0):.4f}",
        "val_macro_f1": f"{float(cal.get('val_macro_f1') or 0):.4f}",
        "bracol_val_macro_f1": "" if bracol in (None, "") else f"{float(bracol):.4f}",
        "bytes": "3077051",
        "quantization": "fp16",
        "int8_parity": f"{float(par.get('pt_vs_onnx_int8') or 0.34):.3f}",
        "qualifies": "0",
        "note": "shipped v1; int8 parity failed so this row does not qualify under the int8 rule",
        "finished": "",
    }


def main() -> int:
    SWEEP.mkdir(parents=True, exist_ok=True)
    if not MANIFEST.exists():
        raise SystemExit(f"missing {MANIFEST}; copy ml/manifest.csv first")
    log("sweep start")
    v1 = v1_row()
    append_row(v1)
    rows = []

    # A sheet
    r = job("sheet", "mobilenetv3_small_100", "sheet", batch=96)
    append_row(r)
    rows.append(r)
    log(f"job A {r['status']} cov={r['val_coverage']} qualifies={r['qualifies']}")

    # B large075
    if past_hard_stop() or too_late_to_start():
        r = {"name": "large075", "arch": "mobilenetv3_large_075", "aug": "v1", "status": "skipped",
             "qualifies": "0", "note": "time cut", "val_coverage": "", "val_selective_acc": "",
             "val_macro_f1": "", "bracol_val_macro_f1": "", "bytes": "", "quantization": "",
             "int8_parity": "", "finished": ""}
    else:
        ok, nbytes, note = probe_large075()
        log(f"large075 probe {note} ok={ok}")
        if not ok:
            r = {"name": "large075", "arch": "mobilenetv3_large_075", "aug": "v1", "status": "skipped",
                 "qualifies": "0", "note": f"untrained export {nbytes} over 4.5 MB; {note}",
                 "val_coverage": "", "val_selective_acc": "", "val_macro_f1": "",
                 "bracol_val_macro_f1": "", "bytes": str(nbytes), "quantization": "",
                 "int8_parity": "", "finished": ""}
        else:
            r = job("large075", "mobilenetv3_large_075", "v1", batch=48)
    append_row(r)
    rows.append(r)
    log(f"job B {r['status']} cov={r.get('val_coverage')} qualifies={r.get('qualifies')}")

    # C combo if A or B passed the rule and there is time
    a_ok = rows[0].get("qualifies") == "1"
    b_ok = rows[1].get("qualifies") == "1"
    if (a_ok or b_ok) and not too_late_to_start() and not past_hard_stop():
        arch = "mobilenetv3_large_075" if b_ok else "mobilenetv3_small_100"
        aug = "sheet" if a_ok else "v1"
        r = job("combo", arch, aug, batch=48 if "large" in arch else 96)
    else:
        r = {"name": "combo", "arch": "", "aug": "", "status": "skipped", "qualifies": "0",
             "note": "A and B did not qualify, or time cut", "val_coverage": "",
             "val_selective_acc": "", "val_macro_f1": "", "bracol_val_macro_f1": "",
             "bytes": "", "quantization": "", "int8_parity": "", "finished": ""}
    append_row(r)
    rows.append(r)
    log(f"job C {r['status']}")

    write_selection(rows, v1)
    log("sweep done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
