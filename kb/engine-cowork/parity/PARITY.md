# Preprocessing and runtime parity (lane EC2)

Measured 4 Oct 2026, 00:00 to 00:45 CEST, cloud container (2 vCPU, x86, no GPU). This lane measures agreement between the Python path and the browser path only. It says nothing about model accuracy.

## 1. Verdict

- `src/preprocess.ts` is bit-exact with the training eval transform. 49 images (20 real, 19 synthetic, 10 shipped parity samples): max uint8 diff after Resize 0, after CenterCrop 0, max tensor diff 0 (exact float32 equality) against torchvision 0.29.1 + Pillow 12.3.0.
- Speed: a 4000x3000 photo takes 118 ms median in Node 22 (exact path). Under the 300 ms bar, so the fast path stays off.
- onnxruntime-web 1.30.0 (latest), WASM, 1 thread, runs every model variant we ship or might ship: fp32, int8 QDQ and fp16. All ops supported. Top-1 agrees with Python onnxruntime on 100 percent of inputs for every variant.
- The shipped `public/model/leaf.onnx` today is **fp16**, not int8 (`model.json` says `"quantization": "fp16"`, 3 077 051 bytes). It runs fine in ort-web.
- **`check_parity.mjs` fails today on the shipped artefacts (1 of 10 samples, 07.jpg, max prob diff 0.028 > 0.02).** The cause is in `export.py`, not in the engine: `expected.json` is computed with PyTorch fp32 on the original source image, but the shipped `.jpg` is a quality 90 re-encode. The re-encode alone moves 07.jpg by 0.024 even in Python. Fix: Request ml-1. With expected values computed from the saved jpg and the shipped onnx, the same check passes with worst diff 0.0056.
- Budget problem: `ort-wasm-simd-threaded.wasm` is 14.24 MB raw. With the 3.08 MB model the precache is 17.3 MB raw, over the 15 MB cap. Transfer size with brotli is about 5.1 MB. See section 7.
- EXIF: Chrome always applies EXIF orientation, Pillow does not. 5 of our 10 JMuBEN test files carry orientation 6 or 8. On those, browser and Python see different pixels (prob diff up to 0.17 on the shipped model). See section 8.

## 2. The transform, as formulas

Python (`app/ml/train.py eval_transform`, unchanged in the live file at 00:05):
`Resize(224) -> CenterCrop(224) -> ToTensor() -> Normalize(mean=(0.485,0.456,0.406), std=(0.229,0.224,0.225))` on a PIL RGB image, `Image.open(p).convert("RGB")`, no EXIF transpose.

TypeScript (`preprocess(rgba, w, h)`), step by step:

1. Output size (torchvision `_compute_resized_output_size`): `short = min(w,h)`, `long = max(w,h)`, `newLong = trunc(224 * long / short)` (float64 division, truncation). Short side becomes 224. If the size is unchanged, the image is passed through untouched (torchvision does the same).
2. Resample: Pillow `BILINEAR` with antialias, `ImagingResample` 8 bpc.
   - `scale = in / out`; `filterscale = max(scale, 1)`; `support = 1 * filterscale`.
   - For output pixel `i`: `center = (i + 0.5) * scale`; `xmin = max(trunc(center - support + 0.5), 0)`; `xmax = min(trunc(center + support + 0.5), in) - xmin`.
   - Weights `k(x) = max(0, 1 - |x|)` at `(xmin + j - center + 0.5) / filterscale`, normalised to sum 1, then fixed point: `round(k * 2^22)` with Pillow's rounding (`k < 0 ? trunc(k - 0.5) : trunc(k + 0.5)`).
   - Horizontal pass first into an 8-bit intermediate, then vertical pass. Each pass: `clip8((sum + 2^21) >> 22)`.
   - Only the rows needed for the crop are computed (same values as full resize then crop).
3. CenterCrop: `top = round((newH - 224) / 2)`, `left = round((newW - 224) / 2)` with Python round half to even (`round(2.5) = 2`, `round(3.5) = 4`).
4. ToTensor + Normalize in float32: `x = fround(u8 / 255)`, `y = fround(fround(x - mean_c) / std_c)`. Done with a 3 x 256 lookup table. Layout NCHW `[1,3,224,224]`.

Alpha is ignored. Input is `getImageData().data` at native resolution.

## 3. Preprocess parity results

`logs/preprocess_test.json` (39 items) and `logs/preprocess_test_work_ps.json` (10 shipped parity samples). Oracle `py/oracle.py` runs the real torchvision transform.

