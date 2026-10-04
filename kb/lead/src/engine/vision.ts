// Photo quality gate and the colour-heuristic MOCK classifier.
// The real classifier is the int8 ONNX model from the ml lane (onnxruntime-web); until it is wired in,
// classifyLeaf uses this transparent colour rule and the UI shows the "mock model" badge.
// Thresholds are assumptions to be calibrated by the ml lane on the validation split.
import type { Label, LeafResult, QualityResult } from "./types";

export const QUALITY = {
  /** Shortest side of the original photo in pixels. */
  minSide: 240,
  /** Mean luminance 0 to 1 below which a photo is "dark". Assumption. */
  minBrightness: 0.18,
  /** Variance of the Laplacian on the 512 px grey image below which a photo is "blurry". Assumption. */
  minBlur: 60,
  /** Analysis size (longest side). */
  analyseSide: 512,
};

export const MOCK_VERSION = "mock-colour-0.1";
/** Top-class probability below which a leaf is "unsure" (abstain). Assumption until calibrated. */
export const ABSTAIN_BELOW = 0.6;

export interface PixelStats {
  width: number;
  height: number;
  brightness: number;
  blur: number;
  /** Share of all pixels. */
  green: number;
  orange: number;
  brown: number;
  paper: number;
}

/** Pure function over RGBA pixels, so it can be unit tested without a browser. */
export function pixelStats(data: Uint8ClampedArray, width: number, height: number): PixelStats {
  const n = width * height;
  const grey = new Float32Array(n);
  let sum = 0, green = 0, orange = 0, brown = 0, paper = 0;
  for (let i = 0; i < n; i++) {
    const r = data[i * 4] / 255, g = data[i * 4 + 1] / 255, b = data[i * 4 + 2] / 255;
    const y = 0.299 * r + 0.587 * g + 0.114 * b;
    grey[i] = y * 255;
    sum += y;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
    const s = max === 0 ? 0 : d / max, v = max;
    let h = 0;
    if (d > 0) {
      if (max === r) h = 60 * (((g - b) / d) % 6);
      else if (max === g) h = 60 * ((b - r) / d + 2);
      else h = 60 * ((r - g) / d + 4);
    }
    if (h < 0) h += 360;
    if (v > 0.75 && s < 0.18) paper += 1;
    else if (s > 0.25 && v > 0.15 && h >= 65 && h <= 170) green += 1;
    else if (s > 0.45 && v > 0.45 && h >= 18 && h < 50) orange += 1;
    else if (s > 0.3 && v > 0.12 && v <= 0.6 && (h < 40 || h > 340)) brown += 1;
  }
  let lapSum = 0, lapSq = 0, m = 0;
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const i = y * width + x;
      const lap = grey[i - 1] + grey[i + 1] + grey[i - width] + grey[i + width] - 4 * grey[i];
      lapSum += lap; lapSq += lap * lap; m += 1;
    }
  }
  const mean = m ? lapSum / m : 0;
  return {
    width, height,
    brightness: n ? sum / n : 0,
    blur: m ? lapSq / m - mean * mean : 0,
    green: green / n, orange: orange / n, brown: brown / n, paper: paper / n,
  };
}

export function qualityFrom(stats: PixelStats, originalWidth: number, originalHeight: number): QualityResult {
  const base = { blur: Math.round(stats.blur), brightness: Number(stats.brightness.toFixed(3)) };
  if (Math.min(originalWidth, originalHeight) < QUALITY.minSide) return { ok: false, reason: "too_small", ...base };
  if (stats.brightness < QUALITY.minBrightness) return { ok: false, reason: "dark", ...base };
  if (stats.blur < QUALITY.minBlur) return { ok: false, reason: "blurry", ...base };
  return { ok: true, ...base };
}

const zero = (): Record<Label, number> => ({ healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 });

/** Transparent colour rule used only while the real model is not loaded. Not a diagnosis. */
export function mockClassify(stats: PixelStats, quality: QualityResult): LeafResult {
  const probs = zero();
  const leafish = stats.green + stats.orange + stats.brown;
  let label: Label;
  let confidence: number;
  if (leafish < 0.12) {
    label = "not_leaf";
    confidence = 0.75;
  } else {
    const rustShare = stats.orange / leafish;
    const brownShare = stats.brown / leafish;
    if (rustShare >= 0.05) {
      label = "rust";
      confidence = Math.min(0.95, 0.62 + rustShare * 2);
    } else if (brownShare >= 0.12) {
      // Brown spots: could be brown eye spot, phoma, miner or old damage. The colour rule cannot tell.
      label = "cercospora";
      confidence = 0.45;
    } else if (rustShare >= 0.02) {
      label = "rust";
      confidence = 0.5;
    } else {
      label = "healthy";
      confidence = Math.min(0.92, 0.6 + (stats.green / leafish) * 0.3);
    }
  }
  const rest = (1 - confidence) / 5;
  for (const l of Object.keys(probs) as Label[]) probs[l] = l === label ? confidence : rest;
  const abstained = !quality.ok || confidence < ABSTAIN_BELOW;
  return {
    label: abstained ? "unsure" : label,
    probs,
    confidence: Number(confidence.toFixed(3)),
    quality,
    abstained,
    modelVersion: MOCK_VERSION,
  };
}

type Drawable = ImageBitmap | HTMLImageElement | HTMLCanvasElement;

/** Downscale to QUALITY.analyseSide and read pixels. Browser only. */
export function readPixels(img: Drawable): { data: Uint8ClampedArray; width: number; height: number } {
  const w0 = "naturalWidth" in img ? img.naturalWidth : img.width;
  const h0 = "naturalHeight" in img ? img.naturalHeight : img.height;
  const scale = Math.min(1, QUALITY.analyseSide / Math.max(w0, h0));
  const width = Math.max(1, Math.round(w0 * scale));
  const height = Math.max(1, Math.round(h0 * scale));
  const canvas: OffscreenCanvas | HTMLCanvasElement =
    typeof OffscreenCanvas !== "undefined" ? new OffscreenCanvas(width, height) : Object.assign(document.createElement("canvas"), { width, height });
  const ctx = canvas.getContext("2d") as OffscreenCanvasRenderingContext2D | CanvasRenderingContext2D | null;
  if (!ctx) throw new Error("2d canvas not available");
  ctx.drawImage(img as CanvasImageSource, 0, 0, width, height);
  return { data: ctx.getImageData(0, 0, width, height).data, width, height };
}

export function analyse(img: Drawable): { stats: PixelStats; quality: QualityResult } {
  const w0 = "naturalWidth" in img ? img.naturalWidth : img.width;
  const h0 = "naturalHeight" in img ? img.naturalHeight : img.height;
  const px = readPixels(img);
  const stats = pixelStats(px.data, px.width, px.height);
  return { stats, quality: qualityFrom(stats, w0, h0) };
}
