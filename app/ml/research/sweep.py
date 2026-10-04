"""Jani overnight research queue: pre-registered jobs, a val-only selection rule, held-out sets scored once.

Run from app/ml with the jani env:
  python research/sweep.py --smoke     # about 3 minutes on CPU; checks the whole path on tiny subsets
  python research/sweep.py             # the overnight queue; waits for v1 to finish first
  python research/sweep.py --status    # where the queue is

What it does, in order:
  1. Waits until v1 is trained and evaluated (ml/calibration.json, its checkpoint, a newer ml/metrics.json).
  2. Freezes v1's split (research/manifest_frozen.csv) and refreshes held-out rows from disk.
  3. Writes PLAN.md: the rule from plan.py, its sha256 and the val-set hash. Refuses to go on
     if plan.py changed after that.
  4. Runs jobs one after another, each in its own process: v1 (re-scored), protocol, mnv4,
     replicate, then combo if the rule allows. Starts no job after --no-start-after and
     stops at --stop-at. Resumes where it left off if restarted.
  5. Applies the rule and writes selection.json (once).
  6. Scores v1 and the winner on Uganda, RoCoLe and wild photos (once) and writes heldout.json.
  7. Writes SUMMARY.md and results.csv.
It never writes outside research/ and never touches public/model/, ml/calibration.json,
ml/metrics.json or docs/EVALUATION.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ML = HERE.parent
for p in (str(ML), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import data as rdata  # noqa: E402
import plan  # noqa: E402
from common import ROOT  # noqa: E402

RESULT_COLS = ["job", "status", "arch_used", "aug", "bracol_weight", "seed", "epochs_run", "minutes",
               "val_acc", "val_macro_f1", "cov95", "threshold95", "temperature", "bracol_n", "bracol_acc",
               "int8_bytes", "parity_int8", "cpu_ms", "note"]


class Sweep:
    def __init__(self, a: argparse.Namespace):
        self.a = a
        self.run = HERE / ("smoke" if a.smoke else a.run_name)
        self.run.mkdir(parents=True, exist_ok=True)
        self.start = datetime.now()
        self.no_start_after = next_time(a.no_start_after, self.start)
        self.stop_at = next_time(a.stop_at, self.start)
        if a.smoke:
            self.no_start_after = self.start + timedelta(minutes=30)
            self.stop_at = self.start + timedelta(minutes=40)

    # ------------------------------------------------------------------ utils
    def log(self, msg: str) -> None:
        line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        with (self.run / "sweep.log").open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def jobdir(self, job: str) -> Path:
        return self.run / "runs" / job

    def result(self, job: str) -> dict | None:
        p = self.jobdir(job) / "result.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def results(self) -> dict[str, dict]:
        return {j: r for j in plan.ORDER if (r := self.result(j))}

    # ------------------------------------------------------------------ steps
    def wait_for_v1(self) -> None:
        cal, met = ML / "calibration.json", ML / "metrics.json"
        if self.a.smoke:
            return
        until = next_time(self.a.wait_v1_until, self.start)
        while True:
            try:
                ready = cal.exists() and (ROOT / json.loads(cal.read_text(encoding="utf-8"))["best_checkpoint"]).exists()
            except (ValueError, KeyError, OSError):  # being rewritten right now
                ready = False
            evaluated = ready and met.exists() and met.stat().st_mtime > cal.stat().st_mtime
            if ready and evaluated:
                self.log("v1 is trained and evaluated")
                return
            if datetime.now() >= until:
                if ready:
                    self.log("v1 trained but eval.py has not finished; starting anyway (eval and sweep share the machine)")
                    return
                raise SystemExit("v1 checkpoint not found by --wait-v1-until; nothing to compare against")
            self.log("waiting for v1 (calibration.json, checkpoint and a newer metrics.json)")
            time.sleep(60)

    def prepare_data(self) -> dict:
        meta = rdata.freeze()
        if meta.get("drift"):
            self.log("WARNING: ml/manifest.csv pool split differs from the frozen copy (manifest.py re-run?). "
                     "The queue uses the frozen copy, which is v1's split.")
        try:
            merged = rdata.merge_heldout(write_ml_manifest=False)
            self.log(f"held-out rows on disk: {json.dumps(merged['heldout'])}")
        except SystemExit:
            raise
        except Exception as e:  # held-out refresh must not block the queue
            self.log(f"held-out refresh skipped: {type(e).__name__}: {e}")
        return meta

    def preregister(self, meta: dict) -> None:
        plan_sha = sha256(HERE / "plan.py")
        trainer_sha = sha256(HERE / "trainer.py")
        rec = self.run / "plan_lock.json"
        if rec.exists():
            lock = json.loads(rec.read_text(encoding="utf-8"))
            if lock["plan_sha256"] != plan_sha:
                raise SystemExit("plan.py changed after pre-registration. Start a new run: --run-name <new>")
            self.log(f"plan lock OK (written {lock['written_at']})")
            return
        lock = {"written_at": datetime.now().isoformat(timespec="seconds"), "plan_version": plan.PLAN_VERSION,
                "plan_sha256": plan_sha, "trainer_sha256": trainer_sha,
                "val_paths_sha256": meta["pool"]["val"], "frozen_manifest_sha256": sha256(rdata.FROZEN),
                "smoke": self.a.smoke}
        rec.write_text(json.dumps(lock, indent=2), encoding="utf-8")
        jobs = "\n".join(f"- **{j}** ({plan.JOBS[j]['kind']}): {plan.JOBS[j]['why']}" for j in plan.ORDER)
        text = (f"# Overnight research plan ({plan.PLAN_VERSION})\n\n"
                f"Pre-registered at {lock['written_at']} local time, before any job ran"
                f"{' (SMOKE RUN: tiny subsets, numbers mean nothing)' if self.a.smoke else ''}.\n\n"
                f"- plan.py sha256: `{plan_sha}`\n- trainer.py sha256: `{trainer_sha}`\n"
                f"- val paths sha256: `{lock['val_paths_sha256']}`\n- frozen manifest sha256: `{lock['frozen_manifest_sha256']}`\n"
                f"- no job starts after {self.no_start_after:%a %H:%M}; everything stops at {self.stop_at:%a %H:%M}\n\n"
                f"## Jobs\n{jobs}\n\nAll jobs: seed as listed, {plan.EPOCHS} epochs, patience {plan.PATIENCE}, "
                f"batch {plan.BATCH}, AdamW lr {plan.LR}, frozen v1 split.\n\n## Rule\n\n{plan.RULE_TEXT}")
        (self.run / "PLAN.md").write_text(text, encoding="utf-8")
        self.log("PLAN.md written (pre-registration)")

    def run_job(self, job: str, extra: list[str] | None = None) -> dict:
        d = self.jobdir(job)
        d.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, "-u", str(HERE / "trainer.py"), "--job", job, "--out", str(d),
               "--deadline", self.stop_at.isoformat(timespec="seconds"), "--device", self.a.device,
               "--workers", str(self.a.workers)] + (["--smoke"] if self.a.smoke else []) + (extra or [])
        timeout = max(60.0, (self.stop_at - datetime.now()).total_seconds() + 600)
        self.log(f"start {job}")
        with (d / "stdout.log").open("a", encoding="utf-8") as f:
            try:
                rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(ML), timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                rc = -9
        r = self.result(job) or {"job": job, "status": "failed", "error": f"no result.json (exit {rc})"}
        if rc == -9 and r.get("status") != "ok":
            r.update(status="truncated", error="killed at stop time")
            (d / "result.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        self.log(f"end {job}: {r.get('status')} cov95={fmt(r.get('cov95'))} bracol={fmt(r.get('bracol_acc'))} "
                 f"int8={r.get('int8_bytes')} parity={fmt(r.get('parity_int8'))} ({r.get('minutes')} min)")
        self.write_results_csv()
        return r

    def run_jobs(self) -> None:
        for job in plan.ORDER:
            existing = self.result(job)
            if existing and (existing.get("status") in ("ok", "skipped") or not self.a.retry_failed):
                self.log(f"skip {job}: result exists ({existing.get('status')})")
                continue
            if job != "v1" and datetime.now() >= self.no_start_after:  # the baseline always runs (a few minutes)
                self.write_skip(job, f"not started: past {self.no_start_after:%H:%M}")
                continue
            if plan.JOBS[job]["kind"] == "combo":
                cfg = plan.combo_config(self.results())
                if cfg is None:
                    self.write_skip(job, "rule: combo runs only if protocol and mnv4 both beat v1")
                    continue
                self.jobdir(job).mkdir(parents=True, exist_ok=True)
                (self.jobdir(job) / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            r = self.run_job(job)
            if job == "v1" and r.get("status") != "ok":
                raise SystemExit("baseline v1 failed; see runs/v1/stdout.log. Nothing to compare against.")

    def write_skip(self, job: str, reason: str) -> None:
        d = self.jobdir(job)
        d.mkdir(parents=True, exist_ok=True)
        (d / "result.json").write_text(json.dumps({"job": job, "status": "skipped", "reason": reason}, indent=2),
                                       encoding="utf-8")
        self.log(f"skip {job}: {reason}")
        self.write_results_csv()

    def select(self) -> dict:
        p = self.run / "selection.json"
        if p.exists():
            self.log("selection.json exists; not re-selecting")
            return json.loads(p.read_text(encoding="utf-8"))
        lock = json.loads((self.run / "plan_lock.json").read_text(encoding="utf-8"))
        if sha256(HERE / "plan.py") != lock["plan_sha256"]:
            raise SystemExit("plan.py changed since pre-registration; refusing to select")
        res = self.results()
        sel = plan.select(res)
        sel.update(selected_at=datetime.now().isoformat(timespec="seconds"), plan_sha256=lock["plan_sha256"],
                   heldout_used=False, smoke=self.a.smoke,
                   metrics={j: {k: r.get(k) for k in ("status", "cov95", "bracol_acc", "val_macro_f1",
                                                     "int8_bytes", "parity_int8", "arch_used")}
                            for j, r in res.items()})
        p.write_text(json.dumps(sel, indent=2), encoding="utf-8")
        self.log(f"SELECTED {sel['winner']}: {sel['reason']} (margin {sel['margin_pp']} pp; {sel.get('margin_note')})")
        return sel

    def heldout(self, sel: dict) -> dict:
        p = self.run / "heldout.json"
        if p.exists():
            self.log("heldout.json exists; held-out sets are scored once only")
            return json.loads(p.read_text(encoding="utf-8"))
        jobs = ["v1"] + ([sel["winner"]] if sel["winner"] != "v1" else [])
        out = {"scored_at": datetime.now().isoformat(timespec="seconds"), "selected_at": sel["selected_at"],
               "winner": sel["winner"], "jobs": {}}
        for job in jobs:
            self.log(f"held-out scoring: {job}")
            d = self.jobdir(job)
            cmd = [sys.executable, "-u", str(HERE / "trainer.py"), "--job", job, "--out", str(d), "--heldout",
                   "--run-dir", str(self.run), "--device", self.a.device] + (["--smoke"] if self.a.smoke else [])
            with (d / "stdout.log").open("a", encoding="utf-8") as f:
                try:
                    subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(ML), timeout=3600)
                except subprocess.TimeoutExpired:
                    self.log(f"held-out scoring for {job} timed out after 60 min")
            hp = d / "heldout.json"
            out["jobs"][job] = json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else {"error": "no output"}
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        return out

    def write_results_csv(self) -> None:
        rows = []
        for j in plan.ORDER:
            r = self.result(j)
            if not r:
                continue
            cfg = r.get("config") or plan.JOBS.get(j, {})
            rows.append({
                "job": j, "status": r.get("status"), "arch_used": r.get("arch_used", ""),
                "aug": cfg.get("aug", ""), "bracol_weight": cfg.get("bracol_weight", ""), "seed": cfg.get("seed", ""),
                "epochs_run": r.get("epochs_run", ""), "minutes": r.get("minutes", ""),
                **{k: r.get(k, "") for k in ("val_acc", "val_macro_f1", "cov95", "threshold95", "temperature",
                                             "bracol_n", "bracol_acc", "int8_bytes", "parity_int8", "cpu_ms")},
                "note": r.get("reason") or r.get("error") or "",
            })
        with (self.run / "results.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=RESULT_COLS)
            w.writeheader()
            w.writerows(rows)

    def summary(self, sel: dict, held: dict | None) -> None:
        res = self.results()
        L = [f"# Overnight research summary{' (SMOKE: numbers mean nothing)' if self.a.smoke else ''}", "",
             f"Run folder `app/ml/research/{self.run.name}/`. Plan pre-registered in PLAN.md. "
             f"Selection uses in-domain val only (JMuBEN, JMuBEN2, BRACOL, negatives).", "",
             "| Job | Status | Backbone | Coverage at 95% (val) | BRACOL val acc | int8 | Parity | CPU ms |",
             "|---|---|---|---|---|---|---|---|"]
        for j in plan.ORDER:
            r = res.get(j)
            if not r:
                continue
            L.append(f"| {j} | {r.get('status')} | {r.get('arch_used', '')} | {pct(r.get('cov95'))} | "
                     f"{pct(r.get('bracol_acc'))} | {mb(r.get('int8_bytes'))} | {pct(r.get('parity_int8'))} | "
                     f"{r.get('cpu_ms', '')} |")
        L += ["", f"**Decision: {sel['winner']}.** {sel['reason']}. Margin {sel.get('margin_pp')} pp "
                  f"({sel.get('margin_note', '')}).", ""]
        for c in sel.get("candidates", []):
            L.append(f"- {c['job']}: qualifies={c['qualifies']}, coverage {c.get('d_cov_pp', 'n/a')} pp, "
                     f"BRACOL {c.get('d_bracol_pp', 'n/a')} pp, beats v1: {c['beats']} "
                     f"{'(' + '; '.join(c['problems']) + ')' if c['problems'] else ''}")
        if held:
            L += ["", "## Held-out (scored once, after the decision)", "",
                  "| Model | Set | n | Top-1 acc | Coverage at threshold | Acc on accepted |", "|---|---|---|---|---|---|"]
            for job, h in held.get("jobs", {}).items():
                for src, e in (h.get("sources") or {}).items():
                    L.append(f"| {job} | {src} | {e.get('n')} | {pct(e.get('top1_acc'))} | "
                             f"{pct(e.get('coverage_at_threshold'))} | {pct(e.get('acc_on_accepted'))} |")
            L += ["", "Uganda and RoCoLe images were never used for training or for the choice. "
                      "Numbers on sets with missing classes say nothing about those classes."]
        L += ["", "## Next (06:30)",
              "- If the decision is v1: nothing to ship; copy the table into EVALUATION.md as the ablation.",
              f"- If a candidate won: export `runs/{sel['winner']}/leaf_int8.onnx` as leaf.onnx with its "
              "threshold95 and temperature in model.json, regenerate parity samples, and have engine confirm "
              "under 1 s per leaf at 4x CPU throttling. Not done by 08:00: keep v1."]
        (self.run / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
        self.log("SUMMARY.md written")

    def status(self) -> None:
        print(f"run folder: {self.run}")
        for j in plan.ORDER:
            r = self.result(j)
            print(f"  {j:10s} {r.get('status') if r else '-':10s} cov95={fmt(r.get('cov95')) if r else ''}")
        for f in ("plan_lock.json", "selection.json", "heldout.json", "SUMMARY.md"):
            print(f"  {f}: {'yes' if (self.run / f).exists() else 'no'}")

    def main(self) -> int:
        if self.a.status:
            self.status()
            return 0
        keep_awake()
        self.log(f"sweep start (smoke={self.a.smoke}, device={self.a.device}); no start after "
                 f"{self.no_start_after:%a %H:%M}, stop at {self.stop_at:%a %H:%M}")
        guarded = [ML.parent / "public" / "model" / "leaf.onnx", ML.parent / "public" / "model" / "model.json",
                   ML / "calibration.json", ML / "metrics.json", ML.parent / "docs" / "EVALUATION.md"]
        before = {str(p): p.stat().st_mtime if p.exists() else None for p in guarded}
        self.wait_for_v1()
        meta = self.prepare_data()
        self.preregister(meta)
        self.run_jobs()
        sel = self.select()
        held = None
        if not self.a.no_heldout:
            held = self.heldout(sel)
        self.summary(sel, held)
        if self.a.smoke:
            return self.smoke_report(before, guarded, held)
        self.log("sweep done")
        return 0

    def smoke_report(self, before: dict, guarded: list[Path], held: dict | None) -> int:
        problems = []
        for job in ("v1", "protocol", "mnv4", "replicate"):
            r = self.result(job) or {}
            if r.get("status") != "ok":
                problems.append(f"{job}: {r.get('status')} {r.get('error', '')[:200]}")
                continue
            if not r.get("fake"):
                if not (self.jobdir(job) / "leaf_int8.onnx").exists():
                    problems.append(f"{job}: no int8 model")
                if r.get("parity_int8") is None:
                    problems.append(f"{job}: no parity")
            self.log(f"smoke {job}: arch={r.get('arch_used')} cov95={fmt(r.get('cov95'))} "
                     f"int8={mb(r.get('int8_bytes'))} parity={pct(r.get('parity_int8'))}")
        if not (self.run / "selection.json").exists():
            problems.append("no selection.json")
        if held is None or not held.get("jobs"):
            problems.append("no held-out output")
        else:
            for job, h in held["jobs"].items():
                if h.get("error"):
                    problems.append(f"held-out {job}: {h['error'][:200]}")
        for p in guarded:
            now = p.stat().st_mtime if p.exists() else None
            if now != before[str(p)]:  # the harness never writes these; the ml lane may have, during the smoke run
                self.log(f"note: {p.name} changed during the smoke run (not written by the harness)")
        if problems:
            self.log("SMOKE FAILED:\n  - " + "\n  - ".join(problems))
            return 1
        self.log("SMOKE OK: every step ran on tiny subsets; shipped files untouched. Ready for the overnight run.")
        return 0


def keep_awake() -> None:
    """Ask Windows not to sleep while this process runs (reverts when it exits). No settings change."""
    if os.name != "nt":
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    except Exception:
        pass


def next_time(hhmm: str, ref: datetime) -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    t = ref.replace(hour=h, minute=m, second=0, microsecond=0)
    return t if t > ref else t + timedelta(days=1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt(x) -> str:
    return "n/a" if x is None or x == "" else f"{float(x):.3f}"


def pct(x) -> str:
    return "n/a" if x is None or x == "" else f"{100 * float(x):.1f}%"


def mb(x) -> str:
    return "n/a" if not x else f"{int(x) / 1024 / 1024:.2f} MB"


def parse(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true", help="tiny subsets, 1 epoch, CPU unless --device says otherwise")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--run-name", default="overnight")
    ap.add_argument("--device", default=None, help="auto | cuda | cpu (default: auto; cpu for --smoke)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--no-start-after", default="05:00")
    ap.add_argument("--stop-at", default="06:15")
    ap.add_argument("--wait-v1-until", default="02:00")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--no-heldout", action="store_true")
    a = ap.parse_args(argv)
    if a.device is None:
        a.device = "cpu" if a.smoke else "auto"
    return a


if __name__ == "__main__":
    sys.exit(Sweep(parse()).main())
