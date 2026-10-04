# Evaluation

Does the leaf model work, on which data, and where does it fail?

Shipped model: `v2-2026-10-04` (`app/public/model/leaf.onnx`, MobileNetV3-Small, int8). Unless a line says otherwise, every number below comes from `app/ml/metrics.json`, which was produced by:

```
python app/ml/evaluate.py --manifest app/ml/manifest_v2.csv --sets in_domain_test heldout_uganda_test heldout_rocole rocole_red_spider_mite synthetic_blank_pages
```

Inference for these numbers: int8 ONNX in onnxruntime on CPU, the engine's preprocessing, no quality gate. v1 numbers come from `app/ml/runs/v2-cpu-20261003-2317/eval_v1/metrics.json` (v1 re-run on the v2 test sets) and from the original v1 run (`git show 12eace3~1:app/ml/metrics.json`).

Rule for this file: no accuracy number without its test set and its n.

## 1. Summary

- On Ugandan phone photos the model answers 45% of leaves, and it is right on 98.7% of those it answers (Uganda test, n = 1,051). It says "unsure" for the rest.
- It does not work on RoCoLe (leaves on the plant, Ecuador). It answers 2% of photos, and rust recall is 0.030 (n = 1,393). It mostly says "unsure", which is safe but not useful.
- The Uganda test images come from the same farms and capture as the Uganda training images, so this is not a cross-country result. RoCoLe is the only fully independent test set.
- The in-domain score (0.969 accuracy) is inflated by heavy augmentation in the source datasets. It does not predict field performance.
- No test here uses Kenyan farm photos, real phones on a paper sheet, or leaves labelled by an extension officer.

## 2. Test sets

Counts from `app/ml/manifest_v2_stats.json` and `metrics.json`. Dataset facts from `kb/research/DATASETS.md`.

| Test set | Source | Country | Images | Role | Independence |
|---|---|---|---|---|---|
| `in_domain_test` | JMuBEN 3,420, JMuBEN2 5,724, BRACOL 154, PlantDoc 61 | Kenya, Brazil (PlantDoc: web images) | 9,359 | Same-source accuracy, per-class F1 | Low. Split by pHash duplicate group, but the sources are heavily augmented (largest duplicate groups hold 1,800 images). Near-copies of training leaves are likely. In-domain numbers overstate real performance. |
| `heldout_uganda_test` | Uganda coffee leaf dataset (Mendeley k36wnd6knb): healthy 378, rust 356, phoma 317 | Uganda | 1,051 | Phone photos close to our target domain | Partial. 35% of the Uganda set by duplicate group. The other 50% (`uganda_train`) was used to train v2 and 15% (`uganda_calib`) to choose the threshold. Same farms and same capture, so **not a cross-country result**. For v1, which never saw Uganda images, it is held out. |
| `heldout_rocole` | RoCoLe: healthy 791, rust levels 1 to 4 mapped to rust 602 | Ecuador | 1,393 | Field conditions, leaves on the plant | Full. Never used in training, threshold choice or model selection. **The only fully independent set.** Robusta, not Arabica. |
| `not_leaf_test` | PlantDoc non-coffee leaves (rows of `in_domain_test`) | Web images | 61 | Out of distribution: other plants | Same PlantDoc collection as the 285 training negatives. |
| `rocole_red_spider_mite` | RoCoLe red spider mite | Ecuador | 167 | Out of scope: a pest with no class | Full. No class fits, so any accepted disease label is wrong. |
| `synthetic_blank_pages` | SYNTHETIC exercise-book pages with no leaf (`synth.py`) | none | 300 | Out of distribution: empty sheet, pen marks, skin-tone blob | Low. Made by the same generator as the 400 synthetic `not_leaf` pages used in v2 training. |

216 Uganda phoma images were exact or near copies of JMuBEN images and are excluded from every set (`manifest_v2_stats.json`, `excluded_heldout_dup_of_train`).

