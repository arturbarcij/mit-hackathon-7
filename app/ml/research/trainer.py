"""Run one research job in its own process, so a crash or CUDA error cannot stop the queue.

  train or baseline:  python research/trainer.py --job protocol --out DIR --deadline 2026-10-04T06:15:00
  held-out (once):    python research/trainer.py --job v1 --out DIR --heldout --run-dir RUN

A job writes only inside --out. It reuses train.py (datasets, transforms, eval loop),
export.py (ONNX export, int8 quantisation, parity) and eval.py (CPU latency, prediction),
so preprocessing is identical to the shipped model. Set JANI_RESEARCH_FAKE=1 to test the
orchestration without torch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ML = HERE.parent
for p in (str(ML), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import data as rdata  # noqa: E402
import plan  # noqa: E402
from common import LABELS, LABEL_TO_IDX, ROOT  # noqa: E402

FAKE = os.environ.get("JANI_RESEARCH_FAKE") == "1"
SHARED = {"uganda": ["healthy", "rust", "phoma"], "rocole": ["healthy", "rust"], "wild": None}


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


def log(out: Path, msg: str) -> None:
    line = f"{datetime.now().strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with (out / "job.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def job_config(job: str, out: Path) -> dict:
    spec = plan.JOBS.get(job)
    if spec and spec["kind"] != "combo":
        return dict(spec)
    cfg = out / "config.json"  # combo: written by sweep.py from plan.combo_config()
    if not cfg.exists():
        raise SystemExit(f"{job}: no config.json in {out}")
    return json.loads(cfg.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- fake mode
def fake_result(job: str, cfg: dict) -> dict:
    spec = json.loads(os.environ.get("JANI_RESEARCH_FAKE_SPEC", "{}")).get(job, {})
    h = int(hashlib.sha256(job.encode()).hexdigest()[:6], 16) / 0xFFFFFF
    res = {
        "status": "ok", "cov95": round(0.6 + 0.2 * h, 4), "bracol_acc": round(0.6 + 0.2 * h, 4),
        "val_macro_f1": 0.9, "val_acc": 0.95, "threshold95": 0.9, "temperature": 1.2,
        "int8_bytes": 2_000_000, "parity_int8": 0.98, "cpu_ms": 5.0, "bracol_n": 173,
        "arch_used": (cfg.get("arch") or ["mobilenetv3_small_100"])[0],
        "epochs_run": 1, "minutes": 0.0, "checkpoint": "", "fake": True,
    }
    res.update(spec)
    return res


# --------------------------------------------------------------------------- torch helpers
def pick_device(name: str):
    import torch
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(name)


def fit_temperature(logits, y) -> float:
    import numpy as np
    import torch
    import torch.nn.functional as F
    y_t = torch.as_tensor(y, dtype=torch.long)
    lo, hi, n = plan.TEMPERATURE_GRID
    best_t, best = 1.0, float("inf")
    for t in np.linspace(lo, hi, n):
        nll = F.cross_entropy(logits / float(t), y_t).item()
        if nll < best:
            best, best_t = nll, float(t)
    return best_t


def int8_size(model, out: Path, cal_paths: list[Path]) -> int:
    from export import export_onnx, quantize
    pre = out / "precheck"
    pre.mkdir(parents=True, exist_ok=True)
    m = model.to("cpu").eval()
    export_onnx(m, pre / "fp32.onnx")
    quantize(pre / "fp32.onnx", pre / "int8.onnx", cal_paths[:8])
    return (pre / "int8.onnx").stat().st_size


def resolve_arch(names: list[str], out: Path, cal_paths: list[Path]):
    import timm
    errors = []
    for name in names:
        try:
            model = timm.create_model(name, pretrained=True, num_classes=len(LABELS))
        except Exception as e:  # unknown name or no pretrained weights
            errors.append(f"{name}: {type(e).__name__}: {str(e)[:160]}")
            continue
        if name == "mobilenetv3_small_100":
            return model, name, None  # v1's backbone, known to fit
        size = int8_size(model, out, cal_paths)
        if size <= plan.INT8_PRECHECK_BYTES:
            return model, name, size
        errors.append(f"{name}: int8 pre-check {size} bytes over {plan.INT8_PRECHECK_BYTES}")
    raise RuntimeError("no usable architecture: " + " | ".join(errors))


def load_checkpoint_model(arch: str, ckpt_path: Path):
    import timm
    import torch
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    model = timm.create_model(arch, pretrained=False, num_classes=len(LABELS))
    model.load_state_dict(ckpt["model"])
    return model.eval()


def v1_checkpoint(smoke: bool) -> tuple[Path, str]:
    cal = ML / "calibration.json"
    if cal.exists():
        c = json.loads(cal.read_text(encoding="utf-8"))
        p = ROOT / c["best_checkpoint"]
        if p.exists():
            return p, "ml/calibration.json"
    if smoke:  # before v1 has finished: newest best.pt is enough to test the path
        cands = sorted((ML / "runs").glob("*/best.pt"), key=lambda q: q.stat().st_mtime)
        if cands:
            return cands[-1], "newest ml/runs/*/best.pt (smoke only)"
    raise SystemExit("v1 checkpoint not found (ml/calibration.json)")


def sampler_weights(rows: list[dict], bracol_weight: float) -> list[float]:
    """Class-balanced like train.py; within a class, BRACOL rows get `bracol_weight` times the mass."""
    s = [bracol_weight if r["source"] == "bracol" else 1.0 for r in rows]
    tot = Counter()
    for r, w in zip(rows, s):
        tot[r["label"]] += w
    k = len(tot)
    return [w / (tot[r["label"]] * k) for r, w in zip(rows, s)]


def evaluate(model, rows: list[dict], device, batch: int, workers: int) -> dict:
    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    from train import LeafDataset, eval_transform, run_eval

    loader = DataLoader(LeafDataset(rows, eval_transform()), batch_size=batch, shuffle=False,
                        num_workers=workers, pin_memory=device.type == "cuda")
    ev = run_eval(model.to(device), loader, device)
    T = fit_temperature(ev["logits"], ev["y"])
    probs = torch.softmax(ev["logits"] / T, dim=1).numpy()
    y = np.asarray(ev["y"])
    conf, pred = probs.max(1), probs.argmax(1)
    correct = pred == y
    cov, thr, acc_acc = plan.coverage_at(conf, correct)
    bi = np.array([i for i, r in enumerate(rows) if r["source"] == "bracol"], dtype=int)
    return {
        "val_n": int(len(y)), "val_acc": float(ev["acc"]), "val_macro_f1": float(ev["macro_f1"]),
        "val_loss": float(ev["loss"]), "temperature": T,
        "cov95": float(cov), "threshold95": float(thr), "acc_on_accepted95": float(acc_acc),
        "bracol_n": int(bi.size), "bracol_acc": float(correct[bi].mean()) if bi.size else None,
        "per_class": ev["per_class"],
    }


def export_and_check(model, out: Path, train_rows: list[dict], test_rows: list[dict], smoke: bool) -> dict:
    from eval import cpu_latency
    from export import export_onnx, parity, quantize

    rng = random.Random(42)
    cal = [ROOT / r["path"] for r in rdata.existing(train_rows)]
    rng.shuffle(cal)
    test = [ROOT / r["path"] for r in rdata.existing(test_rows)]
    rng.shuffle(test)
    m = model.to("cpu").eval()
    fp32, int8 = out / "leaf_fp32.onnx", out / "leaf_int8.onnx"
    export_onnx(m, fp32)
    quantize(fp32, int8, cal[: 16 if smoke else 200])
    par = parity(m, fp32, int8, test[: 10 if smoke else 50])
    ms = cpu_latency(int8, test, n=5 if smoke else 30) * 1000
    return {"int8_bytes": int8.stat().st_size, "fp32_bytes": fp32.stat().st_size,
            "parity": par, "parity_int8": float(par["pt_vs_onnx_int8"]), "cpu_ms": round(ms, 2),
            "int8_sha256": hashlib.sha256(int8.read_bytes()).hexdigest()}


# --------------------------------------------------------------------------- jobs
def run_job(job: str, out: Path, deadline: datetime, device_name: str, smoke: bool, workers: int) -> dict:
    cfg = job_config(job, out)
    if FAKE:
        return fake_result(job, cfg)

    import numpy as np
    import torch
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, WeightedRandomSampler
    from train import LeafDataset, eval_transform, run_eval, set_seed
    from augment import train_transform_for

    t0 = time.time()
    device = pick_device(device_name)
    rows = rdata.read_frozen()
    train_rows = rdata.pool_rows(rows, {"train"})
    val_rows = rdata.pool_rows(rows, {"val"})
    test_rows = rdata.pool_rows(rows, {"test"})
    seed = int(cfg.get("seed", 42))
    if smoke:
        train_rows = rdata.small(train_rows, 4, seed)
        val_rows = rdata.small(val_rows, 3, seed)
        test_rows = rdata.small(test_rows, 2, seed)
        workers = 0
    log(out, f"{job}: device={device} train={len(train_rows)} val={len(val_rows)} smoke={smoke}")
    res: dict = {"job": job, "kind": cfg["kind"], "config": cfg, "device": str(device), "smoke": smoke}

    if cfg["kind"] == "baseline":
        ckpt_path, where = v1_checkpoint(smoke)
        ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        arch = (ck.get("args") or {}).get("arch") or "mobilenetv3_small_100"
        model = load_checkpoint_model(arch, ckpt_path)
        res.update(arch_used=arch, checkpoint=str(ckpt_path.relative_to(ROOT).as_posix()),
                   checkpoint_from=where, epochs_run=int(ck.get("epoch", 0)))
    else:
        set_seed(seed)
        cal_paths = [ROOT / r["path"] for r in rdata.existing(train_rows[:64])]
        model, arch, pre = resolve_arch(list(cfg["arch"]), out, cal_paths)
        res.update(arch_used=arch, int8_precheck_bytes=pre)
        log(out, f"{job}: arch {arch} (pre-check {pre})")
        model.to(device)
        train_ds = LeafDataset(train_rows, train_transform_for(cfg["aug"]))
        val_ds = LeafDataset(val_rows, eval_transform())
        g = torch.Generator()
        g.manual_seed(seed)
        weights = sampler_weights(train_rows, float(cfg.get("bracol_weight", 1.0)))
        sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True, generator=g)
        batch = 8 if smoke else plan.BATCH
        train_loader = DataLoader(train_ds, batch_size=batch, sampler=sampler, num_workers=workers,
                                  pin_memory=device.type == "cuda", drop_last=not smoke)
        val_loader = DataLoader(val_ds, batch_size=batch, shuffle=False, num_workers=workers,
                                pin_memory=device.type == "cuda")
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                lr=plan.LR, weight_decay=plan.WEIGHT_DECAY)
        epochs = 1 if smoke else plan.EPOCHS
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
        use_amp = device.type == "cuda"
        scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
        best_loss, bad, best_epoch, stopped = float("inf"), 0, 0, ""
        best_path = out / "best.pt"
        hist = []
        for epoch in range(1, epochs + 1):
            model.train()
            loss_sum, n = 0.0, 0
            for i, (x, y) in enumerate(train_loader):
                if i % 25 == 0 and datetime.now() >= deadline:
                    stopped = "deadline"
                    break
                x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
                opt.zero_grad(set_to_none=True)
                with torch.amp.autocast("cuda", enabled=use_amp):
                    loss = F.cross_entropy(model(x), y)
                scaler.scale(loss).backward()
                scaler.step(opt)
                scaler.update()
                loss_sum += loss.item() * y.size(0)
                n += y.size(0)
            if stopped:
                break
            sched.step()
            ev = run_eval(model, val_loader, device)
            hist.append({"epoch": epoch, "train_loss": round(loss_sum / max(n, 1), 4),
                         "val_loss": round(ev["loss"], 4), "val_acc": round(ev["acc"], 4),
                         "val_macro_f1": round(ev["macro_f1"], 4), "minutes": round((time.time() - t0) / 60, 1)})
            log(out, f"{job}: {hist[-1]}")
            if ev["loss"] < best_loss - 1e-4:
                best_loss, bad, best_epoch = ev["loss"], 0, epoch
                torch.save({"model": model.state_dict(), "epoch": epoch, "arch": arch,
                            "args": {**{k: v for k, v in cfg.items() if k != "why"}, "arch": arch}}, best_path)
            else:
                bad += 1
                if bad >= plan.PATIENCE:
                    stopped = "early stop"
                    break
        write_json(out / "history.json", hist)
        if not best_path.exists():
            res.update(status="truncated", reason=f"no finished epoch ({stopped})", minutes=round((time.time() - t0) / 60, 1))
            return res
        res.update(checkpoint=str(best_path.relative_to(ROOT).as_posix()), epochs_run=len(hist),
                   best_epoch=best_epoch, stopped=stopped or "all epochs")
        if stopped == "deadline":  # cannot qualify; do not spend more time after the deadline
            res.update(status="truncated", reason="deadline reached during training",
                       minutes=round((time.time() - t0) / 60, 1))
            return res
        model = load_checkpoint_model(arch, best_path)

    res.update(evaluate(model, val_rows, device, 8 if smoke else plan.BATCH, workers))
    res.update(export_and_check(model, out, train_rows, test_rows, smoke))
    res["minutes"] = round((time.time() - t0) / 60, 1)
    res["status"] = "ok"
    return res


def heldout_job(job: str, out: Path, run_dir: Path, device_name: str, smoke: bool) -> dict:
    if not (run_dir / "selection.json").exists():
        raise SystemExit("refusing held-out scoring: selection.json not written yet")
    res = json.loads((out / "result.json").read_text(encoding="utf-8"))
    if FAKE:
        return {"job": job, "fake": True, "sources": {s: {"n": 10, "acc": 0.5} for s in SHARED}}

    import numpy as np
    from eval import predict_rows

    device = pick_device(device_name)
    model = load_checkpoint_model(res["arch_used"], ROOT / res["checkpoint"]).to(device)
    T, thr = float(res["temperature"]), float(res["threshold95"])
    rows = rdata.read_frozen()
    out_sources = {}
    for src, shared in SHARED.items():
        sel = rdata.existing([r for r in rows if r["split"] == f"heldout_{src}"])
        mites = [r for r in sel if r["original_label"] == "red_spider_mite"]
        sel = [r for r in sel if r["label"] in LABEL_TO_IDX and r["original_label"] != "red_spider_mite"]
        if shared:
            sel = [r for r in sel if r["label"] in shared]
        if smoke:
            sel = rdata.small(sel, 3, 42)
        entry: dict = {"n": len(sel), "classes": dict(Counter(r["label"] for r in sel))}
        if sel:
            probs, y = predict_rows(model, sel, device, T)
            conf, pred = probs.max(1), probs.argmax(1)
            acc_mask = conf >= thr
            correct = pred == y
            entry.update(
                top1_acc=float(correct.mean()),
                coverage_at_threshold=float(acc_mask.mean()),
                acc_on_accepted=float(correct[acc_mask].mean()) if acc_mask.any() else None,
                recall={LABELS[c]: float(correct[y == c].mean()) for c in sorted(set(y.tolist()))},
                predicted=dict(Counter(LABELS[int(p)] for p in pred)),
            )
        if src == "rocole" and mites and not smoke:
            probs, _ = predict_rows(model, mites, device, T)
            flagged = (probs.max(1) < thr) | (probs.argmax(1) == LABEL_TO_IDX["not_leaf"])
            entry["red_spider_mite"] = {"n": len(mites), "abstain_or_not_leaf": float(np.mean(flagged))}
        out_sources[src] = entry
    return {"job": job, "arch_used": res["arch_used"], "threshold95": thr, "temperature": T,
            "scored_at": datetime.now().isoformat(timespec="seconds"), "sources": out_sources}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--deadline", default="2099-01-01T00:00:00")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--heldout", action="store_true")
    ap.add_argument("--run-dir", default="")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        if a.heldout:
            r = heldout_job(a.job, out, Path(a.run_dir), a.device, a.smoke)
            write_json(out / "heldout.json", r)
        else:
            r = run_job(a.job, out, datetime.fromisoformat(a.deadline), a.device, a.smoke, a.workers)
            r.setdefault("job", a.job)
            r["finished_at"] = datetime.now().isoformat(timespec="seconds")
            write_json(out / "result.json", r)
        log(out, f"{a.job}: done ({'heldout' if a.heldout else r.get('status')})")
        return 0
    except SystemExit:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        log(out, f"{a.job}: FAILED {type(e).__name__}: {e}")
        if not a.heldout:
            write_json(out / "result.json", {"job": a.job, "status": "failed",
                                             "error": f"{type(e).__name__}: {e}", "traceback": tb[-3000:],
                                             "finished_at": datetime.now().isoformat(timespec="seconds")})
        else:
            write_json(out / "heldout.json", {"job": a.job, "error": f"{type(e).__name__}: {e}",
                                              "traceback": tb[-3000:]})
        return 1


if __name__ == "__main__":
    sys.exit(main())
