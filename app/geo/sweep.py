"""Robustness sweep: rebuild the synthetic registry with many seeds and score the model.

Real NDVI and rainfall stay fixed; only the synthetic plots, deliveries and noise
change. Writes data/sweep.json. Does not touch the committed outputs.
"""
import contextlib
import io
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

import config as C
import make_plots
import outliers
import visit_plan

N_SEEDS = 30


def main():
    real_data, real_out = C.DATA, C.OUT
    rain = (real_data / "rainfall.json").read_text()
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        C.DATA, C.OUT = Path(tmp) / "data", Path(tmp) / "out"
        C.DATA.mkdir()
        (C.DATA / "rainfall.json").write_text(rain)
        (C.DATA / "season_support.json").write_text((real_data / "season_support.json").read_text())
        for k in range(N_SEEDS):
            C.SEED = 1000 + k
            with contextlib.redirect_stdout(io.StringIO()):
                make_plots.main()
                outliers.main()
                visit_plan.main()
            e = json.loads((C.DATA / "eval.json").read_text())
            e["visit"] = json.loads((C.DATA / "visit_eval.json").read_text())
            rows.append(e)
        C.DATA, C.OUT = real_data, real_out

    hit = np.array([e["matchedExpected"] / e["plots"] for e in rows])
    caught = np.array([e["plantedCaught"] / e["planted"] for e in rows])
    false_flags = np.array([e["normalFlagged"] for e in rows])
    top8 = np.array([e["visit"]["precisionRecall"]["top8"]["precision"] for e in rows])
    saving = np.array([e["visit"]["route"]["savingPct"] for e in rows])
    per_scenario: dict = {}
    for e in rows:
        for k, v in e["confusion"].items():
            per_scenario[k] = per_scenario.get(k, 0) + v
    res = {
        "synthetic": True,
        "note": "Each seed rebuilds the synthetic registry and noise. Real NDVI and rainfall are fixed.",
        "seeds": N_SEEDS,
        "matchedExpected": {"mean": round(float(hit.mean()), 3), "min": round(float(hit.min()), 3)},
        "plantedCaught": {"mean": round(float(caught.mean()), 3), "min": round(float(caught.min()), 3)},
        "normalFlagged": {"mean": round(float(false_flags.mean()), 2), "max": int(false_flags.max()),
                          "outOf": rows[0]["normal"]},
        "visitPlan": {"precisionTop8": {"mean": round(float(top8.mean()), 2), "min": round(float(top8.min()), 2)},
                      "randomPrecision": rows[0]["visit"]["randomPrecision"],
                      "routeSavingVsRandomOrderPct": {"mean": round(float(saving.mean())), "min": int(saving.min())}},
        "confusionTotals": dict(sorted(per_scenario.items())),
    }
    (C.DATA / "sweep.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
