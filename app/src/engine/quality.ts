import type { QualityResult } from './types.ts';

// UNCALIBRATED assumptions dated 2026-10-04.
// blur < 40 means blurry. brightness < 40 means dark.
// These cut-offs are not tuned on phone photos yet.
const BLUR_MIN = 40;
const BRIGHTNESS_MIN = 40;
const MIN_SIDE = 64;
const LONG_SIDE = 256;

export function laplacianVariance(gray: Float32Array, width: number, height: number): number {
  if (width < 1 || height < 1 || gray.length < width * height) return 0;
  const count = width * height;
  let sum = 0;
  const response = new Float32Array(count);
  for (let y = 0; y < height; y++) {
    const upY = y > 0 ? y - 1 : 0;
    const downY = y < height - 1 ? y + 1 : y;
    for (let x = 0; x < width; x++) {
      const leftX = x > 0 ? x - 1 : 0;
      const rightX = x < width - 1 ? x + 1 : x;
      const centre = gray[y * width + x];
      const lap =
        gray[upY * width + x] +
        gray[downY * width + x] +
        gray[y * width + leftX] +
        gray[y * width + rightX] -
        4 * centre;
      response[y * width + x] = lap;
      sum += lap;
    }
  }
  const mean = sum / count;
  let square = 0;
  for (let i = 0; i < count; i++) {
    const delta = response[i] - mean;
    square += delta * delta;
  }
  return square / count;
}

export function checkQualityFromGray(
  gray: Float32Array,
  width: number,
  height: number,
  brightness: number,
): QualityResult {
  const blur = laplacianVariance(gray, width, height);
  if (width < MIN_SIDE || height < MIN_SIDE) {
    return { ok: false, reason: 'too_small', blur, brightness };
  }
  if (brightness < BRIGHTNESS_MIN) {
    return { ok: false, reason: 'dark', blur, brightness };
  }
  if (blur < BLUR_MIN) {
    return { ok: false, reason: 'blurry', blur, brightness };
  }
  return { ok: true, blur, brightness };
}

function rgbaToGray(data: Uint8ClampedArray, width: number, height: number): Float32Array {
  const gray = new Float32Array(width * height);
  for (let i = 0, pixel = 0; i < data.length; i += 4, pixel += 1) {
    gray[pixel] = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
  }
  return gray;
}

function fittedSize(width: number, height: number): { width: number; height: number } {
  const longSide = Math.max(width, height);
  const scale = LONG_SIDE / longSide;
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  };
}

function meanLuma(gray: Float32Array): number {
  if (gray.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < gray.length; i++) sum += gray[i];
  return sum / gray.length;
}

function grayCopy(img: ImageBitmap): { gray: Float32Array; width: number; height: number } {
  const size = fittedSize(img.width, img.height);
  if (typeof OffscreenCanvas !== 'undefined') {
    const canvas = new OffscreenCanvas(size.width, size.height);
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Canvas is not available for the quality check');
    context.drawImage(img, 0, 0, size.width, size.height);
    const pixels = context.getImageData(0, 0, size.width, size.height).data;
    return { gray: rgbaToGray(pixels, size.width, size.height), width: size.width, height: size.height };
  }
  if (typeof document === 'undefined') {
    throw new Error('Canvas is not available for the quality check');
  }
  const canvas = document.createElement('canvas');
  canvas.width = size.width;
  canvas.height = size.height;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Canvas is not available for the quality check');
  context.drawImage(img, 0, 0, size.width, size.height);
  const pixels = context.getImageData(0, 0, size.width, size.height).data;
  return { gray: rgbaToGray(pixels, size.width, size.height), width: size.width, height: size.height };
}

export function checkQuality(img: ImageBitmap): QualityResult {
  if (img.width < MIN_SIDE || img.height < MIN_SIDE) {
    return { ok: false, reason: 'too_small', blur: 0, brightness: 0 };
  }
  const copy = grayCopy(img);
  const brightness = meanLuma(copy.gray);
  const blur = laplacianVariance(copy.gray, copy.width, copy.height);
  if (brightness < BRIGHTNESS_MIN) return { ok: false, reason: 'dark', blur, brightness };
  if (blur < BLUR_MIN) return { ok: false, reason: 'blurry', blur, brightness };
  return { ok: true, blur, brightness };
}