| Set | Items | Max u8 diff after Resize | Max u8 diff after crop | Max tensor diff |
|---|---|---|---|---|
| Real images (JMuBEN, Uganda, wild, BRACOL; 83x128 to 2048x1024) | 20 | 0 | 0 | 0 |
| Synthetic: 1x1, 3x5, 13x997, 50x4000, 4000x50, 224x224, 225x224, 227x224, 229x224, 224x231, 449x449, 641x479, 1001x777, 3024x4032, 4000x3000, noise, gradients, hard edges | 19 | 0 | 0 | 0 |
| Shipped `ml/parity_samples/*.jpg` | 10 | 0 | 0 | 0 |

Synthetic cases cover upscale (< 224), extreme aspect, odd sizes and every crop rounding case (`round(0.5)`, `round(1.5)`, `round(2.5)`, `round(3.5)`).

Speed, 4000x3000 RGBA, Node 22.22, median of 7 after warm-up: exact 118 ms, fast path 76 ms. In headless Chromium 141 the 128 to 2048 px images take 2 to 7 ms.

Fast path (`{ fastPath: true }`, off by default): integer box reduce so the image stays at least 2x the target (Pillow `reducing_gap=2.0`), then the exact bilinear. It equals Pillow `resize(..., reducing_gap=2.0)` exactly, but drifts from the training transform: max u8 diff 6, max tensor diff 0.105 on 4000x3000 noise; 5 and 0.087 on 2048x1024 photos. Not needed. Do not enable it.

## 4. Fixture model

`py/make_fixture.py`: `timm mobilenetv3_small_100(num_classes=6, pretrained=False)`, `torch.manual_seed(42)`, exported exactly like `export.py` (opset 17, `dynamo=False`, input `input` [1,3,224,224], output `logits`). Static int8 QDQ with the same settings as the live `export.py` (`quant_pre_process`, `per_channel=True`, MinMax, activations QUInt8 asymmetric, weights QInt8 symmetric) and 50 calibration tensors made by `preprocess.ts` (`tools/write_calib.mjs`). Also the fp16 fallback (`convert_float_to_float16(keep_io_types=True)`), because that is what ships today.

Random weights give near-tied logits, so top-1 here is a weak signal. Logit and prob diffs are the real measure.

| Variant | Bytes | Ops |
|---|---|---|
| fp32 | 6 076 658 | Conv 53, HardSwish 19, Relu 14, HardSigmoid 9, ReduceMean 9, Mul 9, Add 6, GlobalAveragePool, Flatten, Gemm, Identity 37 |
| int8 QDQ | 1 865 273 | QuantizeLinear 128, DequantizeLinear 236, Conv 53, HardSigmoid 28, Mul 28, ReduceMean 9, Add 6, GlobalAveragePool, Flatten, Gemm (pre-process splits HardSwish into HardSigmoid x Mul) |
| fp16 | 3 065 781 | as fp32 plus Cast 2 (float32 in and out) |
| shipped `leaf.onnx` (fp16) | 3 077 051 | Conv 53, HardSwish 19, Relu 14, HardSigmoid 9, ReduceMean 9, Mul 9, Add 6, Cast 2, GlobalAveragePool, Flatten, Gemm |

Python, fixture: PyTorch vs onnxruntime fp32 max logit diff 1.1e-8. PyTorch vs int8: top-1 35/39, max logit diff 0.0046. PyTorch vs fp16: 39/39, 0.00018.

## 5. onnxruntime-web vs Python onnxruntime

`js/run_ortweb.mjs`: onnxruntime-web 1.30.0 in Node, WASM, `numThreads = 1`, on `preprocess.ts` tensors. Python onnxruntime 1.29.0, 1 thread, on torchvision tensors. Same 39 images (or the 10 parity samples). Prob diff at T = 1.5 (fixtures) as the brief asks.

| Model | Top-1 agree | Max logit diff | Max prob diff (T=1.5) | Session create | First run | Median run |
|---|---|---|---|---|---|---|
| fixture fp32 | 39/39 | 1.7e-8 | 1.6e-9 | 631 ms | 62 ms | 13.9 ms |
| fixture int8 | 39/39 | 2.6e-4 | 2.3e-5 | 440 ms | 68 ms | 19.1 ms |
| fixture fp16 | 39/39 | 1.7e-4 | 1.9e-5 | 424 ms | 82 ms | 14.5 ms |
| shipped leaf.onnx, 39 images | 39/39 | 0.28 | 0.0057 | 412 ms | 73 ms | 15.4 ms |
| shipped leaf.onnx, 10 parity samples | 10/10 | 0.17 | 0.0038 | 337 ms | 74 ms | 22.8 ms |

The shipped model's larger logit diff is fp16 arithmetic in two different kernels (x86 MLAS vs WASM). Its logits reach 40 in magnitude, so 0.28 is under 1 percent. Python itself sees up to 0.011 prob diff (T=3.5) between the fp16 and fp32 export of the same checkpoint.

