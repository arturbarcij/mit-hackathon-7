# Jani leaf model

No model has been trained in this checkout. Metrics are not available.

`public/model/` holds a `.gitkeep` only. There is no `leaf.onnx` and no `model.json`. `model.schema.json` in this folder is the shape `export.py` will write after a real checkpoint exists. It is not a model card for a trained network.

## Where to run

Train on Arthur's laptop (Windows, Acer Nitro 5, NVIDIA GPU) from Cursor's terminal. This checkout has no GPU, and the datasets are hundreds of MB to a few GB, so do not download or train here.

```bash
conda create -n jani python=3.11 -y
conda activate jani
nvidia-smi
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install timm onnx onnxruntime onnxscript scikit-learn pandas matplotlib imagehash pillow tqdm
cd app/ml
python download.py
python manifest.py
python train.py
python export.py
python eval.py
```

Check `nvidia-smi` before the torch install and match the CUDA wheel if cu121 is wrong.

If the GPU will not run, use a Kaggle notebook with a free GPU and these same scripts. Raw images stay in `data_raw/` next to `app/` (in this checkout, `/workspace/data_raw`). That directory is outside the git repo. Do not commit it.

CPU fallback: if CUDA is missing, install the CPU wheel from pytorch.org. `train.py` still runs. It prints that it is on the CPU and that the run will be slow. The script is the same one.

Seed is 42. Each run writes the exact command to `runs/<timestamp>/command.txt`.

## Order of scripts

1. `download.py` reads `datasets.json` and saves zips under `data_raw/`. It is idempotent. It prints the licence before each download. It does nothing on import.
2. `manifest.py` writes `manifest.csv` with columns `path`, `source`, `original_label`, `label`, `split`, `out_of_scope`.
3. `train.py` refuses to start if `manifest.csv` is missing. It writes `runs/<timestamp>/` including `best.pt`, `metrics.csv` and `calibration.json`.
4. `export.py` writes `public/model/leaf.onnx` and `public/model/model.json` only when `best.pt` exists and the int8 file passes the shape, 5 MB, calibration and parity checks. If there is no checkpoint it exits 0 and writes neither file. It also writes `parity_samples/` once an int8 model has actually been run.
5. `eval.py` writes `metrics.json` and prints the seven EVALUATION sections. It does not edit `app/docs/EVALUATION.md`. If there is no checkpoint it exits 0 and does not invent numbers.

`python download.py --self-check` and `python manifest.py --self-check` check the label map, the held-out rule and the hash clustering without downloading images.

## Class map

Fixed labels, in model order: `healthy`, `rust`, `cercospora`, `phoma`, `miner`, `not_leaf`.

| Source label | Our label |
| --- | --- |
| healthy, Healthy | healthy |
| leaf rust, Leaf rust, rust, CLR | rust |
| cercospora leaf spot, Cerscospora (JMuBEN folder spelling) | cercospora |
| brown leaf spot | cercospora (assumption, below) |
| phoma, Phoma | phoma |
| leaf miner, Miner | miner |
| PlantDoc folders and photos of paper, hands, tables, soil (`data_raw/negatives/backgrounds`) | not_leaf |
| RoCoLe red spider mite | see below |

JMuBEN contributes rust, cercospora and phoma. JMuBEN2 contributes healthy and miner. BRACOL has no phoma class.

Assumption: BRACOL `brown leaf spot` is mapped to `cercospora`. Coffee brown eye spot is caused by Cercospora coffeicola, and Jani has one cercospora class. BRACOL `cercospora leaf spot` maps to that same class, so the two source labels are merged. DATASETS.md could not confirm this from the zip. Check the label file before trusting a metric that depends on it.

RoCoLe red spider mite stays in `original_label`. The `label` column is `not_leaf` so it stays inside the six names, and `out_of_scope` is `red_spider_mite`. Those rows are held out, they are not trained, and they are not counted as the not_leaf class. They are never labelled rust, even when a rust level is also present.

Images with more than one BRACOL disease are left out of the manifest rather than forced into one class. Near-duplicates whose labels disagree are kept in the file with `out_of_scope` set to `label_clash` and are not trained.

## Held-out rule

Uganda and RoCoLe are held-out only. Their `split` is `heldout`. They are never `train`, `val` or `test`. `download.py` refuses to place either dataset in a folder named `train`. `manifest.py` refuses to write a manifest that puts them anywhere else. `train.py` also drops those sources even if a row were mis-labelled.

