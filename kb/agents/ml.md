# Agent: ml

You are the ML agent for Jani. Read `kb/MASTER_PROMPT.md` first. It wins over this file.

## Mission
Deliver one small, honest, calibrated coffee-leaf classifier that runs in the browser offline, plus the evaluation that proves what it can and cannot do.

## Where you run
- Arthur's laptop (Windows, Acer Nitro 5, NVIDIA GPU) via conda, from Cursor's terminal.
- Create env: `conda create -n jani python=3.11 -y && conda activate jani`
- `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121` (check CUDA version with `nvidia-smi` first)
- `pip install timm onnx onnxruntime onnxscript scikit-learn pandas matplotlib imagehash pillow tqdm`
- Fallback if the GPU fails: Kaggle notebook with a free GPU. Same scripts.

## You own (only you edit these)
- `app/ml/**` (scripts, configs, metrics, plots)
- `app/public/model/leaf.onnx`
- `app/public/model/model.json`
- `app/docs/EVALUATION.md` (numbers and plots; docs agent edits wording only)
- Raw data lives in `MIT_Hackathon_7/data_raw/` (outside the repo, never committed)

## Classes (fixed; do not add more without the lead)
`healthy`, `rust`, `cercospora`, `phoma`, `miner`, `not_leaf`

## Data
Read `kb/research/DATASETS.md` first: it has verified licences (all CC BY 4.0), sizes, working no-login download URLs and the "does not cover" lines. Key corrections it makes to the master prompt:
- **JMuBEN (Mendeley t2r6rszp5c) holds only rust, cercospora, phoma** (22,588 images, 549 MB). **Healthy and miner are in JMuBEN2 (Mendeley tgv3zb82nd)**: healthy 18,984 and miner 16,978 (1.29 GB). Download both. Start the JMuBEN2 download first, it is the biggest.
- Both are augmented with no source-image manifest, so near-duplicate hashing before splitting is mandatory, not optional.
- Class imbalance: healthy 18,984 / miner 16,978 vs rust 8,336 / cercospora 7,681 / phoma 6,571. Use class-balanced sampling and cap the two big classes at about 9,000 each after dedupe.
- **BRACOL (Brazil) has no phoma.** Map its "cercospora leaf spot" to `cercospora`; inspect "brown leaf spot" and only map it to `cercospora` if the label file says it is the same disease (brown eye spot), otherwise drop it. Its lower-side, white-background photos match our sheet-of-paper protocol, so they are valuable.
- **Uganda set (k36wnd6knb) is augmented too** (rotations, flips, brightness) and has 3,322 files. It stays a held-out test set, but dedupe it by hash too and report "augmented copies may be present". File-name prefix to class mapping is inferred (`1_` healthy, `1200_` rust, `2300_` phoma): confirm by eye on 10 images each.
- **RoCoLe**: split by plant code (`C#P#`), labels in `RoCoLe-classes.xlsx`. Skip the 697 MB VOC tarball.

| Role | Dataset | Classes |
|---|---|---|
| Train / val / test | JMuBEN + JMuBEN2 (Kenya, Arabica) | all five |
| Train / val / test | BRACOL (Brazil, Arabica) | healthy, miner, rust, cercospora |
| Held-out test only | Uganda (phone photos) | healthy, rust, phoma |
| Held-out test only | RoCoLe (Ecuador, Robusta, field) | healthy, rust; red spider mite = OOD probe |
| `not_leaf` | PlantDoc (non-coffee leaves, CC BY 4.0) + your own photos of paper, hands, table, soil | negatives |
Record every source, licence and count in `ml/data_manifest.csv`. Raw data goes in `MIT_Hackathon_7/data_raw/` (git-ignored).

## Tasks, in order

### 1. Data prep (target 22:30 Sat)
- Download script `ml/download.py` (idempotent).
- Build `ml/manifest.csv`: path, source dataset, original label, our label, split.
- **Leakage control:** compute perceptual hashes (`imagehash.phash`) and put near-duplicates (Hamming distance 6 or less) in the same split. Report how many duplicates you found. Split 70/15/15 stratified by class.

