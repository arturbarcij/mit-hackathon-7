# Preprocessing and model parity for the Jani engine

For the engine agent. Produced by the EC2 helper lane on 2026-10-03.

## What this gives you

`src/preprocess.ts` reproduces `eval_transform()` from `app/ml/train.py` bit for bit:
Resize(224) with PIL bilinear antialias, CenterCrop(224), ToTensor, Normalize(ImageNet), NCHW float32.
It is pure TypeScript with no DOM dependency. `src/preprocess-browser.ts` is the small glue that gets RGBA out of a File at native size.

Verified on 24 synthetic fixtures (12 sizes from 150x400 to 4032x3024, gradients, noise, checkerboards, a synthetic leaf), in Node and in Chromium 141. All numbers are in `RESULTS.json`.

## Parity numbers

Preprocessing, browser path (Chromium decode, OffscreenCanvas, `preprocess.ts`) against torchvision output:

| Input | Max abs diff in 8 bit levels | Max abs diff in the float tensor | Bit exact |
|---|---|---|---|
| PNG, 24 fixtures | 0 | 0 | yes, 100 percent of values |
| JPEG q90 4:2:0, 24 fixtures | 0 | 0 | yes, 100 percent of values |

Preprocessing, Node path (pngjs / jpeg-js decode, same `preprocess.ts`):

| Input | Max levels | Mean levels | Bit exact |
|---|---|---|---|
| PNG | 0 | 0 | yes |
| JPEG via jpeg-js | 82 | 2.65 | no, see JPEG caveat |

Model logits (untrained mobilenetv3_small_100, 6 classes, exported like `export.py`), same input tensor everywhere:

| Comparison | fp32 max abs diff | int8 max abs diff | top-1 agreement |
|---|---|---|---|
| Chromium onnxruntime-web vs Python onnxruntime | 1.9e-8 | 2.3e-4 | 100 percent, both |
| Node onnxruntime-web vs Python onnxruntime | 1.9e-8 | 2.3e-4 | 100 percent, both |
| Chromium vs Node onnxruntime-web | 0 | 0 | 100 percent |
| Python onnxruntime vs PyTorch | 1.4e-8 | 8.3e-3 | fp32 100 percent |

So the browser gets the same tensor as Python, and the same int8 graph gives logits within 2.3e-4 of Python onnxruntime. That is the number to expect when you run `ml/parity_samples/` in the browser: probabilities should match `expected.json` far inside the 0.02 tolerance in `kb/agents/engine.md`. If you see a difference above about 1e-3 in logits, the cause is preprocessing or a different model file, not onnxruntime.

Ignore the 0.875 int8 vs PyTorch top-1 figure in RESULTS.json. The test model is untrained, so all six logits sit within 0.01 of zero and int8 noise of 0.008 flips argmax. The ML agent's `export.py` parity on the trained model is the real check.

## How to drop it in

1. Copy `src/preprocess.ts` and `src/preprocess-browser.ts` to `app/src/engine/`.
2. In `model.ts`, load `model.json`, then:

```ts
import { preprocess, type PreprocessSpec } from './preprocess';
import { toRawImage } from './preprocess-browser';
import * as ort from 'onnxruntime-web/wasm';

ort.env.wasm.wasmPaths = '/ort/';
ort.env.wasm.numThreads = 1;

const spec = modelJson.input as PreprocessSpec;   // size, resize, mean, std, layout, range
const raw = await toRawImage(file);                // File from <input type="file">
const { tensor, dims } = preprocess(raw, spec);
const out = await session.run({ input: new ort.Tensor('float32', tensor, dims) });
const logits = out.logits.data as Float32Array;    // then / temperature, softmax, threshold
```

`preprocess()` consumes exactly these `model.json` fields: `input.size` (224), `input.resize` (must be `shorter_side_then_center_crop`), `input.mean`, `input.std`, `input.layout` (must be `NCHW`), `input.range` (must be `0-1`). It throws on anything else, so a changed model.json fails loudly.