Op support verdict: HardSwish, HardSigmoid, QuantizeLinear, DequantizeLinear (per-channel), Conv, Gemm, ReduceMean, GlobalAveragePool, Cast (fp16) all run on the ort-web WASM EP with no fallback errors. No WebGPU needed.

Latency on this 2 vCPU x86 box: 14 to 23 ms per leaf in Node, 13 to 22 ms in headless Chromium. Phones will be slower; the engine must still measure with 4x CPU throttle as `kb/agents/engine.md` says.

## 6. check_parity.mjs

`tools/check_parity.mjs`. Run from `app/`:

```
node tools/check_parity.mjs                      # defaults below
  --model public/model                           # leaf.onnx + model.json
  --samples ml/parity_samples                    # *.jpg + expected.json
  --preprocess src/engine/preprocess.ts          # must export preprocess(rgba, w, h)
  --tol 0.02 --json out.json
```

Per sample: decode JPEG, `preprocess`, ort-web WASM 1 thread, softmax(logits / T) with T from `expected.json`. Pass if top-1 equals `expected.label` and max |prob - expected| <= tol. Exit 0 pass, 1 parity failure, 2 setup error. Also warns if `model.json` sha256, bytes or temperature disagree with the files.

Needs Node >= 22.18 (imports the `.ts` with built-in type stripping) and devDependencies `onnxruntime-web` and `sharp`. sharp decodes JPEG with libjpeg-turbo and gave pixels identical to Pillow on all 30 test JPEGs. `jpeg-js` is a fallback only: it differs from Pillow by up to 47 per channel.

Results:

| Case | Result |
|---|---|
| Fixture case (`fixtures/parity_case`, int8 fixture, 6 samples, export.py layout) | pass, worst diff 0.00002 |
| Same, tampered expected.json (`tools/test_check_parity.sh`) | exit 1, 2 rows flagged, as intended |
| Shipped artefacts as they are now | **fail**, 07.jpg diff 0.028 (01.jpg 0.018, 05.jpg 0.016 close) |
| Shipped model, expected.json recomputed from the saved jpg with the shipped onnx | pass, worst diff 0.0056 |

Why the shipped case fails (`logs/expected_drift_decomposition.txt`, T=3.5, max prob diff vs `expected.json`):

| File | Python fp32 onnx on saved jpg | Python fp16 onnx on saved jpg | ort-web fp16 + preprocess.ts |
|---|---|---|---|
| 01.jpg | 0.012 | 0.024 | 0.018 |
| 05.jpg | 0.018 | 0.019 | 0.016 |
| 07.jpg | 0.024 | 0.026 | 0.028 |

Python alone fails the 0.02 bar, so the drift is in how `expected.json` is made, not in the browser path.

## 7. WASM files and the 15 MB budget

Use `import * as ort from "onnxruntime-web/wasm"`, not the default `"onnxruntime-web"`. The default bundle pulls the JSEP (WebGPU) build, twice the size.

| File | Raw | gzip -9 | brotli 11 |
|---|---|---|---|
| ort-wasm-simd-threaded.wasm (needed) | 14 239 897 | 3 687 160 | 2 355 011 |
| ort-wasm-simd-threaded.mjs (needed) | 24 381 | 9 124 | 8 009 |
| ort.wasm.bundle.min.mjs (in the app JS bundle) | 73 054 | 24 603 | 21 707 |
| ort-wasm-simd-threaded.jsep.wasm (avoid) | 28 312 028 | 6 659 266 | 3 952 437 |
| ort.bundle.min.mjs (default import, avoid) | 413 523 | 113 099 | 94 745 |
| shipped leaf.onnx (fp16) | 3 077 051 | 2 820 014 | 2 689 383 |
| fixture int8 onnx | 1 865 273 | 1 510 922 | n/m |

Minimal `public/ort/`: `ort-wasm-simd-threaded.wasm` and `ort-wasm-simd-threaded.mjs`. Tested in Chromium: with `ort.env.wasm.wasmPaths = "/ort/"` the bundle fetches both files from `/ort/`; without the `.mjs` session creation fails ("Failed to fetch dynamically imported module .../ort/ort-wasm-simd-threaded.mjs").

Budget: Cache Storage holds raw bytes. wasm 14.24 MB + fp16 model 3.08 MB = 17.3 MB before app JS, audio and images. Over 15 MB. With an int8 model (about 1.9 MB) it is still 16.1 MB. The download over the network is about 2.4 MB (wasm, brotli) + 2.7 MB (model) = 5.1 MB if the host serves brotli. Options, in order of effort: (a) define the 15 MB budget as transfer size and report raw size beside it; (b) a custom minimal ORT WASM build with only the 12 ops above (not attempted tonight). `maximumFileSizeToCacheInBytes` at 15 MB still lets the 14.24 MB wasm in, but only just.

