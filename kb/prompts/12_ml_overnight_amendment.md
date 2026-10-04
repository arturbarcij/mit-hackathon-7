# 12 ML overnight amendment (lead, Sun 4 Oct, 00:25 CEST)

Paste into the ml Cursor chat now, before 01:00. It changes tonight's sweep. Log it in `kb/DECISIONS.md` as a correction made before any held-out result was seen.

## Why (measured by the lead on the shipped v1; scripts in `kb/edge/`)
- **BRACOL test** (whole leaf on a plain background, our closest proxy for the paper protocol), n=175: coverage 0.54, selective accuracy 0.90. Healthy accepted 0 of 12. Rust 35 of 69 accepted, all correct. Phoma 50 of 55 accepted, all correct. Cercospora and miner: all 9 accepted predictions were wrong.
- **Simulated 10-leaf plots** on BRACOL val, through `rules.json`: a healthy plot gets "too many unsure" 100% of the time. A plot with 10 rust leaves gets the spray card 12% of the time.
- **Field photos** (random 420 from Uganda, 48 iNaturalist Hemileia): 284 of 468 confidently wrong. 77 of 143 healthy Ugandan leaves flagged as a disease. Rust found on 0 of 189.
- **PLAN.md cannot pick a winner.** A candidate must pass int8 parity, and MobileNetV3 int8 parity fails (v1: 4 to 34%). v1 itself shipped fp16.

Conclusion: in-domain coverage is the wrong target. The deployment domain is a whole leaf on a plain page.

## Changes
1. **Qualify on fp16, as v1.** fp16 `leaf.onnx` at most 5 MB, and fp16 vs PyTorch top-1 agreement at least 95% on 50 test images. Drop the int8 condition.
2. **Primary metric:** BRACOL val coverage at 90% selective accuracy, after temperature scaling fitted on BRACOL val. Guards: in-domain val macro F1 at most 2 points below v1; BRACOL val healthy recall above 0. Tie-break: BRACOL val macro F1. Replace v1 only if the winner beats it by 5 points of BRACOL val coverage.
3. **New job D `protocol`, run next (before B):**
   - Make `sweep/manifest_protocol.csv` from `manifest_v1.csv`. Move the 203 BRACOL `unused_capped` rows (69 healthy, 134 miner) to `train`. They were never in val or test, so the split stays clean. Repeat every BRACOL train row 10 times, or use a weighted sampler with weight 10 if `train.py` supports one.
   - `train.py --arch mobilenetv3_small_100 --aug sheet --manifest sweep/manifest_protocol.csv --run-dir sweep/protocol/run --no-global --epochs 8 --patience 2`
   - Fit temperature and threshold on BRACOL val rows only.
4. **Optional job E:** D with `mobilenetv3_large_075`, only if its fp16 export is at most 4.5 MB.
5. Keep job A (`sheet`) and score it with the new rule. Skip B if E runs.
6. Do not train on Uganda, iNaturalist or RoCoLe. If you have 5 minutes before 01:00, start the RoCoLe annotation download so we can score it in the morning.

## 06:30
- Apply the rule. Write `sweep/SUMMARY.md` (5 lines).
- Run `python kb/edge/field_check.py --model <folder with the winner's leaf.onnx and model.json>`, then the same with `--model app/public/model` for v1. Paste both `summary.md` tables into `EVALUATION.md` under "Field check (plot level)". Report BRACOL test once.
- If the winner is not exported, parity-checked and handed to engine by 08:00, keep v1.
- Reply in five lines: done, not done, blocked on, unsure about, next.