## 3. Results

### 3.1 v1 against v2 on every set

Definitions. Accuracy and macro F1: top class before abstention, over all images, on the classes the set contains. Abstention rate: share of images below the threshold (shown as "unsure"). Not_leaf share: share whose top class is `not_leaf`. Accepted accuracy and coverage: accuracy on the images above the threshold, and the share of images above it.

Thresholds: v2 0.985 (temperature 0.971). v1 0.298 (temperature 1.241), which is why v1 almost never abstains.

| Test set | Model | n | Accuracy | Macro F1 | Abstention | Not_leaf share | Accepted accuracy | Coverage (n accepted) |
|---|---|---|---|---|---|---|---|---|
| in_domain_test | v1, original run (capped 1,000 per class) | 5,061 | 0.974 | 0.977 | 0.000 | 0.012 | 0.974 | 1.000 (5,061) |
| in_domain_test | v1, re-run | 9,359 | 0.980 | 0.977 | 0.000 | 0.007 | 0.980 | 1.000 (9,359) |
| in_domain_test | **v2** | 9,359 | 0.969 | 0.918 | 0.147 | 0.005 | 0.995 | 0.853 (7,979) |
| Uganda, whole held-out set | v1, original run (capped 1,000 per class) | 2,894 | 0.180 | 0.245 | 0.000 | 0.322 | 0.180 | 1.000 (2,893) |
| heldout_uganda_test | v1, re-run | 1,051 | 0.170 | 0.227 | 0.001 | 0.310 | 0.170 | 0.999 (1,050) |
| heldout_uganda_test | **v2** | 1,051 | 0.838 | 0.866 | 0.547 | 0.039 | 0.987 | 0.453 (476) |
| heldout_rocole | v1 (original and re-run identical) | 1,393 | 0.000 | 0.000 | 0.000 | 0.993 | 0.000 | 1.000 (1,393) |
| heldout_rocole | **v2** | 1,393 | 0.173 | 0.235 | 0.978 | 0.284 | 0.871 | 0.022 (31) |

Out-of-distribution sets are in section 6. Expected calibration error (15 bins), v2: in-domain 0.012, Uganda test 0.042, RoCoLe 0.409.

v2 in-domain accuracy by source: JMuBEN2 0.994 (n = 5,724), JMuBEN 0.942 (n = 3,420), BRACOL 0.734 (n = 154), PlantDoc 0.639 (n = 61). BRACOL is the only phone-camera source in this set, and it is the weakest coffee source.

### 3.2 v2 per class

Top class before abstention.

`in_domain_test` (n = 9,359):

| Class | n | Precision | Recall | F1 |
|---|---|---|---|---|
| healthy | 3,181 | 0.967 | 1.000 | 0.983 |
| rust | 1,336 | 0.991 | 0.948 | 0.969 |
| cercospora | 1,172 | 0.974 | 0.944 | 0.959 |
| phoma | 1,029 | 0.907 | 0.905 | 0.906 |
| miner | 2,580 | 0.985 | 0.985 | 0.985 |
| not_leaf | 61 | 0.796 | 0.639 | 0.709 |

`heldout_uganda_test` (n = 1,051):

| Class | n | Precision | Recall | F1 |
|---|---|---|---|---|
| healthy | 378 | 0.937 | 0.976 | 0.956 |
| rust | 356 | 0.961 | 0.691 | 0.804 |
| phoma | 317 | 0.836 | 0.839 | 0.838 |

Rust is the class the model misses most on Uganda photos. Of 356 rust leaves, 47 were called phoma, 25 healthy, 24 miner and 14 not_leaf. Rust is also the disease that matters most for Noor's spray decision.

On RoCoLe, healthy recall is 0.282 (n = 791) and rust recall is 0.030 (n = 602).

### 3.3 Confusion matrices

Rows are the true class, columns the top predicted class before abstention.

