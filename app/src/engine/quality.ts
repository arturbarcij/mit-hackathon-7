import { drawRegion } from './canvas';
import type { QualityResult } from './types';

/*
 * Thresholds, set 2026-10-03. Tuned on synthetic leaves on a white sheet (4000 x 3000, Gaussian blur
 * and dimming applied), NOT yet on real phone photos. To re-tune: run checkQuality on 10 sharp and
 * 10 blurry photos of leaves on a plain page, print `blur` and `brightness`, and place the thresholds
 * between the two groups. Record the numbers here.
 *
 *   brightness = mean luma (0 to 255) of a greyscale copy with its longer side at 256 px.
 *   blur       = variance of the Laplacian of that copy divided by brightness squared.
 *                Dividing makes it independent of exposure: a sharp but dim photo has a small raw
 *                variance, which a fixed raw threshold would wrongly call blurry.
 *                Synthetic results: sharp 0.0048 at every exposure from 0.12x to 1x; blur sigma 4 px
 *                0.0035, 8 px 0.0018, 15 px 0.0005, 25 px 0.0001 (sigma in pixels of a 4000 px wide photo).
 *                Higher means sharper. The field name stays `blur` to match CONTRACTS.md.
 */
export const BLUR_MIN = 0.0012;
export const BRIGHTNESS_MIN = 45;
export const MIN_SIDE = 224;
export const ANALYSIS_SIDE = 256;

export function lumaFromRgba(rgba: Uint8ClampedArray | Uint8Array): Float32Array {
  const n = rgba.length / 4;
  const grey = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const o = i * 4;
    grey[i] = 0.299 * rgba[o] + 0.587 * rgba[o + 1] + 0.114 * rgba[o + 2];
  }
  return grey;
}

export function meanOf(values: Float32Array): number {
  if (values.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < values.length; i++) sum += values[i];
  return sum / values.length;
}

/** Variance of the 4-neighbour Laplacian over the interior pixels. Higher means sharper. */
export function laplacianVariance(grey: Float32Array, width: number, height: number): number {
  if (width < 3 || height < 3) return 0;
  let sum = 0;
  let sumSq = 0;
  let count = 0;
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const i = y * width + x;
      const v = grey[i - 1] + grey[i + 1] + grey[i - width] + grey[i + width] - 4 * grey[i];
      sum += v;
      sumSq += v * v;
      count += 1;
    }
  }
  const mean = sum / count;
  return sumSq / count - mean * mean;
}

export function assessQuality(
  grey: Float32Array,
  width: number,
  height: number,
  originalWidth: number,
  originalHeight: number,
): QualityResult {
  const brightness = meanOf(grey);
  const blur = laplacianVariance(grey, width, height) / Math.max(brightness, 1) ** 2;
  if (Math.min(originalWidth, originalHeight) < MIN_SIDE) {
    return { ok: false, reason: 'too_small', blur, brightness };
  }
  if (brightness < BRIGHTNESS_MIN) return { ok: false, reason: 'dark', blur, brightness };
  if (blur < BLUR_MIN) return { ok: false, reason: 'blurry', blur, brightness };
  return { ok: true, blur, brightness };
}

export function checkQuality(img: ImageBitmap): QualityResult {
  const scale = Math.min(1, ANALYSIS_SIDE / Math.max(img.width, img.height));
  const w = Math.max(1, Math.round(img.width * scale));
  const h = Math.max(1, Math.round(img.height * scale));
  const data = drawRegion(img, 0, 0, img.width, img.height, w, h);
  return assessQuality(lumaFromRgba(data.data), w, h, img.width, img.height);
}
