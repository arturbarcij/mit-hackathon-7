import { describe, expect, it } from 'vitest';
import { checkQualityFromGray, laplacianVariance } from '../../src/engine/quality.ts';

function fill(width: number, height: number, value: number): Float32Array {
  const gray = new Float32Array(width * height);
  gray.fill(value);
  return gray;
}

function checker(width: number, height: number): Float32Array {
  const gray = new Float32Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) gray[y * width + x] = (x + y) % 2 === 0 ? 0 : 255;
  }
  return gray;
}

describe('quality', () => {
  it('gives a flat image a low Laplacian variance and a checker a high one', () => {
    const flat = laplacianVariance(fill(32, 32, 128), 32, 32);
    const busy = laplacianVariance(checker(32, 32), 32, 32);
    expect(flat).toBeLessThan(1);
    expect(busy).toBeGreaterThan(40);
    expect(busy).toBeGreaterThan(flat);
  });

  it('prefers too_small, then dark, then blurry', () => {
    const tiny = checkQualityFromGray(fill(32, 32, 10), 32, 32, 10);
    expect(tiny.ok).toBe(false);
    expect(tiny.reason).toBe('too_small');

    const dark = checkQualityFromGray(fill(64, 64, 200), 64, 64, 10);
    expect(dark.ok).toBe(false);
    expect(dark.reason).toBe('dark');

    const blurry = checkQualityFromGray(fill(64, 64, 128), 64, 64, 128);
    expect(blurry.ok).toBe(false);
    expect(blurry.reason).toBe('blurry');

    const sharp = checkQualityFromGray(checker(64, 64), 64, 64, 128);
    expect(sharp.ok).toBe(true);
    expect(sharp.reason).toBeUndefined();
  });
});