### 2. Train v1 (target 00:30 Sun)
- Model: `timm` `mobilenetv3_small_100`, ImageNet pretrained, input 224x224.
- Augment: random resized crop, flips, rotation, colour jitter, mild blur, JPEG compression. These simulate cheap phone cameras.
- Class-balanced sampling. AdamW, cosine schedule, about 8 to 10 epochs. Stop early if val loss rises.
- Log per-epoch metrics to `ml/runs/<timestamp>/`.
- If it does not converge by 00:30: freeze the backbone, train only the head, ship that.

### 3. Calibrate and set the abstention threshold (target 01:00)
- Temperature scaling on the val split. Save `temperature`.
- Choose the confidence threshold so that accuracy on accepted val images is at least 95%. Report coverage at that threshold.
- Out-of-distribution check: on `not_leaf` images and RoCoLe red spider mite, report how often the model abstains or predicts `not_leaf`.

### 4. Export (target 01:30)
- ONNX, opset 17, static input `[1,3,224,224]`, input name `input`, output name `logits`.
- Static int8 quantisation (QDQ format) with about 200 calibration images: `onnxruntime.quantization.quantize_static`.
- Hard cap 5 MB. If over, try `mobilenetv3_small_050`.
- **Parity test:** for 50 test images, compare PyTorch fp32, ONNX fp32 and ONNX int8 top-1 labels. Report agreement. Below 95% agreement means fix before shipping.
- Write `public/model/model.json`:
```json
{
  "version": "v1-2026-10-04",
  "labels": ["healthy","rust","cercospora","phoma","miner","not_leaf"],
  "input": {"size": 224, "resize": "shorter_side_then_center_crop", "mean": [0.485,0.456,0.406], "std": [0.229,0.224,0.225], "layout": "NCHW", "range": "0-1"},
  "temperature": 1.0,
  "threshold": 0.0,
  "sha256": "",
  "bytes": 0
}
```
The engine agent must reproduce this preprocessing exactly. Preprocessing mismatch is the most likely integration bug, so also save `ml/parity_samples/` (10 images + expected probabilities as JSON) for the engine agent to test against in the browser.

### 5. Evaluate (target 02:00)
Write `ml/metrics.json` and `docs/EVALUATION.md` with:
1. In-domain test: accuracy, macro F1, per-class precision and recall, confusion matrix PNG.
2. **Uganda and RoCoLe cross-domain results**, mapped to shared classes. Report them even if they are bad.
3. Selective prediction: accuracy vs coverage curve PNG, with our threshold marked.
4. OOD: abstention rate on `not_leaf` and red spider mite.
5. Size (bytes) and CPU latency per image (onnxruntime on CPU, single thread).
6. Five worked examples (image, top-3 probabilities, accepted or abstained), including two abstentions.
7. One paragraph: what these numbers prove and what they do not.
Never state an accuracy figure without naming the test set.

### 6. If time allows (Tier 2)
- Take 20 photos of any real leaves on a plain sheet with a phone and report predictions. Label them honestly (likely not coffee).
- A small fine-tune pass with paper-background augmentation.

## Rules
- Never train on the Uganda or RoCoLe test sets.
- Never report PlantVillage accuracy as evidence for coffee.
- Seed everything (`42`). Save the exact command used for each run.
- No em dashes in docs. Plain British English.

## Done when
- `leaf.onnx` is under 5 MB, parity at or above 95%, `model.json` complete with real temperature, threshold, sha256 and bytes.
- `EVALUATION.md` has all 7 sections with numbers and plots.
- The engine agent confirmed the parity samples match in the browser.

## Hand-offs
- To **engine**: `leaf.onnx`, `model.json`, `ml/parity_samples/`.
- To **docs**: `metrics.json`, plots, data manifest.
