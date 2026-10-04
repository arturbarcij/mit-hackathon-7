# EVALUATION

Owner: ml agent. Numbers come from `app/ml/eval.py` on the v1 model. Plain British English.

Every accuracy figure names its test set. Uganda and RoCoLe were never used for training.

## 1. In-domain test (JMuBEN + JMuBEN2 + BRACOL + PlantDoc held-out split)

- Images: 6714
- Accuracy: 0.970 on the in-domain test split
- Macro F1: 0.969 on the in-domain test split

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| healthy | 0.997 | 0.997 | 0.997 | 1321 |
| rust | 0.989 | 0.993 | 0.991 | 1221 |
| cercospora | 0.993 | 0.989 | 0.991 | 1458 |
| phoma | 0.919 | 0.924 | 0.921 | 1103 |
| miner | 0.924 | 0.927 | 0.925 | 1109 |
| not_leaf | 0.998 | 0.980 | 0.989 | 502 |

Confusion matrix: `app/ml/plots/cm_indomain.png`.

## 2. Cross-domain (held-out; never trained on)

### Uganda coffee leaf set (Soroti; smartphone; augmented copies may be present)

- Images scored: 424. Only the `1_*` (healthy) prefix was on disk. Rust (`1200_*`) and phoma (`2300_*`) had not finished downloading. So this is a healthy-only slice, not the full set.
- Accuracy: 0.017 on this Uganda healthy slice
- Macro F1 (shared classes): 0.005 on this Uganda healthy slice
- The model almost never called these whole-leaf phone photos `healthy`. Training images are cropped to the lesion. That gap is expected and is why the app uses a sheet-of-paper protocol.

### RoCoLe (Ecuador, Robusta, field)

NOT RUN. Images were not on disk at evaluation time. They are held-out and were never used for training.

## 3. Selective prediction

- Temperature: 3.500
- Confidence threshold: 0.583
- In-domain val accuracy on accepted cases: 0.952
- Coverage at that threshold (in-domain val): 0.940
- In-domain test accuracy on accepted cases: 0.975
- Coverage at that threshold (in-domain test): 0.934

Curve: `app/ml/plots/coverage_val.png`.

## 4. Out-of-distribution

- `not_leaf` in-domain test: abstain or predict not_leaf on 0.998 of 502 images
- RoCoLe red spider mite (OOD probe): abstain or predict not_leaf on 0.000 of 0 images

## 5. Size and latency

- `leaf.onnx`: 3,077,051 bytes (2.93 MB). **fp16 weights**, not int8. Static int8 QDQ and dynamic int8 both collapsed top-1 parity to under 35% on MobileNetV3-Small h-swish. fp16 matched PyTorch on 50/50 test images. Hard cap is 5 MB; we are under it.
- CPU latency (onnxruntime, 1 thread, median of 30 images): 5 ms per leaf
- Device: measured on the training laptop CPU, not a field Android. Field latency is still to measure.

## 6. Worked examples

Images and top-3 probabilities are in `app/ml/examples/`. Two of the five are abstentions.

- `ex_00.jpg`  true=rust  pred=rust  conf=0.527  ABSTAIN  top3={'rust': 0.5269, 'miner': 0.4118, 'phoma': 0.0447}
- `ex_01.jpg`  true=healthy  pred=healthy  conf=0.385  ABSTAIN  top3={'healthy': 0.3849, 'phoma': 0.1959, 'miner': 0.1336}
- `ex_02.jpg`  true=miner  pred=miner  conf=0.999  accept  top3={'miner': 0.9994, 'cercospora': 0.0003, 'phoma': 0.0003}
- `ex_03.jpg`  true=phoma  pred=phoma  conf=0.885  accept  top3={'phoma': 0.885, 'not_leaf': 0.1037, 'cercospora': 0.0084}
- `ex_04.jpg`  true=phoma  pred=phoma  conf=0.962  accept  top3={'phoma': 0.9617, 'miner': 0.0218, 'not_leaf': 0.0138}

## 7. What these numbers prove, and what they do not

These figures show that a small ImageNet-pretrained MobileNetV3-Small, fine-tuned on Kenyan JMuBEN/JMuBEN2 crops plus whatever BRACOL leaves we could extract, can separate the six training labels on a hash-grouped in-domain split. They do not show field accuracy on whole leaves still on the tree, on Kenyan varieties that are not labelled in the source sets, or on mixed infections. JMuBEN images are cropped to the lesion and were augmented without a source-image manifest; near-duplicate hashing reduces leakage but cannot remove it. The Uganda set is itself augmented, so a high number there would still not be a clean cross-country test. RoCoLe is Robusta, not Arabica, and is a field set. We do not report PlantVillage coffee accuracy because that set has no coffee. A single-leaf score is not a plot decision; the app uses ten leaves and abstains when confidence is low.
