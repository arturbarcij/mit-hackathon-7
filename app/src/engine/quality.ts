import { drawRegion } from './canvas';
import type { QualityResult } from './types';

/*
 * Thresholds, set 2026-10-03 and tuned on real photos with tests/eval/quality.mjs:
 *   BRACOL (Brazil, 1,401 smartphone photos of single leaves on a white background, CC BY 4.0), and
 *   the Uganda set (3,322 close-up leaf crops, 256 px, includes genuinely soft and dark frames, CC BY 4.0).
 * Blur is synthetic on top of those photos (Gaussian, in pixels of a 1600 px wide image). There is still
 * no set of real out-of-focus phone photos of leaves on a sheet; add one when we have it.
 *
 *   brightness = mean luma (0 to 255) of a greyscale copy with its longer side at 256 px.
 *                Original BRACOL photos: 5th percentile 139, median 163. Uganda: 5th percentile 81, median 145.
 *   blur       = blur extent from the re-blur method (Crete et al. 2007), 0 sharp to 1 blurry, on the same copy.
 *                It compares neighbour-pixel differences before and after blurring the image again, so it does
 *                not depend on exposure or on how much texture the leaf has. A raw Laplacian variance failed
 *                that: 28% of the Uganda close-ups of smooth healthy leaves scored as blurry.
 *                Original photos: BRACOL 95th percentile 0.47, Uganda 95th percentile 0.56.
 *                Gaussian blur of sigma 0.5 / 1 / 2 px at 256 px (4 / 8 / 16 px at 1600 px): BRACOL median
 *                0.48 / 0.60 / 0.76. BLUR_MAX 0.60 keeps 95% or more of the original photos and rejects blur
 *                of about 1 px at 256 px (8 px at 1600 px) and above.
 */
export const BLUR_MAX = 0.6;
export const BRIGHTNESS_MIN = 45;
export const MIN_SIDE = 224;
export const ANALYSIS_SIDE = 256;
const REBLUR_WINDOW = 9;

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

/** Moving average of the given odd window along one axis, with reflected edges. */
function movingAverage(src: Float32Array, width: number, height: number, window: number, axis: 'x' | 'y'): Float32Array {
  const out = new Float32Array(src.length);
  const half = (window - 1) / 2;
  const len = axis === 'x' ? width : height;
  const lines = axis === 'x' ? height : width;
  const reflect = (i: number) => {
    if (len === 1) return 0;
    const period = 2 * len - 2;
    let k = ((i % period) + period) % period;
    if (k >= len) k = period - k;
    return k;
  };
  for (let line = 0; line < lines; line++) {
    for (let i = 0; i < len; i++) {
      let sum = 0;
      for (let d = -half; d <= half; d++) {
        const j = reflect(i + d);
        sum += axis === 'x' ? src[line * width + j] : src[j * width + line];
      }
      const v = sum / window;
      if (axis === 'x') out[line * width + i] = v;
      else out[i * width + line] = v;
    }
  }
  return out;
}

/**
 * Blur extent from 0 (sharp) to 1 (blurry), after Crete et al. 2007 ("The blur effect"). Blur the image again;
 * a sharp image loses many neighbour differences, an already blurry one loses few.
 */
export function blurExtent(grey: Float32Array, width: number, height: number): number {
  if (width < 3 || height < 3) return 1;
  const bx = movingAverage(grey, width, height, REBLUR_WINDOW, 'x');
  const by = movingAverage(grey, width, height, REBLUR_WINDOW, 'y');
  let origH = 0, origV = 0, lostH = 0, lostV = 0;
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = y * width + x;
      if (x + 1 < width) {
        const d = Math.abs(grey[i + 1] - grey[i]);
        origH += d;
        lostH += Math.max(0, d - Math.abs(bx[i + 1] - bx[i]));
      }
      if (y + 1 < height) {
        const d = Math.abs(grey[i + width] - grey[i]);
        origV += d;
        lostV += Math.max(0, d - Math.abs(by[i + width] - by[i]));
      }
    }
  }
  if (origH === 0 || origV === 0) return 1;
  return Math.max((origH - lostH) / origH, (origV - lostV) / origV);
}

export function assessQuality(
  grey: Float32Array,
  width: number,
  height: number,
  originalWidth: number,
  originalHeight: number,
): QualityResult {
  const brightness = meanOf(grey);
  const blur = blurExtent(grey, width, height);
  if (Math.min(originalWidth, originalHeight) < MIN_SIDE) {
    return { ok: false, reason: 'too_small', blur, brightness };
  }
  if (brightness < BRIGHTNESS_MIN) return { ok: false, reason: 'dark', blur, brightness };
  if (blur > BLUR_MAX) return { ok: false, reason: 'blurry', blur, brightness };
  return { ok: true, blur, brightness };
}

export function checkQuality(img: ImageBitmap): QualityResult {
  const scale = Math.min(1, ANALYSIS_SIDE / Math.max(img.width, img.height));
  const w = Math.max(1, Math.round(img.width * scale));
  const h = Math.max(1, Math.round(img.height * scale));
  const data = drawRegion(img, 0, 0, img.width, img.height, w, h);
  return assessQuality(lumaFromRgba(data.data), w, h, img.width, img.height);
}