## 8. Browser decode and EXIF

`browser/` (Playwright, headless Chromium 141): `createImageBitmap(blob)` then `OffscreenCanvas.getImageData` then `preprocess.ts` then `onnxruntime-web/wasm`.

- Decoder: Chrome RGBA equals Pillow RGBA byte for byte on every file without an EXIF rotation (25 of 30).
- EXIF: files with Orientation 6 or 8 (5 JMuBEN files) are rotated by Chrome and not by Pillow. `imageOrientation: "none"` no longer stops this in Chrome 141 (still 768x1024 for a 1024x768 file tagged 6). Effect on the shipped model on those 5 files: top-1 still 5/5, max prob diff 0.17, max logit diff 34.
- Without EXIF rotation: fixture int8 top-1 15/15, max prob diff 1.8e-5; shipped model 15/15 and 10/10 parity samples, max prob diff 0.0048 and 0.0056 (T=3.5).

Recommendation for phone photos: keep Chrome's behaviour (upright, as the farmer framed it). Make training match it: apply `ImageOps.exif_transpose` when loading images in `train.py` and `export.py` (Request ml-2). Parity samples must carry no EXIF; the current ones do not, because `export.py` re-saves them without EXIF. If ml cannot retrain, the engine can strip the Orientation tag before decoding to match training, but then sideways photos reach the model sideways.

## 9. Files

- `src/preprocess.ts`: pure TS, no DOM. `preprocess(rgba, w, h, opts?) -> Float32Array [1,3,224,224]`, plus `resizedSize`, `centerCropOffsets`, `roundHalfEven`, `resizeAndCrop`, `softmaxT`.
- `src/preprocess.test.ts`: parity test against oracle output (`node src/preprocess.test.ts [workDir]`, exit 1 on any diff). Not vitest; the engine can wrap it or port the cases.
- `tools/check_parity.mjs`, `tools/test_check_parity.sh`, `tools/write_calib.mjs`.
- `py/oracle.py` (torchvision oracle), `py/make_fixture.py`, `py/make_parity_case.py`, `py/ort_ref.py`.
- `js/run_ortweb.mjs`, `js/package.json`; `browser/entry.mjs`, `browser/run.cjs`.
- `fixtures/parity_case/` (2.7 MB): `public/model/{leaf.onnx,model.json}` (int8 fixture, random weights, never ship) and `ml/parity_samples/{00..05.jpg,expected.json}` in the `export.py` layout.
- `logs/`: every number above.
- `images/SOURCES.txt`: where the 20 test images came from (CC BY 4.0 datasets; images not copied to keep fixtures small).

Reproduce: `pip install torch torchvision timm onnx onnxruntime --break-system-packages`; `python3 py/oracle.py`; `node src/preprocess.test.ts`; `node tools/write_calib.mjs`; `python3 py/make_fixture.py`; `tools/test_check_parity.sh`.

## 10. Requests

- ml-1: In `export.py write_parity_samples`, compute `probs` from the saved `dest` jpg (reopen it) with the shipped onnx through onnxruntime, not PyTorch on the source image. Today 07.jpg fails `check_parity` at 0.028 from the re-encode alone. `py/make_parity_case.py` shows the fix.
- ml-2: Apply `ImageOps.exif_transpose` before `convert("RGB")` in train, eval and export loaders, so training sees what Chrome shows. JMuBEN has many Orientation 6/8 files.
- ml-3: The shipped model is fp16 because int8 parity fell under 0.95. Int8 QDQ runs fine in ort-web; if int8 is fixed, the model drops from 3.08 MB to about 1.9 MB, which helps the 15 MB budget.
- engine-1: Copy `src/preprocess.ts` to `app/src/engine/preprocess.ts` as is, and port the parity cases into vitest using `fixtures/parity_case` and the oracle outputs.
- engine-2: Import `onnxruntime-web/wasm`. Put `ort-wasm-simd-threaded.wasm` and `ort-wasm-simd-threaded.mjs` in `public/ort/`; set `wasmPaths = "/ort/"`, `numThreads = 1`. Make sure Vite does not also emit the jsep wasm into the precache.
- engine-3: Decode with `createImageBitmap` + `OffscreenCanvas.getImageData` at native size; do not resize on a canvas first (canvas scaling is not Pillow bilinear).
- engine-4: Add `tools/check_parity.mjs` with devDependencies `sharp` and `onnxruntime-web`; run it in CI or before each model drop. It will fail until ml-1 lands.
- lead/docs: Decide whether the 15 MB budget is raw precache or transfer size. Raw is 17.3 MB today, transfer about 5.1 MB with brotli.
