import { afterEach, describe, expect, it, vi } from 'vitest';
import { checkQuality, judgeQuality, measureGray, MIN_BLUR, MIN_BRIGHTNESS, MIN_SIDE } from '../../src/engine/quality';

function checkerboard(w: number, h: number, cell: number): Float32Array {
  const g = new Float32Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) g[y * w + x] = ((Math.floor(x / cell) + Math.floor(y / cell)) % 2) * 255;
  return g;
}

function boxBlur(g: Float32Array, w: number, h: number, r: number): Float32Array {
  const out = new Float32Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      let sum = 0;
      let n = 0;
      for (let dy = -r; dy <= r; dy++) {
        for (let dx = -r; dx <= r; dx++) {
          const yy = y + dy;
          const xx = x + dx;
          if (yy >= 0 && yy < h && xx >= 0 && xx < w) {
            sum += g[yy * w + xx];
            n += 1;
          }
        }
      }
      out[y * w + x] = sum / n;
    }
  }
  return out;
}

describe('measureGray', () => {
  it('scores a sharp checkerboard far above its box-blurred copy', () => {
    const sharp = checkerboard(64, 64, 8);
    const sharpBlur = measureGray(sharp, 64, 64).blur;
    const softBlur = measureGray(boxBlur(sharp, 64, 64, 3), 64, 64).blur;
    expect(sharpBlur).toBeGreaterThan(MIN_BLUR);
    expect(sharpBlur).toBeGreaterThan(10 * softBlur);
  });

  it('gives low brightness for a dark image and about 0.5 for a checkerboard', () => {
    const dark = new Float32Array(32 * 32).fill(20);
    expect(measureGray(dark, 32, 32).brightness).toBeCloseTo(20 / 255, 5);
    expect(measureGray(dark, 32, 32).brightness).toBeLessThan(MIN_BRIGHTNESS);
    expect(measureGray(checkerboard(32, 32, 4), 32, 32).brightness).toBeCloseTo(0.5, 5);
  });

  it('gives zero blur for a flat image', () => {
    expect(measureGray(new Float32Array(16 * 16).fill(128), 16, 16).blur).toBe(0);
  });
});

describe('judgeQuality', () => {
  it('checks too_small, then dark, then blurry', () => {
    expect(judgeQuality(0, 0, MIN_SIDE - 1).reason).toBe('too_small');
    expect(judgeQuality(0, 0, MIN_SIDE).reason).toBe('dark');
    expect(judgeQuality(0, MIN_BRIGHTNESS, MIN_SIDE).reason).toBe('blurry');
    expect(judgeQuality(MIN_BLUR, MIN_BRIGHTNESS, MIN_SIDE)).toEqual({ ok: true, blur: MIN_BLUR, brightness: MIN_BRIGHTNESS });
  });

  it('keeps the measured numbers on failure', () => {
    expect(judgeQuality(12, 0.4, 500)).toEqual({ ok: false, reason: 'blurry', blur: 12, brightness: 0.4 });
  });
});

describe('checkQuality without a canvas (SSR)', () => {
  afterEach(() => vi.restoreAllMocks());

  it('passes with NaN scores and warns', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const img = { width: 640, height: 480 } as unknown as ImageBitmap;
    const q = checkQuality(img);
    expect(q.ok).toBe(true);
    expect(q.reason).toBeUndefined();
    expect(Number.isNaN(q.blur)).toBe(true);
    expect(Number.isNaN(q.brightness)).toBe(true);
    expect(warn).toHaveBeenCalledOnce();
  });
});
