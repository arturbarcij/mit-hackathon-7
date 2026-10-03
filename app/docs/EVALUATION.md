# Evaluation

Does the leaf model work, on which data, and where does it fail?

Status: skeleton. The ml agent owns every number in this file. The model is not trained yet, so there are no results. Nothing below is a result until it names its test set and links to `app/ml/metrics.json`.

Rule for this file: never show an accuracy number without naming the test set. Show the cross-domain numbers even when they are worse.

Test sets (details in `DATA_CARD.md`):
- **In-domain:** held-out split of JMuBEN, JMuBEN2 and BRACOL, after near-duplicate grouping.
- **Cross-country:** Uganda coffee leaf dataset, de-duplicated, healthy, rust and Phoma only. Never trained on.
- **Field conditions:** RoCoLe (Ecuador, Robusta, leaves on the plant), healthy versus rust. Never trained on.
- **Out of distribution:** non-coffee leaves and random photos.

## 1. In-domain accuracy and per-class F1

Test set: JMuBEN + JMuBEN2 + BRACOL held-out split.

Pending ml (M5). Table to fill: class, number of test images, precision, recall, F1. Plus overall accuracy and macro F1.

## 2. Cross-domain results

Pending ml (M5).

| Test set | Classes scored | Images after de-duplication | Accuracy | Macro F1 |
|---|---|---|---|---|
| Uganda | healthy, rust, Phoma | pending ml | pending ml | pending ml |
| RoCoLe | healthy, rust | pending ml | pending ml | pending ml |

Expected to be worse than in-domain. That gap is the honest measure of how the model may do on Noor's leaves.

## 3. Selective prediction: accuracy against coverage

Pending ml (M3, M5).
- Calibration method: temperature scaling on the validation split. Temperature: pending ml.
- Chosen threshold: pending ml.
- Coverage (share of leaves the model answers) and accuracy on those leaves, at the threshold, for each test set: pending ml.
- Curve image: pending ml.

## 4. Out-of-distribution rejection

Pending ml (M3).
- Share of non-coffee leaves (PlantDoc test images, not used in training) labelled `not_leaf` or unsure: pending ml.
- Share of random non-leaf photos labelled `not_leaf` or unsure: pending ml.

## 5. Model size, bundle size, inference time, airplane mode

Model figures pending ml (M4) and engine (E3).

| Item | Target | Measured | Measured with |
|---|---|---|---|
| `leaf.onnx` (int8) | at most 3 MB, hard cap 5 MB | pending ml | |
| Offline bundle (app, model, audio) | at most 15 MB | pending engine with real model | |
| Download time at 1 Mbit/s | | pending | |
| Inference per leaf | under 1 s | pending engine with real model | |
| Airplane mode, full check | works | pending real model and UI | |

Engine figures measured so far with a test fixture model (not coffee) are in `ARCHITECTURE.md`. They show the pipeline works offline. They say nothing about leaf accuracy.

## 6. Confusion matrix

Pending ml (M5). Image path to add: `app/ml/` (one per test set).

## 7. Worked examples

Pending ml and ui. Five examples, at least two abstentions.

| # | Photo | Test set or source | Prediction | Confidence | Answer card |
|---|---|---|---|---|---|
| 1 | pending | | | | |
| 2 | pending | | | | |
| 3 | pending | | | | |
| 4 (abstention) | pending | | | | |
| 5 (abstention) | pending | | | | |

## 8. What these numbers do and do not prove

Pending ml. To be written once the numbers exist, in plain language: what the in-domain score measures (mostly one Kenyan farm and its preprocessing), what the cross-domain scores suggest for Noor, what the abstention rate costs her (more referrals), and what no test here covers (Kenyan varieties, leaves on the tree, night photos, berries).
