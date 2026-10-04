import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ModelSpec, QualityResult } from '../../src/engine/types';

// Fake onnxruntime-web: records what it was given and returns fixed logits.
const ort = vi.hoisted(() => {
  const state = { logits: [0, 5, 0, 0, 0, 0], fail: false, feeds: [] as unknown[] };
  class Tensor {
    type: string;
    data: Float32Array;
    dims: number[];
    constructor(type: string, data: Float32Array, dims: number[]) {
      this.type = type;
      this.data = data;
      this.dims = dims;
    }
  }
  const run = async (feeds: Record<string, unknown>) => {
    state.feeds.push(feeds);
    return { logits: { data: Float32Array.from(state.logits) } };
  };
  const create = async () => {
    if (state.fail) throw new Error('onnx 404');
    return { inputNames: ['input'], outputNames: ['logits'], run };
  };
  return { state, module: { env: { wasm: {} as Record<string, unknown> }, Tensor, InferenceSession: { create } } };
});
vi.mock('onnxruntime-web/wasm', () => ort.module);

// Quality gate is controlled per test.
const gate = vi.hoisted(() => ({ result: { ok: true, blur: 100, brightness: 0.5 } as QualityResult }));
vi.mock('../../src/engine/quality', () => ({ checkQuality: vi.fn(() => gate.result) }));

// No canvas in node: drawToRgba and readNativeRgba return pixels derived from the image width.
vi.mock('../../src/engine/image', async (orig) => ({
  ...(await orig<typeof import('../../src/engine/image')>()),
  drawToRgba: vi.fn((img: { width: number }, w: number, h: number) => ({
    data: new Uint8ClampedArray(w * h * 4).fill(img.width % 256),
    width: w,
    height: h,
  })),
  readNativeRgba: vi.fn((img: { width: number; height: number }) => ({
    data: new Uint8ClampedArray(img.width * img.height * 4).fill(img.width % 256),
    width: img.width,
    height: img.height,
  })),
}));

import {
  _resetModelForTests,
  classifyLeaf,
  loadModel,
  preprocessRgba,
  softmaxT,
  specProblem,
  toLeafResult,
} from '../../src/engine/model';
import { mockClassify } from '../../src/engine/model.mock';

const okQ: QualityResult = { ok: true, blur: 100, brightness: 0.5 };
const img = (width: number, height = 300) => ({ width, height }) as unknown as ImageBitmap;

const validSpec: ModelSpec = {
  version: 'v-test',
  labels: ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'],
  input: { size: 2, resize: 'shorter_side_then_center_crop', mean: [0.5, 0.5, 0.5], std: [0.5, 0.5, 0.5], layout: 'NCHW', range: '0-1' },
  temperature: 1.5,
  threshold: 0.5,
  sha256: '',
  bytes: 0,
};

function serveSpec(spec: unknown) {
  const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => spec }));
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

