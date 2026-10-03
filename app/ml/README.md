# Jani ML: coffee leaf classifier

Classes (fixed): `healthy`, `rust`, `cercospora`, `phoma`, `miner`, `not_leaf`.

## Setup

```bash
python3 -m venv /workspace/.venv-ml          # needs python3.12-venv on Ubuntu
/workspace/.venv-ml/bin/pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu
/workspace/.venv-ml/bin/pip install -r app/ml/requirements.txt
```
GPU: install torch and torchvision from the CUDA index URL instead (see `requirements.txt`).

## 1. Data

```bash
python app/ml/download.py          # idempotent; writes data_raw/<dataset>/ (git-ignored)
python app/ml/build_manifest.py    # writes manifest.csv and manifest_stats.json (about 3 min on 4 cores)
```
Sources, licences and counts: `data_manifest.csv`. All six sources downloaded without a login.

`manifest.csv` columns: `path` (relative to `data_raw/`), `source`, `original_label`, `label`, `split`, `dup_group`.

Leakage control: 64-bit pHash (same algorithm as `imagehash.phash`). Two images are near-duplicates when the
Hamming distance is 6 or less between one image and any of the 8 flip or 90-degree-rotation variants of the
other, because JMuBEN and Uganda contain flipped and rotated copies. Near-duplicates are joined with
union-find and each group goes into one split. Train sets (JMuBEN, JMuBEN2, BRACOL, PlantDoc sample) are split
70/15/15 per class by image count; Uganda and RoCoLe are `heldout_uganda` and `heldout_rocole`.

Results of the build on 3 Oct (from `manifest_stats.json`):
- 65,134 readable images; 103 files are empty at source (102 Uganda, 1 JMuBEN2).
- 992 duplicate groups inside the train sets, covering 57,381 images; the largest holds 1,800 JMuBEN2 healthy images.
- 39 groups join train-set images with held-out images: 216 Uganda phoma images are copies of JMuBEN phoma
  images (checked by eye). They have split `excluded_heldout_dup_of_train` and are not used for evaluation.
- 67 groups contain images with different labels (272 BRACOL, 56 Uganda, 28 RoCoLe, 1 PlantDoc images).
  Labels were kept as published.

| split | healthy | rust | cercospora | phoma | miner | not_leaf | unmapped |
|---|---|---|---|---|---|---|---|
| train | 12,724 | 6,210 | 5,466 | 4,818 | 12,054 | 285 | 0 |
| val | 3,217 | 1,255 | 1,179 | 1,070 | 2,597 | 61 | 0 |
| test | 3,181 | 1,336 | 1,172 | 1,029 | 2,580 | 61 | 0 |
| heldout_uganda | 1,079 | 1,031 | 0 | 894 | 0 | 0 | 0 |
| heldout_rocole | 791 | 602 | 0 | 0 | 0 | 0 | 167 (red spider mite) |
| excluded_heldout_dup_of_train | 0 | 0 | 0 | 216 | 0 | 0 | 0 |
| excluded (BRACOL mixed stress) | 0 | 0 | 0 | 0 | 0 | 0 | 59 |

Known gaps: `not_leaf` is only PlantDoc non-coffee leaves (407 images); there are no photos of paper,
hands, tables or soil yet. JMuBEN images are 128x128 crops of leaf surface, unlike a whole leaf on a sheet.

## 2. Train

`train.py`: timm `mobilenetv3_small_100` (ImageNet pretrained), 224x224, phone-camera augmentations
(random resized crop, flips, rotation, colour jitter, mild blur, JPEG re-encoding), class-balanced sampling
with replacement, AdamW, cosine schedule with 3% warm-up, early stop when val loss has not improved for 2
epochs. Seed 42. Each run writes `runs/<name>/` with `config.json` (exact command), `metrics.csv`,
`metrics.jsonl`, `train.log`, `val_confusion.json`, and `best.pt` / `last.pt` (git-ignored).
Validation during training uses at most 500 images per class from the val split (`--max-val-per-class`).

Eval preprocessing matches `model.json`: resize shorter side to 224, centre crop 224, scale to 0-1,
ImageNet mean and std, NCHW.

Smoke test (done 3 Oct, CPU): 1 epoch, 50 images per class, completed and wrote a checkpoint.
```bash
.venv-ml/bin/python app/ml/train.py --epochs 1 --max-train-per-class 50 --max-val-per-class 20 --out app/ml/runs/smoke
```

Speed on the cloud VM (4 CPU cores, no GPU, 3 loader workers): full fine-tune 83 images/s in a 60-step test,
63 images/s averaged over the first real epoch (11.2 minutes per epoch over all 41,557 training images,
including validation); frozen backbone (`--freeze-backbone`) about 144 images/s in a 60-step test.

