// Leaf model: loads public/model/model.json and leaf.onnx once, then classifies one photo.
// loadModel() reports mock: true (the UI shows a badge) whenever the real model is not loaded.
// classifyLeaf() uses the mock classifier only with VITE_USE_MOCK_MODEL=true; otherwise a
// missing model gives 'unsure' leaves (modelVersion 'unavailable'), never made-up labels.
// SSR-safe: onnxruntime-web is imported dynamically inside functions only.
// Imports the 'onnxruntime-web/wasm' entry (plain wasm EP): the default entry pulls the
// 28.3 MB jsep wasm. public/ort/ must hold ort-wasm-simd-threaded.wasm and .mjs
// (scripts/copy-ort-wasm.mjs puts them there).
// Preprocessing: preprocess.ts on native-size pixels, bit-exact with app/ml/train.py eval_transform.
import { decodeImage, readNativeRgba } from './image';
import { preprocess } from './preprocess';
import { mockClassify } from './model.mock';
import { checkQuality } from './quality';
import { LABELS, type ClassifyOptions, type ImageInput, type Label, type LeafResult, type ModelInfo, type ModelSpec, type QualityResult } from './types';

export const MODEL_JSON_URL = '/model/model.json';
export const MODEL_ONNX_URL = '/model/leaf.onnx';
export const ORT_WASM_PATH = '/ort/';
/** modelVersion on a leaf result when the real model could not be loaded (and mock mode is off). */
export const UNAVAILABLE_VERSION = 'unavailable';

type Ort = typeof import('onnxruntime-web/wasm');
type Session = Awaited<ReturnType<Ort['InferenceSession']['create']>>;

interface RealModel {
  ort: Ort;
  session: Session;
  spec: ModelSpec;
  inputName: string;
  outputName: string;
}

let loading: Promise<ModelInfo> | null = null;
let real: RealModel | null = null;

/** Clears the cached model so each test starts fresh. */
export function _resetModelForTests(): void {
  loading = null;
  real = null;
}

/**
 * Loads once; concurrent callers share one in-flight promise. Never rejects: falls back to the mock.
 * Only a settled outcome is cached (real model loaded, VITE_USE_MOCK_MODEL, or an invalid model.json).
 * A transient failure (fetch error, HTTP error, onnx load error) returns the mock for that call and
 * clears the cache, so a later call retries the real model.
 */
export function loadModel(): Promise<ModelInfo> {
  if (!loading) {
    const attempt = loadOnce().then(({ info, retry }) => {
      if (retry && loading === attempt) loading = null;
      return info;
    });
    loading = attempt;
  }
  return loading;
}

interface LoadOutcome {
  info: ModelInfo;
  retry: boolean;
}

function useMock(reason: string, retry: boolean): LoadOutcome {
  console.warn(`[model] using the MOCK model: ${reason}${retry ? ' (will retry on next call)' : ''}`);
  real = null;
  return { info: { version: 'mock', mock: true }, retry };
}

async function loadOnce(): Promise<LoadOutcome> {
  if (import.meta.env.VITE_USE_MOCK_MODEL === 'true') return useMock('VITE_USE_MOCK_MODEL=true', false);

  let spec: ModelSpec;
  try {
    const res = await fetch(MODEL_JSON_URL);
    if (!res.ok) return useMock(`${MODEL_JSON_URL} returned HTTP ${res.status}`, true);
    const json: unknown = await res.json();
    const problem = specProblem(json);
    if (problem) return useMock(`${MODEL_JSON_URL} is invalid: ${problem}`, false);
    spec = json as ModelSpec;
  } catch (err) {
    return useMock(`could not load ${MODEL_JSON_URL}: ${String(err)}`, true);
  }

  try {
    const ort = await import('onnxruntime-web/wasm');
    ort.env.wasm.wasmPaths = ORT_WASM_PATH;
    ort.env.wasm.numThreads = 1;
    const session = await ort.InferenceSession.create(MODEL_ONNX_URL, { executionProviders: ['wasm'] });
    const inputName = pickName(session.inputNames, 'input');
    const outputName = pickName(session.outputNames, 'logits');
    real = { ort, session, spec, inputName, outputName };
    return { info: { version: spec.version, mock: false }, retry: false };
  } catch (err) {
    return useMock(`could not load ${MODEL_ONNX_URL}: ${String(err)}`, true);
  }
}

function pickName(names: readonly string[], wanted: string): string {
  if (names.includes(wanted)) return wanted;
  console.warn(`[model] ONNX has no '${wanted}', using '${names[0]}' (names: ${names.join(', ')})`);
  return names[0];
}

/** Returns why model.json is unusable, or null when it is valid. */
export function specProblem(json: unknown): string | null {
  if (!json || typeof json !== 'object') return 'not an object';
  const s = json as Partial<ModelSpec>;
  if (typeof s.version !== 'string' || !s.version) return 'version missing';
  if (!Array.isArray(s.labels) || s.labels.length !== LABELS.length || s.labels.some((l, i) => l !== LABELS[i])) {
    return `labels must be exactly ${LABELS.join(',')}`;
  }
  if (typeof s.temperature !== 'number' || !(s.temperature > 0)) return 'temperature must be > 0';
  if (typeof s.threshold !== 'number' || !(s.threshold > 0 && s.threshold < 1)) return 'threshold must be between 0 and 1 (exclusive)';
  const input = s.input;
  if (!input || !Number.isInteger(input.size) || input.size <= 0) return 'input.size must be a positive integer';
  if (!isTriple(input.mean) || !isTriple(input.std) || input.std.some((v) => v === 0)) return 'input.mean and input.std must be 3 numbers (std non-zero)';
  return null;
}

