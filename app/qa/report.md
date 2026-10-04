# Jani QA report

Generated 2026-10-03 21:56 local time.

**5 pass, 0 fail, 1 warn, 1 skip**

| Check | Status | Detail |
|---|---|---|
| `ml_integrity:split_frozen` | PASS | ml/manifest.csv still has v1's train/val/test split |
| `ml_integrity:heldout_isolated` | PASS | no Uganda, RoCoLe or wild rows in train/val/test |
| `ml_integrity:no_near_duplicate_leak` | PASS | near-duplicate clusters never cross splits |
| `ml_integrity:heldout_complete` | WARN | cross-domain results cannot speak for missing classes; say so in EVALUATION.md |
| `ml_integrity:calibration` | PASS | threshold 0.583, val coverage 94.2% |
| `ml_integrity:int8_parity` | PASS | int8 vs PyTorch top-1 agreement 1.0 |
| `ml_integrity:preregistration` | skip | research queue has not selected yet |

## Details

### ml_integrity:heldout_complete (warn)
- uganda: missing phoma, rust (have {'healthy': 424})
- rocole: missing healthy, rust (have nothing)

