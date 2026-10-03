import { getMockHint, mockClassify } from './model.mock.ts';
import { imageToNchw, readImageBitmap } from './preprocess.ts';
import { checkQuality } from './quality.ts';
import { LABELS, type Label, type LeafResult, type QualityResult } from './types.ts';

export interface ModelFile {
  version: string;
  labels: Label[];
  input: {
    size: number;
    resize: string;
    mean: number[];
    std: number[];
    layout: 'NCHW';
    range: '0-1';
  };
  temperature: number;
  threshold: number;
}

export interface LogitSession {
  run(feeds: { input: Float32Array }): Promise<{ logits: { data: ArrayLike<number> } }>;
}

interface LoadedModel {
  version: string;
  mock: boolean;
  config: ModelFile;
  session: LogitSession | null;
}

const DEFAULT_LABELS: Label[] = [...LABELS];

const MOCK_MODEL: LoadedModel = {
  version: 'mock',
  mock: true,
  config: {
    version: 'mock',
    labels: DEFAULT_LABELS,
    input: {
      size: 224,
      resize: 'shorter_side_then_center_crop',
      mean: [0.485, 0.456, 0.406],
      std: [0.229, 0.224, 0.225],
      layout: 'NCHW',
      range: '0-1',
    },
    temperature: 1,
    threshold: 0,
  },
  session: null,
};

const OK_QUALITY: QualityResult = { ok: true, blur: 100, brightness: 128 };

let loadedPromise: Promise<LoadedModel> | null = null;

function mockForced(): boolean {
  return import.meta.env.VITE_USE_MOCK_MODEL === 'true';
}

function normaliseConfig(value: unknown): ModelFile | null {
  if (!value || typeof value !== 'object') return null;
  const raw = value as {
    version?: unknown;
    labels?: unknown;
    input?: {
      size?: unknown;
      resize?: unknown;
      mean?: unknown;
      std?: unknown;
    };
    temperature?: unknown;
    threshold?: unknown;
  };
  if (!Array.isArray(raw.labels) || raw.labels.length !== DEFAULT_LABELS.length) return null;
  const labels = raw.labels.filter((label): label is Label => DEFAULT_LABELS.includes(label as Label));
  if (labels.length !== DEFAULT_LABELS.length) return null;
  const input = raw.input ?? {};
  const mean = Array.isArray(input.mean) && input.mean.length === 3 ? input.mean.map(Number) : [0.485, 0.456, 0.406];
  const std = Array.isArray(input.std) && input.std.length === 3 ? input.std.map(Number) : [0.229, 0.224, 0.225];
  const size = typeof input.size === 'number' && input.size > 0 ? input.size : 224;
  return {
    version: typeof raw.version === 'string' && raw.version.length > 0 ? raw.version : 'unversioned',
    labels,
    input: {
      size,
      resize: typeof input.resize === 'string' ? input.resize : 'shorter_side_then_center_crop',
      mean,
      std,
      layout: 'NCHW',
      range: '0-1',
    },
    temperature: typeof raw.temperature === 'number' && raw.temperature > 0 ? raw.temperature : 1,
    threshold: typeof raw.threshold === 'number' ? raw.threshold : 0,
  };
}

async function fetchModel(): Promise<{ config: ModelFile; bytes: ArrayBuffer } | null> {
  if (typeof fetch !== 'function') return null;
  try {
    const [metaRes, onnxRes] = await Promise.all([fetch('/model/model.json'), fetch('/model/leaf.onnx')]);
    if (!metaRes.ok || !onnxRes.ok) return null;
    const config = normaliseConfig(await metaRes.json());
    if (!config) return null;
    const bytes = await onnxRes.arrayBuffer();
    if (bytes.byteLength === 0) return null;
    return { config, bytes };
  } catch {
    return null;
  }
}

async function createSession(bytes: ArrayBuffer, config: ModelFile): Promise<LogitSession> {
  const ort = await import('onnxruntime-web/wasm');
  // One thread, because most hosts are not cross-origin isolated.
  // The runtime files are served from /ort/ (ort-wasm-simd-threaded.*).
  ort.env.wasm.wasmPaths = '/ort/';
  ort.env.wasm.numThreads = 1;
  const raw = await ort.InferenceSession.create(bytes, { executionProviders: ['wasm'] });
  return {
    async run(feeds) {
      const tensor = new ort.Tensor('float32', feeds.input, [1, 3, config.input.size, config.input.size]);
      const output = await raw.run({ input: tensor });
      const logits = output.logits;
      if (!logits || !('data' in logits)) throw new Error('Model output "logits" is missing');
      return { logits: { data: logits.data as ArrayLike<number> } };
    },
  };
}