- In-domain test: [confusion_in_domain_test.png](../ml/figures/confusion_in_domain_test.png)
- Uganda test: [confusion_heldout_uganda_test.png](../ml/figures/confusion_heldout_uganda_test.png)
- RoCoLe: [confusion_heldout_rocole.png](../ml/figures/confusion_heldout_rocole.png)

v1 figures for the same sets: `app/ml/runs/v2-cpu-20261003-2317/eval_v1/figures/`.

## 4. How v1 failed and what v2 changed

v1 scored 0.974 on the in-domain test but 0.180 on Ugandan phone photos and 0.000 on RoCoLe, where it called 99.3% of real coffee leaves `not_leaf`. It had learned a shortcut. Every coffee image in training was a clean, cropped leaf, and every `not_leaf` image was a PlantDoc field photo with background. So "there is background" meant "not a coffee leaf". A farmer's real photo of a coffee leaf would have been rejected, or worse, given a confident wrong disease (v1 accepted 125 of 300 blank pages as a disease). v2 changed the data, not the network: coffee crops pasted onto synthetic paper and PlantDoc field backgrounds, 400 synthetic blank pages as `not_leaf`, half of the Uganda set in training with double weight, and a threshold chosen on Ugandan phone photos (Decision 16, run config in `app/ml/runs/v2-cpu-20261003-2317/config.json`).

## 5. Selective prediction

Source: `app/ml/calibration.json` (fitted on PyTorch fp32 logits of `val` plus `uganda_calib`, n = 9,831).

- Temperature: 0.971 (negative log likelihood 0.1098 before, 0.1097 after).
- Threshold: 0.985. Rule: for each split, find the lowest threshold that gives at least 95% accepted accuracy, then take the strictest of these. `val` alone needed only 0.284. `uganda_calib` needed 0.985, at coverage 0.462 and accepted accuracy 0.962 (n accepted 209 of 452).
- A leaf below the threshold is shown as "unsure", whatever its top class.
- Curve: [accuracy_vs_coverage.png](../ml/figures/accuracy_vs_coverage.png). Dots mark the shipped threshold.

Coverage and accepted accuracy at 0.985, by test set:

| Test set | n | Coverage | Accepted accuracy |
|---|---|---|---|
| in_domain_test | 9,359 | 0.853 | 0.995 |
| heldout_uganda_test | 1,051 | 0.453 | 0.987 |
| heldout_rocole | 1,393 | 0.022 | 0.871 (31 accepted, all called healthy) |

### What this does to a 10-leaf check

The plot rule in `app/src/content/rules.json` gives `too_many_unsure` when 3 or more of the leaves are unsure. At 46% per-leaf coverage (Uganda calib), the chance that at least 3 of 10 leaves are unsure is 0.967 (binomial, unsure rate 0.538, assumes leaves are independent). So about 97% of checks on Uganda-like photos would end in "too many unsure". On Uganda test coverage (0.453) the same sum gives 0.971.

The choice of threshold and rule is **pending** (STATUS, "ml to lead"). The options, as written there:

- (A) Keep the per-leaf threshold, change the rule to `uncertain_gte: 6` and decide on the confident leaves only (result in about 53% of checks).
- (B) Threshold 0.691 (90% accepted accuracy, 79% coverage on Uganda calib) and keep `uncertain_gte: 3` (result in about 65% of checks).
- (C) Both (result in about 99%).

Arthur to choose. This file will be updated with the chosen option.

## 6. Out-of-distribution rejection

There is no separate out-of-distribution score. Rejection relies on two things only: the `not_leaf` class and the confidence threshold.