v1 CPU run (started 3 Oct 21:50 UTC, tmux session `ml-train`, full fine-tune, no cap on images per class):
```bash
cd /workspace
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s ml-train -c /workspace \
  "bash -lc '.venv-ml/bin/python app/ml/train.py --device auto --epochs 10 --patience 2 --max-val-per-class 500 --out app/ml/runs/v1-cpu-20261003-2150 2>&1 | grep --line-buffered -v Warning | tee -a /tmp/ml-train.out; exec bash'"
```
Log: `app/ml/runs/v1-cpu-20261003-2150/train.log`. A `DONE` file appears in the run folder when it finishes.
Watch it with `tmux -f /exec-daemon/tmux.portal.conf attach -t ml-train` or `tail -f` on the log.

On a GPU the same command works unchanged (`--device auto` picks CUDA).

## After training

Run from `/workspace` once the run folder has a `DONE` file. Replace `<run>` with the run folder name
(for the v1 CPU run: `v1-cpu-20261003-2150`). All three scripts use one CPU thread by default
(`--threads` on calibrate and export raises it once training has stopped).

```bash
# 1. Temperature scaling and abstention threshold on the whole val split -> app/ml/calibration.json
.venv-ml/bin/python app/ml/calibrate.py --ckpt app/ml/runs/<run>/best.pt

# 2. ONNX export, int8 quantisation, parity -> app/public/model/leaf.onnx, model.json,
#    app/ml/parity_samples/ (10 JPEGs + expected.json + samples.json), app/ml/export_report.json
.venv-ml/bin/python app/ml/export.py --ckpt app/ml/runs/<run>/best.pt --version v1-2026-10-04

# 3. Evaluation of the shipped int8 model -> app/ml/metrics.json, app/ml/figures/*.png
.venv-ml/bin/python app/ml/evaluate.py
```

What each step checks:
- `calibrate.py` picks the lowest threshold whose accepted val accuracy is at least 95% (`--target`), and
  reports coverage there and the thresholds for 98% and 99%. If 95% is never reached it writes threshold 1.0
  and `chosen.reached: false`, and `export.py` then refuses to write the model.
- `export.py` exits with an error and writes nothing to `app/public/model/` if the int8 file is over 5 MB,
  or top-1 agreement with PyTorch on 50 test images is below 95%. `--quant auto` (default) tries static QDQ
  first and falls back to int8 weight-only QDQ (int8 weights, float activations) when static QDQ fails the
  agreement check. Static QDQ failed on the smoke checkpoint and on the v1 epoch-1 checkpoint (30 to 40%
  agreement): per-tensor uint8 ranges cannot hold MobileNetV3's early depthwise and squeeze-excite activations.
  `export_report.json` records both results. `--force` is for smoke tests only.
- `evaluate.py` refuses to run if `model.json` sha256 or bytes do not match `leaf.onnx`, like the engine.
  Every metric sits under the name of its test set. The quality gate is not applied, so in-domain numbers
  include the 128 px JMuBEN crops the app itself would reject as too small; `per_source_accuracy` separates them.

Preprocessing in all three scripts is `export.engine_tensor`, a copy of the engine: EXIF orientation applied,
longer side limited to 1600 px, centre square of the shorter side resized to 224 in one step (PIL bilinear),
RGB 0-1, ImageNet mean and std, NCHW. Parity JPEGs are re-encoded without EXIF or ICC profiles; seven have a
shorter side of exactly 224 px (the engine crop is a pixel copy) and three are larger (the engine resizes).

Engine check once the real files exist (engine branch `cursor/engine-offline-core-d90f`, folder `app/`):
the Playwright test `real model: parity samples match when present` in `tests/e2e/offline.spec.ts` reads
`public/model/` and `ml/parity_samples/` and compares `classifyFile` probabilities with `expected.json`
(tolerance 0.02). Run it with `npm ci && npx playwright install chromium && npm run test:e2e` after the
model files and parity samples are on that branch.

Smoke test of the three scripts (outputs only under `/tmp/mlx/`, numbers meaningless):
```bash
.venv-ml/bin/python app/ml/calibrate.py --ckpt app/ml/runs/smoke/best.pt --max-per-class 30 --out /tmp/mlx/calibration.json
.venv-ml/bin/python app/ml/export.py --ckpt app/ml/runs/smoke/best.pt --calibration /tmp/mlx/calibration.json \
  --out-dir /tmp/mlx/model --parity-dir /tmp/mlx/parity_samples --report /tmp/mlx/export_report.json --force
.venv-ml/bin/python app/ml/evaluate.py --model-dir /tmp/mlx/model --calibration /tmp/mlx/calibration.json \
  --export-report /tmp/mlx/export_report.json --max-per-class 30 --out /tmp/mlx/metrics.json --fig-dir /tmp/mlx/figures
```