function isTriple(v: unknown): v is [number, number, number] {
  return Array.isArray(v) && v.length === 3 && v.every((x) => typeof x === 'number' && Number.isFinite(x));
}

/** Softmax of logits / T, numerically stable. */
export function softmaxT(logits: ArrayLike<number>, T: number): number[] {
  const z = Array.from(logits, (v) => v / T);
  const m = Math.max(...z);
  const e = z.map((v) => Math.exp(v - m));
  const sum = e.reduce((a, b) => a + b, 0);
  return e.map((v) => v / sum);
}

function isBlob(v: unknown): v is Blob {
  return typeof Blob !== 'undefined' && v instanceof Blob;
}

/**
 * size x size RGBA bytes to NCHW float32: RGB, /255, minus mean, divided by std.
 * Kept for callers and tests; classifyLeaf now uses preprocess.ts (bit-exact with training).
 */
export function preprocessRgba(
  rgba: ArrayLike<number>,
  size: number,
  mean: readonly number[],
  std: readonly number[],
): Float32Array {
  const plane = size * size;
  const out = new Float32Array(3 * plane);
  for (let i = 0; i < plane; i++) {
    for (let c = 0; c < 3; c++) out[c * plane + i] = (rgba[i * 4 + c] / 255 - mean[c]) / std[c];
  }
  return out;
}

function zeroProbs(): Record<Label, number> {
  return Object.fromEntries(LABELS.map((l) => [l, 0])) as Record<Label, number>;
}

/** Turns calibrated probabilities into a LeafResult; abstains ('unsure') below threshold. */
export function toLeafResult(
  probs: ArrayLike<number>,
  spec: Pick<ModelSpec, 'labels' | 'threshold' | 'version'>,
  quality: QualityResult,
): LeafResult {
  const record = zeroProbs();
  let best = 0;
  for (let i = 0; i < spec.labels.length; i++) {
    record[spec.labels[i]] = probs[i];
    if (probs[i] > probs[best]) best = i;
  }
  const confidence = probs[best];
  const abstained = confidence < spec.threshold;
  return {
    label: abstained ? 'unsure' : spec.labels[best],
    probs: record,
    confidence,
    quality,
    abstained,
    modelVersion: spec.version,
  };
}

/** Result for a photo that failed the quality gate: no inference, all probs 0. */
export function qualityAbstention(quality: QualityResult, modelVersion: string): LeafResult {
  return { label: 'unsure', probs: zeroProbs(), confidence: 0, quality, abstained: true, modelVersion };
}

/**
 * Quality gate (including the sheet gate unless opts.sheetGate is false), then the model.
 * A photo that fails the gate returns 'unsure' with quality.ok false and is never forced into a class.
 */
export async function classifyLeaf(input: ImageInput | Blob, opts: ClassifyOptions = {}): Promise<LeafResult> {
  await loadModel();
  // A photo file (from <input type="file">) is decoded here at native size.
  const img: ImageInput = isBlob(input) ? await decodeImage(input) : input;
  const quality = checkQuality(img, opts);
  const model = real;
  if (!quality.ok) {
    const version = model ? model.spec.version : import.meta.env.VITE_USE_MOCK_MODEL === 'true' ? 'mock' : UNAVAILABLE_VERSION;
    return qualityAbstention(quality, version);
  }
  if (!model) {
    // The mock gives made-up labels, so it is used only when asked for (VITE_USE_MOCK_MODEL=true).
    // Otherwise a model that failed to load makes every leaf 'unsure' (the plot then goes to
    // too_many_unsure or ask_officer); loadModel() above retries the real model on the next photo.
    if (import.meta.env.VITE_USE_MOCK_MODEL === 'true') return mockClassify(img, quality);
    return qualityAbstention(quality, UNAVAILABLE_VERSION);
  }

  const { ort, session, spec, inputName, outputName } = model;
  const size = spec.input.size;
  // Native-size pixels, then the bit-exact copy of train.py eval_transform
  // (Pillow bilinear Resize(size), CenterCrop(size), ToTensor, Normalize).
  const rgba = readNativeRgba(img);
  const data = preprocess(rgba.data, rgba.width, rgba.height, { size, mean: spec.input.mean, std: spec.input.std });
  const tensor = new ort.Tensor('float32', data, [1, 3, size, size]);
  const out = await session.run({ [inputName]: tensor });
  const logits = out[outputName].data as Float32Array;
  if (logits.length !== spec.labels.length) {
    throw new Error(`[model] expected ${spec.labels.length} logits, got ${logits.length}`);
  }
  return toLeafResult(softmaxT(logits, spec.temperature), spec, quality);
}
