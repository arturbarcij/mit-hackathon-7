# Evaluation

The leaf model is not trained in this checkout. No accuracy is claimed.

Every metric below is the literal token [PENDING: ml]. When a number is filled in, it will name the test set in the same sentence. Cross-domain results stay in the file even if they are worse than the in-domain split.

The in-domain images are JMuBEN (rust, cercospora, phoma), JMuBEN2 (healthy, miner) and BRACOL (no Phoma class). The Uganda set is augmented, so it is not a clean held-out set. RoCoLe is Robusta, on one farm in Ecuador, and is held out. Details are in [DATA_CARD.md](DATA_CARD.md).

## 1. In-domain test

Held-out split of JMuBEN, JMuBEN2 and BRACOL. Not the Uganda set and not RoCoLe.

| Metric | Test set | Result |
|---|---|---|
| Accuracy | JMuBEN + JMuBEN2 + BRACOL held-out split | [PENDING: ml] |
| Macro F1 | JMuBEN + JMuBEN2 + BRACOL held-out split | [PENDING: ml] |
| Per-class F1, healthy | Same split | [PENDING: ml] |
| Per-class F1, rust | Same split | [PENDING: ml] |
| Per-class F1, cercospora | Same split | [PENDING: ml] |
| Per-class F1, phoma | Same split | [PENDING: ml] |
| Per-class F1, miner | Same split | [PENDING: ml] |
| Per-class F1, not a coffee leaf | Same split | [PENDING: ml] |

## 2. Cross-domain results

Reported on their own. They are not pooled with the in-domain split.

| Metric | Test set | Result |
|---|---|---|
| Accuracy on shared classes | Uganda coffee leaf set (augmented, not a clean held-out set) | [PENDING: ml] |
| Per-class F1 on classes present | Uganda set | [PENDING: ml] |
| Accuracy on shared classes | RoCoLe (Ecuador, Robusta, split by plant) | [PENDING: ml] |
| Rust severity sanity check | RoCoLe | [PENDING: ml] |
| Behaviour on red spider mite | RoCoLe | [PENDING: ml] |

## 3. Selective prediction

Accuracy on accepted cases against coverage, at the chosen threshold.

| Metric | Test set | Result |
|---|---|---|
| Threshold | Validation split used for calibration | [PENDING: ml] |
| Coverage at that threshold | Named with the result | [PENDING: ml] |
| Accuracy on accepted cases | Named with the result | [PENDING: ml] |

## 4. Out-of-distribution rejection

| Metric | Test set | Result |
|---|---|---|
| Rejection rate on non-coffee leaves | PlantDoc, or the negative set actually used | [PENDING: ml] |
| Rejection rate on random photos | Named photo set | [PENDING: ml] |

## 5. Size, latency and airplane mode

| Metric | Condition | Result |
|---|---|---|
| Model file size | Built ONNX file | [PENDING: ml] |
| Offline bundle size | App + model + audio | [PENDING: ml] |
| Inference latency | Device or CPU throttle setting named | [PENDING: ml] |
| Airplane-mode test | After first load | [PENDING: ml] |

Design targets, which are not measurements, are in [ARCHITECTURE.md](ARCHITECTURE.md).

## 6. Confusion matrix

The confusion matrix image is [PENDING: ml]. It will be filed next to this note and captioned with the test set name.

## 7. Worked examples

Five worked examples are [PENDING: ml]. Each will show the photo, the prediction, the confidence and the answer card. At least two will be abstentions. None are available in this checkout.

## 8. What these numbers do and do not prove

No accuracy is claimed until the named test sets are run: the held-out split of JMuBEN, JMuBEN2 and BRACOL; the Uganda coffee leaf set; and RoCoLe. Those runs have not been done here. The model is not trained in this checkout.

An in-domain score, once it exists, will say how the network behaves on held-out images from the sets it trained on, after the duplicate rule. It will not by itself show performance on a Kenyan tree, at night, on a berry problem, or on a named variety. The Uganda number will be a cross-country phone-photo check with a known limit: the set is augmented, so it is not a clean held-out set. The RoCoLe number will be a Robusta field check from one Ecuadorian farm, not an Arabica result from Kenya. Coverage at the threshold will say how often the tool abstains. It is [PENDING: ml] until that curve is computed.