| Test set | Model | n | Unsure or not_leaf | Accepted as a coffee class |
|---|---|---|---|---|
| not_leaf_test (PlantDoc non-coffee leaves) | v1 | 61 | 61 (1.000) | 0 |
| not_leaf_test | v2 | 61 | 60 (0.984) | 1 (phoma) |
| synthetic_blank_pages (SYNTHETIC) | v1 | 300 | 175 (0.583) | 125 (118 rust, 4 miner, 3 phoma) |
| synthetic_blank_pages (SYNTHETIC) | v2 | 300 | 298 (0.993) | 2 (rust) |
| rocole_red_spider_mite | v1 | 167 | 166 (0.994) | 1 (phoma) |
| rocole_red_spider_mite | v2 | 167 | 166 (0.994) | 1 (healthy) |

Two cautions. v1's perfect `not_leaf_test` score is the same shortcut described in section 4: it called almost every field photo `not_leaf`, coffee or not. The blank pages come from the same generator as v2's synthetic training negatives, so the v2 page result is optimistic. There is no test on random photos from a farm (soil, hands, other crops).

## 7. Size and speed

| Item | Target | Measured | Measured with, source |
|---|---|---|---|
| `leaf.onnx` | at most 3 MB, hard cap 5 MB | 1,642,557 bytes (1.64 MB) | v2 int8, `app/public/model/model.json` |
| fp32 ONNX before quantisation | | 6,103,320 bytes | `app/ml/export_report.json` |
| Inference per image, CPU | under 1 s | median 4.342 ms, mean 4.357 ms, p90 4.435 ms (200 runs, 1 thread) | v2 int8, onnxruntime in Python, 4-core x86 cloud VM, `metrics.json` `latency` |
| Decode and preprocess, CPU | | median 26.374 ms | 1600 x 800 BRACOL photo, same machine |
| Inference per leaf, browser | under 1 s | ORT load 0.55 s; 3000 x 2250 photo to result 0.10 to 0.15 s | **fixture model, not coffee**. Chrome 148, 4x CPU throttle. Engine STATUS (`cursor/engine-offline-core-d90f`). No v2 browser timing yet. |
| Offline precache | at most 15 MB | 3.1 MiB | **fixture model, not coffee**, no audio. Engine STATUS. |
| Airplane mode, full check | works | Offline reload and full check pass in Chromium (Playwright) | **fixture model, not coffee**. Engine STATUS E2 and E4. Not yet run with v2 or on a real phone. |

Latency caveat: these are timings on a shared cloud VM (1-minute load average 0.97 at start). The v1 re-run on the same VM under heavier load measured a 7.219 ms mean. They are not phone timings.

Quantisation (Decision 15): weight-only int8 (per-channel symmetric int8 weights for Conv and Gemm, float activations). Agreement of the top class on 50 class-balanced in-domain test images (`export_report.json`):

| Comparison | Weight-only int8 (shipped) | Static int8 (rejected) |
|---|---|---|
| PyTorch against fp32 ONNX | 1.00 | 1.00 |
| PyTorch against int8 ONNX | 1.00 | 0.12 |
| fp32 ONNX against int8 ONNX | 1.00 | 0.12 |
| Relative logit error, int8 | 0.057 | 1.015 |
| File size | 1,642,557 bytes | 1,841,608 bytes |

Largest probability difference between PyTorch and the shipped int8 model on those 50 images: 0.078. Accuracy on the sample: 0.88 for both.

Download time at 1 Mbit/s (1,000,000 bits per second, no protocol overhead):
- Model: 1,642,557 bytes x 8 = 13,140,456 bits. 13,140,456 / 1,000,000 = **13.1 s**.
- Current precache (fixture model): 3.1 MiB = 3.1 x 1,048,576 = 3,250,585.6 bytes. x 8 = 26,004,685 bits, so **26.0 s**. The real bundle with v2 and audio is not measured yet.

## 8. Browser parity

