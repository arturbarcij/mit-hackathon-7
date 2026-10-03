import { classifyMock, MOCK_VERSION } from './model.mock';
import { preprocessBitmap } from './preprocess';
import { checkQuality } from './quality';
import { calibratedSoftmax, LABELS, leafResultFromBadQuality, leafResultFromProbs, probsRecord } from './scoring';
import { nameOf } from './source';
import type { Label, LeafResult, ModelConfig } from './types';

type Ort = typeof import('onnxruntime-web/wasm');
type Session = import('onnxruntime-web/wasm').InferenceSession;

interface Loaded {
  mock: boolean;
  version: string;
  config?: ModelConfig;
  session?: Session;
  ort?: Ort;
}

let loading: Promise<Loaded> | null = null;
let lastInferenceMs = 0;

const base = () => import.meta.env.BASE_URL ?? '/';
const wantsMock = () => import.meta.env.VITE_USE_MOCK_MODEL === 'true';

export function parseModelConfig(raw: unknown): ModelConfig {
  const c = raw as Partial<ModelConfig> | null;
  const ok =
    c &&
    typeof c.version === 'string' &&
    Array.isArray(c.labels) &&
    c.labels.length > 0 &&
    c.labels.every((l) => (LABELS as readonly string[]).includes(l)) &&
    c.input &&
    typeof c.input.size === 'number' &&
    Array.isArray(c.input.mean) && c.input.mean.length === 3 &&
    Array.isArray(c.input.std) && c.input.std.length === 3 &&
    typeof c.temperature === 'number' &&
    typeof c.threshold === 'number';
  if (!ok) throw new Error('model.json is missing or malformed');
  return c as ModelConfig;
}

async function sha256Hex(bytes: ArrayBuffer): Promise<string | null> {
  if (typeof crypto === 'undefined' || !crypto.subtle) return null;
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** A missing model (404, or the dev server answering with index.html) is reported as such, not as corruption. */
class ModelMissing extends Error {}

async function loadReal(): Promise<Loaded> {
  let config: ModelConfig;
  try {
    const res = await fetch(`${base()}model/model.json`);
    if (!res.ok) throw new ModelMissing(`model.json: HTTP ${res.status}`);
    const text = await res.text();
    try {
      config = parseModelConfig(JSON.parse(text));
    } catch {
      throw new ModelMissing('model.json is not valid JSON');
    }
  } catch (e) {
    if (e instanceof ModelMissing) throw e;
    throw new ModelMissing(String(e));
  }

  const res = await fetch(`${base()}model/leaf.onnx`);
  if (!res.ok) throw new ModelMissing(`leaf.onnx: HTTP ${res.status}`);
  const bytes = await res.arrayBuffer();
  if (config.sha256) {
    const actual = await sha256Hex(bytes);
    if (actual && actual !== config.sha256.toLowerCase()) {
      throw new Error('leaf.onnx does not match the checksum in model.json. Download it again.');
    }
  }

  const ort = await import('onnxruntime-web/wasm');
  // Absolute URLs on purpose: the Vite dev server appends "?import" to dynamic imports that start with "/",
  // which breaks the runtime's own import of the glue file from public/.
  const ortBase = new URL(`${base()}ort/`, globalThis.location?.href ?? 'http://localhost/').href;
  ort.env.wasm.wasmPaths = {
    mjs: `${ortBase}ort-wasm-simd-threaded.mjs`,
    wasm: `${ortBase}ort-wasm-simd-threaded.wasm`,
  };
  ort.env.wasm.numThreads = 1;
  ort.env.wasm.proxy = false;
  const session = await ort.InferenceSession.create(new Uint8Array(bytes), {
    executionProviders: ['wasm'],
    graphOptimizationLevel: 'all',
  });
  return { mock: false, version: config.version, config, session, ort };
}

async function init(): Promise<Loaded> {
  if (wantsMock()) return { mock: true, version: MOCK_VERSION };
  try {
    return await loadReal();
  } catch (e) {
    if (e instanceof ModelMissing) {
      // The real model has not been delivered yet. Say so loudly and let the UI show its mock badge.
      console.warn(`[jani] Real model not found (${e.message}). Using the mock model.`);
      return { mock: true, version: MOCK_VERSION };
    }
    throw e;
  }
}

export function loadModel(): Promise<{ version: string; mock: boolean }> {
  loading ??= init().catch((e) => {
    loading = null;
    throw e;
  });
  return loading.then(({ version, mock }) => ({ version, mock }));
}

export function lastInferenceTimeMs(): number {
  return lastInferenceMs;
}

/** Runs the network on a preprocessed tensor and returns calibrated probabilities. */
export async function runTensor(loaded: Loaded, tensor: Float32Array): Promise<Record<Label, number>> {
  const { session, ort, config } = loaded;
  if (!session || !ort || !config) throw new Error('Model is not loaded');
  const size = config.input.size;
  const input = new ort.Tensor('float32', tensor, [1, 3, size, size]);
  const inputName = session.inputNames.includes('input') ? 'input' : session.inputNames[0];
  const outputName = session.outputNames.includes('logits') ? 'logits' : session.outputNames[0];
  const t0 = performance.now();
  const out = await session.run({ [inputName]: input });
  lastInferenceMs = performance.now() - t0;
  const logits = out[outputName].data as Float32Array;
  return probsRecord(config.labels, calibratedSoftmax(logits, config.temperature));
}

export async function classifyLeaf(img: ImageBitmap): Promise<LeafResult> {
  await loadModel();
  const loaded = (await loading) as Loaded;
  const quality = checkQuality(img);
  if (loaded.mock) {
    if (!quality.ok) return leafResultFromBadQuality(quality, MOCK_VERSION);
    return classifyMock(nameOf(img), quality);
  }
  const config = loaded.config as ModelConfig;
  if (!quality.ok) return leafResultFromBadQuality(quality, config.version);
  const probs = await runTensor(loaded, preprocessBitmap(img, config.input));
  return leafResultFromProbs(probs, config.threshold, quality, config.version);
}

/** Test hook: runs the loaded real model on an already preprocessed tensor and returns calibrated probabilities. */
export async function inferProbsForTest(tensor: Float32Array): Promise<Record<Label, number>> {
  await loadModel();
  const loaded = (await loading) as Loaded;
  if (loaded.mock) throw new Error('inferProbsForTest needs the real model');
  return runTensor(loaded, tensor);
}