async function doLoad(): Promise<LoadedModel> {
  // leaf.onnx is not in this repo yet, so a missing file (or a forced flag) stays on the mock.
  if (mockForced()) return MOCK_MODEL;
  const found = await fetchModel();
  if (!found) return MOCK_MODEL;
  try {
    const session = await createSession(found.bytes, found.config);
    return { version: found.config.version, mock: false, config: found.config, session };
  } catch {
    return MOCK_MODEL;
  }
}

function ensureLoaded(): Promise<LoadedModel> {
  if (!loadedPromise) {
    loadedPromise = doLoad().catch((error: unknown) => {
      loadedPromise = null;
      throw error;
    });
  }
  return loadedPromise;
}

export function loadModel(): Promise<{ version: string; mock: boolean }> {
  return ensureLoaded().then((state) => ({ version: state.version, mock: state.mock }));
}

export function softmax(logits: ArrayLike<number>): number[] {
  let max = Number.NEGATIVE_INFINITY;
  for (let i = 0; i < logits.length; i++) if (logits[i] > max) max = logits[i];
  if (!Number.isFinite(max)) return [];
  const exps: number[] = [];
  let sum = 0;
  for (let i = 0; i < logits.length; i++) {
    const value = Math.exp(logits[i] - max);
    exps.push(value);
    sum += value;
  }
  return exps.map((value) => value / sum);
}

export function interpretLogits(
  logits: ArrayLike<number>,
  config: ModelFile,
): Pick<LeafResult, 'label' | 'probs' | 'confidence' | 'abstained'> {
  const temperature = config.temperature > 0 ? config.temperature : 1;
  const scaled = Array.from(logits, (value) => value / temperature);
  const probabilities = softmax(scaled);
  const probs = {
    healthy: 0,
    rust: 0,
    cercospora: 0,
    phoma: 0,
    miner: 0,
    not_leaf: 0,
  };
  let bestIndex = 0;
  for (let i = 0; i < config.labels.length; i++) {
    const label = config.labels[i];
    const probability = probabilities[i] ?? 0;
    probs[label] = probability;
    if (probability > probs[config.labels[bestIndex]]) bestIndex = i;
  }
  const label = config.labels[bestIndex];
  const confidence = probs[label] ?? 0;
  if (confidence < config.threshold) {
    return { label: 'unsure', probs, confidence, abstained: true };
  }
  return { label, probs, confidence, abstained: false };
}

export async function classifyPrepared(
  nchw: Float32Array,
  session: LogitSession,
  config: ModelFile,
): Promise<Pick<LeafResult, 'label' | 'probs' | 'confidence' | 'abstained'>> {
  const output = await session.run({ input: nchw });
  if (!output.logits?.data) throw new Error('Model output "logits" is missing');
  return interpretLogits(output.logits.data, config);
}

function canMeasure(img: ImageBitmap | undefined): img is ImageBitmap {
  if (!img || typeof img.width !== 'number' || typeof img.height !== 'number') return false;
  return typeof img.close === 'function';
}

function abstain(quality: QualityResult, state: LoadedModel): LeafResult {
  const mock = mockClassify('');
  return {
    label: 'unsure',
    probs: mock.probs,
    confidence: mock.confidence,
    quality,
    abstained: true,
    modelVersion: state.mock ? 'mock' : state.version,
  };
}

function hintFrom(opts: { hint?: string } | string | undefined): string {
  if (typeof opts === 'string') return opts.length > 0 ? opts : getMockHint();
  if (opts?.hint) return opts.hint;
  return getMockHint();
}

export async function classifyLeaf(img: ImageBitmap, opts?: { hint?: string } | string): Promise<LeafResult> {
  const state = await ensureLoaded();
  const hint = hintFrom(opts);
  let measured: QualityResult | null = null;
  if (canMeasure(img)) {
    try {
      measured = checkQuality(img);
    } catch {
      measured = null;
    }
  }
  if (state.mock) {
    const mock = mockClassify(hint);
    const quality = measured && !measured.ok ? measured : (mock.quality ?? measured ?? OK_QUALITY);
    if (!quality.ok) return abstain(quality, state);
    return {
      label: mock.label,
      probs: mock.probs,
      confidence: mock.confidence,
      quality,
      abstained: mock.abstained,
      modelVersion: 'mock',
    };
  }
  const quality = measured ?? OK_QUALITY;
  if (!quality.ok) return abstain(quality, state);
  if (!state.session) return abstain(quality, state);
  const rgba = readImageBitmap(img);
  const nchw = imageToNchw(rgba, state.config.input);
  const head = await classifyPrepared(nchw, state.session, state.config);
  return { ...head, quality, modelVersion: state.version };
}
