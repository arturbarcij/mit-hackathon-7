// End to end in Node: the 12 bundled demo photos through the real engine (classifyLeaf,
// quality gate, sheet gate, preprocess.ts, the shipped public/model/leaf.onnx on
// onnxruntime-web WASM, 1 thread). Writes fixtures/demo_predictions.json and prints a table.
//
// Node has no canvas, so the image module is replaced: native pixels come from sharp (same
// bytes as Chrome for files without EXIF rotation, see PARITY.md) and the 256 px quality copy
// is a sharp resize, which approximates (not equals) the browser canvas. The blur and dark
// numbers are therefore indicative; the sheet gate and the model input are the real ones.
// Skips when the model or the demo photos are missing.
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import sharp from 'sharp';
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';

const APP = resolve(__dirname, '../..');
const PUBLIC = resolve(APP, 'public');
const DEMO = resolve(PUBLIC, 'demo');
const HAVE = existsSync(resolve(PUBLIC, 'model/leaf.onnx')) && existsSync(DEMO);

interface Px {
  data: Uint8ClampedArray;
  width: number;
  height: number;
}
const pixels = vi.hoisted(() => new Map<string, Map<string, Px>>());

vi.mock('../../src/engine/image', async (orig) => {
  const real = await orig<typeof import('../../src/engine/image')>();
  const get = (img: { id: string }, w: number, h: number) => {
    const px = pixels.get(img.id)?.get(`${w}x${h}`);
    if (!px) throw new Error(`no ${w}x${h} pixels prepared for ${img.id}`);
    return px;
  };
  return {
    ...real,
    drawToRgba: (img: { id: string }, w: number, h: number) => get(img, w, h),
    readNativeRgba: (img: { id: string; width: number; height: number }) => get(img, img.width, img.height),
  };
});

// The engine imports 'onnxruntime-web/wasm' and loads '/model/leaf.onnx' by URL with wasmPaths '/ort/'.
// In Node use the package's own WASM files and read the model from public/.
vi.mock('onnxruntime-web/wasm', async () => {
  const real = await import('onnxruntime-web');
  real.env.wasm.numThreads = 1;
  return {
    ...real,
    env: { wasm: {} },
    InferenceSession: {
      create: (url: string, opts: unknown) =>
        real.InferenceSession.create(readFileSync(resolve(PUBLIC, url.replace(/^\//, ''))), opts as never),
    },
  };
});

import { classifyLeaf, _resetModelForTests } from '../../src/engine/model';
import { sheetGate } from '../../src/engine/gate';
import { QUALITY_SIDE } from '../../src/engine/quality';

const PY_PATH = resolve(__dirname, 'fixtures/demo_python_ort.json');
const PY_ORT: { model_version: string; probs: Record<string, Record<string, number>> } | null = existsSync(PY_PATH)
  ? JSON.parse(readFileSync(PY_PATH, 'utf8'))
  : null;
const files = HAVE ? readdirSync(DEMO).filter((f) => f.endsWith('.jpg')).sort() : [];
const rows: Record<string, unknown>[] = [];

async function prepare(file: string) {
  const path = resolve(DEMO, file);
  const nat = await sharp(path).removeAlpha().ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const width = nat.info.width;
  const height = nat.info.height;
  const map = new Map<string, Px>();
  map.set(`${width}x${height}`, { data: new Uint8ClampedArray(nat.data), width, height });
  // Same size rule as checkQuality.
  const scale = QUALITY_SIDE / Math.max(width, height, 1);
  const qw = Math.max(1, Math.round(width * scale));
  const qh = Math.max(1, Math.round(height * scale));
  const q = await sharp(path).resize(qw, qh, { fit: 'fill' }).removeAlpha().ensureAlpha().raw().toBuffer();
  map.set(`${qw}x${qh}`, { data: new Uint8ClampedArray(q), width: qw, height: qh });
  pixels.set(file, map);
  return { id: file, width, height } as unknown as ImageBitmap;
}

describe.skipIf(!HAVE)('demo photos through the real model', () => {
  beforeAll(() => {
    vi.stubGlobal('fetch', async (url: string) => {
      const p = resolve(PUBLIC, String(url).replace(/^\//, ''));
      if (!existsSync(p)) return new Response('not found', { status: 404 });
      return new Response(readFileSync(p), { status: 200, headers: { 'content-type': 'application/json' } });
    });
    _resetModelForTests();
  });

  afterAll(() => {
    if (rows.length === 0) return;
    const spec = JSON.parse(readFileSync(resolve(PUBLIC, 'model/model.json'), 'utf8'));
    const out = {
      note:
        'Node end-to-end run of classifyLeaf on public/demo with the shipped leaf.onnx (onnxruntime-web WASM, 1 thread). ' +
        'gated = default path (quality + sheet gate). model_* = same photo with { sheetGate: false }. ' +
        'Quality copy resized with sharp, not a browser canvas, so blur/brightness are indicative. ' +
        'Demo labels are source hints, not verified by an agronomist.',
      model: { version: spec.version, threshold: spec.threshold, temperature: spec.temperature, quantization: spec.quantization },
      generated_by: 'app/tests/engine/demo.e2e.test.ts',
      rows,
    };
    writeFileSync(resolve(__dirname, 'fixtures/demo_predictions.json'), JSON.stringify(out, null, 1) + '\n');
    console.table(rows);
  });

  it.each(files)('%s', async (file) => {
    const img = await prepare(file);
    const nat = pixels.get(file)!.get(`${(img as unknown as Px).width}x${(img as unknown as Px).height}`)!;
    const gate = sheetGate(nat.data, nat.width, nat.height);
    const gated = await classifyLeaf(img);
    const raw = await classifyLeaf(img, { sheetGate: false });
    expect(raw.modelVersion).not.toBe('mock');
    // A photo that fails any gate is never forced into a class.
    if (!gated.quality.ok) expect(gated).toMatchObject({ label: 'unsure', abstained: true, confidence: 0 });
    const top = Object.entries(raw.probs).sort((a, b) => b[1] - a[1]);
    // Cross-check against Python onnxruntime on the same file (scripts/make_demo_python_ort.py).
    const py = PY_ORT?.model_version === raw.modelVersion ? PY_ORT.probs[file] : undefined;
    let pyDiff: number | null = null;
    if (py) {
      pyDiff = Math.max(...Object.keys(py).map((k) => Math.abs(py[k] - raw.probs[k as keyof typeof raw.probs])));
      const pyTop = Object.entries(py).sort((a, b) => b[1] - a[1])[0][0];
      expect(top[0][0]).toBe(pyTop);
      expect(pyDiff).toBeLessThanOrEqual(0.02);
    }
    rows.push({
      file,
      hint: file.replace(/^sample\d+_|\.jpg$/g, ''),
      gated_label: gated.label,
      gated_reason: gated.quality.ok ? null : gated.quality.reason,
      sheet_ok: gate.ok,
      sheet_detail: gate.detail ?? null,
      paper: gate.paper,
      edge: gate.edge,
      leaf: gate.leaf,
      model_quality_ok: raw.quality.ok,
      model_quality_reason: raw.quality.reason ?? null,
      model_label: raw.label,
      model_top: top[0][0],
      model_confidence: +raw.confidence.toFixed(4),
      model_abstained: raw.abstained,
      python_ort_max_prob_diff: pyDiff === null ? null : +pyDiff.toFixed(5),
      blur: +raw.quality.blur.toFixed(1),
      brightness: +raw.quality.brightness.toFixed(3),
    });
  });
});
