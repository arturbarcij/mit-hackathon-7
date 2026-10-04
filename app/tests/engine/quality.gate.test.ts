// The sheet gate inside checkQuality and classifyLeaf: a photo not on a page fails quality
// with reason 'not_on_page', is never classified, and counts as unsure in the plot.
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ImageInput } from '../../src/engine/types';

// Synthetic 256 x 192 images stand in for the canvas copy.
const W = 256;
const H = 192;
function img(kind: 'page_leaf' | 'skin' | 'plain_page'): Uint8ClampedArray {
  const d = new Uint8ClampedArray(W * H * 4);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4;
      const inLeaf = ((x - 128) / 60) ** 2 + ((y - 96) / 40) ** 2 <= 1;
      // Mild texture so the blur check passes.
      const t = ((x * 7 + y * 13) % 5) * 12;
      let rgb: number[];
      if (kind === 'skin') rgb = [200 + t / 3, 145, 115];
      else if (kind === 'page_leaf' && inLeaf) rgb = [50, 110 + t, 40];
      else rgb = [235 - t, 233 - t, 228 - t];
      d.set([...rgb, 255], i);
    }
  return d;
}
const current = vi.hoisted(() => ({ kind: 'page_leaf' as 'page_leaf' | 'skin' | 'plain_page' }));
vi.mock('../../src/engine/image', async (orig) => ({
  ...(await orig<typeof import('../../src/engine/image')>()),
  imageSize: () => ({ width: 1024, height: 768 }),
  drawToRgba: (_img: unknown, w: number, h: number) => ({ data: img(current.kind).slice(0, w * h * 4), width: w, height: h }),
}));

import { checkQuality, withSheetGate } from '../../src/engine/quality';
import { classifyLeaf, _resetModelForTests } from '../../src/engine/model';
import { summarisePlot } from '../../src/engine/plot';

const photo = {} as ImageInput;

describe('checkQuality with the sheet gate', () => {
  beforeEach(() => {
    current.kind = 'page_leaf';
    vi.stubEnv('VITE_USE_MOCK_MODEL', 'true');
    _resetModelForTests();
  });

  it('passes a leaf on a page and reports the sheet numbers', () => {
    const q = checkQuality(photo);
    expect(q.ok).toBe(true);
    expect(q.sheet?.paper).toBeGreaterThan(0.3);
    expect(q.sheet?.leaf).toBeGreaterThan(0.08);
  });

  it('fails skin as not_on_page (no_page) and a plain page as not_on_page (leaf_too_small)', () => {
    current.kind = 'skin';
    expect(checkQuality(photo)).toMatchObject({ ok: false, reason: 'not_on_page', sheet: { detail: 'no_page' } });
    current.kind = 'plain_page';
    expect(checkQuality(photo)).toMatchObject({ ok: false, reason: 'not_on_page', sheet: { detail: 'leaf_too_small' } });
  });

  it('sheetGate: false skips only the sheet gate', () => {
    current.kind = 'skin';
    const q = checkQuality(photo, { sheetGate: false });
    expect(q.ok).toBe(true);
    expect(q.sheet).toBeUndefined();
  });

  it('classifyLeaf never forces a not-on-page photo into a class; the plot counts it as unsure', async () => {
    current.kind = 'skin';
    const r = await classifyLeaf(photo);
    expect(r).toMatchObject({ label: 'unsure', abstained: true, confidence: 0, quality: { ok: false, reason: 'not_on_page' } });
    expect(Object.values(r.probs).every((p) => p === 0)).toBe(true);
    const s = summarisePlot([r]);
    expect(s.uncertain).toBe(1);
    expect(s.affected).toBe(0);
  });

  it('withSheetGate keeps blur and brightness', () => {
    const q = withSheetGate({ ok: true, blur: 99, brightness: 0.7 }, img('skin'), W, H);
    expect(q).toMatchObject({ ok: false, reason: 'not_on_page', blur: 99, brightness: 0.7 });
  });
});