RoCoLe has four images per plant. The split is by plant: file names such as `C10P10E1.jpg` share plant id `C10P10`, and those images stay in the same split. Because the whole set is held out, that split is `heldout`.

Uganda file-name prefixes are not defined by the dataset record. Where no folder or label file is present, `manifest.py` uses an inference from the counted sizes: `1_` healthy (counted 1179, stated 1179), `2300_` phoma (counted 1110, stated 1110), `1200_` rust (counted 1033, stated coffee leaf rust 1023, ten extra files). A real label file wins over the prefix rule.

## Splits and leakage

Train, val and test are 70 / 15 / 15 by cluster, stratified by majority label as far as whole clusters allow. Perceptual hashes (`imagehash.phash`) with Hamming distance 6 or less stay in one split. If a train image matches a held-out image within that distance, the whole cluster is `heldout`, so the held-out photo cannot leak into training. The script prints how many duplicate clusters it found.

## Training

- `timm` `mobilenetv3_small_100`, ImageNet pretrained, 224 input. If the int8 file is over 5 MB, retrain with `--arch mobilenetv3_small_050`.
- Augmentations: random resized crop, horizontal and vertical flips, rotation, colour jitter, mild blur, JPEG compression.
- Class-balanced sampler, AdamW, cosine schedule, 10 epochs, early stop when validation loss rises (`--patience`, default 1). `--freeze-backbone` trains only the head. `--workers` defaults to 0 so Windows does not have to spawn extra processes. Use `--workers 2` on Linux if loading is slow.
- Validation and export use a different recipe from training augmentation: resize the shorter side to 224 with bilinear filtering, centre-crop 224, scale pixels to 0-1, then ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`, layout NCHW. That is the contract in `model.json`.
- Temperature is fitted on the validation split. The confidence threshold is the cut with the highest coverage whose accuracy on accepted validation images is at least 95 percent, when such a cut exists. If it does not, `calibration.json` says `target_met` is false and the stored threshold is the best real cut, not a fill-in.

## Export contract

`leaf.onnx`: ONNX opset 17, input `input`, output `logits`, static shape `[1, 3, 224, 224]`, static int8 QDQ quantisation, at most 5 MB (5242880 bytes).

`model.json` matches `model.schema.json` and `kb/agents/ml.md`:

```json
{
  "version": "v1-2026-10-04",
  "labels": ["healthy", "rust", "cercospora", "phoma", "miner", "not_leaf"],
  "input": {"size": 224, "resize": "shorter_side_then_center_crop", "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225], "layout": "NCHW", "range": "0-1"},
  "temperature": 1.0,
  "threshold": 0.0,
  "sha256": "",
  "bytes": 0
}
```

The numbers in that example are the field shapes from the brief. `export.py` fills temperature, threshold, sha256 and bytes from the run. It will not write the file to stand in for a missing checkpoint.

Parity: 50 in-domain test images, top-1 agreement of PyTorch fp32, ONNX fp32 and ONNX int8. Below 95 percent, or fewer than 50 images, the file is not copied to `public/model/`. Ten of those images are copied to `parity_samples/` with JSON probabilities from the int8 model after temperature scaling, for the engine agent.

## Evaluation

`eval.py` reports, when a checkpoint exists: in-domain test accuracy and macro F1, Uganda, RoCoLe (even if poor), selective prediction, out-of-distribution abstention on `not_leaf` and on red spider mite, file size, and single-thread CPU latency. It never states an accuracy without naming the test set. It does not report PlantVillage accuracy.

## Counts in datasets.json

Counted figures are copied from `kb/research/DATASETS.md`. They are not re-measured here.

| Dataset | Role | Counted images | Stated, when the count differs or was not made |
| --- | --- | --- | --- |
| JMuBEN | train | 22588 | stated 22591. Files 7681, 8336, 6571 |
| JMuBEN2 | train | 35962 | files 18984 healthy and 16978 miner |
| BRACOL | train | not counted | stated 1747 whole leaves and 2147 symptom crops |
| Uganda | held-out | 3322 | stated 3312 |
| RoCoLe | held-out | 1560 | four images per plant. The VOC archive is skipped |
| PlantDoc | negatives | not counted | 28 train folders, no coffee class |
| CoLeaf-DB | future, not used for this model | healthy zip 6 | stated 1006. Skipped unless `--include-future` |

Licences for these sets are CC BY 4.0. The script prints that before each download.
