// Sheet gate: TypeScript port against kb/edge/sheet_gate.py on the same images.
// python_gate.json is written by Python (Pillow) from the demo photos, the ml parity samples
// and the synthetic fixtures in fixtures/gate/. Images are decoded here with sharp (no rotation,
// like PIL.Image.open). Pass/fail and the failing test must match; fractions within 0.03.
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import sharp from 'sharp';
import { describe, expect, it } from 'vitest';
import { sheetGate, thumbnailSize } from '../../src/engine/gate';

const APP = resolve(__dirname, '../..');
const PY = JSON.parse(readFileSync(resolve(__dirname, 'fixtures/gate/python_gate.json'), 'utf8')) as {
  results: Record<string, { ok: boolean; reason: string | null; paper: number; edge_touch: number; leaf: number; size: [number, number] }>;
};

async function rgbaOf(path: string) {
  const { data, info } = await sharp(path).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data: new Uint8ClampedArray(data.buffer, data.byteOffset, data.length), width: info.width, height: info.height };
}

describe('thumbnailSize matches PIL Image.thumbnail((256, 256))', () => {
  it.each([
    [640, 480, 256, 192],
    [480, 640, 192, 256],
    [640, 360, 256, 144],
    [427, 640, 171, 256],
    [640, 427, 256, 171],
    [113, 256, 113, 256],
    [128, 128, 128, 128],
    [4000, 3000, 256, 192],
    [4032, 3024, 256, 192],
    [3000, 4000, 192, 256],
    [1080, 1920, 144, 256],
  ])('%i x %i -> %i x %i', (w, h, tw, th) => {
    expect(thumbnailSize(w, h)).toEqual({ width: tw, height: th });
  });
});

describe('sheetGate equals sheet_gate.py', () => {
  const entries = Object.entries(PY.results).filter(([p]) => existsSync(resolve(APP, p)));
  it('has at least 20 reference images', () => expect(entries.length).toBeGreaterThanOrEqual(20));
  it.each(entries)('%s', async (path, py) => {
    const { data, width, height } = await rgbaOf(resolve(APP, path));
    expect([width, height]).toEqual(py.size);
    const ts = sheetGate(data, width, height);
    expect(ts.ok).toBe(py.ok);
    expect(ts.detail ?? null).toBe(py.reason);
    expect(ts.reason ?? null).toBe(py.ok ? null : 'not_on_page');
    expect(Math.abs(ts.paper - py.paper)).toBeLessThanOrEqual(0.03);
    expect(Math.abs(ts.edge - py.edge_touch)).toBeLessThanOrEqual(0.03);
    expect(Math.abs(ts.leaf - py.leaf)).toBeLessThanOrEqual(0.03);
  });
  it('covers both outcomes and every failure kind', () => {
    const vals = Object.values(PY.results);
    expect(vals.some((v) => v.ok)).toBe(true);
    for (const r of ['no_page', 'leaf_cut_off', 'leaf_too_small']) expect(vals.some((v) => v.reason === r), r).toBe(true);
  });
});

describe('sheetGate on bad input', () => {
  it('never throws and fails empty or short buffers as not_on_page', () => {
    expect(sheetGate(new Uint8ClampedArray(0), 0, 0)).toMatchObject({ ok: false, reason: 'not_on_page' });
    expect(sheetGate(new Uint8ClampedArray(10), 4, 4)).toMatchObject({ ok: false, reason: 'not_on_page' });
    expect(sheetGate(null as unknown as Uint8ClampedArray, 10, 10)).toMatchObject({ ok: false, reason: 'not_on_page' });
  });
});
