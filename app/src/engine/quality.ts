// Photo quality gate: runs before the model so a blurry, dark or tiny photo is
// sent back for a retake instead of being classified.
import { sheetGate } from './gate';
import { drawToRgba, imageSize, NoCanvasError } from './image';
import type { ClassifyOptions, ImageInput, QualityResult } from './types';

// provisional, set on synthetic images 3 Oct 2026; tune on 10 sharp and 10 blurry phone photos (E3)
export const MIN_SIDE = 224; // px, shorter side of the original photo
export const MIN_BRIGHTNESS = 0.18; // mean luma, 0 to 1
export const MIN_BLUR = 60; // variance of the 4-neighbour Laplacian on a 0 to 255 grey copy
/** The grey copy used for blur and brightness has this longer side. */
export const QUALITY_SIDE = 256;

/** Rec. 601 luma, 0 to 255, from RGBA bytes. */
export function toGray(rgba: ArrayLike<number>, w: number, h: number): Float32Array {
  const gray = new Float32Array(w * h);
  for (let i = 0; i < w * h; i++) {
    gray[i] = 0.299 * rgba[i * 4] + 0.587 * rgba[i * 4 + 1] + 0.114 * rgba[i * 4 + 2];
  }
  return gray;
}

/** blur = variance of the 4-neighbour Laplacian (interior pixels); brightness = mean luma 0 to 1. */
export function measureGray(gray: ArrayLike<number>, w: number, h: number): { blur: number; brightness: number } {
  let sum = 0;
  for (let i = 0; i < w * h; i++) sum += gray[i];
  const brightness = w * h > 0 ? sum / (w * h) / 255 : 0;

  let n = 0;
  let mean = 0;
  let m2 = 0;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x;
      const lap = gray[i - w] + gray[i + w] + gray[i - 1] + gray[i + 1] - 4 * gray[i];
      // Welford's running variance keeps this numerically stable.
      n += 1;
      const d = lap - mean;
      mean += d / n;
      m2 += d * (lap - mean);
    }
  }
  const blur = n > 0 ? m2 / n : 0;
  return { blur, brightness };
}

/** Checks in order: too_small, dark, blurry. */
export function judgeQuality(blur: number, brightness: number, minSide: number): QualityResult {
  if (minSide < MIN_SIDE) return { ok: false, reason: 'too_small', blur, brightness };
  if (brightness < MIN_BRIGHTNESS) return { ok: false, reason: 'dark', blur, brightness };
  if (blur < MIN_BLUR) return { ok: false, reason: 'blurry', blur, brightness };
  return { ok: true, blur, brightness };
}

/**
 * Checks in order: too_small, dark, blurry, then the sheet gate (not_on_page) on the same
 * 256 px copy. A photo that fails any check is never classified.
 */
export function checkQuality(img: ImageInput, opts: ClassifyOptions = {}): QualityResult {
  const { width, height } = imageSize(img);
  const longer = Math.max(width, height, 1);
  const scale = QUALITY_SIDE / longer;
  const w = Math.max(1, Math.round(width * scale));
  const h = Math.max(1, Math.round(height * scale));
  let rgba;
  try {
    rgba = drawToRgba(img, w, h);
  } catch (err) {
    if (!(err instanceof NoCanvasError)) throw err;
    // SSR or a browser without canvas: skip the gate; model abstention still applies.
    console.warn('[quality] no canvas, skipping the quality gate:', err.message);
    return { ok: true, blur: NaN, brightness: NaN };
  }
  const { blur, brightness } = measureGray(toGray(rgba.data, w, h), w, h);
  const q = judgeQuality(blur, brightness, Math.min(width, height));
  if (!q.ok || opts.sheetGate === false) return q;
  return withSheetGate(q, rgba.data, w, h);
}

/** Adds the sheet gate to a passing quality result. Pure. */
export function withSheetGate(q: QualityResult, rgba: ArrayLike<number>, w: number, h: number): QualityResult {
  const g = sheetGate(rgba, w, h);
  const sheet = { paper: g.paper, edge: g.edge, leaf: g.leaf, ...(g.detail ? { detail: g.detail } : {}) };
  if (!g.ok) return { ok: false, reason: 'not_on_page', blur: q.blur, brightness: q.brightness, sheet };
  return { ...q, sheet };
}