The input type is `{ data: Uint8ClampedArray | Uint8Array, width, height }` with RGBA or RGB bytes. `toRawImage()` produces that from a File, Blob, ImageBitmap, img or canvas by drawing at 1:1 into an OffscreenCanvas. Never let the canvas scale the image; all resampling must happen in `preprocess.ts` or parity is gone.

`PreprocessResult.rgb` is the 224x224x3 uint8 crop before normalisation. Useful for a debug view and for the quality gate (it is the same crop the model sees).

## How the resize matches Pillow

torchvision on a PIL image calls `Image.resize` with bilinear. Pillow's `Resample.c` is not a plain bilinear lookup: it is a triangle filter whose support grows with the downscale factor (that is the antialias), normalised so the weights sum to one, quantised to 22 bit fixed point, applied horizontally then vertically with a round to 8 bit after each pass. `preprocess.ts` copies that exactly, including `int()` truncation in `precompute_coeffs`, the `+0.5` rounding in `normalize_coeffs_8bpc`, `clip8`, and torchvision's output size `int(224 * long / short)` and crop offset `round((h - 224) / 2.0)` with Python's round half to even. Any "just use canvas drawImage to 224" shortcut is off by several levels on edges and that shows up as logit drift.

## JPEG caveat, measured

Browser JPEG decoders and PIL's libjpeg can differ. Chromium and Pillow 12.3 both ship libjpeg-turbo with fancy chroma upsampling, and on these 24 baseline q90 4:2:0 JPEGs the decoded pixels were identical: 0 levels difference, 100 percent exact. Expect the same on Android Chrome. Firefox and Safari use their own decoders and may differ by 1 or 2 levels on chroma edges; that is well below the 0.02 probability tolerance.

jpeg-js (pure JS, used only in the Node test) uses nearest neighbour chroma upsampling, so on 4:2:0 JPEGs it differs from PIL by up to 94 levels on noise and 15 levels mean on checkerboards, and about 0.7 levels mean on the leaf image. On 4:4:4 JPEGs the difference drops to 3 levels max. Do not use jpeg-js in the app. Decode with the browser.

Two more things the browser does that PIL in train.py does not: it applies EXIF orientation (createImageBitmap default), and it applies an embedded ICC profile. `toRawImage` passes `colorSpaceConversion: 'none'`. Orientation is left at the browser default on purpose because the farmer sees the upright image; set `imageOrientation: 'none'` if strict PIL parity on rotated phone photos is ever required.

## onnxruntime-web files for public/ort

Version tested: onnxruntime-web 1.30.0. With `ort.env.wasm.numThreads = 1` and the wasm backend, Chromium loaded exactly these files from `/ort/`:

| File | Bytes |
|---|---|
| `ort-wasm-simd-threaded.wasm` | 14,239,897 (3,659,955 gzipped) |
| `ort-wasm-simd-threaded.mjs` | 24,381 |

Copy both from `node_modules/onnxruntime-web/dist/` to `public/ort/`. If you import `onnxruntime-web/wasm` (the default export is the `.bundle.min.mjs` variant) the `.mjs` loader is inlined and only the `.wasm` is fetched, but copying both costs nothing. Do not copy the `.jsep`, `.jspi` or `.asyncify` wasm files; they are for WebGPU and are 17 to 28 MB each.

Budget warning for the lead: the wasm alone is 14.2 MB on disk. Workbox checks `maximumFileSizeToCacheInBytes` against the uncompressed size, so with a 1.7 to 5 MB model the precache will exceed the 15 MB total in `kb/agents/engine.md`. Set `maximumFileSizeToCacheInBytes` to at least 15 MB (the per file limit) and record the real total in `kb/STATUS.md`. Over the wire with gzip or brotli it is about 3.7 MB.

Loading the session from a URL (`InferenceSession.create('/model/leaf.onnx')`) took 462 ms for fp32 and 198 ms for int8 in Chromium, wasm compile included after the first visit.