The engine's Playwright test runs the shipped `leaf.onnx` in Chromium on the 10 images in `app/ml/parity_samples/` and compares each class probability with `expected.json` (tolerance 0.02 per class, `app/tests/e2e/offline.spec.ts` on the engine branch). v2 passes. It passed only after the Python reference was changed to downscale with a box filter, which is what Chrome's canvas does (`export.py`, commit `8907a79`). Before that change, sample `09_not_leaf.jpg` differed by 0.048 on phoma. In Node, the engine's preprocessing matches Python within 3e-7 (STATUS M4).

## 9. Worked examples

From `app/ml/parity_samples/expected.json` (v2 int8, engine preprocessing, probabilities after temperature). All ten parity images are from the `test` split. Nine of ten are below the threshold, which fits BRACOL's 0.734 in-domain accuracy (section 3.1).

An "unsure" leaf counts towards the 3-unsure rule. The card is decided per check, not per leaf, so a single leaf cannot fix it.

| # | File (source) | True label | Top class | Confidence | Abstained | Likely answer card |
|---|---|---|---|---|---|---|
| 1 | `05_phoma.jpg` (BRACOL) | phoma | phoma | 0.999 | no | Card depends on the other leaves. If phoma is the main problem and fewer than 3 leaves are unsure, `phoma`. |
| 2 | `02_rust.jpg` (BRACOL) | rust | rust | 0.978 | yes, just under 0.985 | Counts as unsure. Card depends on the other leaves; with 2 more unsure leaves, `too_many_unsure`. |
| 3 | `03_cercospora.jpg` (BRACOL) | cercospora | phoma | 0.652 | yes | Counts as unsure, so the wrong top class is not shown. Card depends on the other leaves. |
| 4 | `09_not_leaf.jpg` (PlantDoc, tomato leaf) | not_leaf | not_leaf | 0.711 | yes | Counts as unsure, not as `not_leaf`. Card depends on the other leaves. |
| 5 | `00_healthy.jpg` (BRACOL) | healthy | healthy | 0.926 | yes | Counts as unsure. `healthy_all` needs zero unsure leaves, so this leaf alone rules it out. Card depends on the other leaves. |

Example 3 shows the threshold doing its job: a wrong answer is held back. Example 5 shows the cost: a correct healthy leaf is held back too.

Accepted examples from the in-domain test are listed in `metrics.json` (`worked_examples`), for example a JMuBEN rust leaf accepted as rust at 1.000.

## 10. What these numbers do not cover, and what we would do next

No test set here covers:
- Kenyan farm photos taken by a farmer's phone. JMuBEN and JMuBEN2 are one Kenyan farm (Mutira, Kirinyaga), one camera, cropped and filtered.
- A leaf photographed on a paper sheet with a real phone. Our paper backgrounds are synthetic.
- Named Kenyan varieties (SL28, Ruiru 11, Batian are not labelled in any set). The Uganda set does not state Arabica or Robusta.
- Coffee berry disease (berries), nutrient deficiencies, wilt and root problems, drought stress, mixed infections, night photos, leaves on the tree with clutter.
- Cercospora and leaf miner outside JMuBEN, JMuBEN2 and BRACOL. The Uganda and RoCoLe sets do not contain them.
- Officer-confirmed labels on local photos.

Other limits:
- The threshold and checkpoint were both chosen on `val` plus `uganda_calib`. Test numbers do not reuse those images, but the choice is tuned to them.
- The threshold was fitted on fp32 PyTorch logits. The shipped model is int8, with probability differences up to 0.078 on 50 images.
- v2 is a short CPU run: fine-tuned from v1 for 3 epochs, and the shipped checkpoint is epoch 1 (`metrics.jsonl`, early stop).

Next steps, in order:
1. Collect photos of local leaves on paper, taken with low-cost phones, and have an extension officer label them. Use them as the test set that counts.
2. Train longer on a GPU, with more phone-photo data and fewer near-duplicate crops.
3. Re-measure size, timing and offline behaviour with v2 and audio on a real Android phone.
4. Add a separate out-of-distribution score if `not_leaf` plus the threshold keep failing on farm photos.
