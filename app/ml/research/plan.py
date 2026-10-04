"""Pre-registered plan for Jani's overnight research queue.

Everything that decides the outcome is in this file: the jobs, the metric, the margins and
the selection rule. sweep.py writes PLAN.md with a sha256 of this file before the first job
starts and refuses to select if the file has changed since. Written by the lead, Sat 3 Oct 2026.
Do not edit once the queue has started; start a new run folder instead (sweep.py --run-name).

Pure Python plus numpy, so it can be tested without torch.
"""
from __future__ import annotations

import numpy as np

PLAN_VERSION = "r1-2026-10-03"

# Jobs run in this order. "v1" re-scores the shipped checkpoint with exactly the same code
# as the candidates, so no comparison depends on train.py's own numbers.
ORDER = ["v1", "protocol", "mnv4", "replicate", "combo"]

JOBS: dict[str, dict] = {
    "v1": {
        "kind": "baseline",
        "why": "Re-score the shipped v1 checkpoint with the same code as every candidate.",
    },
    "protocol": {
        "kind": "train",
        "arch": ["mobilenetv3_small_100"],
        "aug": "sheet",
        "bracol_weight": 6.0,
        "seed": 42,
        "why": "BRACOL photos (whole leaves on a plain background) look like Noor's capture protocol; "
               "JMuBEN images are 128 px close-ups of leaf surface. Oversample BRACOL 6x and add "
               "daylight, shadow and white-balance shifts.",
    },
    "mnv4": {
        "kind": "train",
        "arch": [
            "mobilenetv4_conv_small.e2400_r224_in1k",
            "tf_mobilenetv3_large_075.in1k",
            "mobilenetv3_large_100.ra_in1k",
        ],
        "aug": "v1",
        "bracol_weight": 1.0,
        "seed": 42,
        "why": "A ReLU-only backbone (MobileNetV4) should lose less accuracy in int8 than MobileNetV3's "
               "hard-swish and squeeze-excite blocks. Uses the first name that loads with pretrained "
               "weights and passes the int8 size pre-check.",
    },
    "replicate": {
        "kind": "train",
        "arch": ["mobilenetv3_small_100"],
        "aug": "v1",
        "bracol_weight": 1.0,
        "seed": 43,
        "why": "v1 settings with another seed. Measures run-to-run noise, which sets the margin.",
    },
    "combo": {
        "kind": "combo",
        "why": "protocol's data changes on mnv4's backbone. Runs only if both beat v1.",
    },
}

CANDIDATES = ["protocol", "mnv4", "combo"]  # "replicate" is a noise probe, never a winner

EPOCHS = 8
PATIENCE = 2
BATCH = 96
LR = 3e-4
WEIGHT_DECAY = 0.01
TEMPERATURE_GRID = (0.5, 3.0, 26)  # same grid as train.py

SELECTIVE_ACC = 0.95            # coverage is measured where accuracy on accepted val images is at least this
MIN_MARGIN_PP = 2.0             # floor for the coverage margin, percentage points (assumption)
NOISE_MULT = 2.0                # margin = max(MIN_MARGIN_PP, NOISE_MULT * |v1 - replicate| coverage)
BRACOL_MIN_GAIN_PP = 5.0        # about 2 standard errors on the 173 BRACOL val images
BRACOL_MAX_DROP_PP = 5.0
INT8_CAP_BYTES = 5 * 1024 * 1024
INT8_PRECHECK_BYTES = int(4.5 * 1024 * 1024)
PARITY_MIN = 0.95
FALLBACK_MIN_COVERAGE = 0.30

RULE_TEXT = f"""\
Metric. For each model: temperature-scale on val, sort val images by confidence, and take the
largest share of val (coverage) whose most-confident slice is at least {SELECTIVE_ACC:.0%} accurate.
If no slice reaches {SELECTIVE_ACC:.0%}, coverage is 0. Second metric: plain top-1 accuracy on the
BRACOL rows of val (whole leaves on a plain background, the closest real proxy for Noor's protocol).

Qualify. A candidate qualifies only if its job finished ("ok"), its int8 ONNX is at most
{INT8_CAP_BYTES / 1024 / 1024:.0f} MB and int8 vs PyTorch top-1 agreement is at least {PARITY_MIN:.0%} on 50 test images.

Margin. m = max({MIN_MARGIN_PP} pp, {NOISE_MULT} x |coverage(v1) - coverage(replicate)|). If the replicate
job did not finish, m = {MIN_MARGIN_PP} pp.

Beat v1. A qualifying candidate beats v1 if either
  (a) BRACOL accuracy gains at least {BRACOL_MIN_GAIN_PP} pp and coverage drops by less than m, or
  (b) coverage gains at least m and BRACOL accuracy drops by at most {BRACOL_MAX_DROP_PP} pp.

Choose. Among candidates that beat v1, pick the largest (coverage gain + BRACOL gain) in pp;
ties go to higher val macro F1. If none beats v1, keep v1. "replicate" is never a winner.

Combo. "combo" runs only if both "protocol" and "mnv4" beat v1 under the rule above.

Held-out. Uganda, RoCoLe and wild images play no part in any choice. selection.json is written
first; then v1 and the winner are scored on the held-out sets once, and both are reported.
"""