## Latency

CPU: Intel Xeon Processor @ 2.10GHz (2 cores, cloud VM). Single wasm thread. Median over 24 or 20 runs.

| Where | fp32 ms | int8 ms |
|---|---|---|
| Python onnxruntime 1.29, 1 thread | 2.3 | 6.1 |
| Node 22 onnxruntime-web | 25.5 | 18.3 |
| Chromium 141 onnxruntime-web | 13.8 | 15.4 |
| Chromium, CDP CPU throttle 4x | 57.6 | 64.7 |

Inference is far inside the 1 s at 4x throttle budget. Note that int8 QDQ is not faster than fp32 in wasm on this CPU; it only saves bytes (1.67 MB vs 6.08 MB for this model).

Preprocessing a 12 MP (3000x4000) JPEG in Chromium: decode to RGBA 177 ms, `preprocess()` 177 ms unthrottled; 560 ms and 688 ms at 4x throttle. The resize cost scales with the input pixel count because the first pass walks every source row. For a 12 MP phone photo the whole pipeline at 4x throttle is about 1.3 s, with inference only 65 ms of that. If that matters, run `preprocess()` in a Web Worker so the UI stays responsive; do not shrink the image in canvas first, that breaks parity. A 640x480 image preprocesses in under 10 ms.

## Limits

- Fixtures are synthetic. Real phone photos were not available in this lane. The maths does not depend on content, so bit exactness should hold, but run `ml/parity_samples/` in the browser as the final check.
- Only Chromium was measured. Android Chrome uses the same decoder and wasm engine. Firefox and Safari JPEG decoding may differ by a level or two.
- Pillow 12.3 behaviour was reproduced. This resample code has been unchanged in Pillow for many releases, so a different Pillow version on the training machine should match; verify with `ml/parity_samples/`.
- The CenterCrop padding path (image smaller than 224 after resize) is not implemented; it cannot happen after Resize(224) because the short side is always 224.
- `quantize_static` printed "Expected bias ... to be an initializer" warnings on the raw torch export. ML agent: run `onnxruntime.quantization.shape_inference.quant_pre_process(fp32, pre)` before `quantize_static` in `export.py` to fold constants; it is also what the onnxruntime docs recommend. Parity is unaffected either way.
- The 404 in `page_errors` is `favicon.ico`.

## Files

```
src/preprocess.ts            core: Pillow bilinear resize, crop, normalise, NCHW
src/preprocess-browser.ts    File / ImageBitmap to RawImage at native size
tests/preprocess.test.ts     Node parity test against fixture tensors (pngjs, jpeg-js)
tests/ort_node.test.ts       onnxruntime-web in Node vs Python onnxruntime logits
tests/browser/index.html     browser harness: decode, preprocess, run, time
tests/browser_parity.py      Playwright driver, CDP CPU throttle, wasm file log
scripts/make_fixtures.py     24 fixtures as PNG and JPEG q90 plus expected tensors
scripts/export_test_model.py untrained mobilenetv3_small_100 to ONNX fp32 and int8 QDQ
scripts/compare_ort.py       PyTorch vs onnxruntime fp32 and int8 reference logits
RESULTS.json                 every number above, per image
_work/                       venv-free scratch: node_modules, fixtures (107 MB), models, raw results
```

Rerun everything from `_work/`:

```
python3 ../scripts/make_fixtures.py fixtures
npx tsx ../tests/preprocess.test.ts fixtures preprocess_results.json
python3 ../scripts/export_test_model.py model
python3 ../scripts/compare_ort.py fixtures model python_logits.json
npx tsx ../tests/ort_node.test.ts fixtures model python_logits.json node_logits.json
cp ../tests/browser/index.html serve/ && python3 ../tests/browser_parity.py serve python_logits.json node_logits.json browser_results.json
```

`node_modules` at the parity root is a symlink into `_work/node_modules` so the tests resolve their imports. `_work/serve/` holds the static page with symlinks to fixtures and models.