beforeEach(() => {
  _resetModelForTests();
  vi.stubEnv('VITE_USE_MOCK_MODEL', '');
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  ort.state.fail = false;
  ort.state.logits = [0, 5, 0, 0, 0, 0];
  ort.state.feeds = [];
  gate.result = okQ;
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

describe('softmaxT', () => {
  it('sums to 1 and is stable for large logits', () => {
    const p = softmaxT([1000, 1001, 999], 1);
    expect(p.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 10);
    expect(p.every(Number.isFinite)).toBe(true);
  });

  it('sharpens with T < 1 and flattens with T > 1', () => {
    const logits = [2, 1, 0];
    const base = Math.max(...softmaxT(logits, 1));
    expect(Math.max(...softmaxT(logits, 0.5))).toBeGreaterThan(base);
    expect(Math.max(...softmaxT(logits, 3))).toBeLessThan(base);
  });
});

describe('preprocessRgba', () => {
  it('writes NCHW planes in pixel order with mean and std applied', () => {
    // 2x2 RGBA; pixel i has R = 10 + i, G = 20 + i, B = 30 + i, alpha ignored.
    const rgba = [10, 20, 30, 255, 11, 21, 31, 0, 12, 22, 32, 255, 13, 23, 33, 255];
    const mean = [0.1, 0.2, 0.3];
    const std = [0.5, 0.25, 0.125];
    const out = preprocessRgba(rgba, 2, mean, std);
    expect(out).toHaveLength(12);
    for (let i = 0; i < 4; i++) {
      expect(out[0 * 4 + i]).toBeCloseTo(((10 + i) / 255 - 0.1) / 0.5, 6);
      expect(out[1 * 4 + i]).toBeCloseTo(((20 + i) / 255 - 0.2) / 0.25, 6);
      expect(out[2 * 4 + i]).toBeCloseTo(((30 + i) / 255 - 0.3) / 0.125, 6);
    }
  });
});

describe('toLeafResult', () => {
  const spec = { labels: validSpec.labels, threshold: 0.6, version: 'v1' };

  it('abstains below threshold but keeps the probabilities', () => {
    const r = toLeafResult([0.1, 0.5, 0.1, 0.1, 0.1, 0.1], spec, okQ);
    expect(r).toMatchObject({ label: 'unsure', abstained: true, confidence: 0.5, modelVersion: 'v1' });
    expect(r.probs.rust).toBe(0.5);
  });

  it('keeps not_leaf as a normal label above threshold', () => {
    const r = toLeafResult([0.02, 0.02, 0.02, 0.02, 0.02, 0.9], spec, okQ);
    expect(r).toMatchObject({ label: 'not_leaf', abstained: false, confidence: 0.9 });
  });
});

describe('specProblem', () => {
  it('accepts a valid spec and rejects bad ones', () => {
    expect(specProblem(validSpec)).toBeNull();
    expect(specProblem({ ...validSpec, labels: ['rust', 'healthy', 'cercospora', 'phoma', 'miner', 'not_leaf'] })).toMatch(/labels/);
    expect(specProblem({ ...validSpec, temperature: 0 })).toMatch(/temperature/);
    expect(specProblem({ ...validSpec, threshold: 0 })).toMatch(/threshold/);
    expect(specProblem({ ...validSpec, threshold: 1 })).toMatch(/threshold/);
    expect(specProblem({ ...validSpec, input: { ...validSpec.input, size: 2.5 } })).toMatch(/size/);
  });
});

describe('loadModel', () => {
  it('falls back to the mock when fetch rejects', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('offline'))));
    expect(await loadModel()).toEqual({ version: 'mock', mock: true });
    expect(console.warn).toHaveBeenCalled();
  });

  it('uses the mock when VITE_USE_MOCK_MODEL is true, without fetching', async () => {
    vi.stubEnv('VITE_USE_MOCK_MODEL', 'true');
    const fetchMock = serveSpec(validSpec);
    expect(await loadModel()).toEqual({ version: 'mock', mock: true });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('falls back to the mock when model.json is invalid', async () => {
    serveSpec({ ...validSpec, threshold: 0 });
    expect(await loadModel()).toEqual({ version: 'mock', mock: true });
  });

  it('falls back to the mock when the onnx cannot be loaded', async () => {
    serveSpec(validSpec);
    ort.state.fail = true;
    expect(await loadModel()).toEqual({ version: 'mock', mock: true });
  });

  it('reports the real model and configures wasm when everything loads', async () => {
    serveSpec(validSpec);
    expect(await loadModel()).toEqual({ version: 'v-test', mock: false });
    expect(ort.module.env.wasm).toMatchObject({ wasmPaths: '/ort/', numThreads: 1 });
  });

  it('retries the real model after a transient fetch failure', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('offline'))));
    expect(await loadModel()).toEqual({ version: 'mock', mock: true });
    serveSpec(validSpec);
    expect(await loadModel()).toEqual({ version: 'v-test', mock: false });
  });

  it('retries after the onnx fails to load, then caches the success', async () => {
    const fetchMock = serveSpec(validSpec);
    ort.state.fail = true;
    expect(await loadModel()).toEqual({ version: 'mock', mock: true });
    ort.state.fail = false;
    expect(await loadModel()).toEqual({ version: 'v-test', mock: false });
    expect(await loadModel()).toEqual({ version: 'v-test', mock: false });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('caches an invalid model.json (no refetch per leaf)', async () => {
    const fetchMock = serveSpec({ ...validSpec, threshold: 0 });
    await loadModel();
    await loadModel();
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('shares one promise between concurrent callers', async () => {
    const fetchMock = serveSpec(validSpec);
    const a = loadModel();
    const b = loadModel();
    expect(a).toBe(b);
    await Promise.all([a, b]);
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});

describe('classifyLeaf', () => {
  it('abstains without inference when the quality gate fails', async () => {
    serveSpec(validSpec);
    gate.result = { ok: false, reason: 'blurry', blur: 5, brightness: 0.5 };
    const r = await classifyLeaf(img(400));
    expect(r).toMatchObject({ label: 'unsure', abstained: true, confidence: 0, modelVersion: 'v-test' });
    expect(Object.values(r.probs).every((p) => p === 0)).toBe(true);
    expect(ort.state.feeds).toHaveLength(0);
  });

  it('runs the real model with an NCHW tensor and applies temperature', async () => {
    serveSpec(validSpec);
    const r = await classifyLeaf(img(400));
    const feeds = ort.state.feeds[0] as Record<string, { dims: number[]; data: Float32Array }>;
    expect(feeds.input.dims).toEqual([1, 3, 2, 2]);
    expect(feeds.input.data).toHaveLength(12);
    const expected = softmaxT(ort.state.logits, 1.5);
    expect(r.label).toBe('rust');
    expect(r.confidence).toBeCloseTo(Math.max(...expected), 6);
    expect(r.modelVersion).toBe('v-test');
  });

  // Gate blocker (4 Oct): a model that fails to load must not give made-up mock labels.
  it('gives unsure leaves, not mock labels, when the model fails to load outside mock mode', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('offline'))));
    for (const w of [400, 401, 402, 777]) {
      const r = await classifyLeaf(img(w));
      expect(r.label).toBe('unsure');
      expect(r.abstained).toBe(true);
      expect(r.confidence).toBe(0);
      expect(r.modelVersion).toBe('unavailable');
    }
  });

  it('gives unsure leaves when the onnx cannot be loaded, then uses the real model once it loads', async () => {
    serveSpec(validSpec);
    ort.state.fail = true;
    expect((await classifyLeaf(img(400))).label).toBe('unsure');
    ort.state.fail = false;
    const r = await classifyLeaf(img(400));
    expect(r.label).toBe('rust');
    expect(r.modelVersion).toBe('v-test');
  });

  it('uses the mock classifier in mock mode', async () => {
    vi.stubEnv('VITE_USE_MOCK_MODEL', 'true');
    const r = await classifyLeaf(img(400));
    expect(r.modelVersion).toBe('mock');
    expect(r).toEqual(mockClassify(img(400), okQ));
  });

});

describe('mockClassify', () => {
  it('is deterministic per image', () => {
    expect(mockClassify(img(333, 222), okQ)).toEqual(mockClassify(img(333, 222), okQ));
  });

  it('gives a mix of labels and about 1 in 6 unsure', () => {
    const results = Array.from({ length: 600 }, (_, i) => mockClassify(img(i, 480), okQ));
    const labels = new Set(results.map((r) => r.label));
    expect(labels.size).toBeGreaterThanOrEqual(5);
    const unsure = results.filter((r) => r.label === 'unsure').length;
    expect(unsure).toBeGreaterThan(50);
    expect(unsure).toBeLessThan(160);
    for (const r of results) {
      expect(r.modelVersion).toBe('mock');
      expect(r.abstained).toBe(r.label === 'unsure');
      expect(Object.values(r.probs).reduce((a, b) => a + b, 0)).toBeCloseTo(1, 6);
    }
  });
});
