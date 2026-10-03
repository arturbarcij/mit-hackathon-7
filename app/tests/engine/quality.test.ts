import { describe, expect, it } from 'vitest';
import { assessQuality, blurExtent, BLUR_MAX, BRIGHTNESS_MIN, lumaFromRgba } from '../../src/engine/quality';

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

/** A grey "sheet" with three dark leaf-shaped ellipses and a midrib, the capture protocol in miniature. */
function leafOnSheet(w: number, h: number, exposure: number): Float32Array {
  const g = new Float32Array(w * h).fill(235 * exposure);
  for (let k = 0; k < 3; k++) {
    const cx = (w * (k + 1)) / 4;
    const cy = h / 2;
    const rx = w / 8;
    const ry = h / 6;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const e = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2;
        if (e <= 1) g[y * w + x] = (Math.abs(y - cy) < 1 ? 170 : 85) * exposure;
      }
    }
  }
  return g;
}

describe('quality gate', () => {
  it('judges sharpness independently of exposure', () => {
    for (const exposure of [1, 0.6, 0.35]) {
      const q = assessQuality(leafOnSheet(W, H, exposure), W, H, 4000, 3000);
      expect(q.reason, `exposure ${exposure}`).toBeUndefined();
    }
    const dimSharp = assessQuality(leafOnSheet(W, H, 0.35), W, H, 4000, 3000);
    const brightSharp = assessQuality(leafOnSheet(W, H, 1), W, H, 4000, 3000);
    expect(Math.abs(dimSharp.blur - brightSharp.blur)).toBeLessThan(0.02);
  });

  it('still rejects a blurred leaf on a sheet', () => {
    const blurred = boxBlur(leafOnSheet(W, H, 1), W, H, 4);
    const q = assessQuality(blurred, W, H, 4000, 3000);
    expect(q.reason).toBe('blurry');
  });

  it('accepts a sharp, well lit image', () => {
    const q = assessQuality(noise(W, H), W, H, 3000, 2250);
    expect(q.ok).toBe(true);
    expect(q.blur).toBeLessThan(BLUR_MAX);
  });

  it('rejects a blurred image', () => {
    const q = assessQuality(boxBlur(noise(W, H), W, H, 8), W, H, 3000, 2250);
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

  it('measures a flat image as fully blurred and tiny buffers as blurred', () => {
    expect(blurExtent(new Float32Array(W * H).fill(100), W, H)).toBe(1);
    expect(blurExtent(new Float32Array(4), 2, 2)).toBe(1);
  });

  it('blur extent rises as an image is blurred more', () => {
    const base = leafOnSheet(W, H, 1);
    const a = blurExtent(base, W, H);
    const b = blurExtent(boxBlur(base, W, H, 1), W, H);
    const c = blurExtent(boxBlur(base, W, H, 3), W, H);
    expect(a).toBeLessThan(b);
    expect(b).toBeLessThan(c);
    expect(a).toBeGreaterThanOrEqual(0);
    expect(c).toBeLessThanOrEqual(1);
  });

  it('does not call a sharp smooth surface with a few veins blurry', () => {
    // Close-up of a healthy leaf: flat green with thin bright lines, like the Uganda crops.
    const g = new Float32Array(W * H).fill(120);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if ((x + y * 0.3) % 24 < 1.5) g[y * W + x] = 190;
    expect(assessQuality(g, W, H, 256, 256).reason).toBeUndefined();
  });

  it('converts RGBA to luma', () => {
    const grey = lumaFromRgba(new Uint8Array([255, 255, 255, 255, 0, 0, 0, 255]));
    expect(grey[0]).toBeCloseTo(255, 3);
    expect(grey[1]).toBe(0);
  });
});