def coverage_at(conf, correct, target: float = SELECTIVE_ACC) -> tuple[float, float, float]:
    """Largest coverage whose most-confident slice is at least `target` accurate.

    Returns (coverage, threshold, accuracy_on_accepted). Coverage is 0.0 (threshold 1.0,
    accept nothing) when no slice reaches the target.
    """
    conf = np.asarray(conf, dtype=float)
    correct = np.asarray(correct, dtype=float)
    n = len(conf)
    if n == 0:
        return 0.0, 1.0, 0.0
    order = np.argsort(-conf, kind="stable")
    cum = np.cumsum(correct[order]) / np.arange(1, n + 1)
    ok = np.flatnonzero(cum >= target)
    if ok.size == 0:
        return 0.0, 1.0, float(cum[-1])
    k = int(ok[-1]) + 1
    return k / n, float(conf[order][k - 1]), float(cum[k - 1])


def margin_pp(v1: dict, replicate: dict | None) -> tuple[float, str]:
    if not replicate or replicate.get("status") != "ok" or replicate.get("cov95") is None:
        return MIN_MARGIN_PP, f"replicate did not finish; floor of {MIN_MARGIN_PP} pp used"
    noise = abs(float(v1["cov95"]) - float(replicate["cov95"])) * 100
    return max(MIN_MARGIN_PP, NOISE_MULT * noise), f"seed-to-seed coverage difference {noise:.2f} pp"


def qualifies(r: dict) -> tuple[bool, list[str]]:
    problems = []
    if r.get("status") != "ok":
        problems.append(f"status {r.get('status')}")
    b = r.get("int8_bytes")
    if not b or b > INT8_CAP_BYTES:
        problems.append(f"int8 size {b} missing or over cap")
    p = r.get("parity_int8")
    if p is None or p < PARITY_MIN:
        problems.append(f"parity {p} below {PARITY_MIN}")
    return (not problems), problems


def compare(r: dict, v1: dict, m: float) -> dict:
    d_cov = (float(r["cov95"]) - float(v1["cov95"])) * 100
    if r.get("bracol_acc") is None or v1.get("bracol_acc") is None:
        # No BRACOL rows to compare: only route (b) can apply, with no BRACOL guard.
        b = d_cov >= m
        return {"d_cov_pp": round(d_cov, 2), "d_bracol_pp": None, "beats": bool(b),
                "how": "b: in-domain gain (no BRACOL rows)" if b else "no"}
    d_br = (float(r["bracol_acc"]) - float(v1["bracol_acc"])) * 100
    a = d_br >= BRACOL_MIN_GAIN_PP and d_cov > -m
    b = d_cov >= m and d_br >= -BRACOL_MAX_DROP_PP
    return {
        "d_cov_pp": round(d_cov, 2),
        "d_bracol_pp": round(d_br, 2),
        "beats": bool(a or b),
        "how": "a: protocol gain" if a else ("b: in-domain gain" if b else "no"),
    }


def select(results: dict[str, dict]) -> dict:
    """Apply the pre-registered rule. Pure function of the job results."""
    v1 = results.get("v1")
    if not v1 or v1.get("status") != "ok" or v1.get("cov95") is None:
        return {"winner": "v1", "reason": "baseline did not finish; keep v1 by default",
                "margin_pp": None, "candidates": []}
    m, note = margin_pp(v1, results.get("replicate"))
    rows, best = [], None
    for name in CANDIDATES:
        r = results.get(name)
        if not r:
            continue
        ok, problems = qualifies(r)
        row = {"job": name, "status": r.get("status"), "qualifies": ok, "problems": problems}
        if r.get("cov95") is not None:
            row.update(compare(r, v1, m))
            row["beats"] = bool(row["beats"] and ok)
            if row["beats"]:
                key = (row["d_cov_pp"] + (row["d_bracol_pp"] or 0.0), float(r.get("val_macro_f1") or 0.0))
                if best is None or key > best[0]:
                    best = (key, name)
        else:
            row["beats"] = False
        rows.append(row)
    winner = best[1] if best else "v1"
    reason = (f"{winner} beats v1 under the rule" if best else "no candidate beat v1 under the rule; keep v1")
    return {"winner": winner, "reason": reason, "margin_pp": round(m, 2), "margin_note": note,
            "candidates": rows}


def combo_config(results: dict[str, dict]) -> dict | None:
    """Config for the combo job, or None when the rule says skip it."""
    v1 = results.get("v1")
    if not v1 or v1.get("status") != "ok":
        return None
    m, _ = margin_pp(v1, results.get("replicate"))
    p, b = results.get("protocol"), results.get("mnv4")
    for r in (p, b):
        if not r or not qualifies(r)[0] or r.get("cov95") is None or not compare(r, v1, m)["beats"]:
            return None
    return {
        "kind": "train",
        "arch": [b["arch_used"]],
        "aug": JOBS["protocol"]["aug"],
        "bracol_weight": JOBS["protocol"]["bracol_weight"],
        "seed": 42,
        "why": JOBS["combo"]["why"],
    }
