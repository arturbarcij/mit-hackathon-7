import { describe, expect, it } from 'vitest';
import { assessQuality, BLUR_MIN, BRIGHTNESS_MIN, laplacianVariance, lumaFromRgba } from '../../src/engine/quality';

function noise(w: number, h: number, level = 128, amp = 100): Float32Array {
  const g = new Float32Array(w * h);
  let seed = 12345;
  for (let i = 0; i < g.length; i++) {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    g[i] = level + ((seed / 2 ** 32) - 0.5) * 2 * amp;
  }
  return g;
}

function boxBlur(src: Float32Array, w: number, h: number, passes: number): Float32Array {
  let cur = src;
  for (let p = 0; p < passes; p++) {
    const out = new Float32Array(cur.length);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let s = 0;
        let c = 0;
        for (let dy = -2; dy <= 2; dy++) {
          for (let dx = -2; dx <= 2; dx++) {
            const xx = x + dx;
            const yy = y + dy;
            if (xx >= 0 && xx < w && yy >= 0 && yy < h) {
              s += cur[yy * w + xx];
              c++;
            }
          }
        }
        out[y * w + x] = s / c;
      }
    }
    cur = out;
  }
  return cur;
}

const W = 256;
const H = 192;

describe('quality gate', () => {
  it('accepts a sharp, well lit image', () => {
    const q = assessQuality(noise(W, H), W, H, 3000, 2250);
    expect(q.ok).toBe(true);
    expect(q.blur).toBeGreaterThan(BLUR_MIN);
  });

  it('rejects a blurred image', () => {
    const q = assessQuality(boxBlur(noise(W, H), W, H, 3), W, H, 3000, 2250);
    expect(q.ok).toBe(false);
    expect(q.reason).toBe('blurry');
  });

  it('rejects a dark image', () => {
    const q = assessQuality(noise(W, H, 15, 14), W, H, 3000, 2250);
    expect(q.ok).toBe(false);
    expect(q.reason).toBe('dark');
    expect(q.brightness).toBeLessThan(BRIGHTNESS_MIN);
  });

  it('rejects a tiny image', () => {
    const q = assessQuality(noise(100, 100), 100, 100, 100, 100);
    expect(q.ok).toBe(false);
    expect(q.reason).toBe('too_small');
  });

  it('measures a flat image as zero blur', () => {
    expect(laplacianVariance(new Float32Array(W * H).fill(100), W, H)).toBe(0);
  });

  it('converts RGBA to luma', () => {
    const grey = lumaFromRgba(new Uint8Array([255, 255, 255, 255, 0, 0, 0, 255]));
    expect(grey[0]).toBeCloseTo(255, 3);
    expect(grey[1]).toBe(0);
  });
});
